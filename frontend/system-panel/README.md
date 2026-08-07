# AMU Pulse — System Panel

## What AMU Pulse is

**AMU Pulse** is a precious-metals pricing, history and market-analysis service.
It collects gold and precious-metal prices from many sources — Iranian market
boards, wholesalers, world XAU feeds, the USD rate and the published premium
("bubble") — normalizes them into its own database, folds each asset's readings
into a single price, keeps the history as tickers and candles, and pairs that
with news to produce a directional read-out of the market: the *pulse*.

Its most fragile layer is the crawl, so sources are isolated behind pluggable
adapters that never raise: a gateway answers with a quote or with an error, and
one broken source leaves the rest of the system standing.

## What this project is

**This is the system panel of AMU Pulse** — the console the project's own
developers and operators run the service from, not the app end users see. That
one is `client-panel`, a sibling of this directory.

Everything here is aimed at whoever is on the hook for the running system:

- **Logs and reports** — every request and task run the backend ships to
  Elasticsearch, searchable, with the full trace behind a request id.
- **The guarded surface** — every `/panel/*` route the backend exposes: the
  source catalogue and its config, assets and their pricing order, symbols,
  bubbles, candles, and the admin accounts themselves.
- **An API explorer** — the panel reads the backend's own `openapi.json`, lists
  every operation it finds, and lets an operator build and send any request by
  hand with the current session's token. A new backend route shows up here
  without a frontend change.

English only, LTR only, dark only. It is an operator tool, not a product
surface.

## Running it

```bash
npm install
npm run dev          # http://localhost:5174
npm run type-check
npm test
npm run lint
```

`/api` is proxied to `VITE_PROXY_TARGET` (default `http://127.0.0.1:8000`), so
the browser stays same-origin in development. Copy `.env.example` to `.env` to
point at a different backend.

## Layout

```text
src/
├── core/            router, navigation map, env config
├── infra/http/      axios client, envelope unwrapping, token rotation
├── layout/          console shell (sidebar + topbar)
├── modules/         one folder per domain: auth, explorer, …
├── common/          shared components and the icon registry
└── views/           routes that belong to no single domain
```

## Backend surface this panel drives

| Section | Prefix | Guard |
| --- | --- | --- |
| Auth | `/auth/admins/{login,refresh,me}` | public / bearer |
| Logs | `/panel/logs` | admin |
| Assets | `/panel/assets` | admin |
| Sources | `/panel/sources` | admin |
| Symbols | `/panel/symbols` | admin |
| Bubbles | `/panel/bubbles` | admin |
| Candles | `/panel/candles` | admin |
| Admins | `/panel/admins` | super admin |

The guards are read off the path prefix, not off the contract: the backend's
dependencies check the `Authorization` header directly instead of declaring a
FastAPI security scheme, so `openapi.json` carries no `security` block.

## Status

Built: the scaffold, the HTTP layer with refresh-and-retry, sign in, the console
shell, and the API explorer over `openapi.json`.

Next: the logs and traces views, then a dedicated view per panel section.
