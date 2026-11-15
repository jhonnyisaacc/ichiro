# Trade journal

Every trade, paper or manual, gets a pre-entry entry written before the order is sent, and a review after it closes. This follows the "thesis, invalidation, take-profit before entry" process attributed to Galileo Wilson (`UNVERIFIED`).

## Pre-entry (fill in before the order)

| Field | Example |
| --- | --- |
| Decision id | 2026-11-16T14:15Z-SOL-PERP-S1 |
| Market | SOL-PERP |
| Track | scalp / swing |
| Setup | S1 wick rejection |
| Regime | hot |
| Direction | long |
| Thesis (one sentence) | The sweep below the 20-bar low was rejected on a hot day. Trapped shorts fuel a move back to the range mid. |
| Entry plan | limit 182.40 |
| Invalidation | 181.10. Below this the thesis is wrong |
| TP1 / TP2 | 183.70 (1R) / 184.95 (range mid) |
| Risk | 0.5% equity, R = $50 |
| Size and leverage | notional $7,000 on $10,000 equity, 0.7x |
| Liquidation distance / stop distance | 22x |
| Checks passed | filter, sizing, overlays |
| Why not "no trade"? | Spread 2 bp, ATR percentile 81, funding neutral |

## Post-trade review

| Field | Example |
| --- | --- |
| Exit reason | TP1 then TP2 / stop / time / overlay |
| Result in R | +1.4R |
| Costs in R | 0.12R |
| Followed the plan? | yes / no, and what differed |
| Mistake tag | none / late entry / moved stop / oversize / outside setup |
| Lesson (one sentence) | |

## JSONL schema

One JSON object per line in `journal/YYYY-MM.jsonl`. Pre-entry and review are separate events linked by `decision_id`.

```json
{"event":"decision","decision_id":"2026-11-16T14:15Z-SOL-PERP-S1","ts":"2026-11-16T14:15:00Z","mode":"paper","market":"SOL-PERP","track":"scalp","setup":"S1","regime":"hot","action":"enter","direction":"long","thesis":"Sweep below 20-bar low rejected on a hot day","entry":182.40,"invalidation":181.10,"tp":[183.70,184.95],"risk_frac":0.005,"notional":7000,"leverage":0.7,"liq_to_stop":22.0,"strategy_version":"v0.1"}
{"event":"decision","decision_id":"2026-11-16T15:00Z-BTC-PERP","ts":"2026-11-16T15:00:00Z","mode":"paper","market":"BTC-PERP","action":"no_trade","reason":"spread_above_limit","strategy_version":"v0.1"}
{"event":"review","decision_id":"2026-11-16T14:15Z-SOL-PERP-S1","ts":"2026-11-16T17:40:00Z","exit_reason":"tp2","r_multiple":1.4,"cost_r":0.12,"followed_plan":true,"mistake":"none","lesson":""}
```

Required fields for `action: "enter"`: `decision_id`, `ts`, `mode`, `market`, `setup`, `direction`, `thesis`, `entry`, `invalidation`, `tp`, `risk_frac`, `strategy_version`. The schema becomes a JSON Schema file when the journal CLI lands.
