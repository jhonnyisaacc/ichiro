# Galileo Wilson

- Seat or context: Singapore qualifier winner, Frontier Traders Season 1 Grand Final. `SOURCED`: https://luma.com/frontier-traders-grand-final-london
- Last reviewed: 2026-11-15

## Observed behavior

- Markets traded: unknown.
- Holding time: short. Scalps. `UNVERIFIED`
- Direction bias: selective shorts of pumps. `UNVERIFIED`
- Entry pattern: wick rejections. `UNVERIFIED`
- Exit pattern: take-profit levels fixed before entry. `UNVERIFIED`
- Risk behavior: avoids overtrading. Treats "no trade" as a valid decision. `UNVERIFIED`
- Process: journals thesis, invalidation, and take-profit before each entry. `UNVERIFIED`

## Metrics

No public metrics found.

## Extractable rules

| Rule | Hypothesis |
| --- | --- |
| Wick at least 2x body, close back inside range, enter against the wick | H1 |
| Short the top 1% of 1h moves on the first lower high | H2 |
| No-trade regime filter | H4 |
| Trade budget per session | H6 |
| Thesis, invalidation, TP1 and TP2 logged before entry | [journal template](../../strategies/journal-template.md) |

## What cannot be copied

Reading order flow on the screen in real time, and judging which pump is exhausted. H1 and H2 approximate this with fixed thresholds and will miss some of it.

## Open questions

1. Which markets and timeframes?
2. Typical leverage outside the contest?
3. Is a public trading log or Phoenix wallet available?
