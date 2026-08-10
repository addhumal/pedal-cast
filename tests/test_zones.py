"""Zones are a clustering over station coordinates, fit once and persisted.

The BigQuery stations table has no lat/lon, so coordinates come from the City of
Austin kiosk endpoint. Everything that can go wrong without a cloud round-trip is
asserted here: parsing, the office dock exclusion, the fit, the persist/load round
trip, and the station-hour → zone-hour rollup.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from src.config import Settings
from src.data.station_coords import (
    OFFICE_STATION_ID,
    fetch_station_coords,
    parse_kiosk_rows,
)
from src.features.zones import (
    ZoneModel,
    aggregate_to_zones,
    fit_zones,
    load_zones,
    save_zones,
)

FIXTURE = Path(__file__).parent / "fixtures" / "kiosks_sample.json"


def _stations_frame() -> pd.DataFrame:
    return parse_kiosk_rows(FIXTURE.read_text())


def _demand_frame(stations: list[int], hours: int = 3) -> pd.DataFrame:
    start = datetime(2024, 1, 1, tzinfo=UTC)
    rows = []
    for station_id in stations:
        for i in range(hours):
            rows.append(
                {
                    "station_id": station_id,
                    "hour_ts": start + timedelta(hours=i),
                    "trip_count": station_id % 7 + i,
                }
            )
    return pd.DataFrame(rows)


# --- coordinates -----------------------------------------------------------


def test_parse_kiosk_rows_yields_station_lat_lon() -> None:
    frame = _stations_frame()
    assert set(frame.columns) == {"station_id", "name", "status", "lat", "lon"}
    assert len(frame) == 12
    assert frame["station_id"].is_unique
    assert frame["lat"].between(30.0, 31.0).all()
    assert frame["lon"].between(-98.0, -97.0).all()


def test_parse_drops_rows_without_coordinates() -> None:
    raw = (
        '[{"kiosk_id":"1","kiosk_name":"A","kiosk_status":"active",'
        '"location":{"latitude":"30.1","longitude":"-97.7"}},'
        '{"kiosk_id":"2","kiosk_name":"B","kiosk_status":"active"}]'
    )
    frame = parse_kiosk_rows(raw)
    assert list(frame["station_id"]) == [1]


def test_parse_rejects_duplicate_station_ids() -> None:
    raw = (
        '[{"kiosk_id":"1","kiosk_name":"A","kiosk_status":"active",'
        '"location":{"latitude":"30.1","longitude":"-97.7"}},'
        '{"kiosk_id":"1","kiosk_name":"A2","kiosk_status":"active",'
        '"location":{"latitude":"30.2","longitude":"-97.8"}}]'
    )
    with pytest.raises(ValueError, match="duplicate"):
        parse_kiosk_rows(raw)


def test_fetch_reads_a_local_path(tmp_path: Path) -> None:
    """Gate 1 can point at a snapshot instead of hitting the live endpoint."""
    path = tmp_path / "kiosks.json"
    path.write_text(FIXTURE.read_text())
    frame = fetch_station_coords(source=str(path))
    assert len(frame) == 12


# --- fitting ---------------------------------------------------------------


def test_fit_produces_one_zone_per_station() -> None:
    model = fit_zones(_stations_frame(), n_zones=4)
    assert isinstance(model, ZoneModel)
    assert set(model.mapping["station_id"]) == set(_stations_frame()["station_id"]) - {
        OFFICE_STATION_ID
    }
    assert model.mapping["zone_id"].nunique() == 4
    assert model.mapping["zone_id"].min() == 0
    assert model.mapping["zone_id"].max() == 3


def test_fit_excludes_the_office_test_dock() -> None:
    """Station 1001 is Bike Share of Austin's own shop — not a public kiosk."""
    model = fit_zones(_stations_frame(), n_zones=3)
    assert OFFICE_STATION_ID not in set(model.mapping["station_id"])


def test_fit_is_deterministic() -> None:
    a = fit_zones(_stations_frame(), n_zones=4)
    b = fit_zones(_stations_frame(), n_zones=4)
    pd.testing.assert_frame_equal(
        a.mapping.sort_values("station_id").reset_index(drop=True),
        b.mapping.sort_values("station_id").reset_index(drop=True),
    )


def test_fit_rejects_too_few_stations_for_the_requested_zones() -> None:
    frame = _stations_frame().head(3)
    with pytest.raises(ValueError, match="stations"):
        fit_zones(frame, n_zones=10)


def test_fit_respects_configured_zone_count() -> None:
    """Default stays inside the architecture 10-30 band; EDA picked 20."""
    settings = Settings()
    assert settings.zone_count == 20
    # Fixture is too small for 20, so just assert the setting — the real fit uses
    # the full kiosk snapshot at Gate 1.
    assert 10 <= settings.zone_count <= 30


# --- persist / load --------------------------------------------------------


def test_save_and_load_round_trip(tmp_path: Path) -> None:
    model = fit_zones(_stations_frame(), n_zones=4)
    path = tmp_path / "zones.parquet"
    save_zones(model, path)
    loaded = load_zones(path)
    pd.testing.assert_frame_equal(
        loaded.mapping.sort_values("station_id").reset_index(drop=True),
        model.mapping.sort_values("station_id").reset_index(drop=True),
    )
    assert loaded.n_zones == model.n_zones


# --- aggregate -------------------------------------------------------------


def test_aggregate_sums_trip_counts_per_zone_hour() -> None:
    model = fit_zones(_stations_frame(), n_zones=3)
    stations = model.mapping["station_id"].tolist()[:4]
    demand = _demand_frame(stations, hours=2)
    zoned = aggregate_to_zones(demand, model.mapping)

    assert set(zoned.columns) == {"zone_id", "hour_ts", "trip_count"}
    # Every station-hour lands in exactly one zone-hour, so totals match.
    assert zoned["trip_count"].sum() == demand["trip_count"].sum()
    assert zoned.duplicated(["zone_id", "hour_ts"]).sum() == 0


def test_aggregate_drops_stations_without_a_zone() -> None:
    """A station missing from the mapping must not invent a zone or silently zero."""
    model = fit_zones(_stations_frame(), n_zones=3)
    demand = _demand_frame([11, 99999], hours=1)
    zoned = aggregate_to_zones(demand, model.mapping)
    mapped = demand[demand["station_id"] == 11]["trip_count"].sum()
    assert zoned["trip_count"].sum() == mapped
