# Event mechanics

What the Frontier Traders format rewarded, and what that means for a strategy that trades real capital. Labels follow [frontier-traders-notes.md](frontier-traders-notes.md).

## Two different games

| | Season leaderboards | Live events and Grand Final |
| --- | --- | --- |
| Money | Real funds on Phoenix and Solflare `SOURCED` | Paper trading on Phoenix's onchain orderbook `SOURCED` |
| Ranking | Season and weekly PnL, season and weekly volume `SOURCED` | Three rounds, one champion `SOURCED`. Scoring formula `UNVERIFIED` |
| Leverage | Venue limits (Phoenix leverage tiers) | "Varying leverage" per game mode `SOURCED`. Up to 500x `UNVERIFIED` |
| Extra incentives | Crates by taker volume, weekly pools `SOURCED` | "Hot-market multipliers" `SOURCED` |

Only the season leaderboard tells us about real-capital behavior. The live final tells us about a high-variance contest.

## Hot markets

The live game applies multipliers to selected markets. The exact multiplier and selection rule are unknown. For ichiro, a hot market is defined from data, not from a contest label:

- `hot = volume_zscore_24h >= 2.0 AND realized_vol_pct_30d >= 70`
- Both thresholds are `PROPOSED` and are tested in H7.

## Liquidation dynamics

- On Phoenix, maximum leverage depends on position size through leverage tiers, and liquidation follows account health and risk tiers. See the Phoenix docs on leverage tiers, margin math, and risk tiers.
- At 100x, a 1% adverse move consumes the whole margin before fees. At 500x, a 0.2% move does. A normal SOL-PERP spread plus one tick of noise can be enough. In a high-leverage mode, survival is mostly luck about the next tick.
- Rule carried into ichiro: at entry, the distance to the liquidation price must be at least 3 times the stop distance (`PROPOSED`). This makes the stop, not the liquidation engine, the exit.

## Scoring incentives and their bias

- Winner-takes-all over three rounds makes variance valuable. A trader behind in round 3 should raise leverage, which is rational in the contest and ruinous with capital.
- Volume boards and crates pay for turnover. A taker fee of a few basis points per side on $187M of volume is a large cost unless rebates and crates offset it.
- Consequence: ichiro scores strategies on net PnL, maximum drawdown, and expectancy per trade in R. Turnover is reported as a cost.

## Open questions

1. Per-round rules: duration, starting balance, available markets, leverage per mode.
2. Scoring: absolute PnL, percent return, or rank points?
3. Liquidation in the paper game: same engine as live Phoenix, or simplified?
4. Hot-market selection: announced in advance, or revealed during the round?
