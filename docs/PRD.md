# bikeshare-demand-mlops — Product Requirements Document

Related: [architecture.md](architecture.md) · [phases.md](phases.md) · [design.md](design.md) · [rules.md](rules.md)

## Problem

Bike-share operators need reliable hourly demand forecasts per zone to rebalance fleets and plan capacity. Manual planning and simple heuristics miss complex seasonal patterns and weather effects.

## Target users

| Audience | Access / role |
|---|---|
| Portfolio reviewer / hiring manager | Reads README and source code; may run `make check` |
| Demo consumer | Calls public `/v1/predict` API |
| Operator (portfolio framing) | Hypothetically consumes hourly forecasts per zone |

## Goals

1. Predict hourly trip starts per station cluster / zone on a public bike-share dataset.
2. Serve predictions via a versioned public REST API.
3. Run an automated train → evaluate → register → deploy → monitor → retrain loop on GCP.
4. Demonstrate scikit-learn, XGBoost, MLflow, Vertex AI, Terraform, and CI/CD with canary deploys.

## Non-goals

- No deep learning (XGBoost is sufficient for tabular + seasonality).
- No real-time streaming ingestion (batch hourly/daily is realistic).
- No feature store in v1 (Feast is a documented stretch goal).
- No GPU, multi-region HA, or API authentication.

## Feature set (current)

- Hourly zone demand forecasting pipeline.
- Public prediction API (`/v1/predict`, `/v1/health`, `/v1/ready`, `/v1/metadata`).
- Automated Vertex AI training pipeline with conditional model promotion.
- Cloud Run serving with canary deploys and rollback.
- Drift monitoring with Evidently.

## Future scope

- Feast online feature store.
- Drift-triggered retraining.
- Auto-promotion on metrics.
- Optuna hyperparameter search.
- Probabilistic (quantile) forecasts.

## Success metrics

- Model beats seasonal naive baseline by ≥ X% on validation MAE.
- `p95` latency < 200 ms warm under light load.
- Error rate < 2% in production.
- One successful Vertex AI pipeline run visible in console.
- Drift report produced weekly.

## Constraints

- GCP only; target cost < $10/month.
- No exported JSON service-account keys; use Workload Identity Federation.
- Public datasets only; no PII.
- No secrets in code or committed env files.
