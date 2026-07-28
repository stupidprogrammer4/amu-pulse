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

- [ ] Source adapters: buy/sell sites, global price API, USD rate, premium
- [ ] Clean-data schema and price-history storage
- [ ] User-defined aggregations
- [ ] Charting endpoints
- [ ] News ingestion
- [ ] Analysis component → score in [-1, 1] + confidence + reason
- [ ] Automatic evaluation loop from realized future prices
- [ ] User feedback capture
- [ ] Presentation (e.g. a colored gauge from sell-red to buy-green)

## License

TBD.
