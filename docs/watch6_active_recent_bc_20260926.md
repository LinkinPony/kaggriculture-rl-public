# Six-Party Active Version and Recent Submission BC Dataset

This compilation includes existing collected replays involving teachers DSM, M & M & P & Q, DECEM, Boey, Vadim Vasilenko, and our unknown Mother-Goose (team ID **16730612**).

## Filtering Rules and Freeze Source

Five opponents using union: **currently publicly active submissions, or official `dateSubmitted` submissions from Beijing Time 2026-09-25 00:01 onward (inclusive of boundaries)**. The UTC lower bound is **2026-09-24 16:01:00**. The public list snapshot was taken from 9/26 at **00:09:56–00:10:06 UTC**, containing 10 currently public versions; 8 additional non-active versions meeting the date criteria were added, totaling **18 versions**.
Boey's two active versions, although occurring before the date lower bound, are included according to the union rule.
No additional filtering by win/loss, score, or cash is applied; the rule of excluding submissions from `56414341` throughout the entire game is maintained.

Our side uses the existing replay seat **`createTime >= 2026-09-24T16:01:00Z`** as specified by the user's subsequent clarification, evaluating based on the start time of the game rather than the submission date.
The team ID, display name, and four submission IDs all match the official game records and the historical submissions under this account.
Only the selected teacher seats are monitored; both players in a game are retained if they meet their respective conditions.

Original collector snapshot covers 9/26 **00:04:28–00:13:22 UTC**.
Merge activities from five lists with historical records, deduplicate by episode ID, then select from existing replays.
Additional collection lists include Vadim's two recent older versions contributing **22 games**, and 1 game for M & M & P & Q.
Our total is **108 games / 108 trajectories**, of which 79 align with the five-party data, and 29 are newly added.
Entries containing only metadata and no collected replays are excluded; no additional replays were downloaded.

| My submitted | Number of trajectories |
| --- | ---: |
| 56519499 | 25 |
| 56525914 | 34 |
| 56538672 | 34 |
| 56554776 | 15 |

Final selection frozen at **1,874 games / 2,078 teacher trajectories**.
The original selections and confirmed datasets from the five parties are retained, while the six-party outputs use a separate directory.
Source evidence and immutable hashes are available at
[Five-party submission selection](../outputs/datasets/derived-v5b-watch5-active-recent-20260926-train-val-q100/source-manifests/selection.json),
[Our game selection](../outputs/datasets/derived-v5b-watch6-active-recent-20260926-train-val-q100/source-manifests/own/selection.json), and
[Merged scope verification](../outputs/analysis/watch6-active-bc-20260926/scope-verification.json).

## Coding and Acceptance

All **1,874 games** completed encoding, with no whole games excluded; 204 games involved both selected teachers.
Training set: **1,777 games / 1,972 trajectories / 1,417,582 effective supervised turns**;
Validation set: **97 games / 106 trajectories / 76,200 effective supervised turns**.
300 unsupervised turns retained context and masked loss; total array size is **84,241,545,022 bytes**.

| Teacher | Training Trajectory | Validation Trajectory | Total |
| --- | ---: | ---: | ---: |
| DSM | 533 | 24 | 557 |
| M & M & P & Q | 220 | 15 | 235 |
| DECEM | 441 | 19 | 460 |
| Boey | 484 | 38 | 522 |
| Vadim Vasilenko | 192 | 4 | 196 |
| Unknown Mother-Goose | 102 | 6 | 108 |

manifest SHA256: `e931b6bd87ec3546b20ece61220b2ea11bef17c6f445da05af544009917c7ea7`.
**5,622 array hashes**, all identity and environment seed splits verified.
Random sampling covering six teachers, 22 submissions, and two partitions, totaling 24 games,
**20,851 lines of encoding / 34,560 official observations** all consistent.
6 tests related to filtering, identity, and seat merging, Ruff, and 24 data module files passed mypy.
See [Data Acceptance](../outputs/analysis/watch6-active-bc-20260926/data-verification.json).

## Data Ingestion and Reproduction

[Six-party Hydra Configuration](../configs/sequences_watch6_active_recent_20260926.yaml) inheritance
[Five-party Configuration](../configs/sequences_watch5_active_recent_20260926.yaml), fixed with existing five-party selections and appending our own seat.
Use complete `grounded-derived-context-v5b`, 27,915-dimensional input, retain all 719 decision turns per trajectory.
Unsupervised decisions only mask losses; full context is preserved. Partition train/val by environment seed,
partition seed **62001**; the two teacher seats within the same game remain in the same partition.

Data entry point is
[`manifest.json`](../outputs/datasets/derived-v5b-watch6-active-recent-20260926-train-val-q100/manifest.json).
The adjacent directory stores parsing configuration, complete source list, game-by-game records, and observation / action / eligible arrays.

Reproduce the selection, encoding, and verification of freezing in the root directory of the warehouse:

```bash
mkdir -p tmp/watch6-active-bc-20260926
export PYTHONPATH=src TMPDIR="$PWD/tmp/watch6-active-bc-20260926"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m kagg_revue.datasets.sequences.submissions --config-name sequences_watch5_active_recent_20260926
python -m kagg_revue.datasets.sequences.own --config-name sequences_watch6_active_recent_20260926
python -m kagg_revue.datasets.sequences.prepare --config-name sequences_watch6_active_recent_20260926
python -m kagg_revue.datasets.sequences.verification --config-name sequences_watch6_active_recent_20260926
```

Existing frozen snapshots will not change with continuous data collection or leaderboard updates; the encoding entry verification already matches the existing array's task identity and hash thereafter.
