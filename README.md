# amu-pulse

A **precious-metals pricing, history, and market-analysis service**.

`amu-pulse` collects gold and precious-metal prices from multiple sources, stores their history, lets consumers define their own aggregations, fetches related news, and produces a transparent market read-out — the "pulse" of the market — that consuming services can display.

> **Status:** early development. This README describes the intended design.

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

### Next up

Each bullet below is scoped to stand on its own as one issue. Owners are
the person the work is assigned to, not the only person allowed to touch it.

#### Backend — Aida

- [ ] **Split `identity` into four modules** — `identity/admins` holds the superadmins, a username and a password and nothing else; `identity/users` holds the people, with a first name, a last name, a mobile number and an email address, each of them filled in only if the user wants to; `identity/otp` holds the one-time codes a user signs in with; `identity/auth` is pure auth logic and owns no table of its own
- [ ] **`ops/messages`** — one module that sends an email or an SMS, and the only way anything leaves the system as a message. Every message we send goes through it, the OTP codes included
- [ ] **`content` group — news and analysis** — a `content/news` module and a `content/analysis` module, both crawled from news and signal sites. A row keeps the whole record, the site it came from included; the crawl follows the shape `price/engine` already uses (a gateway per source that never raises, a flusher that writes clean rows)

#### Backend — Pouya

- [ ] **Job and API logging on the ELK stack** — every task run and every request shipped to Elasticsearch, searchable in Kibana
- [ ] **Signal agent** — the smart agent that reads the charts and the news and produces the signal

#### DevOps

- [ ] **Dockerize the project** — a Dockerfile per service (API, worker, scheduler) and a compose file bringing up Postgres, Redis and Elasticsearch alongside them, so the whole stack starts with one command in development and ships as an image in production

#### Frontend

- [ ] **Admin console** *(first)* — the screens the system is run from: sources and their config, assets and their pricing order, symbols, margins, and the charts to see what the engine is doing
- [ ] **User app** — the public side: prices, charts, news and the read-out

#### Still to design

- [ ] User-defined aggregations
- [ ] Analysis component → score in [-1, 1] + confidence + reason
- [ ] Automatic evaluation loop from realized future prices
- [ ] User feedback capture
- [ ] Presentation (e.g. a colored gauge from sell-red to buy-green)

## License

TBD.
