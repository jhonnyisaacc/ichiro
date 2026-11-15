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
