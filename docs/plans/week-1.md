# Week 1 — Data, zones, baselines

[Master plan](../phases.md) · [architecture.md](../architecture.md) §4

**Goal:** turn the chosen public dataset into a validated hourly-per-zone table, and establish the baselines the model must beat.

**Status:** planned. Blocked on Gate 0 for the dataset and `T_NOW`.

---

## Deliverables

- `src/data/queries/` — raw trips extract, hourly `(zone_id, hour_ts, trip_count)` aggregate, NOAA GSOD daily weather join. Every query carries `maximum_bytes_billed`.
- `src/data/schemas.py` — pandera schemas for the raw aggregate and the feature table: types, non-null, `trip_count >= 0`, temperature bounds, and timestamp continuity so silent gaps fail loudly.
- `src/features/zones.py` — k-means on station lat/lon, fit once and persisted. Zone count decided in EDA, then recorded in [architecture.md](../architecture.md) §4.
- `notebooks/eda.ipynb` — EDA only, ending in the zone-count decision. Outputs are stripped by `nbstripout` on commit.
- `src/train/baselines.py` — seasonal naive (t-168h) and the simpler t-24h.
- README metrics table gains both baseline MAE values.

The `holidays` country code follows the dataset chosen at Gate 0 (London means UK), so it is pinned here rather than guessed earlier.

## Tests

- Pandera schemas accept a valid frame and reject each violation class individually.
- Timestamp continuity check catches an induced gap.
- Baselines produce the arithmetically correct answer on a small synthetic frame with a known shape.
- Zone assignment is deterministic across runs given a fixed seed.

## Human gate 1

```bash
# Ingestion, with a bytes cap
make ingest

# Snapshot the raw extract — architecture.md §14 mitigation for the
# public dataset changing or disappearing under us
gcloud storage cp gs://PROJECT-raw/trips_raw.parquet gs://PROJECT-raw/snapshots/

# Baselines
make baselines
```

**Report back:** validation MAE for both baselines, and the zone count EDA settles on.

## Definition of done

- [ ] `make check` green.
- [ ] Both baseline MAE numbers written into the README metrics table.
- [ ] Raw extract snapshotted to GCS.
- [ ] Zone count recorded in [architecture.md](../architecture.md) §4.

## Results

| Item | Value |
|---|---|
| Zone count | — |
| Seasonal naive MAE (t-168h) | — |
| Simple baseline MAE (t-24h) | — |
| Rows in feature table | — |
| Raw snapshot path | — |
