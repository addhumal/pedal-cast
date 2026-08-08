"""Pandera schemas for the raw layer (docs/architecture.md 4).

These run over what BigQuery hands back, not over what the SQL was meant to produce.
A wrong extract is worse than a missing one: the pipeline keeps running and the model
learns from it, so every check below fails loudly rather than warning.
"""

import pandas as pd
import pandera.pandas as pa

HOURLY_DEMAND = pa.DataFrameSchema(
    {
        "station_id": pa.Column(int, coerce=True),
        # Timezone-aware for the same reason T_NOW is (src/config.py): a naive
        # timestamp moves the split boundaries across Austin's DST changes.
        "hour_ts": pa.Column("datetime64[ns, UTC]"),
        "trip_count": pa.Column(int, pa.Check.ge(0), coerce=True),
    },
    # Two rows for one station-hour double-count demand and skew every lag built
    # from it, which is invisible in aggregate metrics.
    unique=["station_id", "hour_ts"],
    strict=True,
    name="hourly_station_demand",
)

DAILY_WEATHER = pa.DataFrameSchema(
    {
        "weather_date": pa.Column("object"),
        # Ranges are Austin-plausible, not physically possible: the point is to catch
        # a unit slip (Fahrenheit, inches, knots) rather than to police the weather.
        "temp_c": pa.Column(float, pa.Check.in_range(-30, 55), nullable=True),
        "precip_mm": pa.Column(float, pa.Check.in_range(0, 500), nullable=True),
        "wind_mps": pa.Column(float, pa.Check.in_range(0, 60), nullable=True),
    },
    unique=["weather_date"],
    strict=True,
    name="daily_weather",
)


def assert_hourly_continuity(frame: pd.DataFrame) -> None:
    """Fail if any station's hourly series skips an hour inside its own span.

    Ingestion writes explicit zeros for quiet hours, so a genuinely missing row means
    data loss. Left alone it reads as zero demand once lags are built, which teaches
    the model that the station goes dead at exactly the wrong times.

    Stations open and close at different dates, so continuity is checked per station
    between its own first and last observed hour, never against a global calendar.
    """
    gaps = []
    for station_id, group in frame.groupby("station_id"):
        observed = pd.DatetimeIndex(group["hour_ts"]).sort_values()
        missing = pd.date_range(observed[0], observed[-1], freq="h").difference(observed)
        if len(missing):
            gaps.append(f"station {station_id}: {len(missing)} missing hours from {missing[0]}")
    if gaps:
        raise ValueError("hourly demand has gaps — " + "; ".join(gaps))
