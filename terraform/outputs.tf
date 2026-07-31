output "artifacts_bucket" {
  description = "MLflow artifacts and model binaries."
  value       = google_storage_bucket.artifacts.name
}

output "raw_bucket" {
  description = "Raw extract snapshots — the upstream-dataset-changed mitigation."
  value       = google_storage_bucket.raw.name
}

output "reports_bucket" {
  description = "Evidently drift reports. Private; read via signed URL."
  value       = google_storage_bucket.reports.name
}

output "bq_dataset" {
  description = "BigQuery dataset holding aggregates, features, and the prediction sink."
  value       = google_bigquery_dataset.main.dataset_id
}

output "artifact_registry" {
  description = "Docker repository for serving images."
  value       = google_artifact_registry_repository.docker.name
}

output "service_account_emails" {
  description = "The four service accounts, for wiring into Cloud Build and Cloud Run."
  value = {
    cicd      = google_service_account.cicd.email
    serving   = google_service_account.serving.email
    pipeline  = google_service_account.pipeline.email
    pr_checks = google_service_account.pr_checks.email
  }
}
