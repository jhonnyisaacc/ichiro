# ichiro

Read [CHARTER.md](CHARTER.md) before any work. The posture is `RESEARCH_AND_PAPER_ONLY_HUMAN_GATED`.

## Rules an agent cannot infer

- Never write code that signs, places a live order, or handles a private key or seed phrase. Never ask anyone for one.
- Never write, edit, or infer a file in `decisions/`. Those are Jhonny's. Do not invent approval evidence.
- A risk value stays `PROPOSED` until a decision record approves it. Do not choose or change a value after seeing a backtest result.
- Freeze a strategy version before scoring it. Record every trial in `research/hypotheses.md`, including failures. Do not rerun on the holdout.
- A claim about a named trader cites a public source, or it carries `UNVERIFIED`. Record public trading behavior only, nothing personal.
- Raw market data stays out of git. Anything over about 1 MB goes to external storage, with a manifest in `data/`.
- No code comments.
- Everything committed is in English.

## Git

- Branches match `policy/branch-name.regex`: `<feat|fix|hotfix|chore|docs|refactor|test|release>/<kebab-case>`.
- Run `bash scripts/agent-preflight.sh` before the first commit. Commits are signed by `jhonnyisaacc` and carry no AI co-author trailer.
- Pull requests open as drafts with `## Why`, `## What changed`, `## How to test`. One pull request, one job. Squash merge only.
- Editing `policy/`, `.github/workflows/`, `scripts/check-*.sh`, the charter, or anything near execution or secrets is Tier A and needs Jhonny's approval.
