# Four service accounts, each holding the least it can do its job with
# (docs/architecture.md 10.1). Bindings are scoped to individual buckets and the
# one dataset rather than granted project-wide, because "storage.objectAdmin on
# the project" is how least privilege quietly stops being least privilege.

# --- Accounts ---------------------------------------------------------------

resource "google_service_account" "cicd" {
  account_id   = "sa-cicd"
  project      = var.project_id
  display_name = "CI/CD — build and deploy"
}

resource "google_service_account" "serving" {
  account_id   = "sa-serving"
  project      = var.project_id
  display_name = "Serving — Cloud Run runtime identity"
}

resource "google_service_account" "pipeline" {
  account_id   = "sa-pipeline"
  project      = var.project_id
  display_name = "Pipeline — Vertex AI training runs"
}

# Runs pull-request builds. This repository is public, so anyone can fork it and
# open a PR that edits cloudbuild.yaml. That PR runs as this account, which is why
# it can do nothing but run tests and write logs — no deploy, no registry write.
resource "google_service_account" "pr_checks" {
  account_id   = "sa-pr-checks"
  project      = var.project_id
  display_name = "PR checks — test-only, deliberately powerless"
}

# --- sa-cicd: build, push, deploy ------------------------------------------

resource "google_project_iam_member" "cicd_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_artifact_registry_repository_iam_member" "cicd_push" {
  project    = var.project_id
  location   = google_artifact_registry_repository.docker.location
  repository = google_artifact_registry_repository.docker.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.cicd.email}"
}

# Needed to deploy a Cloud Run service that *runs as* sa-serving. Scoped to that
# one account, not granted project-wide.
resource "google_service_account_iam_member" "cicd_acts_as_serving" {
  service_account_id = google_service_account.serving.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cicd.email}"
}

# --- sa-serving: read a model, read features, write logs -------------------

resource "google_storage_bucket_iam_member" "serving_reads_artifacts" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.serving.email}"
}

resource "google_bigquery_dataset_iam_member" "serving_reads_dataset" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.main.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.serving.email}"
}

resource "google_project_iam_member" "serving_bq_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.serving.email}"
}

resource "google_project_iam_member" "serving_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.serving.email}"
}

resource "google_project_iam_member" "serving_metrics" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.serving.email}"
}

# --- sa-pipeline: train, write features, register models -------------------

resource "google_project_iam_member" "pipeline_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_bigquery_dataset_iam_member" "pipeline_writes_dataset" {
  project    = var.project_id
  dataset_id = google_bigquery_dataset.main.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_project_iam_member" "pipeline_bq_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_storage_bucket_iam_member" "pipeline_artifacts" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_storage_bucket_iam_member" "pipeline_raw" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_project_iam_member" "pipeline_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

# --- sa-pr-checks: logs and nothing else ----------------------------------

resource "google_project_iam_member" "pr_checks_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.pr_checks.email}"
}
