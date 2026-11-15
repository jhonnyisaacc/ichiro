# Backtest reports

One folder per run: `strategies/backtests/<strategy-version>/<YYYY-MM-DD>-<hypothesis>/`. A report is committed whether it passes or fails.

## A report must contain

1. Strategy version and the git commit or tag it was frozen at.
2. Hypothesis id and the trial number from the ledger in [hypotheses.md](../../research/hypotheses.md).
3. Data: markets, date range, source, and the manifest hash from `data/`.
4. The split: development, walk-forward folds, holdout. State whether the holdout was touched in this run.
5. The cost model used, with each value.
6. Results on each fold and on the holdout: trade count, win rate, expectancy in R, total R, cost in R, max drawdown, return over max drawdown, longest losing streak, exposure time.
7. A bootstrap 95% interval for expectancy.
8. A baseline: the same exits on random entries with matched timing and count.
9. A verdict against the pre-stated pass bar and kill criterion: `PASS`, `FAIL`, or `INCONCLUSIVE`. No reinterpretation after the fact.
10. The trade list as a file, or a pointer to external storage if it is over 1 MB.

## Not allowed

- Picking the best variant out of many without counting each variant as a trial.
- Tuning on the holdout.
- Reporting gross results without costs.
