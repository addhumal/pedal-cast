"""BigQuery ingestion: public source tables into this project's own dataset.

HUMAN ONLY (`make ingest`). Every job carries `maximum_bytes_billed`, because the
source tables are public and large enough that one careless query outspends the
month (docs/architecture.md 10.5).

The full history is ingested, including data after `T_NOW`: training filters to
before it, and the drift job replays what comes after (docs/architecture.md 2).

Grain is per station-hour, not per zone-hour. Zones are a clustering over stations
decided in Week 1 EDA, so keeping the raw layer zone-free means re-zoning is a
feature-layer change and not a re-ingest.
"""

import argparse
from dataclasses import dataclass

import pandas as pd
from google.cloud import bigquery

from src.config import Settings, get_settings
from src.data.schemas import (
    DAILY_WEATHER,
    HOURLY_DEMAND,
    STATIONS,
    assert_hourly_continuity,
)

STATIONS_TABLE = "stations"
HOURLY_DEMAND_TABLE = "hourly_station_demand"
WEATHER_TABLE = "daily_weather"

# Downtown Austin. NOAA station ids are not stable enough to hardcode, so the
# weather query selects by distance from here instead.
_AUSTIN_LAT = 30.2672
_AUSTIN_LON = -97.7431
_WEATHER_RADIUS_M = 30_000

# Austin B-Cycle opened in December 2013; earlier GSOD years hold no trips to join.
_FIRST_WEATHER_YEAR = 2013

# GSOD encodes "no reading" as an out-of-range sentinel rather than NULL. Averaging
# them in shifts a whole day's weather by hundreds of degrees.
_MISSING_TEMP = 9999.9
_MISSING_PRCP = 99.99
_MISSING_WDSP = 999.9

_STATIONS_SQL = """
SELECT
  station_id,
  name,
  status,
  council_district,
  number_of_docks
FROM `{source}`
WHERE station_id IS NOT NULL
"""

# Quiet hours are real observations of zero demand, so they are materialised rather
# than left absent. The grid spans each station's own first-to-last observed hour,
# which avoids inventing history for a station before it opened.
_HOURLY_DEMAND_SQL = """
WITH counts AS (
  SELECT
    start_station_id AS station_id,
    TIMESTAMP_TRUNC(start_time, HOUR) AS hour_ts,
    COUNT(*) AS trip_count
  FROM `{source}`
  WHERE start_time IS NOT NULL
    AND start_station_id IS NOT NULL
  GROUP BY station_id, hour_ts
),
span AS (
  SELECT station_id, MIN(hour_ts) AS first_hour, MAX(hour_ts) AS last_hour
  FROM counts
  GROUP BY station_id
),
grid AS (
  SELECT span.station_id, hour_ts
  FROM span,
  UNNEST(GENERATE_TIMESTAMP_ARRAY(span.first_hour, span.last_hour, INTERVAL 1 HOUR)) AS hour_ts
)
SELECT
  grid.station_id,
  grid.hour_ts,
  IFNULL(counts.trip_count, 0) AS trip_count
FROM grid
LEFT JOIN counts USING (station_id, hour_ts)
"""

# Averaging the stations within the radius rather than taking the nearest one keeps a
# day of readings when a single station reports nothing. It also smooths a localised
# thunderstorm across the city — acceptable at a daily grain, and noted in the README
# limitations alongside the "observed, not forecast" simplification.
_WEATHER_SQL = """
WITH nearby AS (
  SELECT usaf, wban
  FROM `bigquery-public-data.noaa_gsod.stations`
  WHERE lat IS NOT NULL
    AND lon IS NOT NULL
    AND ST_DWITHIN(ST_GEOGPOINT(lon, lat), ST_GEOGPOINT({lon}, {lat}), {radius})
),
daily AS (
  SELECT
    PARSE_DATE('%Y-%m-%d', CONCAT(gsod.year, '-', gsod.mo, '-', gsod.da)) AS weather_date,
    -- GSOD types these columns inconsistently across years (`wdsp` in particular is
    -- STRING in some), and GoogleSQL will not compare a STRING column to a numeric
    -- literal. Casting first makes the sentinel comparison type-agnostic.
    NULLIF(SAFE_CAST(gsod.temp AS FLOAT64), {missing_temp}) AS temp_f,
    NULLIF(SAFE_CAST(gsod.prcp AS FLOAT64), {missing_prcp}) AS precip_inches,
    NULLIF(SAFE_CAST(gsod.wdsp AS FLOAT64), {missing_wdsp}) AS wind_knots
  FROM `bigquery-public-data.noaa_gsod.gsod*` AS gsod
  JOIN nearby ON gsod.stn = nearby.usaf AND gsod.wban = nearby.wban
  WHERE _TABLE_SUFFIX BETWEEN '{first_year}' AND '{last_year}'
)
SELECT
  weather_date,
  ROUND((AVG(temp_f) - 32) * 5 / 9, 2) AS temp_c,
  ROUND(AVG(precip_inches) * 25.4, 2) AS precip_mm,
  ROUND(AVG(wind_knots) * 0.514444, 2) AS wind_mps
FROM daily
GROUP BY weather_date
"""


