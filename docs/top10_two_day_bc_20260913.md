# Historical top-ten demonstrations from September 11–12 and current high-scoring public replays

## Selection criteria

The official daily index was refreshed on 2026-09-13, with the latest two complete UTC dates being **September 11 and 12**, containing **657 and 655 games**, respectively. The complete original ZIP files have been obtained and verified for date, number of games, size, and SHA-256. September 11 reused the existing ZIP; September 12 was newly downloaded. Source available at [daily manifest](../data/external/kaggriculture-top10-2d-20260913/raw/daily/manifest.json).

The leaderboard is frozen at **2026-09-13 01:46:59 UTC**, and all current top ten entries are strictly above 2900.
Select candidate teams based on team ranking, then filter versions by **submission's publicly available score > 2900**.
Each team can view at most two versions currently available via the API; the submission timestamp does not indicate the version corresponding to the leaderboard score.
Among the 20 publicly available versions in this round, **14** meet the score threshold, while **6** do not.

| Rank | Team | Snapshot Score |
| --- | --- | ---: |
| 1 | Majkel1337 | 3236.2 |
| 2 | M & M & P & Q | 3137.4 |
| 3 | Mengfei Li | 3044.0 |
| 4 | ymg_aq | 3021.1 |
| 5 | SpaTaro | 3021.0 |
| 6 | THIRD FARM CLUB | 3017.8 |
| 7 | feel the agi | 3002.4 |
| 8 | Otter Vibe | 2989.4 |
| 9 | Kaggriculture Agent | 2973.8 |
| 10 | QQ Farming | 2955.5 |

Snapshots, per-team version responses, per-version game lists, and acquisition times are all stored in `data/external/kaggriculture-top10-2d-20260913/raw/`.
All completed public games ending on or before the snapshot date are included; no sampling, no selection based on win/loss, and no inclusion of validation games. The supplement has no lower date limit two days prior, covering the full historical availability of eligible versions.
14 versions are consolidated into **3,789 games**, of which **1,066 games** overlap with two-day daily records, and an additional **2,723 games** are supplemented.
Supplemental replays prioritize reusing existing public replays and precise episode IDs from earlier daily records, avoiding redundant downloads.

## The Boundary of Historical Ranking Evidence

Currently, only three verifiable ranking snapshots are available: **August 27, September 11, and September 13**.
The union of the top ten teams across these snapshots consists of **25 team IDs**, with **16 teams** appearing in two or more daily records.
Based on these evidences, **1,285 games** and **2,216 demonstration seats** are retained; additionally, **408 seats** lack evidence from the top ten in the available snapshots, corresponding to **32 displayed names**. All original data is preserved, and a seat-by-seat exclusion list is maintained for reconstruction after additional ranking evidence is collected.
No prior curated exclusion rules applied to our teams in this round.

This is a collection of "snapshots that can prove a team reached the top ten," **but cannot be considered to exhaust all historical top-ten teams**.
The current Kaggle ranking and public submission API do not provide complete historical rankings; the data list explicitly marks
`history_complete: false`. In particular, unverified teams such as Artem The Farmer, redblackbst, and keiz
cannot be deemed to have never entered the top ten simply because they lack snapshots. A clarification of the scope has been proposed to users, and candidate data are generated based on the above verifiable collection until further supplemental lists are provided.

Daily raw replays show only team display names, not submission IDs. Names use aliases of existing team IDs.
Linking: error is reported if cross-team name collisions occur; the entire team's history is not considered equivalent to a single strategy version.
Supplementary replays are selected by precisely matching the submission ID from the API to designate the demonstration seat.

## Coding and Building

The original merged list consists of **4,008 games**, with each episode retained only once. A full frame-by-frame audit reveals **5 games** where a TIMEOUT occurred mid-play but the final state was still marked as DONE: 108275644, 108281700, 108128841, 108156174, 108195261. All anomalies occurred at THIRD FARM CLUB, with a total of 350 TIMEOUT states in the source decisions. Excluding these 5 games and 7 demonstration slots based on the existing complete trajectory contracts, the original files are fully preserved. See [Full Frame-by-Frame Audit](../outputs/analysis/top10-2d-20260913/raw-frames-audit.json).

