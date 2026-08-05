# Week 4b — Interactive city landing + live widget

[Master plan](../phases.md) · [design.md](../design.md) · [architecture.md](../architecture.md) §6

**Goal:** make the system legible in sixty seconds via an interactive Three.js city (mouse explore, click landmarks), with a widget that actually calls the API.

**Status:** planned. Blocked on the Week 4a response contract being frozen.

**Scope note:** Week 4b owns the full interactive experience. If it overruns, cut scene polish first — never testing, never the reduced-motion fallback, never the widget contract. Craft inspiration is [bruno-simon.com](https://bruno-simon.com/); this is **not** a driveable game (no vehicle, no physics). Interaction is orbit / pan / zoom and click, aimed at an AI / MLOps engineer portfolio.

---

## Deliverables

- `web/` — Vite + React + TypeScript, Tailwind, `@react-three/fiber` + `@react-three/drei` for the city, animate-ui via the shadcn CLI for panel chrome, Recharts for the forecast plot.
- Interactive city per [design.md](../design.md): landmarks open architecture, metrics, decisions, links, and the **live prediction widget** as HUD panels. Deep-link `?panel=…` for demo jumps.
- Widget: zone selector plus timestamp input, calls `POST /v1/predict` **on submit only**, renders 24 hours with Recharts. Four visible states — idle, loading, success, error — with HTTP 429 getting its own message.
- **Reduced-motion / no-WebGL fallback:** 2D scroll page with the same content (Lenis + animate-ui). Canvas does not mount.
- `Dockerfile` gains a Node build stage; only `dist/` is copied into the Python runtime stage. Lazy-load the Three.js chunk where practical.
- `src/serve/app.py` mounts `StaticFiles` **last**, after `/v1` and `/docs`. CSP updated only as needed for WebGL/workers, with the final policy recorded.
- `make check-web` (tsc, eslint, `npm audit`, Vitest) wired into `make check`. Dependabot gains an `npm` ecosystem entry for `web/`.

Only the API base URL goes into a `VITE_*` variable. Vite inlines those into the shipped bundle, so anything else there is public.

## Accessibility (requirements, not polish)

- `prefers-reduced-motion` (or missing WebGL) → 2D fallback; 3D does not mount.
- Every landmark reachable from a keyboard landmark list; panels trap focus; Escape closes.
- Forecast chart carries a table equivalent.
- Error and rate-limit states carry text, never colour alone.

## Tests

- Vitest: widget idle, loading, success, empty, and error states; 429 renders its specific message.
- Vitest: reduced-motion preference mounts the fallback and does not mount the canvas.
- Vitest: landmark → panel open/close and `?panel=` deep-link.
- Contract test (Python side): an unknown `/v1` path returns JSON, **not** `index.html`.
- Contract test: `/docs` still resolves after the static mount.

## Human gate 4b

```bash
make smoke           # build the combined image locally, verify API + city + fallback
# then merge to deploy
```

**Report back:** page loads; mouse orbit works; a landmark opens the widget and returns a forecast; reduced-motion fallback works; `/v1` and `/docs` still resolve; measured JS bundle size and cold start (publish honestly).

## Definition of done

- [ ] Interactive city live at the public URL (mouse explore + click landmarks).
- [ ] Widget returns a real forecast from the deployed model.
- [ ] Reduced-motion / no-WebGL fallback verified.
- [ ] `/v1/*` and `/docs` unaffected by the static mount.
- [ ] Bundle size and cold start measured and recorded in Results.
- [ ] `make check` green, including `check-web`.

## Results

| Item | Value |
|---|---|
| JS bundle (gzip, main + 3D chunk) | — |
| Image size before / after | — |
| Lighthouse accessibility score | — |
| Cold start with bundle | — |
| CSP deltas for WebGL | — |
