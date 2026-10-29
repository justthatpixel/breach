# Breach — web

Next.js (App Router) frontend. Level select, the game screen, and the
debrief — all driven by fixture data in `src/fixtures/level3.ts`, transcribed
from the design mockups' own sample data (`design/*.dc.html`). No backend is
wired up yet: "Run attack" calls a canned mock result rather than the real
engine (M2) — that wiring happens in M5.

## Dev

```bash
npm install
npm run dev       # http://localhost:3000
```

## Tests

```bash
npm run test       # Vitest — store logic
npm run test:e2e   # Playwright — plays Level 3 end to end, incl. a
                    # prefers-reduced-motion run
```

`npm run build` and `npm run lint` are also wired up.
