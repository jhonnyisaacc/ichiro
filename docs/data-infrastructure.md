# Data and infrastructure plan

Python is the research language: pandas or polars, pyarrow, DuckDB, pytest, and uv for environments. This matches Rocket's research stack and idatsy's public `python-base-uv` template. The collector can move to Rust or TypeScript later if latency matters. The Phoenix Rise SDK has both.

Nothing here signs or trades. Collectors are read-only.

## Data sources

| Source | What | Access | Use |
| --- | --- | --- | --- |
| Phoenix REST, exchange data | orderbook, market stats history, candles, funding rate history, mark price, exchange status, market fills | `perp-api.phoenix.trade` (see the docs index at docs.phoenix.trade/llms.txt) | candles and funding for backtests, fills for order flow, status for the venue-health filter |
| Phoenix WebSocket | live book and trade updates | `wss://perp-api.phoenix.trade/v1/ws` | real-time features and alerts |
| Phoenix liquidation history | liquidation events | REST history endpoints | H8 cascades |
| Phoenix market parameters | leverage tiers, margin, fees, tick and lot sizes | docs and API | sizing, liquidation distance, cost model |
| Phoenix index and mark price | index for RWA perps, mark bounds | docs and API | stale-price filter |
| Solana RPC or a geyser stream | raw program accounts and transactions | own or third-party RPC | ground truth, reconstructing fills that the API misses |
| Third-party indexers | Phoenix perps trades and positions | for example Bitquery's Phoenix Perpetuals API | backfill, cross-checking |
| Pyth | oracle prices | Hermes API | reference price, stale-oracle detection |
| CEX perps (Binance, Bybit, Hyperliquid) | candles, funding, open interest, liquidations | public APIs | lead-lag reference, regime context, longer history than Phoenix |
| Frontier Traders leaderboards | public volume and PnL ranks | website | trader research only, not a trading signal |

Phoenix perps are young. History may be months, not years. Backtests that need longer history use CEX data as a proxy, with a cost model widened for Phoenix's spread, and say so in the report.

## Storage

```
data/
├── manifests/                     committed: one JSON per dataset with source, range, row count, sha256
├── raw/<venue>/<channel>/<market>/date=YYYY-MM-DD/*.parquet      not committed
└── derived/<feature_set>/<version>/<market>/date=YYYY-MM-DD/*.parquet   not committed
```

- Raw data is append-only and never edited. Fixes go in a new derived version.
- Every row has `event_ts` (exchange time) and `recv_ts` (collector time). Features use `recv_ts` for point-in-time correctness, so a backtest never sees data before it arrived.
- Parquet partitioned by date, queried with DuckDB. QuestDB or ClickHouse can come later for live tick storage.
- Large data lives outside git, for example in a Hugging Face dataset or an object store, with the manifest committed.

## Features (v0.1)

| Group | Features |
| --- | --- |
| Price | returns over 1m, 5m, 1h, 4h; ATR(14) on 5m, 15m, 1h; realized volatility percentiles; EMA(20, 50) |
| Candle shape | body, upper wick, lower wick, wick-to-body ratio, position of close in range |
| Range | 20-bar high and low, 50-bar mean and standard deviation, RSI(14) |
| Volume | volume z-score over 24h, taker buy and sell notional, imbalance ratio |
| Book | spread, depth at 5 and 10 levels, top-of-book imbalance |
| Funding | current rate, 30-day percentile, accrued funding per position |
| Liquidations | 5m liquidation notional, percentile, side |
| Regime | `hot`, `trend_up`, `trend_down`, `range`, `no_trade` |
| Venue | status, seconds since last book update, oracle staleness |

## Backtest harness sketch

```
ichiro/
├── pyproject.toml
├── src/ichiro/
│   ├── data/        loaders that read manifests and Parquet
│   ├── features/    pure functions: frame in, frame out
│   ├── rules/       regime, setups S1 to S5, sizing, exits, overlays (one module each)
│   ├── sim/         event loop, fill model, cost model, funding accrual, liquidation check
│   ├── journal/     writes the JSONL decisions from the journal template
│   └── report/      metrics, bootstrap, baseline, report writer
└── tests/           synthetic fixtures only
```

Design:

1. Event-driven over closed bars, with an optional orderbook replay mode for scalps. One code path for backtest and paper, so the paper bot runs the same rules.
2. The fill model takes the configured slippage, fills limits only when price trades through by one tick, and fills stops at the worse of the stop price and the next bar's open.
3. Costs come from the charter's cost model. Funding accrues at the venue's funding interval.
4. The liquidation check uses the venue's leverage tiers. A liquidation in a backtest is reported as a defect in the rules.
5. Output is the journal JSONL, so backtests, paper runs, and manual trades are analyzed with the same tools.
6. Walk-forward splitting and the holdout lock live in the harness, not in notebooks. The holdout reader refuses a second read for the same strategy version unless a new version is tagged.

## Monitoring and alerts (Phase 1)

| Alert | Trigger | Channel |
| --- | --- | --- |
| Hot market | the `hot` flag turns on for a market | Telegram or Slack |
| Setup armed | an S1 to S4 trigger fires on a closed bar | same, with a pre-filled journal entry |
| Funding extreme | funding beyond the 90th or 10th percentile | same |
| Liquidation spike | 5m liquidations above the 95th percentile | same |
| Collector health | no data for 60s, or a candle gap | same, high priority |

Alerts inform a human. They never place orders.
