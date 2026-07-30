# bikeshare-demand-mlops — Phases

Related: [PRD.md](PRD.md) · [architecture.md](architecture.md) · [design.md](design.md)

## Phase 0 — Foundation

Status: in progress

- GCP project + billing alert via Terraform.
- Choose dataset and `T_NOW` (Week 0 checkpoint).
- Seed repo governance and initial commit.

## Phase 1 — Data + baselines

Status: planned

- Ingestion queries, hourly zone aggregates, pandera schemas.
- EDA notebook and zone count decision.
- Seasonal naive and t-24h baselines with validation MAE.

## Phase 2 — Features + model + MLflow

Status: planned

- Leakage-safe feature build (lags, rolling, calendar, weather, zones).
- sklearn + XGBoost pipeline, randomized search, MLflow logging.
- Segment metrics and promotion rule (unit-tested).

## Phase 3 — Vertex AI pipeline

Status: planned

- Componentize flow into KFP v2 components.
- Compile, run end-to-end on Vertex, conditional registration.
- Check compiled pipeline JSON into repo.

## Phase 4 — Serving + CI/CD

Status: planned

- FastAPI service, model loading from GCS, hardening.
- Dockerfile, Cloud Build canary deploy, smoke tests, WIF auth.

## Phase 5 — Monitoring + failure drill

Status: planned

- Evidently drift job, dashboard, alert policies.
- Locust run, deliberate bad deploy + rollback.
- Weekly retraining schedule.

## Phase 6 — Portfolio packaging

Status: planned

- README, demo video, LinkedIn post.

## How to advance

1. One vertical slice per change set.
2. Follow project `docs/rules.md` + global TDD / ponytail User Rules.
3. Update this file’s status and append to [memory.md](memory.md) when a stage
   completes or scope changes.
