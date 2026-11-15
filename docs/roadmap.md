# Roadmap

Each phase has entry and exit criteria. A phase that fails its exit criteria ends that line, with the evidence kept. It does not lower its own bar.

## Phase 1: Research, journaling, and alerts

- Entry: this repository and its charter.
- Work: read-only Phoenix collector (candles, funding, fills, liquidations, status), data manifests, feature library, journal CLI, alert service.
- Exit: 30 days of continuous collection with under 1% gaps, alerts running for 14 days, and at least 30 journaled manual or simulated decisions.

## Phase 2: Backtests with frozen rules

- Entry: Phase 1 data, plus v0.1 frozen and tagged.
- Work: the backtest harness, then H1 to H9 in priority order H4, H1, H2, H7, H3, H5, H6, H8, H9.
- Exit to Phase 3: at least one setup passes its hypothesis on the holdout at the pass bar in [hypotheses.md](../research/hypotheses.md), with a random-entry baseline beaten and max drawdown within the proposed halt.
- Stop: every setup fails. Record it and stop, or start a new hypothesis family with a fresh trial count.

## Phase 3: Paper trading

- Entry: a Phase 2 pass.
- Work: a paper bot that runs the same rules module as the harness against live data, with simulated fills or the venue's paper mode. It holds no key that can move funds.
- Exit: 8 weeks or 100 trades, whichever comes later. Paper expectancy must sit inside the backtest's bootstrap interval, there must be no unexplained journal gaps, and every overlay must fire correctly at least once in tests or live paper.
- Stop: paper expectancy below zero after 100 trades, or a drift from backtest that the fill model cannot explain.

## Phase 4: Live with hard safety limits

- Entry: a Phase 3 pass, plus a capital authorization in `decisions/` signed by Jhonny, with every risk parameter APPROVED. See the [charter](../CHARTER.md).
- Work: a separate execution service reviewed as security work, using a subaccount that holds only the authorized capital. Venue-side reduce-only stops. A kill switch that flattens and stops within one minute.
- Limits: the approved values in the charter, plus the pilot max loss from the authorization. Hitting the pilot max loss stops everything until a new decision.

## Automatable versus discretionary

| Element | Category | Notes |
| --- | --- | --- |
| Market and regime filter | Automatable | Pure features |
| Hot-market detection | Automatable | H7 decides whether it is useful |
| Wick rejection, pump fade, continuation, mean reversion triggers | Automatable | Fixed thresholds lose some nuance |
| Sizing, leverage cap, liquidation distance | Automatable | Should never be discretionary |
| Predefined TP and SL, time stops | Automatable | |
| Risk overlays and kill switch | Automatable | Must be automatic to be trusted |
| Journaling the plan | Automatable for the bot, semi-automatable for manual trades | Alerts pre-fill the entry |
| Order-flow reading | Semi-automatable | S5 is a crude proxy for screen reading |
| Choosing which pump is exhausted | Discretionary | H2 tests a rule; a skilled trader will still beat it on some events |
| Crowd and narrative reading | Discretionary | Not modeled |
| Contest tactics: comeback leverage, volume farming | Out of scope | Rewarded by contests, harmful with capital |
| Composure under pressure | Replaced | Hard rules take the place of nerves |
