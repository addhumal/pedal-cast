# bikeshare-demand-mlops — Engineering Rules

Project-specific rules. Global Cursor User Rules already cover TDD and ponytail
(lazy senior / ask before acting) — do not duplicate them here. Add only what is
unique to this repo.

Related: [PRD.md](PRD.md) · [architecture.md](architecture.md) · [memory.md](memory.md)

## Project invariants

1. `make check` must pass before any task is considered complete.
2. Cloud-cost commands (pipeline runs, deploys, BQ queries) are human-run only; agents do not run them.
3. No secrets, credentials, or JSON service-account keys in code or commits.
4. All feature code is shared between training and serving (`src/features`) to prevent model/feature skew.
5. Time-based splits are never random; all leakage rules in `docs/design.md` §4 are hard constraints.

## Scope

- Follow global ponytail ladder (YAGNI → reuse → stdlib → dep → min code).
- Fewest files; fix root cause once.
- Mark deliberate ceilings with a `ponytail:` comment + upgrade path.

## Verification

```bash
make check
```

## Decision log

Append notable decisions to [memory.md](memory.md) (newest last).
