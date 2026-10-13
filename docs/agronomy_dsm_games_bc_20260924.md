# U3207: DSM Game BC Occurring from September 22 onwards

Stop s80001 PPO, retrieve the latest Actor at the time of stopping, and use the previously collected **802 games**
DSM game launch a new BC. This range follows the official game **`createTime`**, not the submission version date.

**Next state:** User requested transition to RL; this BC has been normally stopped at
**Batch 737 / 4,239,224 supervision turns** at **07:10:49 UTC**. The latest Actor used to initiate
[s82001: 50% self-play PPO](agronomy_dsm_games_ppo50_20260924.md), and the full state of the original BC is preserved.

## Parent Run and New Run

`agronomy-v4-m384-dsm-grouped-ppo-20260923-s80001` stopped normally at **2026-09-24 06:54:07 UTC** in **U3207 / 410,496 games of RL**, and the supervision process was restored and exited normally.
Actor/Critic Adam optimizers each took 9,621 steps; the original optimizer, RNG, PFSP, and historical artifacts are retained.
Parent checkpoint `checkpoints/update-003207.pt`, SHA256:
`d6cd5117af1d6a72aa474458027305c0dab202c43b2c2b724e50de86f178f3d9`.

New BC `agronomy-v4-m384-u3207-dsm-games-bc100-20260924-s81001` started at **06:57:29 UTC** running GPU0+GPU1, training ID `edada32ea5844242a251488d10d6b22b`.
The initial Actor's **347 tensor** configuration and model layout are identical to U3207; a new BC Adam is created.
Configuration details are available in [Training Configuration](../configs/learning_agronomy_dsm_games_bc_20260924.yaml),
[Stop Verification](../outputs/analysis/dsm-games-bc-20260924/stop-verification.json),
[Start Verification](../outputs/analysis/dsm-games-bc-20260924/initial-verification.json), and
[Startup Log](../outputs/analysis/dsm-games-bc-20260924/launch.json).

## Data Range

Fixed `2026-09-22T00:00:00Z <= createTime < 2026-09-24T06:49:20.533067Z`.
The original collection list is fixed at 06:50:08 UTC, during which this date still reports **802 games** to users:
9/22 accounts for 413 games, 9/23 for 348 games, and 9/24 for 41 games, all of which already have independent compressed replay.
Coverage includes 8 DSM versions, encompassing versions submitted prior to the start but participating within the range.
No filtering by win/loss, score, or cash is applied; supervision is limited to the seat of team ID **16732748 / DSM**.

Complete trajectory check exclusion **112052628** (opponent timeout during game; same anomalous field as previous DSM dataset), original file retained. Final **801 games / 801 DSM trajectories**, each with 719 supervised turns:

| Partition | Trajectory | Supervision Turn |
| --- | ---: | ---: |
| train | 768 | 552,192 |
| val | 33 | 23,727 |
| Total | 801 | 575,919 |

Reuse environment seed hash and partition seed 62001, 95% train / 5% val bucket mapping; no test set.
801 environment seeds across partitions with no leakage. Q100 truncation involves 143 turns, all context turns are supervised.
Total array size: 25,662,682,305 bytes, located in repository `outputs/datasets/`.

Data entry: [manifest.json](../outputs/datasets/agronomy-v4-dsm-games-20260922-24-train-val-q100/manifest.json),
SHA256 `a6ea4d18d6dd5d127977d860270ae5f9e9857892c77049effda30724c647721b`.
The original inventory, 802 game selections, and provenance are saved in the same directory `source-manifests/`.
All 2,403 array hashes passed; all 17,280 observations from 12 complete official games matched;
Verification covers all dates, versions, and two partitions, see
[Data Validation](../outputs/analysis/dsm-games-bc-20260924/data-verification.json).

## Training Protocol

Reuse the previous DSM group loss BC: 16 × 384 network, 384 turn memory, v4 features, q100;
Normalize the five action types separately, with equal weights of 1. Fixed learning rate **1e-4**, dual-GPU BF16 computation, FP32 parameters and Adam; global 8 complete trajectories, 4 per GPU, 48 turn sequence blocks.
Each epoch: **96 training batches / 5 validation batches**, totaling **9,600 Adam updates** over 100 epochs, accumulating **55,219,200 training supervision turns**. Save full state every 16 batches and at epoch boundaries.
No early stopping, terminate after budget is exhausted; `pretraining_only=true`, no automatic entry into PPO.

## Reproduction and Recovery

Add `datasets.sequences.episode_window` fixed list by game time, and verify exact game count, download integrity, exclusion items, and teacher status. Re-run the reused frozen original, and the collector continues to update without altering this dataset.

```bash
PYTHONPATH=src .venv/bin/python -m kagg_revue.datasets.sequences.episode_window
PYTHONPATH=src .venv/bin/python -m kagg_revue.datasets.sequences.prepare \
  --config-name sequences_dsm_games_20260924
PYTHONPATH=src .venv/bin/python -m kagg_revue.datasets.sequences.verification \
  --config-name sequences_dsm_games_20260924
```

After normal termination, continue training the same BC via the archive recovery entry:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-u3207-dsm-games-bc100-20260924-s81001
```

3 tests for new window and old window, 14 related BC tests passed; new code Ruff, formatting, and mypy passed.

## Official Operation Verification

**07:00:37 UTC** Verified complete checkpoint of the **48th / 276,096th supervision turn**, SHA256
`7cff33c87efced36935c1f9564b97e3e7053f2b6d89616d9ca7d8c89bb25db56`.
Adam for 48 steps, LR 1e-4, with dual rank RNG complete; all model and optimizer tensors are finite,
335 actor tensors have been updated, data and loss identities match configuration. steady-state time is approximately **0.74 seconds per batch**.
Supervision process and two GPU workers are alive; training continues, RL update count is 0.
See [formal verification](../outputs/analysis/dsm-games-bc-20260924/formal-verification.json).
