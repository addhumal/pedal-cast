# Week 6 — Portfolio packaging

[Master plan](../phases.md) · [PRD.md](../PRD.md)

**Goal:** a stranger understands and can reproduce the project from the README alone.

**Status:** planned.

---

## Deliverables

By this point the README metrics table has been filled incrementally across Weeks 1, 2, and 5, so this block assembles rather than authors.

- **README** — Mermaid architecture diagram, the populated metrics table including baselines, decisions and tradeoffs, honest limitations, cost breakdown against the actual bill, and an agentic-workflow section naming where the human gates were.
- **60-second demo video** filmed against the live landing page.
- **LinkedIn post** — no hard metrics in the post itself, link to the repo.
- Repo pinned on GitHub.

## Limitations to state plainly

Being honest here is the point, not a disclaimer:

- Weather uses same-day **observed** values, not forecasts. A real system would need forecast weather at inference time.
- No online feature store; lag and rolling features come from a precomputed serving table. Feast is the named upgrade.
- `T_NOW` is simulated inside a historical data window. The README states the window explicitly.
- Frontend commits produce model-style canary revisions, because one Cloud Run service serves both. The upgrade path is a separate service or a CDN.
- Cold start is real and published rather than hidden; `min-instances=1` is the fix and its cost is stated.
- Cloud Armor decision from Week 5, with the price it would have cost.

## Definition of done

- [ ] A stranger can understand and reproduce the project from the README alone.
- [ ] Demo video recorded and linked.
- [ ] Cost breakdown reflects the real bill, not the estimate.
- [ ] All limitations stated plainly.
- [ ] `make check` green.

## Results

| Item | Value |
|---|---|
| Demo video link | — |
| Total spend over the build | — |
| README review by a stranger | — |
