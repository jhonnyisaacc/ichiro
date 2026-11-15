# Rule set v0.1

Status: draft, not frozen. Every number is `PROPOSED` (see the [charter](../CHARTER.md)). A version is frozen by tagging the commit `strategy-v0.1` before the first scored backtest. After that, any change makes v0.2.

The rule set is five modules that run in order. Each module returns a value a machine can check.

```
regime filter → setup trigger → sizing → order plan → exits
       ↑                                              ↓
       └──────────── risk overlays (veto any step) ───┘
```

## 1. Market and regime filter

A market can be traded only if all of these hold at decision time. Every feature uses only data available before the decision bar closes.

| Check | Rule | Status |
| --- | --- | --- |
| History | at least 90 days of candles | PROPOSED |
| Liquidity | median spread over 24h at or under 5 bp, and top-of-book depth on each side at least 20x the planned order notional | PROPOSED |
| Volatility band | ATR(14, 1h) percentile over 30 days between 20 and 95 | PROPOSED |
| Funding | absolute 8h-equivalent funding at or under 0.1% | PROPOSED |
| Venue health | Phoenix exchange status normal, no stale oracle or index price for more than 60s | PROPOSED |

Regime label, used by the setups:

| Label | Definition |
| --- | --- |
| `hot` | volume z-score over 24h at least 2.0, and realized volatility percentile over 30 days at least 70 |
| `trend_up` / `trend_down` | EMA(20, 1h) above / below EMA(50, 1h), and the 4h close above / below EMA(50, 4h) |
| `range` | neither trend condition holds |
| `no_trade` | any filter check fails, or a risk overlay is active |

`no_trade` is a normal output. It is logged like a trade decision.

## 2. Setup triggers

Each setup defines the trigger, the invalidation price, and the planned targets before an order exists. Bars are closed bars. Entry is at the next bar's open, or with a limit at the trigger close.

### S1: Wick rejection (track: scalp, 15m; swing, 1h)

- Allowed regimes: `hot`, `range`.
- Trigger, long: lower wick at least 2.0x the body, the low below the prior 20-bar low, and the close back above that prior low. The short is the mirror.
- Invalidation: the wick extreme minus 0.25 ATR(14) for a long, or plus 0.25 ATR(14) for a short.
- Targets: TP1 at 1R, TP2 at the midpoint of the 20-bar range or 2R, whichever is nearer.
- Hypothesis: H1.

### S2: Pump fade (track: scalp)

- Allowed regimes: `hot`.
- Trigger: the 1h return is above the 99th percentile of the trailing 30 days, then the first 5m lower high closes below the prior 5m low.
- Invalidation: the pump high plus 0.25 ATR(14, 5m).
- Targets: TP1 at 1R, TP2 at a 38.2% retrace of the pump.
- Skip if funding is below its 10th percentile, so shorts are already crowded.
- Hypothesis: H2, H3.

### S3: Momentum continuation (track: swing)

- Allowed regimes: `trend_up` or `trend_down`.
- Trigger, long: a pullback to EMA(20, 1h) that holds (the close is above it), followed by a close above the pullback's high.
- Invalidation: the pullback low minus 0.5 ATR(14, 1h).
- Targets: TP1 at 1.5R, then trail the remainder.
- Skip if funding is above its 90th percentile.
- Hypothesis: H3, H8.

### S4: Mean-reversion extreme (track: swing)

- Allowed regimes: `range`.
- Trigger, long: the close is at least 2.5 standard deviations below the 50-bar mean on 1h, and RSI(14) is under 20, then a bar closes back inside 2.0 standard deviations.
- Invalidation: the extreme low minus 0.5 ATR(14, 1h).
- Target: the 50-bar mean.
- Time stop: 24h.

### S5: Order-flow imbalance (track: scalp, research only in v0.1)

- Trigger: aggressive buy notional over 5m is at least 3x aggressive sell notional, top-of-book bid size is at least 2x ask size, and price breaks the 1h high.
- Invalidation: back below the breakout level by 0.25 ATR(14, 5m).
- Status: data feasibility first (fills with side, book snapshots). Not traded in Phase 3 until H8 or a dedicated hypothesis passes.

## 3. Sizing

