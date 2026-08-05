# pedal-cast

Hourly bike-share demand forecasting per station zone, served from a public REST API on GCP, with an automated train → evaluate → register → deploy → monitor → retrain loop.

An end-to-end MLOps system, not a notebook. [docs/architecture.md](docs/architecture.md) is the source of truth for architecture and decisions.

## Status

Week 0, foundation. Nothing is deployed yet. Dataset and simulated `T_NOW` are not yet chosen; see [docs/architecture.md](docs/architecture.md) §2.

## Metrics

Filled in as each number is measured, not before. Empty rows mean not measured yet.

| Metric | Value | Measured |
|---|---|---|
| Seasonal naive baseline (MAE, t-168h) | — | Week 1 |
| Simple baseline (MAE, t-24h) | — | Week 1 |
| Model MAE (validation) | — | Week 2 |
| Model RMSE (validation) | — | Week 2 |
| MAE peak vs off-peak | — | Week 2 |
| MAE weekday vs weekend | — | Week 2 |
| API p50 / p95 (warm) | — | Week 5 |
| Cold start | — | Week 5 |

## Stack

BigQuery · scikit-learn + XGBoost · MLflow · Vertex AI Pipelines (KFP v2) · Vertex Model Registry · FastAPI on Cloud Run · Terraform · Cloud Build with canary deploys · Evidently drift monitoring · React + Vite frontend

## Project docs

- [docs/PRD.md](docs/PRD.md): product requirements, goal and scope
- [docs/architecture.md](docs/architecture.md): architecture and decisions
- [docs/design.md](docs/design.md): UI design system
- [docs/phases.md](docs/phases.md): week-by-week roadmap

## Local development

```bash
uv sync              # install pinned dependencies
make check           # lint, typecheck, security lint, tests
```

Cloud commands (deploys, BigQuery queries, Vertex pipeline runs) are manual. Do not script them into CI without a human gate.

## Security

This is a public repository. See [docs/architecture.md](docs/architecture.md) §10 for the posture and [SECURITY.md](SECURITY.md) for reporting.
