# ichiro charter

Safety posture: `RESEARCH_AND_PAPER_ONLY_HUMAN_GATED`.

Adopted 2026-11-15. See [decisions/0001](decisions/0001-repo-and-safety-posture.md).

## Goal

Find out if a small set of systematic rules for Solana perpetual futures has positive expectancy after conservative costs, and if it does, run it under hard risk limits. Ending a line of research with preserved negative evidence is an acceptable outcome.

## Allowed

- Reading public market data: orderbooks, fills, candles, funding, liquidations, oracle and index prices, and public wallet activity.
- Storing and deriving features from that data.
- Backtests and walk-forward evaluation.
- Alerts and dashboards that inform a human.
- Paper trading against a local simulator or a venue's paper or simulated mode, with no keys that can move funds.
- Manual journaling of trades a human places outside this repo.

## Forbidden until a capital authorization exists

- Signing a transaction or placing a live order.
- Holding, generating, or requesting a private key or seed phrase in this repo, its CI, or its agents.
- Any code path that could reach a live order endpoint without the authorization check described below.

## The live-capital gate

Live execution needs a file `decisions/NNNN-capital-authorization.md`, written and dated by Jhonny. It states:

| Field | Meaning |
| --- | --- |
| Venue and account | Where, and which account or subaccount |
| Instruments | Which markets |
| Capital | Maximum capital at risk |
| Maximum loss | The loss at which everything stops, and who resets it |
| Duration | Start and end date |
| Risk parameters | Each value in the table below, marked APPROVED |
| Kill switch | How a human stops it within one minute |
| Revocation | How the authorization is withdrawn |

An agent never writes, edits, or infers this file. Phase 4 of the [roadmap](docs/roadmap.md) cannot start without it.

## Risk parameters

Values are `PROPOSED` until a decision record marks them `APPROVED`. A proposed value is a starting point for backtests. It is not a risk approval. An agent may not choose or change a value after seeing results.

| Parameter | Proposed value | Status |
| --- | --- | --- |
| Risk per trade (loss at stop, fraction of equity) | 0.5% | PROPOSED |
| Max effective leverage, swing | 3x | PROPOSED |
| Max effective leverage, scalp | 5x | PROPOSED |
| Max concurrent positions | 2 | PROPOSED |
| Max correlated same-direction exposure | 1 position per correlated cluster | PROPOSED |
| Daily loss stop | -2% of start-of-day equity | PROPOSED |
| Weekly loss stop | -5% of start-of-week equity | PROPOSED |
| Max drawdown halt (from equity peak) | -10% | PROPOSED |
| Consecutive-loss cooldown | 3 losses, then 24h pause | PROPOSED |
| Minimum distance to liquidation at entry | 3x the stop distance | PROPOSED |
| Cost model for backtests | Taker fee + half spread + 1 tick slippage per side + funding | APPROVED ([0002](decisions/0002-pass-bar-and-costs.md)) |
| Pilot capital and pilot max loss | none | HUMAN_DECISION_REQUIRED |

## Research integrity

- Each strategy version is frozen in `strategies/` before it is scored. Scoring a changed rule creates a new version, and the old result stays.
- Every hypothesis test counts as a trial in [research/hypotheses.md](research/hypotheses.md), including failures and parameter variants.
- Holdout data is chosen before the first test and is used once per strategy version.
- A strategy reaches paper trading only after it meets the Phase 2 exit criteria in the [roadmap](docs/roadmap.md).

## Changes to this charter

Only Jhonny changes this charter. Each change is a decision record and a pull request labeled `tier-a`.