Fixed-fractional risk to the stop.

```
risk_amount   = equity × risk_per_trade                 (0.5%, PROPOSED)
stop_distance = |entry − invalidation| / entry
notional      = risk_amount / (stop_distance + round_trip_cost)
leverage      = notional / equity
```

Rejection rules, applied in order:

1. `leverage` above the track cap (3x swing, 5x scalp, `PROPOSED`) means notional is cut to the cap. The trade is skipped if the resulting R:R to TP1 falls below 1.0.
2. The distance to liquidation must be at least 3x `stop_distance`. Otherwise skip.
3. Notional above 5% of the market's top-10-level depth means skip. The book cannot absorb it.
4. Phoenix leverage-tier limits for the position size always apply on top.

## 4. Order plan

- Entries use post-only limit orders at the trigger close, falling back to a taker entry only if the S1 or S2 setup is still valid one bar later. The fallback is logged.
- The stop is a reduce-only stop-market order, placed in the same action as the entry.
- TP1 and TP2 are reduce-only limit orders.
- The order plan is written to the journal before submission. A paper fill that has no journal row is a bug.

## 5. Exits

| Exit | Rule | Status |
| --- | --- | --- |
| TP1 | close 50% at TP1, then move the stop to break-even plus costs | PROPOSED |
| TP2 | close the rest at TP2 | PROPOSED |
| Trailing (S3 after TP1) | stop trails at the highest close minus 2 ATR(14, 1h) | PROPOSED |
| Invalidation | stop hit, full exit | PROPOSED |
| Time stop | scalp 4h, swing 72h, S4 24h: close at market if neither TP nor SL hit | PROPOSED |
| Regime exit | if the regime turns `no_trade` because of venue health, close | PROPOSED |
| Funding exit | if accrued funding exceeds 0.3R, close | PROPOSED |

No widening a stop. No adding to a loser.

## 6. Risk overlays

Overlays can veto any step and close positions.

| Overlay | Rule | Status |
| --- | --- | --- |
| Daily loss stop | realized plus unrealized PnL at or below -2% of start-of-day equity: flatten, no entries until 00:00 UTC | PROPOSED |
| Weekly loss stop | at or below -5% of start-of-week equity: no entries until Monday 00:00 UTC | PROPOSED |
| Drawdown halt | at or below -10% from the equity peak: flatten, stop, and require a human review entry in the journal before restarting | PROPOSED |
| Loss streak | 3 consecutive losing trades: 24h pause | PROPOSED |
| Concurrency | at most 2 open positions, and at most 1 per correlated cluster (for example SOL and SOL-beta memecoins) | PROPOSED |
| Trade budget | at most 4 entries per market per 24h | PROPOSED |
| Data staleness | last book update older than 10s, or a gap in candles: no entries | PROPOSED |
| Event blackout | no new entries 30 min before and after scheduled high-impact macro releases | PROPOSED |

## 7. Journal

Every decision, including `no_trade` and skipped setups, writes a journal row using the [journal template](journal-template.md). A trade without a pre-entry row is invalid and is excluded from performance, with the exclusion counted.

## What v0.1 leaves out on purpose

- Contest-style leverage and comeback sizing (martingale-like behavior).
- Volume farming.
- Discretionary overrides. A human can stop the system at any time but cannot force an entry through the rules.

## v0.1 implementation spec (frozen 2026-11-15, before any scored run)

This section pins down how the rules above are computed in the first backtest. Where it is narrower than the prose above, this section wins for v0.1.

### Data and split

- Markets: Phoenix SOL, BTC, ETH, pooled. Manifest: `data/manifests/phoenix-v0.1.json`.
- Phoenix trading was thin before February 2026: under $2M per month per market. Scored data therefore starts at 2026-02-01 00:00 UTC. Earlier bars are used only to warm up features.
- Holdout: the last 20% of the scored span by time, the same cutoff for all markets. The first 80% is development, reported in 3 equal folds. No parameter is fitted on any fold.
- Costs per side: taker 3.5 bp, plus the half spread and 1 tick measured from the order-book snapshot in the manifest. Funding: the hourly Phoenix series, charged on notional while the position is open. Positive rate means longs pay.

### Features (all from closed bars only)

