# Viability check, November 2026

Question: do the v0.1 rules have positive expectancy on Phoenix after costs?

Answer for v0.1: **no**. No trial passed. Four of six failed, and two were inconclusive because the setup never traded. Report: [backtest v0.1](../strategies/backtests/v0.1/2026-11-15-phoenix-majors/report.md). Rules, costs, and the holdout were frozen before the run (tag `strategy-v0.1`, [decision 0002](../decisions/0002-pass-bar-and-costs.md)).

## Verdicts

Holdout: 2026-09-18 to 2026-11-15, Phoenix SOL, BTC, ETH pooled. The baseline uses random entries with the same exits.

| Trial | Setup | Holdout n | Expectancy | 95% CI | Baseline expectancy | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | S1 wick rejection, 15m | 73 | -0.279R | [-0.452, -0.096] | -0.311R | FAIL |
| 2 | S1 + H4 filter | 58 | -0.268R | [-0.475, -0.054] | -0.317R | FAIL |
| 3 | S3 momentum continuation, 1h | 36 | -0.115R | [-0.487, +0.282] | -0.317R | FAIL |
| 4 | S3 + H4 filter | 32 | -0.044R | [-0.453, +0.387] | -0.396R | FAIL |
| 5 | S4 mean reversion, 1h | 0 | | | | INCONCLUSIVE |
| 6 | S4 + H4 filter | 0 | | | | INCONCLUSIVE |

FAIL follows the kill rule in [hypotheses.md](hypotheses.md): holdout expectancy at or below zero.

## What the numbers say

Measured:

- **Costs sink the 15m scalp.** S1 pays about 0.25R per trade in costs, because its stops are tight relative to 4 to 6 bp per side. Its expectancy before costs is near zero in every fold. That puts it barely above the random baseline.
- **S3 beats random but doesn't make money.** In the holdout it lost less than random entries (-0.04R against -0.40R with H4 on), and costs are small (0.08R). The interval is wide: only 32 to 36 trades. Positive on SOL in the holdout (n=10 to 13), negative on BTC and ETH. That split is too small to act on.
- **The H4 no-trade filter** removed 30 to 40% of trades and changed expectancy little. On this data, H4 is not supported, but it is not refuted either.
- **S4 is too strict.** "Range regime" and "2.5σ extreme with RSI under 20" almost never hold together on 1h majors. One signal fired in 14 months.
- **The risk overlays worked.** The loss-streak and drawdown pauses kept the S1 holdout drawdown under 10% while it lost.

Inferred:

- On Phoenix majors, a 15m wick-rejection scalp with taker entries cannot clear its costs. Any scalp idea would need maker entries (0.5 bp) or targets several times wider.
- The swing trend setup shows some direction skill against random entries, but not enough after a 1:1.5 first target and a 2 ATR trail. With these trial counts, this is a lead, not an edge.

## Consequences

1. v0.1 does not enter Phase 3. Per [decision 0002](../decisions/0002-pass-bar-and-costs.md), paper trading may still run as `exploratory`. Its results are forward observations, not evidence of a pass.
2. The exploratory paper bot runs the best variant of each testable setup: S3 + H4 and S1 + H4. It also runs Track B, the Upbit-open short from the `~/coins` study, which has its own out-of-sample record.
3. A v0.2 must be a new, frozen version with a fresh trial count. These six trials stay in the ledger. Candidates suggested by this run, not yet tested: maker-only entries for S1, a wider S3 target, and S4 without the range requirement. Any of them chosen after seeing these results counts as a new trial.

## Limits

- 9.5 months of Phoenix history, with thin liquidity before February 2026.
- Spread and tick come from one order-book snapshot. Real spreads vary.
- Taker fills at the next bar open, with no queue or depth model.
- No macro-event blackout, no venue-health filter.
