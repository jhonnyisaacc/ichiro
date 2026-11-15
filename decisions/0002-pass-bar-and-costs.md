# 0002: Pass bar, cost model, and holdout

- Date: 2026-11-15
- Decided by: Jhonny
- Recorded by: an agent, from Jhonny's answers in the 2026-11-15 planning session, before any backtest ran
- Status: accepted

## Decision

1. Pass bar for a setup: on the holdout, expectancy at or above +0.10R per trade after costs, at least 100 trades, and a bootstrap 95% interval for expectancy that excludes zero.
2. Cost model, per side: Phoenix taker fee 3.5 bp, plus the measured half spread, plus 1 tick of slippage. Funding is charged from Phoenix's actual hourly funding series.
3. Holdout: the last 20% of each series by time, read once per strategy version.
4. If no setup passes, paper trading may still run the best setups, labeled `exploratory`. Exploratory paper results are not Phase 3 evidence.

## Approved values

These charter rows become APPROVED: the cost model. All other risk parameters stay PROPOSED.

## How to undo

A later decision replaces these values for a new strategy version. Results already scored under these values stay as they are.
