# pedal-cast — Decision Memory

Append-only. Newest entries at the **bottom**. Do not rewrite history; add a
superseding entry instead.

Agents: consult before reversing a prior choice. After a notable decision,
append a dated bullet here.

---

## 2026-07-30 — Bootstrap

- Seeded governance docs from `~/.cursor/templates/governance/`.
- Added initial `docs/design.md` as the source-of-truth architecture document for the bikeshare-demand-mlops project.
- Repository was empty; created initial commit with governance and design docs.

---

## 2026-07-31 — Week 0 foundation

**Naming.** Project is `pedal-cast`, matching the remote. The earlier
`bikeshare-demand-mlops` name is retired.

**Doc restructure.** The 278-line architecture document moved from
`docs/design.md` into `docs/architecture.md`, replacing the 84-line summary that
duplicated its §3. `docs/design.md` now holds the UI design system, which is what
the governance template reserves that filename for. §1 was trimmed to a pointer at
`PRD.md` and §13 to a pointer at `phases.md`, so goal/scope and the week plan each
live in exactly one place.

**Plan structure.** `docs/phases.md` is now the master week plan, with a detail
sub-doc per block in `docs/plans/`. Reused rather than adding a new master, which
would have made `phases.md` a stale third copy.

**Always-apply context cost.** `@docs/architecture.md` was removed from
`.cursor/rules/project-memory.mdc`. That file tripled in size and the rule injects
on every turn. Agents read it on demand instead; `docs/rules.md` and the week plans
point at it.

**Python 3.12 via uv.** The local interpreter is 3.14, ahead of reliable
`xgboost` and `kfp` wheels. uv manages a pinned 3.12, so the system Python is
untouched. The full runtime stack was declared up front so that resolving `kfp`,
`mlflow`, and `evidently` together surfaced conflicts on day one — it resolved
cleanly, 217 packages.

**Scaffold moved from Week 1 to Week 0.** Week 1's definition of done is
`make check` green, which is impossible before `pyproject.toml` and the `Makefile`
exist. Week 0 therefore exceeds its original one-hour budget. Deviation from the
original §13 plan, recorded rather than silently applied.

**UI added, having originally been out of scope.** A React landing page with a
live prediction widget: Vite, Tailwind, animate-ui via the shadcn CLI,
`lenis/react`, and Recharts through the shadcn chart components. Week 4 split into
4a (API, verified first) and 4b (the frontend that consumes it).

**One-service hosting, with a known ceiling.** The static build is served by the
same FastAPI container, so there is one image, one deploy, and no CORS. The cost is
that frontend commits produce model-style canary revisions, softening the "a new
revision means a new model" semantics in §6. Marked with a `ponytail:` comment;
upgrade path is a separate Cloud Run service or a CDN. Considered and rejected for
now: a second Cloud Run service (cold-starts the landing page) and a CDN (leaves
the single-platform story).

**Swagger `/docs` is the API demo surface**, kept enabled in production.

**Public-repo security posture.** The repo is public, so §10 was expanded well
past the original four bullets. Two items were live vulnerabilities in the original
design:

1. The WIF provider had no `attribute_condition`. Without one it trusts GitHub's
   entire issuer, so any repository on GitHub could exchange a token for this
   project — and Terraform applies happily without it. Now pinned to
   `assertion.repository == 'addhumal/pedal-cast'`, with a repo-scoped
   `principalSet` on the IAM binding as a second gate.
2. The PR trigger would have run as `sa-cicd`. Anyone can fork a public repo and
   open a PR editing `cloudbuild.yaml`, which would have handed a stranger deploy
   credentials. A fourth service account, `sa-pr-checks`, now runs PR builds with
   log-write permission and nothing else.

Also added: gitleaks and nbstripout in pre-commit, ruff's `S` ruleset rather than a
separate bandit dependency, `pip-audit` in the gate, Dependabot on `uv.lock`,
public access prevention on every bucket, and `LICENSE` plus `SECURITY.md`.

**Branch protection.** `main` requires a pull request and passing checks, so all
work happens on feature branches from Week 0 onward. Protection arrives in two
steps because requiring checks is meaningless before Cloud Build exists: force-push
and deletion protection at Gate 0, required status checks at Gate 4a.

**Cloud Armor deferred** to a Week 5 decision, since it is roughly $5–7/month
against an under-$10 budget. Either outcome gets recorded in the README with the
price attached.

**Terraform state in GCS**, with the state bucket created by hand at Gate 0 — the
single manual resource, since Terraform cannot create the bucket that stores its
own state. Backend bucket is supplied via `-backend-config` at init time because
the project ID is unknown until Gate 0.
