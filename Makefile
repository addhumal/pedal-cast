.DEFAULT_GOAL := help
SHELL := /bin/bash

# Targets marked HUMAN ONLY spend money or mutate cloud state. Agents must not run
# them (docs/rules.md invariant 2). They are here so a human has one obvious way to
# run each step, not so automation can.

.PHONY: help
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Gate — must be green before any task counts as complete
# ---------------------------------------------------------------------------
.PHONY: check
check: check-py check-web ## Run the full gate (Python + frontend)

.PHONY: check-py
check-py: ## Lint, format check, typecheck, dependency audit, tests
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src tests
	uv export --no-hashes --format requirements-txt | uv run pip-audit --requirement /dev/stdin
	uv run pytest

.PHONY: check-web
check-web: ## Frontend gate (skipped until web/ exists in Week 4b)
	@if [ -d web ]; then \
		cd web && npm ci && npm run check; \
	else \
		echo "web/ not present yet (Week 4b) — skipping"; \
	fi

.PHONY: fmt
fmt: ## Apply formatting and safe lint fixes
	uv run ruff format .
	uv run ruff check --fix .

# ---------------------------------------------------------------------------
# Data and training — local
# ---------------------------------------------------------------------------
.PHONY: baselines
baselines: ## Compute the seasonal-naive and t-24h baselines (Week 1)
	uv run python -m src.train.baselines

.PHONY: train
train: ## Train once with current config (Week 2)
	uv run python -m src.train.pipeline

.PHONY: tune
tune: ## Randomized search, logged to MLflow (Week 2)
	uv run python -m src.train.tune

.PHONY: pipeline-compile
pipeline-compile: ## Compile the KFP pipeline to JSON — local, no cost (Week 3)
	uv run python -m pipelines.pipeline

# ---------------------------------------------------------------------------
# HUMAN ONLY — these spend money or mutate cloud state
# ---------------------------------------------------------------------------
.PHONY: ingest
ingest: ## HUMAN ONLY. Run BigQuery ingestion (Week 1)
	@echo "HUMAN ONLY: runs BigQuery jobs. Ctrl-C to abort." && sleep 3
	uv run python -m src.data.ingest

.PHONY: pipeline-run
pipeline-run: ## HUMAN ONLY. Submit the pipeline to Vertex AI (Week 3)
	@echo "HUMAN ONLY: submits a paid Vertex AI run. Ctrl-C to abort." && sleep 3
	uv run python -m pipelines.submit

.PHONY: smoke
smoke: ## Build the container locally and hit /v1/predict (Week 4)
	docker build -t pedal-cast:local .
	uv run python -m src.serve.smoke

.PHONY: deploy
deploy: ## HUMAN ONLY. Deploy a canary revision to Cloud Run (Week 4)
	@echo "HUMAN ONLY: deploys to Cloud Run. Ctrl-C to abort." && sleep 3
	./scripts/deploy.sh

.PHONY: promote
promote: ## HUMAN ONLY. Shift 100% traffic to the canary revision
	@echo "HUMAN ONLY: promotes the canary to all traffic. Ctrl-C to abort." && sleep 3
	./scripts/promote.sh

.PHONY: rollback
rollback: ## HUMAN ONLY. Shift 100% traffic to the previous revision
	./scripts/rollback.sh

.PHONY: drift-run
drift-run: ## HUMAN ONLY. Execute the Evidently drift Cloud Run Job (Week 5)
	@echo "HUMAN ONLY: runs a Cloud Run Job. Ctrl-C to abort." && sleep 3
	./scripts/drift_run.sh

.PHONY: load-test
load-test: ## HUMAN ONLY. Locust burst against /v1/predict (Week 5)
	uv run --group load locust -f locustfile.py
