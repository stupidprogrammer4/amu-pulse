# amu-pulse

A **precious-metals pricing, history, and market-analysis service**.

`amu-pulse` collects gold and precious-metal prices from multiple sources, stores their history, lets consumers define their own aggregations, fetches related news, and produces a transparent market read-out — the "pulse" of the market — that consuming services can display.

> **Status:** the pricing engine, the panel API and the log stack run; the analysis side is still design. Sections marked in the roadmap say which is which.

## What it does

1. **Data collection** — gathers prices from buy/sell sites (via crawling) and from global market APIs, alongside the USD rate and the local premium ("bubble").
2. **Calculation & aggregation** — computes derived prices (e.g. by purity, with premium) and supports **user-defined aggregations** over prices.
3. **Storage & charts** — keeps price history and exposes it for charting.
4. **News** — fetches gold/market news for context.
5. **Market read-out** — combines charts and news to produce an analysis with a single directional score.

## The directional score

For each analysis, `amu-pulse` produces a score in **[-1, 1]**:

- closer to **+1** → conditions lean toward **buying**
- closer to **-1** → conditions lean toward **selling**
- around **0** → **hold**

The score is continuous on purpose, so it conveys *strength*, not just direction (0.9 and 0.3 both lean "buy," but very differently).

### Confidence travels with the score
Every score is paired with a **confidence** value. A 0.6 from clear, aligned signals is very different from a 0.6 the model half-guessed on conflicting inputs. Confidence lets a consumer know when to lean on the score and when to stay cautious.

### It's a suggestion, not financial advice
Output is explicitly framed as a **read-out and analysis**, not a buy/sell command. The service summarizes the situation ("price is up 3% over 7 days; three positive and two negative news items; overall tone cautious") and leaves the decision to the user.

### Explanations are required
The analysis component is asked to produce a **reason** alongside the number, not just the number. This gives users transparency, gives us something to debug, and tends to improve the score itself (the model has to "think" before committing).

## Feedback & evaluation loop

Users can mark a read-out as accurate or not. Just as important, the service records:

- exactly what data went into the analysis (which chart window, which news items),
- what the analysis said, and
- what the price actually did afterward.

