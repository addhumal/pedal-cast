# Week 5 — Monitoring and failure drill

[Master plan](../phases.md) · [architecture.md](../architecture.md) §9

**Goal:** prove the system notices when something is wrong, and prove recovery works by breaking it on purpose.

**Status:** planned.

---

## Deliverables

- `monitoring/drift_job.py` — Evidently. Reference is the training feature distribution; current is a replayed post-`T_NOW` window that advances each week. The simulated-time design is what makes drift real and demonstrable on historical data. Outputs an HTML report to GCS plus a drift-share metric.
- Terraform: Cloud Run Job, Cloud Scheduler entries (weekly retrain, weekly drift), and alert policies for error rate > 2% over 5 min, p95 > 500 ms over 15 min, and drifted-feature share > 30%.
- `monitoring/dashboard.json` — one dashboard: traffic, latency, errors, drift metric.
- `locustfile.py` — light 10–50 RPS burst **against `/v1/predict` specifically**, so static asset serving does not flatter the published p95.
- README metrics table gains p50, p95, and cold start.

The drift-report bucket stays private. Reports are read via signed URL or `gcloud storage cp` — wanting to view the HTML is not a reason to make a bucket public.

## Cloud Armor decision point

With real traffic visible in the dashboard, decide whether a WAF and edge rate limiting justify roughly $5–7/month against the under-$10 budget. Either answer goes in the README **with the price attached**; "we chose app-level limits and here is what that gives up" reads better than silence.

## Tests

- Drift job produces a report and a metric on a fixture window with known drift.
- Drift-share threshold logic tested either side of 30%.
- Alert policy definitions validated by `terraform plan`.

## Human gate 5

```bash
make drift-run              # Cloud Run Job — human only
make load-test              # Locust, once, publish the numbers

# Failure drill: break it on purpose, then recover
make deploy                 # deploy a deliberately broken revision
make rollback               # shift 100% traffic back
```

**Report back:** p50/p95, cold-start time, drift-share value, confirmation the alert fired, and screenshots of the rollback.

## Definition of done

- [ ] Drift report in GCS.
- [ ] An alert fired in a test.
- [ ] Rollback proven, with screenshots.
- [ ] Latency numbers in the README table.
- [ ] Weekly retraining schedule live.
- [ ] Cloud Armor decision recorded.
- [ ] `make check` green.

## Results

| Item | Value |
|---|---|
| p50 (warm) | — |
| p95 (warm) | — |
| Cold start | — |
| Drift share on first replay window | — |
| Alert fired | — |
| Rollback duration | — |
| Cloud Armor decision | — |
| Actual monthly cost | — |
