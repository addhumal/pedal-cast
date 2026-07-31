# Week 4a — API, Docker, CI/CD

[Master plan](../phases.md) · [architecture.md](../architecture.md) §6, §8, §10

**Goal:** a hardened public API, deployed by a canary pipeline, with the Workload Identity setup provably locked to this repository.

**Status:** planned.

---

## Deliverables

- `src/serve/app.py` — `POST /v1/predict` (single and batch), `GET /v1/health`, `/v1/ready`, `/v1/metadata`. Swagger `/docs` enabled with example bodies, since it is the API-level demo surface.
- `src/serve/model_loader.py` — model-free image; artifact pulled from GCS at container start and cached in memory.
- `src/serve/middleware.py` — structured JSON logs, global exception handler leaking no stack traces, request size limit, per-IP rate limit, security headers. **Static-path exemptions for rate limiting and prediction logging are written now**, so Week 4b only adds the mount.
- Serving imports `src/features` directly — the [architecture.md](../architecture.md) §14 mitigation for train/serve skew.
- `Dockerfile` — multi-stage, slim base, non-root user, locked dependencies.
- `cloudbuild.yaml` — `make check`, build and push, canary at 10% traffic, smoke test, with promotion left to a manual `make promote`.
- Terraform: Cloud Run (min 0, max 2, CPU only), WIF pool and provider, `sa-pr-checks` for PR builds.
- **The response contract is frozen at the end of this block**, so Week 4b builds against a fixed target.

## Security, specifically

Three things here are the difference between working and safe:

- **`attribute_condition = "assertion.repository == 'addhumal/pedal-cast'"`** on the WIF provider. Without it the provider trusts every repository on GitHub, and Terraform applies without complaint.
- **`principalSet` scoped to `attribute.repository/addhumal/pedal-cast`** on the `workloadIdentityUser` binding, never the whole pool. Two gates: one decides who may exchange a token, the other who may impersonate.
- **The PR trigger runs as `sa-pr-checks`** with no deploy and no registry write, with `--comment-control=COMMENTS_ENABLED` set explicitly. A forked PR editing `cloudbuild.yaml` then gains nothing.

A Terraform validation check fails the build if the condition or the scoped binding is missing, because this is precisely the mistake that works in testing and stays broken for years.

## Tests

- Contract tests: valid and invalid payloads, error shapes, unknown zone, out-of-range timestamp, metadata correctness.
- Security headers present on responses.
- Rate limiting keyed off `X-Forwarded-For`, tested with a forged header — behind Cloud Run a naive key function throttles the entire world as one client.
- Batch endpoint respects the request size limit.

## Human gate 4a

```bash
cd terraform && terraform apply

# Verify the provider is actually locked. EMPTY OUTPUT MEANS VULNERABLE.
gcloud iam workload-identity-pools providers describe github-provider \
  --workload-identity-pool=github-pool --location=global \
  --format="value(attributeCondition)"

# Then merge a PR to trigger the first canary
make promote        # after the canary smoke test passes
```

In GitHub settings: add required status checks to the `main` rule now that Cloud Build exists, and enable Dependabot and CodeQL.

**Report back:** the public URL, the `attributeCondition` output, and the canary revision name.

## Definition of done

- [ ] Public URL returns predictions.
- [ ] A merge to `main` deploys a canary automatically.
- [ ] `attributeCondition` verified non-empty.
- [ ] Required status checks, Dependabot, and CodeQL enabled.
- [ ] `make check` green.

## Results

| Item | Value |
|---|---|
| Service URL | — |
| First canary revision | — |
| `attributeCondition` | — |
| Image size | — |
| Feature serving choice (BQ vs GCS parquet) | — |
