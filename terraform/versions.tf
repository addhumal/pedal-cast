terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # State lives in GCS, never on a laptop.
  #
  # The bucket is supplied at init time because the project ID is not known until
  # Gate 0, and because Terraform cannot create the bucket that stores its own
  # state. That one bucket is the single manual resource in this project:
  #
  #   gcloud storage buckets create gs://PROJECT_ID-tfstate --uniform-bucket-level-access
  #   terraform init -backend-config="bucket=PROJECT_ID-tfstate"
  backend "gcs" {
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
