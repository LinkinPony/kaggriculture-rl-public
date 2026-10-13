# Daily Replay Integration, Fourth Plot, and Scoring Coverage: 2026-09-22

Subsequently, 10 replays involving submission `56414341` have been deleted as per user request. The current merged entry and statistical output have been updated to **17,538 games**, with the actual SE subset used being **1,471 games** (among the deleted 10 games, 2 involved opponents using SE terrain). The number of unlocked SE games is now **1,497**. Date and rating distributions have been recalculated.
The following records the original snapshot counts prior to deletion.
This change is documented in [Explicit Exclusion Record](mm_pq_replay_watch.md#section-dfa13629b0d0).

Refresh [official daily index](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index),
obtain the latest complete daily package **2026-09-21 / 638 games**. Among them, 10 games already have local standalone replays,
net increase of **628 distinct games**. Reuse the daily package 9/3–20 days, totaling **12,441 games** over 19 days;
merge with deduplicated local standalone supplements of **5,107 games**, resulting in **17,548 games, 35,096 player trajectories**.
2 duplicate daily packages have identical SHA256 hashes; 862 standalone replays are deduplicated by episode ID, with daily entries prioritized.

The original file is retained in its original location; the unified entry point is
[`catalog.json`](../data/external/kaggriculture-daily-merged-20260922/raw/catalog.json),
source and SHA256 are available at
[`merged-manifest.json`](../data/external/kaggriculture-daily-merged-20260922/raw/merged-manifest.json).
The collection freeze time is **06:05:37 UTC**; subsequent metadata additions do not alter the membership of this collection.

## Fourth Plot SE

Iterate over each observation in the complete replay. Unlock based on `unlocked_quadrants` containing SE; actual usage is based on SE having previously been planted or placed in chicken coops/pastures, excluding weeds and empty facilities.
If either side meets the condition in the same game, the game is counted only once; trajectories are separately recorded for both sides.

| Range | Total Games | Unlocked SE Games / Trajectories | Actual Used SE Games / Trajectories |
|---|---:|---:|---:|
| Latest 9/21 daily | 638 | 21 / 21 | 21 / 21 |
| 19-day daily | 12,441 | 622 / 638 | 619 / 635 |
| All Combined | 17,548 | 1,499 / 1,605 | 1,473 / 1,571 |

Full-scale parsing with zero failures. Additionally, an independent coordinate traversal was used to confirm 72 trajectories, covering daily positive and negative samples as well as all trajectories with facilities but no crops/animals; for the first time, frame numbers and cumulative frame counts were consistent.
See [Complete Report](../outputs/analysis/daily-land-20260922/report.md),
[SE Game Entry](../outputs/analysis/daily-land-20260922/se-productive-catalog.json),
[Per-Trajectory CSV](../outputs/analysis/daily-land-20260922/se-productive-trajectories.csv),
and [Verification](../outputs/analysis/daily-land-20260922/verification.json).

## Date and rating

Dates use UTC game creation time; a total of **17,544 games** have dates, ranging from **8/27 to 9/22**, with 4 missing; **1,473 SE replays all have dates**.
SE games are concentrated in 9/11–16, totaling **1,124 games (76.31%)**; the peak at 9/14 is **284 games**.
This includes local independent supplements, so the total SE for 9/21 is 105 games, while the daily count for that day contains only 21 games.

Rating is defined as the average score of both players in a game: daily using official `avg_score`, and independently supplementing with the average of both players' `updatedScore` from metadata. The maximum difference among 63 overlapping evidences is **4.89e-7**, consistent with daily six-decimal rounding. The final cash balance and current leaderboard scores are not used as alternatives.

| Scope | rating coverage | mean | P25 / median / P75 | range |
|---|---:|---:|---:|---:|
| All merged | 12,547 / 17,548 (71.50%) | 2,981.7 | 2,910.1 / 2,992.7 / 3,045.4 | 608.4–3,239.8 |
| SE subset | 632 / 1,473 (42.91%) | 2,997.5 | 2,961.5 / 2,991.7 / 3,033.1 | 726.2–3,187.7 |
| SE daily | 619 / 619 (100%) | 3,004.3 | 2,963.1 / 2,992.8 / 3,034.1 | 2,805.5–3,187.7 |

The SE subset missing ratings for **841 games** does not participate in the rating distribution, so the rated subset cannot be considered representative of all SE.
The average score of both sidesalso cannot be directly taken as the personal rating of the SE-using side.
See [Daily and Binned Report](../outputs/analysis/daily-land-20260922/date-rating/report.md),
[Game-by-Game CSV](../outputs/analysis/daily-land-20260922/date-rating/episodes.csv),
[Distribution Chart](../outputs/analysis/daily-land-20260922/date-rating/distributions.png),
and [Metadata Evidence](../data/external/kaggriculture-daily-merged-20260922/raw/date-rating-evidence.json).

## Reproduction

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m kagg_revue.datasets.land.cli survey.workers=18
.venv/bin/python -m kagg_revue.datasets.land.distributions
```

Hydra is configured as [`configs/daily_land.yaml`](../configs/daily_land.yaml). A previous snapshot recreation will verify frozen file hashes; when refreshing future dates, specify new `survey.raw` and `survey.output`.
Original data is stored in gitignored `data/external/`, and statistical outputs are stored in `outputs/analysis/`.
Ruff, full mypy (925 source files), and 3 essential tests pass.
