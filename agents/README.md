# agents

Automation lives here: collectors, the alert service, the journal CLI, and later the paper bot.

Under the [charter](../CHARTER.md), nothing here signs a transaction, places a live order, or holds a private key. A live execution service, if one is ever authorized, is a separate reviewed component and does not start in this folder.

## Paper bot (exploratory)

`src/ichiro/paper.py` runs two tracks against live Phoenix data. It holds no keys and places no orders.

- Track A: v0.1 S3 + H4 (1h) and S1 + H4 (15m) on SOL, BTC, ETH. Each is a separate $10,000 paper account. On every cycle the bot replays the backtest simulator from the paper start time over closed bars. A restart rebuilds the same state and writes no duplicate journal rows.
- Track B: polls Upbit's market list. A new `KRW-<coin>` that trades on Phoenix becomes a $1,000 paper short under the `~/coins` rule. It is skipped if Phoenix bid depth within 1% is under 2× the notional.

Every row is labeled `exploratory`, because v0.1 failed its backtest ([viability](../research/viability-2026-11.md)). Paper results are forward observations, not a Phase 3 pass.

```
PYTHONPATH=src nohup .venv/bin/python -m ichiro.paper run >> logs/paper.log 2>&1 &
PYTHONPATH=src .venv/bin/python -m ichiro.paper status
```

The state lives in `state/paper.json` and the journal in `journal/YYYY-MM.jsonl`. Neither is committed. Differences from the plan: overlays apply per paper account, not to combined equity, and costs are frozen from the order book at the first start.
