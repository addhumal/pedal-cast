# Security

`pedal-cast` is a public portfolio project. It serves a public, unauthenticated,
rate-limited prediction API and holds no user data.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting on this repository
(**Security → Report a vulnerability**). Please do not open a public issue for
anything exploitable.

I will acknowledge a report within a week. This is a personal project, not a
staffed product, so please size your expectations accordingly.

## Scope

In scope:

- The prediction API and the static frontend it serves.
- Infrastructure-as-code in `terraform/`, especially the Workload Identity
  Federation configuration.
- CI/CD configuration in `cloudbuild.yaml`.

Out of scope, because they are deliberate design decisions documented in
[docs/architecture.md](docs/architecture.md):

- **The API requires no authentication.** It is a public demo, rate-limited
  rather than authenticated ([PRD.md](docs/PRD.md) non-goals).
- **Cold starts.** Cloud Run scales to zero to stay inside a hobby budget.
- **Absence of a WAF.** Cloud Armor was evaluated against the under-$10/month
  budget; the decision and its price are recorded in the README.

## What this project does to protect itself

Detail in [docs/architecture.md](docs/architecture.md) §10. Briefly:

- No service-account keys anywhere. GitHub authenticates to GCP through
  Workload Identity Federation, with the provider pinned to this repository and
  a repo-scoped `principalSet` on the IAM binding.
- Pull-request builds run under a test-only service account with no deploy or
  registry-write permission, so a forked pull request gains nothing.
- Secret scanning, push protection, `gitleaks` in pre-commit and CI, and
  notebook output stripping.
- `ruff` security rules, CodeQL, Dependabot, `pip-audit`, and `npm audit` in the
  build gate.
- Every bucket private, with public access prevention enforced. The one manual
  state bucket at Gate 0 must be created the same way (see
  `terraform/versions.tf`); Terraform cannot create the bucket that holds its
  own state.

## Known dependency exceptions

`make check` currently ignores `PYSEC-2026-3552` (transitive `cryptography` via
`google-auth` / `evidently`). Forcing `cryptography>=50` collapses the `mlflow`
pin in the lockfile. Revisit when upstream allows a clean bump; do not treat the
ignore as permanent.
