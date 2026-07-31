# pedal-cast — Design System

Related: [PRD.md](PRD.md) · [architecture.md](architecture.md)

Scope: the single-page React landing site in `web/`, which sells the project and embeds a live prediction widget. Built in Week 4b, after the API contract is frozen in Week 4a.

---

## Principles

- **The system is the product.** The page exists to make an MLOps pipeline legible in sixty seconds. Motion serves comprehension — a diagram revealing in the order data actually flows — never decoration for its own sake.
- **One honest number beats three vague ones.** Metrics shown are the measured ones, baselines included, with the model's weak segments visible rather than hidden.
- **Dark by default.** This reads as an engineering artifact, not a marketing site. No light-mode toggle in v1.
- **The widget must feel alive but cost nothing.** It fetches on submit, never on load, because every automatic fetch is a cold start and a bite out of a visitor's rate limit.

---

## Stack

- **React + Vite + TypeScript.** Static build, no SSR. Served by the FastAPI container (see [architecture.md](architecture.md) §6).
- **Tailwind CSS** for styling. No CSS-in-JS.
- **animate-ui** via the shadcn CLI — components are copied into `web/src/components/`, owned by this repo, not tracked as a dependency.
- **`lenis/react`** for smooth scroll, initialised with `anchors: true`.
- **Recharts**, arriving through the shadcn chart components, for the forecast plot.
- **Vitest** for component tests.

No icon library until something actually needs more than three icons.

---

## Layout

Single scrolling page, sections in this order:

1. **Hero** — what it predicts, one sentence, and the live public URL.
2. **What it does** — the problem and the zone-level forecast, in plain language.
3. **Architecture** — the Mermaid flow from [architecture.md](architecture.md) §3, revealed as it scrolls.
4. **Live widget** — zone selector, timestamp input, submit, 24-hour Recharts plot.
5. **Metrics** — baselines, model MAE, segment breakdown, p50/p95, cold start.
6. **Decisions** — the tradeoffs, including the ones that cost something.
7. **Links** — repo, Swagger `/docs`, LinkedIn.

Breakpoints are Tailwind defaults. The widget collapses to a stacked form under `md`.

---

## Color / type

| Token | Use |
|---|---|
| `bg-base` | Page background, near-black |
| `bg-raised` | Cards, the widget panel |
| `fg-primary` | Body copy |
| `fg-muted` | Captions, axis labels, secondary metrics |
| `accent` | Single accent for interactive elements and the forecast line |
| `accent-warn` | Rate-limit and error states only |

One accent colour. Charts inherit `accent` and `fg-muted` rather than introducing a palette.

Type: one sans stack for UI and headings, one mono stack for numbers, metrics, and code. Tabular figures wherever numbers sit in a column.

---

## Accessibility (hard constraints, not polish)

Lenis replaces native scrolling and animate-ui animates on scroll, so these are requirements with tests, not a wishlist:

- **`prefers-reduced-motion` disables lenis entirely** and drops animate-ui transitions to instant state changes.
- **Lenis is initialised with `anchors: true`.** It breaks in-page anchor links otherwise, which its own README states plainly.
- **Keyboard navigation and focus order are verified with smooth scroll active**, including that focus never lands off-screen.
- **The forecast chart carries a table or text equivalent.** A canvas plot alone is invisible to a screen reader.
- Colour is never the only signal — error and rate-limit states carry text.
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
- Content-Security-Policy is set by the serving middleware ([architecture.md](architecture.md) §10.4), so inline scripts and remote script sources need a deliberate decision, not a convenient exception.

---

## Code organization

```
web/src/
├── components/     # animate-ui components copied in, plus local ones
├── sections/       # one file per scroll section above
├── widget/         # form, chart, state machine, API client
├── lib/            # formatting, reduced-motion hook
└── styles/
```

Presentational components take props and hold no fetch logic. The widget's API calls live in `widget/`, so the rest of the page has no network code at all.
