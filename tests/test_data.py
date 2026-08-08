"""Ingestion is HUMAN ONLY (it spends BigQuery quota), so the parts that can be
wrong without anyone noticing are the ones asserted here: the cost cap that keeps a
runaway query off the budget, the destination wiring, and the schema and continuity
checks that decide whether a silently broken extract reaches the model."""

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest
from pandera.errors import SchemaError

from src.config import Settings
from src.data.ingest import (
    HOURLY_DEMAND_TABLE,
    STATIONS_TABLE,
    WEATHER_TABLE,
    ingest_targets,
)
from src.data.schemas import (
    DAILY_WEATHER,
    HOURLY_DEMAND,
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
    frame = pd.DataFrame(
        {
            "weather_date": [datetime(2024, 1, 1).date()],
            "temp_c": [80.0],
            "precip_mm": [1.0],
            "wind_mps": [2.0],
        }
    )
    with pytest.raises(SchemaError):
        DAILY_WEATHER.validate(frame)


# --- continuity ------------------------------------------------------------


def test_continuous_series_passes() -> None:
    assert_hourly_continuity(_demand_frame())


def test_missing_hour_is_reported_with_its_station() -> None:
    """A dropped hour is not a zero-demand hour, and reads as one once lags are built."""
    frame = _demand_frame(hours=4, station_id=7).drop(index=2).reset_index(drop=True)
    with pytest.raises(ValueError, match="7"):
        assert_hourly_continuity(frame)


def test_continuity_is_per_station() -> None:
    """Stations open and close at different times; that is not a gap."""
    early = _demand_frame(hours=3, station_id=1)
    late = _demand_frame(hours=3, station_id=2)
    late["hour_ts"] += timedelta(days=30)
    assert_hourly_continuity(pd.concat([early, late], ignore_index=True))
