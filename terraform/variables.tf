variable "project_id" {
  description = "GCP project ID. Created by hand at Gate 0."
  type        = string
}

variable "region" {
  description = "Primary region. Defaults to London, matching the london_bicycles dataset."
  type        = string
  default     = "europe-west2"
}

variable "billing_account_id" {
  description = "Billing account the project is linked to. Needed for the budget."
  type        = string
}

variable "budget_amount_usd" {
  description = "Monthly budget ceiling. Alerts fire against this; the spend target is under $10."
  type        = number
  default     = 15
}

variable "alert_email" {
  description = "Address that receives budget and alerting-policy notifications."
  type        = string
}

variable "github_repository" {
  description = "owner/name of the GitHub repo allowed to federate into this project."
  type        = string
  default     = "addhumal/pedal-cast"

  validation {
    condition     = can(regex("^[^/]+/[^/]+$", var.github_repository))
    error_message = "Must be exactly owner/name — it is interpolated into the WIF attribute condition."
  }
}

variable "artifact_retention_days" {
  description = "Days before non-model artifacts are deleted. Registered models are exempt."
  type        = number
  default     = 90
}
