"""Ingestion is HUMAN ONLY (it spends BigQuery quota), so the parts that can be
wrong without anyone noticing are the ones asserted here: the cost cap that keeps a
runaway query off the budget, the destination wiring, and the schema and continuity
checks that decide whether a silently broken extract reaches the model."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import pytest
from pandera.errors import SchemaError

from src.config import Settings
from src.data.ingest import (
    HOURLY_DEMAND_TABLE,
    STATIONS_TABLE,
    WEATHER_TABLE,
    dry_run_ingestion,
    ingest_targets,
    run_ingestion,
)
from src.data.schemas import (
    DAILY_WEATHER,
    HOURLY_DEMAND,
    STATIONS,
    assert_hourly_continuity,
)


def _demand_frame(hours: int = 4, station_id: int = 1) -> pd.DataFrame:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    return pd.DataFrame(
        {
            "station_id": [station_id] * hours,
            "hour_ts": [start + timedelta(hours=i) for i in range(hours)],
            "trip_count": list(range(hours)),
        }
    )


def _weather_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "weather_date": [datetime(2024, 1, 1).date()],
            "temp_c": [18.0],
            "precip_mm": [1.0],
            "wind_mps": [2.0],
        }
    )


def _stations_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "station_id": [1],
            "name": ["Rio Grande"],
            "status": ["active"],
            "council_district": pd.array([9], dtype="Int64"),
            "number_of_docks": pd.array([13], dtype="Int64"),
        }
    )


class _FakeQueryJob:
    total_bytes_processed = 1024

    def result(self) -> None:
        return None


class _FakeClient:
    """Records what was submitted and hands back whatever the test wants read.

    Typed loosely on purpose: it stands in for `bigquery.Client` across three methods
    out of hundreds, so the alternative is a protocol nobody else needs.
    """

    def __init__(self, frames: dict[str, pd.DataFrame] | None = None) -> None:
        self.frames = frames or {}
        self.submitted: list[dict[str, Any]] = []

    def query(self, query: str, job_config: Any, location: str) -> _FakeQueryJob:
        self.submitted.append({"query": query, "config": job_config, "location": location})
        return _FakeQueryJob()

    def list_rows(self, destination: Any) -> Any:
        frame = self.frames[destination.table_id]
        return type("_Rows", (), {"to_dataframe": lambda _self: frame})()


# --- ingestion targets -----------------------------------------------------


def test_every_target_caps_bytes_billed() -> None:
    """One uncapped job against a public dataset can outspend the whole month."""
    settings = Settings(maximum_bytes_billed=12345)
    for target in ingest_targets(settings):
        assert target.job_config.maximum_bytes_billed == 12345


def test_targets_write_into_the_projects_own_dataset() -> None:
    settings = Settings(gcp_project_id="proj", bq_dataset="ds")
    destinations = {t.table: t.job_config.destination for t in ingest_targets(settings)}
    assert set(destinations) == {STATIONS_TABLE, HOURLY_DEMAND_TABLE, WEATHER_TABLE}
    for table, destination in destinations.items():
        assert destination is not None
        assert (destination.project, destination.dataset_id, destination.table_id) == (
            "proj",
            "ds",
            table,
        )


def test_time_series_targets_are_partitioned() -> None:
    """Unpartitioned, every later query scans the full history (architecture.md 10.5)."""
    partitioning = {
        t.table: t.job_config.time_partitioning and t.job_config.time_partitioning.field
        for t in ingest_targets(Settings())
    }
    assert partitioning[HOURLY_DEMAND_TABLE] == "hour_ts"
    assert partitioning[WEATHER_TABLE] == "weather_date"
    assert partitioning[STATIONS_TABLE] is None


def test_queries_follow_the_configured_source_dataset() -> None:
    settings = Settings(
        source_dataset="other.bikes",
        source_trips_table="trips_v2",
        source_stations_table="stations_v2",
    )
    sql = {t.table: t.query for t in ingest_targets(settings)}
    assert "`other.bikes.trips_v2`" in sql[HOURLY_DEMAND_TABLE]
    assert "`other.bikes.stations_v2`" in sql[STATIONS_TABLE]


def test_ingestion_covers_the_post_t_now_replay_window() -> None:
    """Drift replay reads data after T_NOW, so ingestion must not stop at it."""
    for target in ingest_targets(Settings()):
        assert "2024-05-05" not in target.query


def test_gsod_sentinels_are_compared_as_numbers() -> None:
    """GSOD types these columns inconsistently and GoogleSQL will not compare a STRING
    column to a numeric literal, so a quoted sentinel fails the whole weather job."""
    weather_sql = next(t.query for t in ingest_targets(Settings()) if t.table == WEATHER_TABLE)
    for sentinel in ("9999.9", "99.99", "999.9"):
        assert f"'{sentinel}'" not in weather_sql
        assert f"AS FLOAT64), {sentinel})" in weather_sql


# --- running and dry-running -----------------------------------------------


def test_dry_run_asks_for_an_estimate_and_writes_nothing() -> None:
    """The pre-flight has to stay free: a destination or the bytes cap would turn it
    into a real job or a rejection instead of the estimate it exists to report."""
    client: Any = _FakeClient()
    estimates = dry_run_ingestion(client=client, settings=Settings())

    assert set(estimates) == {STATIONS_TABLE, HOURLY_DEMAND_TABLE, WEATHER_TABLE}
    assert len(client.submitted) == 3
    for submission in client.submitted:
        assert submission["config"].dry_run is True
        assert submission["config"].destination is None


def test_run_validates_every_table_it_writes() -> None:
    client: Any = _FakeClient(
        {
            STATIONS_TABLE: _stations_frame(),
            HOURLY_DEMAND_TABLE: _demand_frame(),
            WEATHER_TABLE: _weather_frame(),
        }
    )
    assert run_ingestion(client=client, settings=Settings()) == {
        STATIONS_TABLE: 1,
        HOURLY_DEMAND_TABLE: 4,
        WEATHER_TABLE: 1,
    }


def test_run_fails_on_a_gapped_extract() -> None:
    """A successful query is not a good extract, and only the read-back catches it."""
    client: Any = _FakeClient(
        {
            STATIONS_TABLE: _stations_frame(),
            HOURLY_DEMAND_TABLE: _demand_frame().drop(index=2),
            WEATHER_TABLE: _weather_frame(),
        }
    )
    with pytest.raises(ValueError, match="gaps"):
        run_ingestion(client=client, settings=Settings())


def test_run_fails_on_an_empty_extract() -> None:
    client: Any = _FakeClient(
        {
            STATIONS_TABLE: _stations_frame().iloc[:0],
            HOURLY_DEMAND_TABLE: _demand_frame(),
            WEATHER_TABLE: _weather_frame(),
        }
    )
    with pytest.raises(SchemaError):
        run_ingestion(client=client, settings=Settings())


# --- schemas ---------------------------------------------------------------


def test_valid_demand_frame_passes() -> None:
    HOURLY_DEMAND.validate(_demand_frame())


def test_negative_demand_is_rejected() -> None:
    frame = _demand_frame()
    frame.loc[0, "trip_count"] = -1
    with pytest.raises(SchemaError):
        HOURLY_DEMAND.validate(frame)


def test_duplicate_station_hour_is_rejected() -> None:
    """Two rows for one zone-hour double-count demand and silently skew every lag."""
    frame = pd.concat([_demand_frame(hours=1), _demand_frame(hours=1)], ignore_index=True)
    with pytest.raises(SchemaError):
        HOURLY_DEMAND.validate(frame)


def test_naive_timestamps_are_rejected() -> None:
    """A naive hour_ts silently shifts every split boundary (see src/config.py)."""
    frame = _demand_frame()
    frame["hour_ts"] = frame["hour_ts"].dt.tz_localize(None)
    with pytest.raises(SchemaError):
        HOURLY_DEMAND.validate(frame)


def test_impossible_weather_is_rejected() -> None:
    frame = _weather_frame()
    frame["temp_c"] = 80.0
    with pytest.raises(SchemaError):
        DAILY_WEATHER.validate(frame)


def test_a_number_is_not_a_weather_date() -> None:
    """Coercion turns a stray number into an epoch offset rather than failing."""
    frame = _weather_frame()
    frame["weather_date"] = 1.5
    with pytest.raises(SchemaError):
        DAILY_WEATHER.validate(frame)


def test_valid_stations_frame_passes() -> None:
    STATIONS.validate(_stations_frame())


def test_duplicate_station_is_rejected() -> None:
    frame = pd.concat([_stations_frame(), _stations_frame()], ignore_index=True)
    with pytest.raises(SchemaError):
        STATIONS.validate(frame)


@pytest.mark.parametrize(
    ("schema", "frame"),
    [
        (STATIONS, _stations_frame()),
        (HOURLY_DEMAND, _demand_frame()),
        (DAILY_WEATHER, _weather_frame()),
    ],
)
def test_empty_extracts_are_rejected(schema: Any, frame: pd.DataFrame) -> None:
    """Zero rows pass every column check, so emptiness needs its own check."""
    with pytest.raises(SchemaError):
        schema.validate(frame.iloc[:0])


# --- continuity ------------------------------------------------------------


def test_continuous_series_passes() -> None:
    assert_hourly_continuity(_demand_frame())


def test_missing_hour_is_reported_with_its_station() -> None:
    """A dropped hour is not a zero-demand hour, and reads as one once lags are built."""
    frame = _demand_frame(hours=4, station_id=7).drop(index=2).reset_index(drop=True)
    with pytest.raises(ValueError, match="7"):
        assert_hourly_continuity(frame)


def test_empty_frame_is_not_a_continuous_series() -> None:
    with pytest.raises(ValueError, match="empty"):
        assert_hourly_continuity(_demand_frame().iloc[:0])


def test_continuity_is_per_station() -> None:
    """Stations open and close at different times; that is not a gap."""
    early = _demand_frame(hours=3, station_id=1)
    late = _demand_frame(hours=3, station_id=2)
    late["hour_ts"] += timedelta(days=30)
    assert_hourly_continuity(pd.concat([early, late], ignore_index=True))
