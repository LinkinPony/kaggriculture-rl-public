# U2349 → Four 9/24 Initial Download of Data BC

**Next state:** Stopped normally as per user request at
**2026-09-25 13:46:38 UTC**
at the **5,992nd batch / 34,329,530 supervision turns**, having completed 25 epochs and entering the 26th.
The latest complete checkpoint `pretraining/shard-005992.pt` has been used as the initial Actor starting point for the new RL;
the original BC optimizer, dual-GPU RNG, epoch weights, and historical data are all preserved. See
[Stop verification](../outputs/analysis/watch4-bc-to-rl-20260925/stop-verification.json).
The new run is available at [Quad BC → RL](watch4_bc_to_rl_20260925.md).
The following retains the original BC startup and runtime records.

User explicitly selects filtering by **replay first download time**: from `2026-09-24T00:00:00Z` onward,
including all available replays from the four existing ongoing collection tasks: DSM, M & M & P & Q, DECEM, and Boey.

## Stop and Weight

Boey ran standalone BC at **2026-09-25 12:11:58 UTC** and normally stopped at the **1,029th batch**,
completing 51 epochs and 5,772,132 cumulative supervision turns. Full Adam, dual-GPU RNG, weights, and
history are preserved, see [stop verification](../outputs/analysis/watch4-collected-since-20260924-bc-20260925/stop-verification.json).

New BC initialized from `agronomy-v4-m384-dsm-games-ppo50-20260924-s82001` latest complete
**U2349 / 300,672 games** of Actor reinitialized, new Adam and random seed established.
Parent checkpoint is `checkpoints/update-002349.pt`, SHA256:
`c4244971cc6a28286e2e377374a1849d7fc72c76f866e043cb24041351d968df`.
Complete v5b, 384 turn memory, 351 Actor tensors, identical layout.

## Download Time and Data

Save four original collector manifests and immutable copies of the downloaded provenance, read
`retrieved_utc`, for the same episode, take the earliest timestamp from the four sources. Old daily ZIPs are excluded from the group because they are proven to have been obtained before the lower bound by existing records for 9/21 and 9/22; do not infer the first download based on file modification time, game date, or submission date. Subsequent collections do not alter the frozen data of this round.

Snapshot range is **9/25 12:07:34–12:15:59 UTC**; the initial download time coverage spans
**9/24 00:00:15–9/25 12:15:14 UTC**. There are additionally 2 datasets frozen in the DSM list that have not been downloaded and are not included in the current round's collected data. Only the existing `56414341` exclusion items from the collector are retained; no filtering is applied based on score, cash, or win/loss. Previous score-based filtering for specific datasets using `56509757` is not applied to this "all-data" collection.

Frozen **1,850 games / 1,978 teacher trajectories / 20 submission versions**.
Two abnormal complete trajectories containing non-ACTIVE decision frames, `112769598` and `113215371`, cannot be accessed.
Existing BC encoding retained; original files preserved; final **1,848 games / 1,976 teacher trajectories**.
128 games are teacher-versus-teacher matchups, with both qualified seats supervising, deduplicated by episode ID.

| Teacher | Training Trajectory | Validation Trajectory | Total |
| --- | ---: | ---: | ---: |
| DSM | 511 | 14 | 525 |
| M & M & P & Q | 416 | 20 | 436 |
| DECEM | 686 | 23 | 709 |
| Boey | 292 | 14 | 306 |

Reusing environment seed and partition seed 62001: Training 1,779 games / 1,905 trajectories / 1,369,271 effective supervised turns; Validation 69 games / 71 trajectories / 51,033 effective supervised turns.
440 unsupervised turns only mask the loss, preserving the complete memory context.

[Frozen scope and source evidence](../outputs/datasets/derived-v5b-watch4-collected-since-20260924-train-val-q100/source-manifests/selection.json),
[Data manifest](../outputs/datasets/derived-v5b-watch4-collected-since-20260924-train-val-q100/manifest.json);
manifest SHA256: `9299c7725a5236ac2dcefa86cbac2231780199bfc56d1d745eeaa7aebc166372`.

## BC Configuration

**2026-09-25 12:21:43 UTC** Start new run
`derived-v5b-m384-u2349-watch4-bc100-20260925-s88001`.
Fixed learning rate **1e-5**, **100 epoch, no early stopping**; dual-GPU BF16 computation, FP32 parameters and Adam,
five action groups equally weighted, global 8 complete trajectories, 4 per GPU, 48 turns per gradient block.
239 training batches and 9 validation batches per epoch, totaling 23,900 Adam updates.
Save every 16 batches and at epoch boundaries; retain epoch weights; stop after BC completion.

Training configuration (../configs/learning_watch4_collected_bc_20260925.yaml),
Data configuration (../configs/sequences_watch4_collected_20260925.yaml),
Startup record (../outputs/analysis/watch4-collected-since-20260924-bc-20260925/launch.json), and
Real-time progress (../outputs/learning/derived-v5b-m384-u2349-watch4-bc100-20260925-s88001/learning-progress.json).

5,544 array hash values and all identity, environment seed splits have passed verification; independent spot checks covering 20 submitted versions, four teachers, and two partitions, totaling 20 games, 17,256 lines of code, and 28,800 official observations, all consistent.
6 tests for download time filtering and seat merging have passed, and the newly added code Ruff/mypy has passed.
See [Data Verification](../outputs/analysis/watch4-collected-since-20260924-bc-20260925/data-verification.json) and [Audit Records](../outputs/analysis/watch4-collected-since-20260924-bc-20260925/checks.json).

run ID is `1a672d2cfc0e4527a5f6cec71dd04dd3`. The initial 351 actor tensors are identical to s82001 U2349 bit-by-bit, and BC uses a fresh Adam optimizer. **12:24:23 UTC** has confirmed checkpoint **64 / 367,983** supervision turns: Adam has taken 64 steps, actual LR is **1e-5**, 339 actor tensors have been updated, the model and optimizer are all finite, and both rank RNGs are intact.
Training continues on two GPUs; the ledger hashes of s82001 and the BC that has stopped Boey remain unchanged.
See [Start Verification](../outputs/analysis/watch4-collected-since-20260924-bc-20260925/initialization-verification.json) and [Run Verification](../outputs/analysis/watch4-collected-since-20260924-bc-20260925/running-verification.json).

Restore by archiving source code after stopping:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-u2349-watch4-bc100-20260925-s88001
```
