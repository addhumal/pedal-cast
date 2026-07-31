# Week 4b — Landing page and live widget

[Master plan](../phases.md) · [design.md](../design.md) · [architecture.md](../architecture.md) §6

**Goal:** make the system legible in sixty seconds, with a widget that actually calls the API.

**Status:** planned. Blocked on the Week 4a response contract being frozen.

---

## Deliverables

- `web/` — Vite + React + TypeScript, Tailwind, animate-ui components pulled in via the shadcn CLI (copied into the repo, owned here, not a tracked dependency), `lenis/react` for smooth scroll.
- Scroll sections per [design.md](../design.md): hero, what it does, architecture, live widget, metrics, decisions, links.
- Widget: zone selector plus timestamp input, calls `POST /v1/predict` **on submit only**, renders 24 hours with Recharts. Four visible states — idle, loading, success, error — with HTTP 429 getting its own message rather than a generic failure.
- `Dockerfile` gains a Node build stage; only `dist/` is copied into the Python runtime stage, so the image grows by the bundle and nothing else.
- `src/serve/app.py` mounts `StaticFiles` **last**, after `/v1` and `/docs`.
- `make check-web` (tsc, eslint, `npm audit`, Vitest) wired into `make check`.

Only the API base URL goes into a `VITE_*` variable. Vite inlines those into the shipped bundle, so anything else there is public.

## Accessibility (requirements, not polish)

Lenis replaces native scrolling and animate-ui animates on scroll, so:

- `prefers-reduced-motion` disables lenis entirely and drops animations to instant state changes.
- Lenis is initialised with `anchors: true`, since it breaks in-page anchor links otherwise.
- Keyboard navigation and focus order verified with smooth scroll active; focus never lands off-screen.
- The forecast chart carries a table equivalent — a canvas plot alone is invisible to a screen reader.
- Error and rate-limit states carry text, never colour alone.

## Tests

- Vitest: widget idle, loading, success, empty, and error states; 429 renders its specific message.
- Vitest: reduced-motion preference disables smooth scroll and animation.
- Contract test (Python side): an unknown `/v1` path returns JSON, **not** `index.html`. This is the regression that route-mount ordering exists to prevent.
- Contract test: `/docs` still resolves after the static mount.

## Human gate 4b

```bash
make smoke           # build the combined image locally, verify both surfaces
# then merge to deploy
```

**Report back:** confirmation that the page loads, the widget returns a forecast, and `/v1` plus `/docs` still resolve.

## Definition of done

- [ ] Landing page live at the public URL.
- [ ] Widget returns a real forecast from the deployed model.
- [ ] `/v1/*` and `/docs` unaffected by the static mount.
- [ ] Reduced-motion path verified.
- [ ] `make check` green, including `check-web`.

## Results

| Item | Value |
|---|---|
| Bundle size | — |
| Image size before / after | — |
| Lighthouse accessibility score | — |
| Cold start with bundle | — |
