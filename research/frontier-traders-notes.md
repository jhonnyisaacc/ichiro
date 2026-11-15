# Frontier Traders Season 1: finalist notes

Status: v0.1, written 2026-11-15, the day after the London Grand Final.

## How to read this file

Each claim carries a label:

- `SOURCED`: a public page states it. The source is in [Sources](#sources).
- `SOURCED (weak)`: a community-edited or secondary page states it, and no official page confirms it.
- `UNVERIFIED`: it came from the brief that started this repo, or from a post that could not be retrieved. Treat it as a lead, not a fact.

Notes record public trading behavior only. Nothing personal goes in this file.

## Event summary

- The Solana Foundation runs Frontier Traders. Season 1 ran Sept 21 to Nov 7, 2026, and Phoenix and Solflare perps volume counted. `SOURCED` [S1]
- Season leaderboards rank real traders on Season PnL and Season Volume. Maker and taker fills both count toward leaderboard volume. Crate milestones count taker volume only. `SOURCED` [S1]
- The terms exclude wash trading, self-trading, spoofing, layering, and "uneconomic trading lacking a legitimate economic purpose." `SOURCED` [S3]
- The live events are "a perpetual futures paper trading game, built on Phoenix's onchain orderbook," with "multiple game modes with varying leverage and hot-market multipliers." `SOURCED` [S2]
- Qualifier events: Belgrade (Aug 27), Seoul (Sep 30), Singapore (Oct 6, at Solana Summit). `SOURCED` [S1]
- London Grand Final: eight finalists and three rounds of live trading. The official pages list the date as 14 November 2026 in one place and Nov 15 in another. `SOURCED` [S1][S4]
- Eight seats: three qualifier winners, best Season PnL, Season Volume Champion, one Frontier Wildcard, and two seats from new season tracks. `SOURCED` [S1]
- Prize: US$250,000 in stablecoin, or a Porsche 911 GT3 RS. `SOURCED` [S1]
- Up to 500x leverage in some game modes. `UNVERIFIED`. The official pages say only "varying leverage."
- idatsy won the Grand Final. `UNVERIFIED`. A secondary news post reports a comeback from a loss of about $50K to a profit of about $152K late in the final. The post could not be retrieved while writing, and no official result page was found.

See [event-mechanics.md](event-mechanics.md) for the rules that matter for strategy design.

## Finalists

The finalist list and seat labels come from the event page [S4].

### idatsy (online winner seat)

- Seat: "online winner." `SOURCED` [S4]
- Season Volume Champion, about $187M or more in volume. `UNVERIFIED`. The Sol Eco Perps volume board lists iDatsY at #5 with $8.68M. `SOURCED (weak)` [S5]
- Public GitHub shows Rust and Python infrastructure work, including a QuestDB wrapper, a uv Python template, and Solana and Ethereum protocol tooling. `SOURCED` [S6]
- Style: very aggressive, high-leverage directional swings and fast flips, with composure under pressure. `UNVERIFIED`
- Reported Grand Final path: a deep drawdown, then a late recovery to first. `UNVERIFIED`

Extractable rules:

1. Volume and PnL are different games. Leaderboard volume rewards turnover, and turnover without an edge is a cost. ichiro measures PnL net of costs and treats volume as a constraint, not a goal.
2. Tooling as an edge: a time-series store such as QuestDB fed by a low-latency collector is plausible infrastructure for fast flips. This is an inference from the public repos, not an observation of trading.
3. A recovery from a deep drawdown in a three-round paper game is survivorship. The rule set does not copy it. The drawdown halt in [v0-rules](../strategies/v0-rules.md) would have stopped that path.

### Galileo Wilson (Singapore seat)

- Seat: Singapore qualifier winner. `SOURCED` [S4]
- Style: scalps wicks, shorts pumps selectively, avoids overtrading, sets take-profit levels in advance, and says "sometimes the best trade is no trade." `UNVERIFIED`
- Process: journals thesis, invalidation, and take-profit before every entry. `UNVERIFIED`

Extractable rules, the most systematizable of the eight:

1. Wick rejection entry: a candle whose wick is at least twice its body and whose close is back inside the prior range. See H1 in [hypotheses](hypotheses.md).
2. Pump fade: short only the top tail of short-horizon moves, and only after rejection. See H2.
3. Planned exits: TP levels and invalidation are fixed before entry and logged. See the [journal template](../strategies/journal-template.md).
4. A no-trade state is a valid output of the regime filter. See H4.
5. Trade-count budget per session, to avoid overtrading. See H6.

### Sailor / solana_sailor (Belgrade seat)

- Seat: Belgrade qualifier winner. `SOURCED` [S4], and `SOURCED (weak)` [S7] for the handle.
- Style: no public detail found. `UNVERIFIED`

### Saewoo / HYNSAEWOOO (Seoul seat)

- Seat: Seoul qualifier winner. `SOURCED` [S4]. The handle mapping is `UNVERIFIED`.
- Style: no public detail found.

### Maurits / mauritsneo (Frontier Wildcard)

- Seat: wildcard. `SOURCED` [S4]. The handle mapping is `UNVERIFIED`.
- Style: no public detail found.

### Richard Ptardio (London seat)

- Seat listed as "London." `SOURCED` [S4]
- Traditional trading-desk background. `UNVERIFIED`
- Lead to research: desk-style risk habits such as fixed risk per trade and daily loss limits. These are already the base of the v0 risk overlays.

### Tristan Thompson (NBA champion)

- Celebrity seat. `SOURCED` [S4]
- Not a source of systematic rules. Kept for completeness.

### Jadoodoo (fan favourite)

- Seat: fan favourite. `SOURCED` [S4]
- Style: no public detail found.

## Cross-finalist patterns

| Pattern | Evidence | Systematizable? |
| --- | --- | --- |
| Volume farming for leaderboards and crates | Season rules reward volume [S1]. Individual behavior `UNVERIFIED` | No. It optimizes ranking, not PnL. Track turnover cost instead |
| High-leverage directional swings | `UNVERIFIED` | Partly. Direction and timing can be tested. Contest leverage cannot be used |
| Fast liquidations in high-leverage modes | `UNVERIFIED` | Yes, as a risk lesson: minimum distance to liquidation at entry |
| Hot-market multipliers steer activity | "hot-market multipliers" [S2] | Yes. Hot-market detection becomes a regime feature (volume and volatility z-scores) |
| Journaling, predefined exits, selectivity | Galileo, `UNVERIFIED` | Yes. Journal schema, fixed TP and SL, trade budget |
| Composure under pressure | `UNVERIFIED` | Replaced by hard rules. A bot has no nerves, but it also has no judgment |

## Limits of copying these traders

1. Survivorship: eight finalists out of a whole season, with one winner from three rounds. Many traders with the same style blew up and are invisible.
2. Paper fills: the final was a simulation on Phoenix's orderbook. Real fills at size take depth, move the book, and pay fees and funding.
3. Contest payoff: a winner-takes-all prize rewards variance. The best strategy for a contest is close to the worst strategy for a capital account. Leverage of 500x, if it was offered, belongs to the contest only.
4. Volume incentives: crates and volume boards pay for turnover, which bends behavior away from net PnL.
5. Discretion: reading the room, sensing crowd positioning, and deciding when to sit out are real skills that rules approximate poorly. See the automatable versus discretionary table in the [roadmap](../docs/roadmap.md).
6. Sample size: a live final gives a few hours of trades per person. No statistical conclusion about any trader's edge can be drawn from it.

## Open questions

1. What were the exact game modes, leverage caps, hot-market multipliers, starting balances, and scoring rules per round? Source: Campaign Terms and the event recording.
2. Is the Grand Final recording public, so trades can be reconstructed from the stream?
3. Are finalists' real Season 1 wallets public on the leaderboard? Their fills on Phoenix would give real, not paper, behavior.
4. Which Phoenix markets were "hot" during the season, and did hot status lead or lag volatility?
5. How much of the Season Volume Champion's volume was maker versus taker, and what did it cost in fees net of rebates and crates?

## Sources

- [S1] Frontier Traders, Season One: https://www.frontiertraders.com/seasons/s1
- [S2] Frontier Traders, How it works: https://www.frontiertraders.com/seasons/s1/how-it-works
- [S3] Solana Compass, Frontier Traders Season 1 opens: https://solanacompass.com/news/frontier-traders-season-1-opens-with-1m-in-perps-rewards-on-phoenix-and-solflare
- [S4] Luma, Frontier Traders: Grand Final: https://luma.com/frontier-traders-grand-final-london
- [S5] Frontier Traders, Sol Eco Perps Volume campaign: https://www.frontiertraders.com/campaigns/soleco-perps
- [S6] GitHub, idatsy: https://github.com/idatsy
- [S7] IQ.wiki, Frontier Traders: Seoul Showdown (community-edited): https://iq.wiki/events/frontier-traders-seoul-showdown
- Unretrieved: KuCoin community post on the Grand Final comeback: https://www.kucoin.com/news/community/BTC/6af94fc440903b0007ae1dc6
