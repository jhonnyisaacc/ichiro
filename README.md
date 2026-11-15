# ichiro

Systematic swing-trading research for Solana perpetual futures, starting with Phoenix.

ichiro takes the observable behavior of top traders and turns it into rules that can be tested. It backtests those rules with conservative costs and paper-trades the survivors. Holding times range from hours to days, plus a separate scalping track. The question is whether any edge survives honest testing, not how to copy anyone's aggression.

Safety: `RESEARCH_AND_PAPER_ONLY_HUMAN_GATED`. Research, backtests, alerts and paper trading are allowed. Live orders and signing are disabled until Jhonny records a capital authorization in [`decisions/`](decisions/). See [CHARTER.md](CHARTER.md).

## Map

| Path | What it holds |
| --- | --- |
| [CHARTER.md](CHARTER.md) | What is allowed, what is forbidden, and the risk parameters with their approval status |
| [AGENTS.md](AGENTS.md) | Rules for agents working in this repo |
| [decisions/](decisions/) | Dated human decisions. A risk value or a capital authorization takes effect only here |
| [research/frontier-traders-notes.md](research/frontier-traders-notes.md) | Frontier Traders Season 1 finalists: observed style and extractable rules |
| [research/event-mechanics.md](research/event-mechanics.md) | How the competition worked, and what is still unknown |
| [research/hypotheses.md](research/hypotheses.md) | Testable hypotheses with kill criteria |
| [research/trader-profiles/](research/trader-profiles/) | One file per trader, from a shared template |
| [strategies/v0-rules.md](strategies/v0-rules.md) | v0.1 modular rule set |
| [strategies/journal-template.md](strategies/journal-template.md) | Pre-trade and post-trade journal (Markdown and JSONL) |
| [strategies/backtests/](strategies/backtests/) | What every backtest report must contain |
| [docs/data-infrastructure.md](docs/data-infrastructure.md) | Data sources, storage, features, backtest harness, alerts |
| [docs/roadmap.md](docs/roadmap.md) | Phases 1 to 4 with entry and exit criteria |
| [data/](data/), [notebooks/](notebooks/), [agents/](agents/) | Data layout, exploratory notebooks, automation |

## Principles

1. Capital preservation first. Every rule has an invalidation and a size derived from it.
2. Rules are frozen before results. A changed rule is a new version, and the old result stays in the record.
3. A failed hypothesis is a result. It is recorded, never rewritten.
4. A claim about a trader cites a public source or is marked `UNVERIFIED`.
5. No discretionary override by an LLM or an agent.

## Relation to other repos

[Rocket](https://github.com/jhonnyisaacc/rocket) is read-only BTC derivatives research under its own charter. [Whale](https://github.com/jhonnyisaacc/whale) is the wallet. ichiro imports neither. Execution, when a capital authorization exists, goes through a separately reviewed path.

## Workflow

Branches match `policy/branch-name.regex`. Pull requests open as drafts with `## Why`, `## What changed`, and `## How to test`, and merge by squash. Run `bash scripts/agent-preflight.sh` before the first commit.