- ATR(14): Wilder. EMA: standard span. RSI(14): Wilder.
- 1h features are joined to 15m bars from the last fully closed 1h bar.
- `vol_z`: the 24h rolling sum of 1h quote volume, z-scored against the previous 30 days of that series.
- `rv_pct`: the percentile of the 24h realized volatility of 1h log returns against the previous 30 days.
- `atr_pct`: the percentile of ATR(14, 1h)/close against the previous 30 days.
- `funding_8h`: the last hourly rate times 8.

### Regime and filters

- `hot`: `vol_z >= 2.0` and `rv_pct >= 0.70`.
- `trend_up`: EMA(20, 1h) above EMA(50, 1h), and the last closed 4h close above EMA(50, 4h). `trend_down` is the mirror. `range` is neither.
- Base filter, always on: `|funding_8h| <= 0.001`.
- H4 filter, the variable under test: `0.20 <= atr_pct <= 0.95` and `rv_pct >= 0.20`. Spread history does not exist, so the spread part of H4 is not tested.
- Not testable on history, so not applied in the backtest: depth, venue health, data staleness, macro blackout. The paper bot applies the depth and staleness checks.

### Setups

- S1 (15m, scalp): regimes `hot` or `range`. Long: `low < min(low[t-20..t-1])`, `close > that min`, and `(min(open, close) - low) >= 2 × |close - open|`, with a zero body counting as a pass when the wick is positive. Short is the mirror on highs. Stop: the wick extreme ∓ 0.25 × ATR(14, 15m). TP1 at 1R. TP2 at whichever is nearer to entry: the midpoint of the 20-bar range, or 2R. If the midpoint is not beyond TP1, TP2 equals 2R.
- S3 (1h, swing): long in `trend_up`. A pullback is a bar whose low touches EMA(20) while its close stays above it. Entry fires when a later bar, within 6 bars, closes above that pullback bar's high. Stop: the pullback low minus 0.5 × ATR(14, 1h). TP1 at 1.5R, then trail. Short is the mirror. Skip a long if `funding_8h` is above its trailing 30-day 90th percentile, and a short if below the 10th.
- S4 (1h, swing): regime `range`. Long: the previous bar closed at least 2.5 standard deviations below the 50-bar mean with RSI(14) under 20, and this bar closes back above mean − 2.0 standard deviations. Stop: the lowest low of the last 3 bars minus 0.5 × ATR(14, 1h). Single target: the 50-bar mean at signal time, closing the full position. Short is the mirror.

### Fills and exits

- Entry: taker at the next bar's open, plus costs.
- Within a bar, the stop is checked before any target. A stop fills at the worse of the stop price and the bar's open. A target fills at its price only if the bar trades through it.
- TP1 closes 50% and moves the stop to entry plus round-trip costs. TP2 closes the rest. In S3, after TP1 the stop trails at the highest close since entry minus 2 × ATR(14, 1h), and it never loosens.
- Time stops: S1 4h, S3 72h, S4 24h, closed at the next bar's open.
- Funding exit: if accrued funding cost exceeds 0.3R, close at the next bar's open.

### Sizing and overlays

- Paper equity starts at $10,000. Risk is 0.5% of current equity. `notional = risk / (stop_distance + round_trip_cost)`.
- Leverage caps: 5x for S1, 3x for S3 and S4. A capped trade keeps its stop, so its R is smaller in dollars. Results are measured in R relative to each trade's own dollar risk.
- Liquidation distance is approximated as `0.5 / leverage`. Skip if that is below 3 × the stop distance.
- Overlays, across all markets and setups within one trial:
  - Only 1 open position, because SOL, BTC and ETH count as one correlated cluster.
  - At most 4 entries per market per 24h.
  - Daily stop at −2%, weekly stop at −5%.
  - Drawdown halt at −10%. In the backtest a halt pauses entries for 7 days instead of requiring a human.
  - Loss streak: after 3 consecutive losses, a 24h pause.

### Trials

Six trials, each scored once on the holdout: S1, S3 and S4, each with H4 off and on. A random-entry baseline per trial uses the same number of entries on random bars of the same markets, random direction, the trial's median stop distance in ATR, and the same exit rules. The baseline does not count as a trial.
