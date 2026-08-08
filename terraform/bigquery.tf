resource "google_bigquery_dataset" "main" {
  dataset_id = "pedal_cast"
  project    = var.project_id
  # Not var.region: a query cannot read `bigquery-public-data` (US multi-region) and
  # write to a dataset elsewhere, so ingestion only works if this dataset is US.
  location    = var.bq_location
  description = "Hourly station aggregates, feature tables, and the prediction log sink."

  # No default_table_expiration_ms: feature tables must persist. Cost is
  # controlled by partitioning (per table, Week 1) and by maximum_bytes_billed
  # on every job, not by expiring the data.

  delete_contents_on_destroy = false

  depends_on = [google_project_service.enabled]
}

resource "google_artifact_registry_repository" "docker" {
  provider = google

  repository_id = "pedal-cast"
  project       = var.project_id
  location      = var.region
  format        = "DOCKER"
  description   = "Serving container images, tagged with the git SHA."

  # Keep the last few images; every merge to main pushes one.
  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }

  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      older_than = "${var.artifact_retention_days * 24}h"
    }
  }

  depends_on = [google_project_service.enabled]
}
