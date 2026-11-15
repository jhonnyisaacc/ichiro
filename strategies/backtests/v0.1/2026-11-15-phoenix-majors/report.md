# Backtest v0.1: Phoenix SOL, BTC, ETH

Run: 2026-11-15T10:12:23.119474+00:00. Manifest: `data/manifests/phoenix-v0.1.json`. Scored span 2026-02-01 00:00 to 2026-11-15 00:00 UTC.
Development folds start at 2026-02-01 00:00, 2026-04-18 12:48, 2026-07-04 01:36. Holdout starts 2026-09-18 14:24. The holdout was read once, in this run.
Cost per side: SOL 5.58 bp, BTC 3.73 bp, ETH 4.32 bp, plus hourly Phoenix funding.

## Trial 1: S1 H4 off: **FAIL**

Signals 926. Trades 395. Skipped decisions: {'paused': 214, 'position_open': 99, 'trade_budget': 25}.

| Segment | n | Win | Exp R | 95% CI | Total R | Cost R | Return | Max DD | Max loss streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev fold 1 | 84 | 40.5% | -0.342 | [-0.512, -0.164] | -28.7 | 0.212 | -13.46% | -13.46% | 7 |
| dev fold 2 | 120 | 49.2% | -0.172 | [-0.316, -0.026] | -20.6 | 0.248 | -9.87% | -11.03% | 6 |
| dev fold 3 | 118 | 55.1% | -0.129 | [-0.274, +0.012] | -15.3 | 0.244 | -7.43% | -8.46% | 8 |
| **holdout** | 73 | 45.2% | -0.279 | [-0.452, -0.096] | -20.4 | 0.268 | -9.75% | -9.75% | 9 |
| baseline holdout | 97 | 43.3% | -0.311 | [-0.465, -0.157] | -30.2 | 0.263 | -14.07% | -14.43% | 6 |
| baseline all | 583 | 51.3% | -0.170 | [-0.237, -0.104] | -99.1 | 0.233 | -39.37% | -41.50% | 6 |

Exit reasons (all): stop 188, tp2 98, stop_after_tp 86, time 23
By market (holdout): BTC n=21 exp=-0.387, ETH n=15 exp=-0.194, SOL n=37 exp=-0.253

## Trial 2: S1 H4 on: **FAIL**

Signals 573. Trades 272. Skipped decisions: {'paused': 115, 'position_open': 77, 'trade_budget': 11}.

| Segment | n | Win | Exp R | 95% CI | Total R | Cost R | Return | Max DD | Max loss streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev fold 1 | 54 | 35.2% | -0.386 | [-0.597, -0.166] | -20.9 | 0.187 | -9.95% | -10.42% | 9 |
| dev fold 2 | 86 | 51.2% | -0.155 | [-0.329, +0.018] | -13.3 | 0.230 | -6.52% | -8.21% | 5 |
| dev fold 3 | 74 | 58.1% | -0.085 | [-0.267, +0.092] | -6.3 | 0.247 | -3.17% | -5.18% | 7 |
| **holdout** | 58 | 46.6% | -0.268 | [-0.475, -0.054] | -15.5 | 0.242 | -7.52% | -7.52% | 7 |
| baseline holdout | 82 | 43.9% | -0.317 | [-0.485, -0.151] | -26.0 | 0.244 | -12.26% | -12.79% | 10 |
| baseline all | 430 | 48.4% | -0.229 | [-0.304, -0.153] | -98.4 | 0.237 | -39.09% | -40.14% | 10 |

Exit reasons (all): stop 130, tp2 69, stop_after_tp 50, time 23
By market (holdout): BTC n=14 exp=-0.306, ETH n=14 exp=-0.456, SOL n=30 exp=-0.162

## Trial 3: S3 H4 off: **FAIL**

Signals 942. Trades 175. Skipped decisions: {'position_open': 450, 'paused': 94}.

| Segment | n | Win | Exp R | 95% CI | Total R | Cost R | Return | Max DD | Max loss streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev fold 1 | 42 | 31.0% | -0.196 | [-0.564, +0.256] | -8.2 | 0.062 | -4.12% | -7.04% | 9 |
| dev fold 2 | 48 | 33.3% | -0.189 | [-0.520, +0.175] | -9.1 | 0.070 | -4.51% | -6.53% | 4 |
| dev fold 3 | 49 | 34.7% | +0.012 | [-0.562, +0.936] | +0.6 | 0.086 | -0.17% | -5.44% | 10 |
| **holdout** | 36 | 36.1% | -0.115 | [-0.487, +0.282] | -4.1 | 0.080 | -2.10% | -6.14% | 5 |
| baseline holdout | 48 | 31.2% | -0.317 | [-0.606, -0.021] | -15.2 | 0.079 | -7.39% | -7.54% | 6 |
| baseline all | 230 | 40.9% | -0.035 | [-0.200, +0.133] | -8.0 | 0.076 | -4.38% | -9.64% | 7 |

Exit reasons (all): stop 112, stop_after_tp 54, time 8, end_of_data 1
By market (holdout): BTC n=17 exp=-0.091, ETH n=6 exp=-0.841, SOL n=13 exp=+0.189

## Trial 4: S3 H4 on: **FAIL**

Signals 659. Trades 140. Skipped decisions: {'position_open': 300, 'paused': 55}.

| Segment | n | Win | Exp R | 95% CI | Total R | Cost R | Return | Max DD | Max loss streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev fold 1 | 35 | 28.6% | -0.229 | [-0.633, +0.285] | -8.0 | 0.053 | -4.02% | -7.41% | 12 |
| dev fold 2 | 35 | 31.4% | -0.128 | [-0.534, +0.311] | -4.5 | 0.068 | -2.29% | -4.16% | 6 |
| dev fold 3 | 38 | 31.6% | -0.305 | [-0.638, +0.079] | -11.6 | 0.075 | -5.70% | -5.70% | 8 |
| **holdout** | 32 | 40.6% | -0.044 | [-0.453, +0.387] | -1.4 | 0.077 | -0.75% | -4.75% | 6 |
| baseline holdout | 39 | 23.1% | -0.396 | [-0.728, +0.007] | -15.5 | 0.079 | -7.50% | -8.17% | 7 |
| baseline all | 213 | 40.8% | -0.029 | [-0.198, +0.141] | -6.2 | 0.075 | -3.45% | -10.27% | 7 |

Exit reasons (all): stop 89, stop_after_tp 42, time 9
By market (holdout): BTC n=16 exp=-0.257, ETH n=6 exp=-0.154, SOL n=10 exp=+0.364

## Trial 5: S4 H4 off: **INCONCLUSIVE**

Signals 1. Trades 0. Skipped decisions: none.

| Segment | n | Win | Exp R | 95% CI | Total R | Cost R | Return | Max DD | Max loss streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev fold 1 | 0 | | | | | | | | |
| dev fold 2 | 0 | | | | | | | | |
| dev fold 3 | 0 | | | | | | | | |
| **holdout** | 0 | | | | | | | | |
| baseline holdout | 0 | | | | | | | | |
| baseline all | 0 | | | | | | | | |

## Trial 6: S4 H4 on: **INCONCLUSIVE**

Signals 1. Trades 0. Skipped decisions: none.

| Segment | n | Win | Exp R | 95% CI | Total R | Cost R | Return | Max DD | Max loss streak |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev fold 1 | 0 | | | | | | | | |
| dev fold 2 | 0 | | | | | | | | |
| dev fold 3 | 0 | | | | | | | | |
| **holdout** | 0 | | | | | | | | |
| baseline holdout | 0 | | | | | | | | |
| baseline all | 0 | | | | | | | | |

