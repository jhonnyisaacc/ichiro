# 0001: Repository and safety posture

- Date: 2026-11-15
- Decided by: Jhonny
- Status: accepted

## Context

The ichiro work was first planned as a folder inside Rocket. Rocket's charter is `READ_ONLY_RESEARCH_ONLY_HUMAN_GATED`: it forbids paper and live execution, and it allows data infrastructure only for experiments that pass its admission process. ichiro's roadmap needs paper trading, and possibly live trading later.

## Decision

1. ichiro is its own public repository, `jhonnyisaacc/ichiro`, governed by binah's rules and by its own [charter](../CHARTER.md).
2. The posture is `RESEARCH_AND_PAPER_ONLY_HUMAN_GATED`. Live orders need a separate capital authorization recorded in this folder.
3. Risk values in the charter and in `strategies/v0-rules.md` are concrete, conservative proposals marked `PROPOSED`. None of them is approved by this decision.

## Alternatives considered

- A folder inside Rocket, docs only. Rejected because it blocks Phases 3 and 4 under Rocket's charter.
- Amending Rocket's charter. Rejected because it would mix a BTC research line with Solana perps execution.

## How to undo

Archive the repository. Nothing in Rocket or Whale depends on it.
