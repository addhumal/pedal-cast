# Week 0 — Docs restructure, scaffold, Terraform, security baseline

[Master plan](../phases.md) · [architecture.md](../architecture.md)

**Goal:** make the repo buildable and safe to be public, and settle the dataset question that everything downstream depends on.

**Status:** in progress.

---

## Deliverables

### Documentation restructure

- [x] Absorb the original 278-line `design.md` into [architecture.md](../architecture.md), replacing the thin summary that duplicated its §3.
- [x] Trim §1 to a pointer at [PRD.md](../PRD.md) and §13 to a pointer at [phases.md](../phases.md), so goal/scope and the week plan each live in one place.
- [x] Repurpose [design.md](../design.md) as the real UI design system.
- [x] Rename the project to `pedal-cast` throughout.
- [x] Correct §12 repo structure for the `docs/` layout, `docs/plans/`, and `web/`.
- [x] Drop `@docs/architecture.md` from the always-apply rule, with a comment recording why.
- [x] This master plan plus eight sub-docs.

### Toolchain

- [x] `uv` 0.12.0 and Terraform 1.15.8 installed locally.
- [x] `pyproject.toml` pinned to Python 3.12 with the full runtime stack and dev group, plus `uv.lock` (217 packages, resolved with no conflicts).
- [x] `Makefile`: `check`, `check-py`, `check-web`, `fmt`, and targets for training and pipeline work. Cloud-cost targets are labelled HUMAN ONLY and pause before running.
- [x] `src/config.py` — pydantic-settings holding `T_NOW`, dataset IDs, promotion thresholds, `maximum_bytes_billed`.

### Security baseline (public repo)

- [x] `.gitignore` covering `.env*`, credential JSON patterns, `*.tfstate*`, `mlruns/`, `mlflow.db`, `node_modules/`, `.venv`, `dist/`. Note `.terraform.lock.hcl` is committed on purpose.
- [x] `.pre-commit-config.yaml` with `gitleaks`, `nbstripout`, `detect-private-key`, and large-file guards.
- [x] Ruff `S` ruleset enabled; `pip-audit` wired into `make check-py`.
- [x] `LICENSE` (MIT) and `SECURITY.md`.
- [x] `.github/dependabot.yml` using the `uv` ecosystem. npm and docker ecosystems get added when `web/` and the `Dockerfile` exist.

### Terraform

- [x] `backend "gcs"` with partial config; bucket supplied at init time.
- [x] **Billing budget with a $15 alert, first** — thresholds at 50%, 80%, 100%, plus a forecasted-spend rule, which is the only alert that arrives early enough to act on.
- [x] BigQuery dataset; three GCS buckets, all with uniform bucket-level access and public access prevention **enforced**.
- [x] Artifact Registry with cleanup policies.
- [x] Service accounts `sa-cicd`, `sa-serving`, `sa-pipeline`, and `sa-pr-checks`, with bucket- and dataset-scoped bindings rather than project-wide grants.
- [x] `terraform validate` passes; `terraform fmt` clean.

WIF and Cloud Run are deliberately **not** here — they belong to Week 4a, along with the strict `attribute_condition`.

## Tests

`src/config.py` carries the checks that matter: `T_NOW` must be timezone-aware and must be in the past. A future value would push every split beyond the end of the data and yield empty frames rather than an error, which is the kind of failure that wastes an afternoon.

9 tests passing. `make check` green end to end: ruff, format, mypy, `pip-audit` (no known vulnerabilities), pytest, and `check-web` skipping cleanly since `web/` does not exist yet.

## Human gate 0

Run in this order; each step depends on the one before.

```bash
# 1. Authenticate as the personal account and create the project
gcloud auth login          # aditya.dhumal2364@gmail.com
gcloud projects create PROJECT_ID
gcloud billing projects link PROJECT_ID --billing-account=BILLING_ACCOUNT_ID

# 2. The one manual resource: Terraform cannot create the bucket holding its own state
gcloud storage buckets create gs://PROJECT_ID-tfstate --uniform-bucket-level-access

# 3. Budget first, so the guardrail is live before anything else exists
cd terraform && terraform init
terraform apply -target=google_billing_budget.budget

# 4. Dataset recency — the answer decides T_NOW and the holidays country
bq query --use_legacy_sql=false --maximum_bytes_billed=100000000 \
  'SELECT MAX(start_date) FROM `bigquery-public-data.london_bicycles.cycle_hire`'
# repeat for austin_bikeshare and new_york_citibike
```

Then in GitHub repo settings: enable secret scanning, push protection, private vulnerability reporting, and force-push/deletion protection on `main`. Required status checks wait for Gate 4a, since no checks exist yet.

**Verify gitleaks actually detects, once.** The hook passes on a clean repo, which proves only that it ran. Confirm the ruleset is live by scanning a throwaway file outside the repo:

```bash
D=$(mktemp -d)
printf 'aws_access_key_id = "AKIA<20 chars>"\n' > "$D/sample.tf"   # invent a value
gitleaks detect --no-git --source "$D" --redact    # expect a finding and a non-zero exit
rm -rf "$D"
```

This is a human step on purpose: agents should not be writing credential-shaped strings, even fake ones. A secret scanner assumed to work is the same class of mistake as a WIF provider assumed to be scoped.

**Report back:** the three max dates. They get recorded in [architecture.md](../architecture.md) §2 along with the chosen `T_NOW`, plus a dated bullet in [memory.md](../memory.md).

## Definition of done

- [ ] Budget alert live in the new project.
- [ ] Dataset chosen and `T_NOW` recorded in [architecture.md](../architecture.md) §2.
- [ ] `make check` green.
- [ ] Repo security settings enabled.

## Results

| Item | Value |
|---|---|
| GCP project ID | — |
| State bucket | — |
| `london_bicycles` max date | — |
| `austin_bikeshare` max date | — |
| `new_york_citibike` max date | — |
| Dataset chosen | — |
| `T_NOW` | — |
| `holidays` country | — |
