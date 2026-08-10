"""Station → zone clustering (docs/architecture.md §4).

K-means on lat/lon, fit once, persisted. The raw layer stays per station-hour so
re-zoning is a feature-layer rerun rather than a re-ingest. Zone count was chosen
by silhouette on the City of Austin kiosk coordinates (Week 1 EDA) and lives in
`Settings.zone_count`.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.cluster import KMeans

from src.config import Settings, get_settings
from src.data.station_coords import OFFICE_STATION_ID, fetch_station_coords


@dataclass(frozen=True)
class ZoneModel:
    """Fitted mapping of station_id → zone_id, plus the zone count it was fit for."""

    mapping: pd.DataFrame
    n_zones: int


def fit_zones(stations: pd.DataFrame, n_zones: int) -> ZoneModel:
    """Cluster stations by lat/lon. Excludes the office test dock."""
    required = {"station_id", "lat", "lon"}
    missing = required - set(stations.columns)
    if missing:
        raise ValueError(f"stations frame missing columns: {sorted(missing)}")

    frame = stations.loc[stations["station_id"] != OFFICE_STATION_ID, ["station_id", "lat", "lon"]]
    frame = frame.dropna(subset=["lat", "lon"]).drop_duplicates("station_id")
    if len(frame) < n_zones:
        raise ValueError(
            f"need at least {n_zones} stations to fit {n_zones} zones, have {len(frame)}"
        )

    # random_state pins the labels; n_init>1 picks the best of a few starts.
    labels = KMeans(n_clusters=n_zones, n_init=20, random_state=0).fit_predict(
        frame[["lat", "lon"]].to_numpy()
    )
    mapping = frame.copy()
    mapping["zone_id"] = labels.astype(int)
    mapping = mapping[["station_id", "zone_id", "lat", "lon"]].sort_values("station_id")
    mapping = mapping.reset_index(drop=True)
    return ZoneModel(mapping=mapping, n_zones=n_zones)


def save_zones(model: ZoneModel, path: Path | str) -> None:
    """Persist the mapping as parquet. Centroids are recoverable from the points."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = model.mapping.copy()
    # n_zones as a column of constants — parquet attrs are not reliably round-tripped.
    frame["n_zones"] = model.n_zones
    frame.to_parquet(path, index=False)


def load_zones(path: Path | str) -> ZoneModel:
    frame = pd.read_parquet(path)
    if "n_zones" not in frame.columns:
        raise ValueError(f"zone mapping at {path} is missing the n_zones column")
    n_zones = int(frame["n_zones"].iloc[0])
    mapping = frame[["station_id", "zone_id", "lat", "lon"]].copy()
    return ZoneModel(mapping=mapping, n_zones=n_zones)


def aggregate_to_zones(demand: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Roll station-hour demand up to zone-hour demand.

    Stations absent from the mapping are dropped — inventing a zone for them would
    silently mis-attribute demand, and zeroing would look like a real quiet zone.
    """
    required_demand = {"station_id", "hour_ts", "trip_count"}
    missing = required_demand - set(demand.columns)
    if missing:
        raise ValueError(f"demand frame missing columns: {sorted(missing)}")

    merged = demand.merge(mapping[["station_id", "zone_id"]], on="station_id", how="inner")
    zoned: pd.DataFrame = merged.groupby(["zone_id", "hour_ts"], as_index=False).agg(
        trip_count=("trip_count", "sum")
    )
    return zoned.sort_values(["zone_id", "hour_ts"]).reset_index(drop=True)


def fit_and_save(
    settings: Settings | None = None,
    source: str | None = None,
    output: Path | str | None = None,
) -> ZoneModel:
    """Fetch coordinates, fit, and persist. The Gate 1 / local entry point."""
    settings = settings or get_settings()
    source = source or settings.station_coords_source
    output = Path(output or settings.zones_path)
    stations = fetch_station_coords(source=source)
    model = fit_zones(stations, n_zones=settings.zone_count)
    save_zones(model, output)
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        default=None,
        help="kiosk JSON path or URL (default: Settings.station_coords_source)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="parquet path for the mapping (default: Settings.zones_path)",
    )
    args = parser.parse_args()
    model = fit_and_save(source=args.source, output=args.output)
    sizes = model.mapping.groupby("zone_id").size()
    print(
        f"zones: {model.n_zones}; stations: {len(model.mapping)}; "
        f"size min/mean/max: {sizes.min()}/{sizes.mean():.1f}/{sizes.max()}"
    )


if __name__ == "__main__":
    main()
