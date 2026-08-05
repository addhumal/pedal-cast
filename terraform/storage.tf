# Every bucket here is private, with uniform bucket-level access and public access
# prevention ENFORCED (docs/architecture.md 10.1). This matters most for the
# reports bucket: wanting to view an Evidently HTML report is a standing
# temptation to make it public. Read those with a signed URL or `gcloud storage cp`.

locals {
  bucket_defaults = {
    location                    = var.region
    uniform_bucket_level_access = true
    public_access_prevention    = "enforced"
  }
}

# MLflow artifacts and model binaries.
resource "google_storage_bucket" "artifacts" {
  name                        = "${var.project_id}-artifacts"
  project                     = var.project_id
  location                    = local.bucket_defaults.location
  uniform_bucket_level_access = local.bucket_defaults.uniform_bucket_level_access
  public_access_prevention    = local.bucket_defaults.public_access_prevention
  force_destroy               = false

  versioning {
    enabled = true
  }

  # Experiment noise expires; registered models under models/ do not.
  # docs/architecture.md 10.5: "delete artifacts > 90 days except registered models".
  lifecycle_rule {
    condition {
      age            = var.artifact_retention_days
      matches_prefix = ["mlflow/", "staging/"]
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.enabled]
}

# Raw extract snapshots. Deliberately has NO expiry: this bucket is the
# docs/architecture.md 14 mitigation for the public dataset changing or
# disappearing, so deleting it would remove the thing it exists to protect.
resource "google_storage_bucket" "raw" {
  name                        = "${var.project_id}-raw"
  project                     = var.project_id
  location                    = local.bucket_defaults.location
  uniform_bucket_level_access = local.bucket_defaults.uniform_bucket_level_access
  public_access_prevention    = local.bucket_defaults.public_access_prevention
  force_destroy               = false

  # Cheaper storage after a month; snapshots are read rarely but must survive.
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  depends_on = [google_project_service.enabled]
}

# Evidently drift reports.
resource "google_storage_bucket" "reports" {
  name                        = "${var.project_id}-reports"
  project                     = var.project_id
  location                    = local.bucket_defaults.location
  uniform_bucket_level_access = local.bucket_defaults.uniform_bucket_level_access
  public_access_prevention    = local.bucket_defaults.public_access_prevention
  force_destroy               = true

  lifecycle_rule {
    condition {
      age = var.artifact_retention_days
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.enabled]
}
