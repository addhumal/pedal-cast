# Week 3 — Vertex AI pipeline

[Master plan](../phases.md) · [architecture.md](../architecture.md) §7

**Goal:** the same code that runs locally runs as a managed pipeline, with registration gated on the promotion rule.

**Status:** planned.

---

## Deliverables

- `pipelines/components/` — `ingest`, `validate`, `build_features`, `train`, `evaluate`, `register`, `notify`. Each is a **thin wrapper** over already-tested `src/` functions, so the logic stays unit-testable without Vertex and there is no second implementation to drift.
- `pipelines/pipeline.py` — KFP v2 definition. Parameters: `T_NOW`, dataset config, tuning trial count, promotion thresholds.
- `evaluate` pulls current champion metrics from the registry for comparison.
- `register` runs only when the promotion rule passes, uploads to Vertex Model Registry, and writes the GCS model path.
- `notify` logs the outcome, including the "champion retained" case, which must be visible rather than silent.
- Compiled pipeline JSON committed to the repo.

## Tests

- Each component's wrapped logic is tested directly through `src/`, not through KFP.
- Compilation is tested: the pipeline compiles and the resulting JSON contains the expected component graph and parameter set.
- Conditional registration is tested by driving the promotion rule both ways with fixture metrics.

## Human gate 3

```bash
make pipeline-compile          # local, no cost
make pipeline-run             # submits to Vertex — human only
```

**Report back:** run URL, whether registration fired, and the registered model version.

## Definition of done

- [ ] One successful Vertex run visible in the console.
- [ ] Model in the Vertex Model Registry.
- [ ] Compiled JSON committed.
- [ ] `make check` green.

## Results

| Item | Value |
|---|---|
| Pipeline run ID | — |
| Registered model version | — |
| Promotion outcome | — |
| Run duration | — |
| Run cost | — |
