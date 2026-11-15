# Hypotheses

Each hypothesis is stated so that it can fail. A test is a trial. Every trial, including a failed one or a parameter variant, gets a row in the ledger below. Thresholds are `PROPOSED` and are frozen before the first test of that hypothesis.

Shared defaults for every test unless the hypothesis says otherwise:

- Universe: Phoenix perps with at least 90 days of history and a median spread at or under 5 bp.
- Costs: the charter's cost model.
- Split: the earliest 70% of history for development, then walk-forward. The last 20% is a holdout, used once per strategy version.
- Pass bar: expectancy at or above +0.10R per trade after costs on the holdout, at least 100 trades, and a bootstrap 95% interval that excludes zero.

## H1: Wick rejection on hot markets

- Statement: on 15m bars in a hot market, a candle whose rejecting wick is at least 2x its body and whose close is back inside the prior 20-bar range, entered on the next bar against the wick, has positive expectancy.
- Data: 15m candles, hot-market flag.
- Test: event study, stop beyond the wick extreme plus 0.25 ATR, TP1 at 1R and TP2 at 2R.
- Kill: holdout expectancy below 0, or the pass bar missed on two of three walk-forward folds.
- Source: Galileo Wilson's wick scalping, `UNVERIFIED`.

## H2: Fading the top tail of pumps beats chasing them

- Statement: after a 1h return in the top 1% of the trailing 30-day distribution, a short entered on the first lower high has better expectancy in R than a long continuation entry on the same events.
- Data: 1m and 1h candles, funding.
- Test: paired comparison on the same event set.
- Kill: fade expectancy is not higher than continuation, or fade expectancy is negative.
- Source: selective pump shorting, `UNVERIFIED`.

## H3: Funding extremes as a filter

- Statement: adding "skip longs when the funding rate is above its 90th percentile, and skip shorts when it is below its 10th" improves the expectancy of H1 and H2 without cutting the trade count by more than half.
- Data: Phoenix funding history.
- Kill: no improvement on the holdout.

## H4: A no-trade filter reduces drawdown

- Statement: skipping all entries when realized volatility is below its 20th percentile, or when spread is above 2x its median, lowers maximum drawdown by at least 20% and keeps at least 80% of expectancy.
- Kill: either condition fails.
- Source: "sometimes the best trade is no trade," `UNVERIFIED`.

## H5: A consecutive-loss cooldown improves the equity curve

- Statement: pausing 24h after 3 consecutive losses improves the ratio of return to max drawdown compared with no pause.
- Test: apply to the H1 and H2 trade lists. Compare against random pauses of the same total length.
- Kill: not better than random pauses.

## H6: A trade budget prevents overtrading

- Statement: capping entries at 4 per 24h per market keeps at least 90% of net PnL and cuts costs by at least 25%.
- Kill: either condition fails.

## H7: Hot-market detection leads volatility

- Statement: the data-defined hot flag (`volume_zscore_24h >= 2` and `realized_vol_pct_30d >= 70`) predicts above-median realized volatility over the next 4h, with a hit rate at or above 60%.
- Kill: hit rate below 55% on the holdout.

## H8: Liquidation cascades continue

- Statement: after liquidations exceeding the 95th percentile of 5m notional, price continues in the cascade direction for 15 to 60 minutes often enough to give positive expectancy for a momentum entry with a 1 ATR stop.
- Data: Phoenix liquidation history.
- Kill: holdout expectancy below 0.

## H9: Session timing

- Statement: H1 entries during the 13:00 to 17:00 UTC overlap have higher expectancy than entries outside it.
- Kill: no difference in the bootstrap interval.

## Trial ledger

Append rows. Do not edit earlier rows.

| Date | Hypothesis | Strategy version | Data range | Trials used | Result | Report |
| --- | --- | --- | --- | --- | --- | --- |
