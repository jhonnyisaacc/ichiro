# idatsy

- Seat or context: "online winner" seat at the Frontier Traders Season 1 Grand Final. `SOURCED`: https://luma.com/frontier-traders-grand-final-london
- Public sources: https://github.com/idatsy
- Last reviewed: 2026-11-15

## Observed behavior

- Markets traded: unknown.
- Holding time: short directional swings with fast flips. `UNVERIFIED`
- Leverage behavior: very high in the contest. `UNVERIFIED`
- Risk behavior: reportedly recovered from a deep drawdown late in the final. `UNVERIFIED`
- Tooling: public repos include a Python QuestDB wrapper, a uv Python project template, and Rust protocol tooling for Solana and Ethereum. `SOURCED`

## Metrics

| Metric | Value | Label | Source |
| --- | --- | --- | --- |
| Season volume | about $187M or more | UNVERIFIED | brief |
| Weekly volume, one week | $9M, ranked first | SOURCED (weak) | https://www.frontiertraders.com/campaigns/soleco-perps |
| Grand Final result | Champion, about $152K profit after a loss of about $50K | UNVERIFIED | unretrieved KuCoin community post |

## Extractable rules

| Rule | Hypothesis |
| --- | --- |
| Treat hot markets as where the movement is | H7 |
| Momentum after forced flows | H8 |
| Infrastructure: a time-series store fed by a fast collector | [data-infrastructure](../../docs/data-infrastructure.md) |

## What cannot be copied

Contest-level leverage, and a comeback that depends on surviving a drawdown the ichiro halt rule would have stopped. Volume leadership is an incentive result, not an edge.

## Open questions

1. How much of the season volume was maker versus taker?
2. Net PnL for the season after fees, funding, and rebates?
3. Is a recording of the final public?