Because the future real price is known, the system can grade its own past read-outs **automatically**, even without user feedback. This labeled data is used to **measure accuracy**, **improve prompts/logic**, and — much later — potentially train a smaller specialized model. (Note: per-user feedback does **not** train the LLM on its own; it feeds our evaluation, not the model's memory.)

## Architecture: decouple sources from consumers

Crawling is the **most fragile** part of the whole system — sites change markup, go down, or block requests. So the source layer is isolated from everything else:

```
Sources ──► Ingestion layer (one adapter per source) ──► your database ──► Aggregation · Charts · Analysis · API
 crawl                                                       (clean data)
 global API
 USD / premium
 news
```

Each source is a **pluggable adapter** that writes clean, normalized data into our own database. Everything downstream reads from that database — never directly from external sites — so one broken crawler leaves the rest of the system standing (that source just goes stale).

### Before investing in crawling
- Prefer any **official or public API/endpoint** a source offers — far more stable than parsing HTML.
- Check each source's **terms** — some prohibit crawling or will ban it. Verify which sources permit access before building against them.

## Running it

Everything runs from `backend/`. Each app is configured by a single
`config.yml` mounted into its container and reads no environment variable at
all, so nothing in Compose can override a setting. Copy `config.yml.sample` to
`config.yml` for running on the host and to `config.docker.yml` for running in
a container — they differ only in the addresses of Postgres, Redis and
Elasticsearch — and keep the two in step. Both are git-ignored.

```sh
./run.sh                # infrastructure only: postgres, redis, rabbitmq, elasticsearch
./run.sh -a -f          # a working api on an empty database (app + migrate + seed)
./run.sh -e -m          # everything, ai and log shippers included
./run.sh -A <name>      # the first super admin, prompting for the password
./run.sh -p             # what is running, and whether it is healthy
./run.sh -t worker      # follow one service's logs
./run.sh -d             # stop everything, keep the data
./run.sh -h             # every flag
```

Infrastructure always comes up; the flags say what joins it (`-a` app, `-i` ai,
`-l` logs, `-e` all three) and what runs on the way (`-m` migrations, `-s` seed,
`-f` both). Bare `./run.sh` is what the integration tests need. Compose profiles
decide what runs; `run.sh` decides in what order, because alembic has to finish
before the api that reads its tables starts, and it waits on the healthchecks
rather than returning the moment a container is created.

| Service | Address |
| --- | --- |
| API | <http://localhost:8000> · OpenAPI at `/docs` |
| ai API | <http://localhost:8100> |
| Kibana | <http://localhost:5601> |
| RabbitMQ | <http://localhost:15672> |

Those host ports are the only thing Compose reads an environment for: put
`API_PORT`, `POSTGRES_PORT` and the rest in `backend/.env` when something on
the host already holds one. The applications themselves still read nothing but
`config.yml`.

### Tests

```sh
cd backend/api
pytest tests/unit          # no services needed
pytest tests/integration   # needs ./run.sh (infrastructure)
```

## Roadmap

### Landed

- [x] **Source catalogue** — every source with its own config, credentials and the error its last fetch left behind
- [x] **Assets** — what we publish a price for, and the order of markets each one is priced from (two markets may share a level)
- [x] **Symbols** — the lines a source actually quotes: a gram of 18 carat in Rial, a mesghal from a wholesaler, an ounce abroad. Three symbols, one asset
- [x] **Source adapters** — Iranian market boards, wholesalers, world XAU feeds, and the published premium. A gateway never raises: it answers with a quote or with an error
- [x] **Sign-in** — the sources that need credentials are signed in on their own weekly schedule
- [x] **The crawl** — every 30 seconds: read the config, call every source at once, cache each reading under its symbol, and stamp every source with what it just did
- [x] **Price calculator** — fold a symbol's readings into one price per asset: convert units (mesghal → gram, ounce → gram) and currency (cent → Rial), drop the outliers, aggregate the rest by the asset's own rule, and walk the asset's markets until one of them answers
- [x] **Aggregation rule per asset** — median, mean, min, max or a quartile, chosen for each asset and applied to that asset's readings
- [x] **Bubble** — settle every published premium into one per asset, and price world parity off it
- [x] **Price ticker** — a snapshot of every price on the five-minute marks, drawn back as a chart over the window a caller asks for, with how far the price moved across it
- [x] **Candles** — every price and every source reading folds into an open five-minute window in Redis; a closed window is written down as a candle, and the hourly, five-hourly and daily candles are rolled up out of it on Tehran's clock
- [x] **Candle charts** — one endpoint per asset and per source, drawn as fine as the span asked for: a day five minutes at a time, a week hour by hour, two months five hours at a time, longer day by day
- [x] **Admins and their sign-in** — an admin is a username, a password and whether they are a super admin. The password is bcrypt over an HMAC of the password and a configured pepper, derived on a worker thread so the cost factor burns its own CPU rather than the event loop's, and a sign-in against a username that does not exist still runs a hash so both halves of a wrong guess take the same time. Sign-in answers with a JWT pair; trading the refresh token spends it, so one that leaks is good for a single use
- [x] **A guarded surface and a public one** — every route the panel drives sits under `/panel` behind the guard, and a route cannot be added to it without inheriting one, because the guard is on the router rather than on the handlers. Prices, charts and reading a media file are the public half. The guard reads the token's claims and asks no database, so a request costs no query; the price is that a change of role lands on the next refresh
- [x] **First super admin** — `docker compose run --rm scripts create-super-admin -u <name>` puts one into a fresh database, prompting for the password so it stays out of the shell history. Rerunning it leaves an existing admin alone rather than resetting a password someone has since changed
- [x] **Logging on the ELK stack** — the api, the worker and the scheduler write one ECS-shaped JSON object per line, Filebeat reads them off the Docker host and indexes them into a data stream, and an ILM policy rolls it daily and drops a backing index after two weeks. Every logger in the process goes through one handler, uvicorn's and taskiq's included, and one correlation id follows a request or a task execution from the first line to the last
- [x] **Reading the logs back** — `/panel/logs` searches them by level, logger, container, correlation id, free text and time; `/panel/logs/traces/{id}` gathers everything one request or one task wrote, oldest first; `/panel/logs/chart/{bucket}` counts what a container wrote per bucket, with the min, max and mean computed by Elasticsearch rather than in Python. The filter options travel with the answer and are computed outside the filter that uses them, so picking one level does not leave the others unreachable
- [x] **Docker** — one image per app and a compose file behind profiles: a bare `docker compose up` is Postgres, Redis, RabbitMQ and Elasticsearch, which is what the tests need and nothing more, while the app, the ai stack and the log shippers each sit behind a profile of their own. `run.sh` drives the orderings profiles cannot express, since alembic has to finish before the api that reads its tables starts

### Next up

Each bullet below is scoped to stand on its own as one issue. Owners are
the person the work is assigned to, not the only person allowed to touch it.

#### Backend — Aida

- [ ] **Finish `identity`** — `identity/admins` and `identity/auth` have landed; `identity/auth` owns no table of its own, as intended. Still to build: `identity/users` for the people, with a first name, a last name, a mobile number and an email address, each of them filled in only if the user wants to, and `identity/otp` for the one-time codes a user signs in with
- [ ] **`ops/messages`** — one module that sends an email or an SMS, and the only way anything leaves the system as a message. Every message we send goes through it, the OTP codes included
- [ ] **`content` group — news and analysis** — a `content/news` module and a `content/analysis` module, both crawled from news and signal sites. A row keeps the whole record, the site it came from included; the crawl follows the shape `price/engine` already uses (a gateway per source that never raises, a flusher that writes clean rows)

#### Backend — Pouya

- [ ] **Signal agent** — the smart agent that reads the charts and the news and produces the signal

#### DevOps

- [ ] **Deployment** — the images and the compose file exist and run the whole stack locally; what is missing is the production side: TLS, a real Elasticsearch password, secrets that do not sit in a mounted config file, and somewhere to run it

#### Frontend

- [ ] **Admin console** *(first)* — the screens the system is run from: sources and their config, assets and their pricing order, symbols, margins, the charts to see what the engine is doing, and the log search and its charts
- [ ] **User app** — the public side: prices, charts, news and the read-out

#### Still to design

- [ ] User-defined aggregations
- [ ] Analysis component → score in [-1, 1] + confidence + reason
- [ ] Automatic evaluation loop from realized future prices
- [ ] User feedback capture
- [ ] Presentation (e.g. a colored gauge from sell-red to buy-green)

## License

TBD.
