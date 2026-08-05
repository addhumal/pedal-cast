# pedal-cast — Engineering Rules

Project-specific rules. Global Cursor User Rules already cover TDD and ponytail
(lazy senior / ask before acting) — do not duplicate them here. Add only what is
unique to this repo.

Related: [PRD.md](PRD.md) · [architecture.md](architecture.md) · [memory.md](memory.md)

## Project invariants

1. `make check` must pass before any task is considered complete. It covers Python and the frontend.
2. Cloud-cost commands (pipeline runs, deploys, BigQuery queries, `terraform apply`) are human-run only. Agents do not run them.
3. No secrets, credentials, or JSON service-account keys in code or commits. Nothing secret in `VITE_*` variables, which Vite inlines into the shipped bundle.
4. All feature code is shared between training and serving (`src/features`) to prevent model/feature skew.
5. Time-based splits are never random; the leakage rules in [architecture.md](architecture.md) §4 are hard constraints, and the tests that enforce them do not get relaxed.
6. Every change reaches `main` by pull request. `main` is branch-protected and a merge deploys.
7. **Stacked PRs for separate features.** One concern per PR. Base each PR on the branch it depends on (not a kitchen-sink branch). When the base merges into `main`, retarget the next PR to `main`. Do not pile unrelated features onto an open PR.
8. The Workload Identity provider must always carry an `attribute_condition` pinned to this repository, and the IAM binding must use a repo-scoped `principalSet`. See [architecture.md](architecture.md) §10.1 — an empty `attributeCondition` means anyone on GitHub can impersonate the service account.
9. No bucket is ever made public, including the drift-report bucket. Read reports via signed URL or `gcloud storage cp`.
10. The UI accessibility constraints in [design.md](design.md) are requirements with tests, not polish: `prefers-reduced-motion` (or missing WebGL) mounts the 2D fallback and does not mount the Three.js canvas; landmarks remain keyboard-reachable; the forecast chart carries a text equivalent.

## Scope

- Follow global ponytail ladder (YAGNI → reuse → stdlib → dep → min code).
- Fewest files; fix root cause once.
- Mark deliberate ceilings with a `ponytail:` comment + upgrade path.

## Verification

```bash
make check       # ruff (incl. S security rules), mypy, pip-audit, pytest, then check-web
make check-web   # tsc, eslint, npm audit, vitest
```

## Decision log

Append notable decisions to [memory.md](memory.md) (newest last).
