# pedal-cast — Master Week Plan

Related: [PRD.md](PRD.md) · [architecture.md](architecture.md) · [memory.md](memory.md)

Eight blocks. Each has a detail sub-doc in [plans/](plans/) carrying deliverables, tests, the human gate, and a results section filled in as real numbers land.

Two rules govern progress: a block is not done until `make check` is green **and** its definition of done is satisfied; and every block that needs a cloud-cost command stops at a **human gate**, because agents do not run those ([rules.md](rules.md) invariant 2).

## Blocks

| Block | Goal | Definition of done | Status |
|---|---|---|---|
| [Week 0](plans/week-0.md) | Docs restructure, scaffold, Terraform, security baseline | Budget alert live; dataset and `T_NOW` chosen and recorded | In progress |
| [Week 1](plans/week-1.md) | Data, zones, baselines | `make check` green; both baseline MAE numbers in the README table | Planned |
| [Week 2](plans/week-2.md) | Features, model, MLflow | Model beats seasonal naive; MLflow screenshot saved; promotion rule unit-tested | Planned |
| [Week 3](plans/week-3.md) | Vertex AI pipeline | One successful Vertex run in the console; model in registry; compiled JSON in repo | Planned |
| [Week 4a](plans/week-4a.md) | API, Docker, CI/CD | Public URL returns predictions; a merge deploys a canary; WIF provably pinned to this repo | Planned |
| [Week 4b](plans/week-4b.md) | Landing page and live widget | Landing page live; widget returns a real forecast; `/v1` and `/docs` still resolve | Planned |
| [Week 5](plans/week-5.md) | Monitoring and failure drill | Drift report in GCS; alert fired in a test; rollback proven; latency in README | Planned |
| [Week 6](plans/week-6.md) | Portfolio packaging | A stranger can understand and reproduce the project from the README alone | Planned |

## Human gates

Seven points where a human runs the command and reports back:

| Gate | After | What the human does |
|---|---|---|
| 0 | Week 0 | Create project, link billing, create state bucket, apply budget, run dataset recency queries, enable repo security settings |
| 1 | Week 1 | Run ingestion query, snapshot raw extract to GCS, run baselines, report MAE |
| 2 | Week 2 | Run tuning sweep, save MLflow screenshot, report best-trial metrics |
| 3 | Week 3 | Submit the Vertex pipeline run |
| 4a | Week 4a | Apply WIF and verify `attributeCondition` is non-empty, enable required checks, Dependabot, CodeQL, merge to deploy the first canary |
| 4b | Week 4b | Deploy the combined image, verify the page and widget |
| 5 | Week 5 | Run drift job, force an alert, run Locust, perform the rollback drill |

## Deviations from the original draft

Recorded here rather than silently applied, with dated bullets in [memory.md](memory.md):

- **Repo scaffold moved from Week 1 into Week 0.** Week 1's definition of done is `make check` green, which is impossible before `pyproject.toml` and the `Makefile` exist. Week 0 therefore runs longer than its original one-hour budget.
- **Week 4 split into 4a and 4b**, so the API ships and is verified before the frontend that consumes it exists.
- **A frontend was added** after the original draft had no UI at all.

## How to advance

1. One vertical slice per pull request.
2. Follow [rules.md](rules.md) plus the global TDD and ponytail user rules.
3. Update the status column here and append to [memory.md](memory.md) when a block completes or scope changes.