The final encoded dataset consists of **4,003 games, 5,066 demonstration slots**, including 1,283 daily games and 2,720 supplementary matches. Original trajectories of both sides are retained for environment reconstruction; BC labels are provided only for slots meeting selection criteria. The mainline grounded-v2 is continued, with quantity labels categorized into **1–100**; each partition consistently truncates any quantity label exceeding 100 to 100. Partition distribution remains at **90% / 5% / 5% for `SHA256("62001:{episode_seed}")`**, with no cross-partitioning within the same environment seed. All valid entries are equally weighted, without using source frequency weighting, with-replacement resampling, or win/loss-based weighting.

Data catalog: `outputs/datasets/grounded-v2-top10-20260911-12-q100/`, totaling **502 shards**.
The SHA-256 of [manifest.json](../outputs/datasets/grounded-v2-top10-20260911-12-q100/manifest.json) is
`8f27747120b10c6de3aa907546a6b8857fb47a5febd3bc153632b871431249f9`.
Array size approximately 99.01 GB; the training set does not have a sampling_weights file, maintaining row-wise equal-weight traversal.

| Partition | Games | Demonstration Seats | Valid Decision Rows | Unsupported Unit Action Rows | Rows with Quantity Truncation |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 3,601 | 4,559 | 3,277,090 | 831 | 5,443 |
| selection | 202 | 263 | 189,050 | 47 | 309 |
| confirmation | 200 | 244 | 175,368 | 68 | 397 |

Total effective decisions amount to **3,641,508 rows**, with no rows lost due to missing quantity tables in any of the three partitions.
Final array, seat, and partition validations are available at
[dataset-verification.json](../outputs/analysis/top10-2d-20260913/dataset-verification.json).
A comprehensive trajectory audit covers two daily dates, three partitions, and all supplementary submissions, available at
[replay-verification.json](../outputs/analysis/top10-2d-20260913/replay-verification.json).
**Final acceptance has been passed**: All hashes, shapes, finite values, seat assignments, and quantity ranges for 2,008 array files have passed verification; no duplication of episodes or decision rows; environment seeds are consistent across partitions and do not enter online retention intervals.
All 25 original API metadata responses match their recorded SHA-256 hashes at the time of retrieval.
25,920 observations and model input features from 18 full replays are consistent, and the retained labels exhibit finite likelihood under a random model. This constitutes a clear, source-verified sample of complete episodes, not a full corpus-level state equivalence proof.

Two complete daily pre-inspection checks have been passed, involving the replay comparison of 2,880 observed and model input features, and it has been verified that retained actions exhibit finite likelihood under a stochastic model; see
[Pre-inspection Report](../outputs/analysis/top10-2d-20260913/daily-replay-preflight.json).
The selected seat encodings from the mixed ZIP/GZIP runs have also passed pre-inspection, generating 1,438 rows with no missing quantity tables.
9 related tests, Ruff, and full mypy (733 source files) have passed.

When encountering HTTP 429, enforce the server's `Retry-After` across all worker threads and persist the retry deadline; restarting does not bypass ongoing waits. Verify breakpoint recovery by checking the source and hash of existing files, and only retrieve missing episodes. Explicitly log all network and verification failures; do not publish a final training set if the download is incomplete.

## Recreation

Obtain the program using the already installed and authenticated Kaggle Python environment; coding and acceptance using project `.venv`:

```bash
PYTHONPATH=src python -m kagg_revue.datasets.ranked.acquisition
.venv/bin/python -m kagg_revue.datasets.ranked.audit
.venv/bin/python -m kagg_revue.datasets.ranked.prepare
.venv/bin/python -m kagg_revue.datasets.ranked.verification
```

Configurations are [ranked_acquisition.yaml](../configs/ranked_acquisition.yaml) and [demonstrations_ranked.yaml](../configs/demonstrations_ranked.yaml). Enable breakpoint retry on acquisition; code must specify a new output directory to prevent overwriting of already authenticated datasets.
