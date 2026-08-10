"""Station coordinates from the City of Austin open-data kiosk endpoint.

`bigquery-public-data.austin_bikeshare.bikeshare_stations` has no latitude or
longitude — Google's loader drops them. The city's own kiosk dataset still has
them, keyed by `kiosk_id` which matches `station_id` in the trips table. That is
the coordinate source for k-means zoning (docs/architecture.md §4).

Prefer a local snapshot path when one exists (`make snapshot-station-coords`); the
live URL is the fallback. Either way the parse path is the same, so tests never
need the network.
"""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

# Bike Share of Austin's own shop/test dock — not a public kiosk, not demand.
OFFICE_STATION_ID = 1001

# City of Austin "Austin MetroBike Kiosk Locations".
DEFAULT_KIOSK_URL = "https://data.austintexas.gov/resource/qd73-bsdg.json?$limit=5000"


def parse_kiosk_rows(raw: str | bytes) -> pd.DataFrame:
    """Turn the kiosk JSON payload into a stations frame with lat/lon."""
    rows = json.loads(raw)
    records = []
    for row in rows:
        location = row.get("location") or {}
        lat = location.get("latitude")
        lon = location.get("longitude")
        if lat is None or lon is None or row.get("kiosk_id") is None:
            continue
        records.append(
            {
                "station_id": int(row["kiosk_id"]),
                "name": row.get("kiosk_name"),
                "status": row.get("kiosk_status"),
                "lat": float(lat),
                "lon": float(lon),
            }
        )
    frame = pd.DataFrame.from_records(
        records, columns=["station_id", "name", "status", "lat", "lon"]
    )
    if frame["station_id"].duplicated().any():
        dupes = frame.loc[frame["station_id"].duplicated(), "station_id"].tolist()
        raise ValueError(f"duplicate station_id values in kiosk payload: {dupes}")
    return frame


def fetch_station_coords(source: str = DEFAULT_KIOSK_URL) -> pd.DataFrame:
    """Load coordinates from a local path or the live open-data URL."""
    path = Path(source)
    if path.exists():
        return parse_kiosk_rows(path.read_text())
    with urlopen(source) as response:  # noqa: S310 — URL comes from config, not a request
        return parse_kiosk_rows(response.read())


def snapshot_station_coords(destination: Path | str, source: str = DEFAULT_KIOSK_URL) -> Path:
    """Write the live kiosk JSON to disk so zone fitting does not need the network."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(source) as response:  # noqa: S310 — URL comes from config, not a request
        destination.write_bytes(response.read())
    return destination


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="data/station_coords.json",
        help="where to write the kiosk JSON snapshot",
    )
    parser.add_argument("--source", default=DEFAULT_KIOSK_URL)
    args = parser.parse_args()
    path = snapshot_station_coords(args.output, source=args.source)
    frame = parse_kiosk_rows(path.read_text())
    print(f"{path}: {len(frame)} stations with coordinates")


if __name__ == "__main__":
    main()