@dataclass(frozen=True)
class IngestTarget:
    """One destination table and the query that fills it."""

    table: str
    query: str
    job_config: bigquery.QueryJobConfig


def _job_config(
    settings: Settings, table: str, partition_field: str | None = None
) -> bigquery.QueryJobConfig:
    return bigquery.QueryJobConfig(
        destination=bigquery.TableReference.from_string(
            f"{settings.gcp_project_id}.{settings.bq_dataset}.{table}"
        ),
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        maximum_bytes_billed=settings.maximum_bytes_billed,
        time_partitioning=(
            bigquery.TimePartitioning(field=partition_field) if partition_field else None
        ),
    )


def ingest_targets(settings: Settings | None = None) -> tuple[IngestTarget, ...]:
    """The three extracts, in dependency-free order."""
    settings = settings or get_settings()
    source = settings.source_dataset
    # Table identifiers cannot be query parameters; these come from config, not requests.
    stations_sql = _STATIONS_SQL.format(source=f"{source}.{settings.source_stations_table}")
    demand_sql = _HOURLY_DEMAND_SQL.format(source=f"{source}.{settings.source_trips_table}")
    weather_sql = _WEATHER_SQL.format(
        lat=_AUSTIN_LAT,
        lon=_AUSTIN_LON,
        radius=_WEATHER_RADIUS_M,
        missing_temp=_MISSING_TEMP,
        missing_prcp=_MISSING_PRCP,
        missing_wdsp=_MISSING_WDSP,
        first_year=_FIRST_WEATHER_YEAR,
        # The replay window runs past T_NOW, so weather has to cover that year too.
        last_year=settings.t_now.year + 1,
    )
    return (
        IngestTarget(STATIONS_TABLE, stations_sql, _job_config(settings, STATIONS_TABLE)),
        IngestTarget(
            HOURLY_DEMAND_TABLE,
            demand_sql,
            _job_config(settings, HOURLY_DEMAND_TABLE, partition_field="hour_ts"),
        ),
        IngestTarget(
            WEATHER_TABLE,
            weather_sql,
            _job_config(settings, WEATHER_TABLE, partition_field="weather_date"),
        ),
    )


_SCHEMAS = {
    STATIONS_TABLE: STATIONS,
    HOURLY_DEMAND_TABLE: HOURLY_DEMAND,
    WEATHER_TABLE: DAILY_WEATHER,
}


def _validate(table: str, frame: pd.DataFrame) -> None:
    _SCHEMAS[table].validate(frame)
    if table == HOURLY_DEMAND_TABLE:
        assert_hourly_continuity(frame)


def dry_run_ingestion(
    client: bigquery.Client | None = None, settings: Settings | None = None
) -> dict[str, int]:
    """Validate every query without running it, returning bytes each would bill.

    Free, and the only pre-flight that catches a SQL or type error before the real
    run does. It also shows what each extract would cost against
    `maximum_bytes_billed`, which the real run enforces as a hard failure.
    """
    settings = settings or get_settings()
    client = client or bigquery.Client(project=settings.gcp_project_id)
    # Deliberately not the real job config: a dry run needs no destination, and the
    # bytes cap would reject the job rather than report the estimate we are after.
    config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    estimates = {}
    for target in ingest_targets(settings):
        job = client.query(target.query, job_config=config, location=settings.bq_location)
        estimates[target.table] = job.total_bytes_processed
    return estimates


def run_ingestion(
    client: bigquery.Client | None = None, settings: Settings | None = None
) -> dict[str, int]:
    """Execute every extract, validate what landed, and return rows written per table.

    Validation runs here rather than being left to the next stage: an extract that is
    empty, gapped, or wrongly typed otherwise looks like a successful run and is only
    noticed as a bad model weeks later.
    """
    settings = settings or get_settings()
    client = client or bigquery.Client(project=settings.gcp_project_id)
    written = {}
    for target in ingest_targets(settings):
        job = client.query(
            target.query, job_config=target.job_config, location=settings.bq_location
        )
        job.result()
        # Reads the whole table into memory. Fine for Austin (single-digit millions of
        # rows); a city-scale system would validate a sample plus SQL-side aggregates.
        frame = client.list_rows(target.job_config.destination).to_dataframe()
        _validate(target.table, frame)
        written[target.table] = len(frame)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the SQL and report bytes billed, without running anything",
    )
    if parser.parse_args().dry_run:
        for table, byte_count in dry_run_ingestion().items():
            print(f"{table}: would bill {byte_count / 1024**3:.2f} GiB")
        return
    for table, rows in run_ingestion().items():
        print(f"{table}: {rows} rows")


if __name__ == "__main__":
    main()
