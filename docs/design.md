# pedal-cast — Design System

Related: [PRD.md](PRD.md) · [architecture.md](architecture.md)

Scope: the React landing experience in `web/`, an interactive Three.js city that makes the MLOps system legible, with a live prediction widget opened from landmarks. Built in Week 4b, after the API contract is frozen in Week 4a.

**Craft inspiration:** [bruno-simon.com](https://bruno-simon.com/). Immersive Three.js portfolio craft, not a clone. That site is a driveable game world; this one is for an AI / MLOps engineer. Exploration is mouse (orbit / pan / zoom) and click, never a vehicle, physics sim, or game loop.

---

## Principles

- **The system is the product.** The page exists to make an MLOps pipeline legible in sixty seconds. The 3D city is a spatial map of the system — zones, data flow, serving — not decoration for its own sake.
- **Engineer, not game designer.** Interaction serves comprehension and demoing the forecast. No scores, achievements, whispers, or driveable physics.
- **One honest number beats three vague ones.** Metrics shown are the measured ones, baselines included, with the model's weak segments visible rather than hidden.
- **Dark by default.** This reads as an engineering artifact, not a marketing site. No light-mode toggle in v1.
- **The widget must feel alive but cost nothing.** It fetches on submit, never on load, because every automatic fetch is a cold start and a bite out of a visitor's rate limit.

---

## Stack

- **React + Vite + TypeScript.** Static build, no SSR. Served by the FastAPI container (see [architecture.md](architecture.md) §6).
- **Three.js via `@react-three/fiber` + `@react-three/drei`.** Interactive city scene; mouse orbit / pan / zoom; clickable landmarks.
- **Tailwind CSS** for HUD / panel chrome. No CSS-in-JS.
- **animate-ui** via the shadcn CLI — panel transitions and 2D chrome; components copied into `web/src/components/`, owned by this repo.
- **`lenis/react`** only on the reduced-motion / no-WebGL fallback page (see Accessibility). Primary experience is the 3D canvas, not a long scroll.
- **Recharts**, arriving through the shadcn chart components, for the forecast plot inside the widget panel.
- **Vitest** for widget and landmark-panel state; canvas interaction smoke-tested lightly (no pixel golden masters).

No Rapier / physics. No Howler / soundtrack required in v1. No icon library until something actually needs more than three icons.

<!-- Three.js grows the JS bundle and can worsen Cloud Run cold start.
     Measure and publish honestly in Week 4b/5 results. Upgrade path:
     lazy-load the canvas chunk, or ship a static 2D hero and keep 3D behind a
     "Enter city" gate. -->

---

## Experience model

One full-viewport Three.js city (bike-share zones as the spatial metaphor). The visitor explores with the mouse and opens content by clicking landmarks — Bruno-style *spatial storytelling*, reframed for an AI engineer.

| Landmark | Opens |
|---|---|
| Hero / city overview | What it predicts — one sentence, public URL |
| Data / warehouse | What it does — problem and zone-level forecast in plain language |
| Pipeline / train | Architecture — Mermaid (or simplified) flow from [architecture.md](architecture.md) §3 |
| Station / zone cluster | **Live widget** — zone selector, timestamp, submit, 24-hour Recharts plot |
| Monitor / tower | Metrics — baselines, MAE, segments, p50/p95, cold start |
| Tradeoffs / signboard | Decisions — including bundle and cold-start cost of the 3D choice |
| Exit / links | Repo, Swagger `/docs`, LinkedIn |

Panels are HUD overlays (slide or fade over the canvas). Closing a panel returns focus to the city. Deep-linkable panel ids (`?panel=widget`) so the demo video and README can jump straight to a forecast.

Mobile: orbit still works with touch; landmarks remain tappable; panels go full-screen under `md`.

---

## Color / type

| Token | Use |
|---|---|
| `bg-base` | Page / canvas clear colour, near-black |
| `bg-raised` | HUD panels, the widget |
| `fg-primary` | Body copy |
| `fg-muted` | Captions, axis labels, secondary metrics |
| `accent` | Interactive landmarks, forecast line, focus rings |
| `accent-warn` | Rate-limit and error states only |

One accent colour. Charts and landmark highlights inherit `accent` and `fg-muted`.

Type: one sans stack for UI and headings, one mono stack for numbers, metrics, and code. Tabular figures wherever numbers sit in a column.

---

## Accessibility (hard constraints, not polish)

WebGL is not accessible on its own, so these are requirements with tests:

- **`prefers-reduced-motion` (or missing WebGL) swaps to a 2D fallback** — same content as landmarks, as a normal scroll page with Lenis (`anchors: true`) and animate-ui. The 3D canvas does not mount.
- **Every landmark has a keyboard-reachable control** in a skip-nav or landmark list, so the city is never mouse-only.
- **Panels trap focus while open** and restore it on close; Escape closes.
- **The forecast chart carries a table or text equivalent.** A canvas plot alone is invisible to a screen reader.
- Colour is never the only signal — landmarks and errors carry text labels.
- Contrast meets WCAG AA against `bg-base` and `bg-raised`.

---

## Widget behaviour

- Fetches on submit only.
- Shows four distinct states: idle, loading, success, error. Rate limiting (HTTP 429) gets its own visible message rather than a generic failure.
- Renders the `model_version` returned by the API, so the page always says which model answered.
- Never retries automatically. A failed request stays failed until the user asks again.

---

## Security

- **No secrets in `VITE_*` variables.** Vite inlines them into the shipped bundle, where anyone can read them. The frontend receives the API base URL and nothing else.
- The API is same-origin, so there is no CORS configuration and no third-party request surface.
- Content-Security-Policy is set by the serving middleware ([architecture.md](architecture.md) §10.4). Three.js may need an explicit CSP exception (e.g. `worker-src`, blob URLs) — decide in Week 4b and document the final policy; do not silently widen to `unsafe-inline` / `unsafe-eval` without recording why.

---

## Code organization

```
web/src/
├── world/          # R3F canvas, city scene, landmarks, camera controls
├── panels/         # HUD overlays opened by landmarks (one file per content block)
├── components/     # animate-ui copies plus local chrome
├── widget/         # form, chart, state machine, API client
├── fallback/       # 2D scroll page for reduced-motion / no-WebGL
├── lib/            # formatting, reduced-motion hook, panel deep-links
└── styles/
```

`world/` has no network code. The widget's API calls live in `widget/`. Panels are presentational shells that compose content.
