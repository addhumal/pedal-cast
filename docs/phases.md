# pedal-cast — Roadmap

Related: [PRD.md](PRD.md) · [architecture.md](architecture.md)

Eight blocks. A block is done when `make check` is green and the definition of done below is met. Cloud-cost steps (deploys, BigQuery jobs, Vertex runs, `terraform apply`) are manual.

## Blocks

| Block | Goal | Definition of done | Status |
|---|---|---|---|
| Week 0 | Scaffold, Terraform, security baseline | Budget alert live; dataset and `T_NOW` chosen and recorded in architecture §2 | In progress |
| Week 1 | Data, zones, baselines | `make check` green; both baseline MAE numbers in the README table | Planned |
| Week 2 | Features, model, MLflow | Model beats seasonal naive; MLflow screenshot saved; promotion rule unit-tested | Planned |
| Week 3 | Vertex AI pipeline | One successful Vertex run in the console; model in the registry; compiled JSON in the repo | Planned |
| Week 4a | API, Docker, CI/CD | Public URL returns predictions; a merge deploys a canary; WIF pinned to this repo | Planned |
| Week 4b | Landing page and live widget | Landing page live; widget returns a forecast; `/v1` and `/docs` still resolve | Planned |
| Week 5 | Monitoring and failure drill | Drift report in GCS; alert fired in a test; rollback proven; latency in README | Planned |
| Week 6 | Portfolio packaging | A stranger can understand and reproduce the project from the README alone | Planned |

## Human gates

| Gate | After | What happens |
|---|---|---|
| 0 | Week 0 | Create project, link billing, create state bucket, apply budget, run dataset recency queries, enable repo security settings |
| 1 | Week 1 | Run ingestion, snapshot raw extract to GCS, run baselines, report MAE |
| 2 | Week 2 | Run tuning sweep, save MLflow screenshot, report best-trial metrics |
| 3 | Week 3 | Submit the Vertex pipeline run |
| 4a | Week 4a | Apply WIF and verify `attributeCondition` is non-empty, enable required checks, Dependabot, CodeQL, merge to deploy the first canary |
| 4b | Week 4b | Deploy the combined image; verify the page and widget |
| 5 | Week 5 | Run drift job, force an alert, run Locust, perform the rollback drill |

## Notes

- Scaffold landed in Week 0 (Week 1 needs `make check`).
- Week 4 is split into 4a (API) and 4b (frontend) so the contract freezes before the UI.
- Work lands as stacked PRs: one concern per PR, base on the branch it depends on, retarget to `main` after that base merges.
