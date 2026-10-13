# Specified Eight Teams Five-Day BC Dataset: September 21, 2026

Extract the latest five complete UTC dates from the [Kaggle official daily episodes index](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index), ranging from **2026-09-16 to 2026-09-20**.
Each daily package contains 639, 650, 649, 646, and 639 games, totaling **3,223 games**.
Filter by replay `info.TeamNames` to precisely match the eight specified teams as user-defined, without inferring name changes, aliases, or team IDs.
No additional filtering by win/loss, cash, score, or leaderboard ranking is applied. The scope covers samples from these five official daily packages.

Finally retained **2,777 distinct games, 4,189 complete teacher trajectories**, with no full games excluded.
When two designated teams meet, retain both seats; otherwise, retain only the seat of the designated team.

| Team | Trajectory Count | Supervisable Turns |
| --- | ---: | ---: |
| M & M & P & Q | 251 | 180,469 |
| DSM | 793 | 570,167 |
| THIRD FARM CLUB | 485 | 348,680 |
| Unknown Mother-Goose | 563 | 404,797 |
| SpaTaro | 638 | 458,716 |
| Majkel1337 | 817 | 587,423 |
| ymg_aq | 593 | 426,188 |
| Artem The Farmer 🍅 | 49 | 35,049 |

Artem appears in the daily package only in 9/18–20; M & M & P & Q appear only in 9/16, 9/17, and 9/20.
All teams have a trajectory in all three zones; they are divided by the environment seed hash based on the original root seed `62001`,
teams from the same world and playing against each other are always located in the same zone.

| Partition | Game | Trajectory | Supervised Turns |
| --- | ---: | ---: | ---: |
| Training | 2,532 | 3,815 | 2,742,636 |
| Validation (selection) | 125 | 181 | 130,124 |
| Confirmation | 120 | 193 | 138,729 |
| Total | 2,777 | 4,189 | 3,011,489 |

Continue with the current mainline's `grounded-production-context-v4`, full trajectory
`complete-turn-seat-v1` and q100 action interface: 719 decision turns per trajectory,
22,003 FP16 features per observation. A total of **3,011,891 context turns** are retained;
402 turns with unrepresentable unit actions are masked from supervision loss, but context observations are preserved.
739 turns contain more than 100 quantity requests, truncated to 100 as per existing q100 encoding.
Array size: **134,207,917,437 bytes (approximately 125.0 GiB)**.

Data entry:
[`outputs/datasets/agronomy-v4-selected8-5d-20260921-q100/manifest.json`](../outputs/datasets/agronomy-v4-selected8-5d-20260921-q100/manifest.json).
Original indices, the 20-day package (9/17) and source confirmation are located at
[`data/external/kaggriculture-selected8-5d-20260921/raw/daily/`](../data/external/kaggriculture-selected8-5d-20260921/raw/daily/),
9/16 daily package reuses authenticated historical original files; specific paths and SHA256 values are listed in the source inventory.
The new dataset is stored independently; the current training configuration has not been switched to this dataset.

Recreation of Conversion and Verification:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1 NUMPY_MADVISE_HUGEPAGE=0
.venv/bin/python -m kagg_revue.datasets.sequences.prepare \
  --config-name sequences_selected8_20260921
.venv/bin/python -m kagg_revue.datasets.sequences.verification \
  --config-name sequences_selected8_20260921
```

The date is fixed in [Hydra Configuration](../configs/sequences_selected8_20260921.yaml),
filtering method, source hash, seat, date, environment seed, and supervision mask are all recorded in the data sheet.
Verification results are available in [Data Validation Report](../outputs/analysis/selected8-5d-20260921/data-verification.json).

All 8,331 arrays passed SHA256 verification, 2,777 environment seeds showed no leakage across partitions,
all array sizes, types, and supervision mask counts are consistent. A random sample of 17 complete replays was checked, covering five dates, eight teams, and all partitions; all 24,480 observations from official environment replays matched exactly, with reconstructed actions and masks being consistent.
Relevant modules Ruff, mypy, and two targeted tests passed.

manifest SHA256：
`8def06dbcad7881bcb4b3c2fbc2049c702cb050a1a8aaeb8121dac66088c34eb`。
