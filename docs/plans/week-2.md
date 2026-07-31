# Week 2 — Features, model, MLflow

[Master plan](../phases.md) · [architecture.md](../architecture.md) §4, §5

**Goal:** a tuned model that beats the baselines, with every trial tracked and the promotion decision encoded rather than judged.

**Status:** planned.

---

## Deliverables

- `src/features/build.py` — lags (t-1h, t-24h, t-168h), 24h and 168h rolling mean/std per zone, calendar features via `holidays`, weather join, zone statics.
- `src/train/splits.py` — time-based train / validation / test boundaries derived from `T_NOW`. Never random.
- `src/train/pipeline.py` — sklearn `Pipeline` with `ColumnTransformer` into `XGBRegressor`. Compare `reg:squarederror` against `count:poisson` and record the winner in [architecture.md](../architecture.md) §5.
- `src/train/tune.py` — randomized search, 30–50 trials, each logged to MLflow with params, metrics, and a feature-importance plot.
- `src/train/metrics.py` — MAE, RMSE, and MAE by segment (peak vs off-peak, weekday vs weekend).
- `src/train/promote.py` — challenger replaces champion only if validation MAE improves ≥ 2% **and** no segment degrades by > 5%.
- README metrics table gains model and segment numbers.

## Tests

**Leakage tests are the priority of this block.** They encode the hard constraints in [architecture.md](../architecture.md) §4 and are the tests most likely to be quietly wrong:

- No feature computed for time `t` reads any data at or after `t`. Asserted per feature, not in aggregate.
- Rolling and lag windows never cross a split boundary.
- Splits are contiguous, ordered, and non-overlapping, with the test window untouched until the end.

Plus:

- Promotion rule tested at both boundaries: exactly 2% improvement, exactly 5% segment degradation, and the combination where MAE improves but a segment regresses.
- Model-quality gate: the trained model beats seasonal naive on validation or CI fails.

## Human gate 2

```bash
make tune            # 30-50 trials, logged to MLflow
mlflow ui            # save a screenshot of the run comparison
```

**Report back:** best-trial validation MAE and RMSE, segment breakdown, and which objective won.

## Definition of done

- [ ] Model beats seasonal naive on validation.
- [ ] MLflow screenshot saved for the README.
- [ ] Promotion rule implemented and unit-tested at both boundaries.
- [ ] Model and segment metrics in the README table.
- [ ] `make check` green.

## Results

| Item | Value |
|---|---|
| Objective chosen | — |
| Best validation MAE | — |
| Best validation RMSE | — |
| Improvement over seasonal naive | — |
| MAE peak / off-peak | — |
| MAE weekday / weekend | — |
| Trials run | — |
