# The guardrail. Applied FIRST at Gate 0, before any resource that can spend:
#
#   terraform apply -target=google_billing_budget.monthly
#
# docs/architecture.md 10.5 targets under $10/month; this alerts against $15 so
# there is headroom to notice rather than to be surprised by an invoice.

resource "google_monitoring_notification_channel" "email" {
  project      = var.project_id
  display_name = "pedal-cast alerts"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }

  depends_on = [google_project_service.enabled]
}

resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account_id
  display_name    = "pedal-cast monthly budget"

  budget_filter {
    projects               = ["projects/${var.project_id}"]
    calendar_period        = "MONTH"
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.budget_amount_usd)
    }
  }

  # Early warning matters more than the final alarm: 50% of a $15 budget is
  # already over the monthly target.
  threshold_rules {
    threshold_percent = 0.5
  }

  threshold_rules {
    threshold_percent = 0.8
  }

  threshold_rules {
    threshold_percent = 1.0
  }

  # Fires when the month is *projected* to exceed the budget, which is the only
  # alert that arrives in time to act on.
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = [google_monitoring_notification_channel.email.id]
    disable_default_iam_recipients   = false
  }

  depends_on = [google_project_service.enabled]
}
