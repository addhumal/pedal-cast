# pedal-cast — Product Requirements Document

Related: [architecture.md](architecture.md) · [phases.md](phases.md) · [design.md](design.md)

## Problem

Bike-share operators need reliable hourly demand forecasts per zone to rebalance fleets and plan capacity. Manual planning and simple heuristics miss complex seasonal patterns and weather effects.

## Goal

Predict hourly bike-share demand (trip starts) per station cluster / zone, served via a public REST API, with a fully automated train → evaluate → register → deploy → monitor → retrain loop on GCP.

**Why it exists (portfolio framing):** public, pointable evidence of scikit-learn, XGBoost, MLflow, Vertex AI, CI/CD with canary deploys, and drift monitoring — an end-to-end MLOps system, not a notebook.

## Target users

| Audience | Access / role |
|---|---|
| Portfolio reviewer / hiring manager | Reads the README and source; may run `make check` |
| Demo visitor | Uses the landing page widget, or calls `/v1/predict` directly |
| Operator (portfolio framing) | Hypothetically consumes hourly forecasts per zone |

## Goals

1. Predict hourly trip starts per station zone on a public bike-share dataset.
2. Serve predictions from a versioned public REST API.
3. Run an automated train → evaluate → register → deploy → monitor → retrain loop on GCP.
4. Demonstrate scikit-learn, XGBoost, MLflow, Vertex AI, Terraform, and CI/CD with canary deploys.
5. Make the system legible to a stranger in sixty seconds, via a landing page and the README.

## Non-goals (v1)

- No deep learning — XGBoost is the right tool for tabular data with strong seasonality, and defending that choice is itself the point.
- No real-time streaming ingestion; batch hourly/daily is realistic for this problem.
- No feature store — Feast is a documented stretch goal.
- No GPU anywhere.
- No multi-region or HA beyond what Cloud Run gives for free.
- No user auth on the API. It is a public demo, rate-limited instead.
- No light mode, no SSR, no client-side routing in the frontend.

## Feature set (current)

- Hourly zone demand forecasting pipeline on a BigQuery public dataset.
- Public prediction API: `POST /v1/predict`, `GET /v1/health`, `/v1/ready`, `/v1/metadata`, plus Swagger `/docs`.
- Automated Vertex AI training pipeline with a coded promotion rule and conditional registration.
- Cloud Run serving with canary deploys and a proven rollback path.
- Drift monitoring with Evidently on a replayed post-`T_NOW` window.
- React landing page with a live prediction widget, served by the same container.

## Future scope

- Feast online feature store.
- Drift-triggered retraining.
- Auto-promotion on metrics.
- Optuna hyperparameter search.
- Probabilistic (quantile) forecasts.
- Frontend on its own Cloud Run service or a CDN.

## Success metrics

- Model beats the seasonal naive baseline on validation MAE by a margin recorded in the README.
- API p95 under 200 ms warm, with cold start measured and published honestly.
- Error rate under 2% in production.
- One successful Vertex AI pipeline run visible in the console, with a model in the registry.
- A drift report produced weekly and an alert proven to fire.
- A stranger can understand and reproduce the project from the README alone.

## Constraints

- GCP only; target cost under $10/month with a budget alert at $15.
- No exported JSON service-account keys; Workload Identity Federation, pinned to this repository.
- Public repository, so the security posture assumes hostile readers and forked pull requests.
- Public datasets only, no PII.
- No secrets in code, committed env files, or `VITE_*` variables.
- Roughly 4–5 hours per week of human time.
