# U2902: DSM and M & M & P & Q Data BC100

Stop the current PPO according to user request, using the continuous data collected by two players and the latest complete weights at the time of stop.
Start a new BC. The user explicitly selects **100 epoch, learning rate 1e-4, dual GPU**.

**Post-run status:** The user requested early termination of BC and transition to a new RL on the same day. This run was normally stopped at
**12:07:02 UTC**, with the latest complete checkpoint saved as `pretraining/shard-002120.pt`,
completing **7 epochs + Round 8, 195/275 batches**, accumulating **12,182,704 supervised turns**.
The original 100-epoch budget was not fulfilled; the model, BC Adam, dual rank RNG, data cursor, and original ledger are retained.
See [Stop Verification](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/bc-stop-verification.json).

## Parent Process Termination and Weights

`agronomy-v4-m384-selected8-ppo-20260921-s76001` stopped normally at **2026-09-22 11:28:49 UTC**, finally saving **U2902 / 371,456 games of RL**, with supervisor exit code 0 upon recovery.
The parent process and two GPU worker processes have all terminated; original weights, optimizer, dual rank RNG, PFSP, and ledger are preserved.

Parent checkpoint: `checkpoints/update-002902.pt`, SHA256:
`8ca9bf199ab92d8ccd4399affc278c7ec958099739f5b397b3a27b0aa4bf1251`.
The full checkpoint and ledger hash match; all 2,071 tensor limits are satisfied.
See [Stop Verification](../outputs/analysis/watch2-bc-20260922/stop-verification.json).

## Fixed Data Snapshot

The snapshot is taken from DSM's **11:28:23 UTC** list and M & M & P & Q's **11:27:27 UTC** list.
Both data collection tasks continue to run, and subsequent new games do not alter the current BC data identity.

- DSM: 12 versions, 1,529 trajectories; submission start point remains 2026-09-17 00:00 UTC.
- M & M & P & Q: 6 versions, 917 trajectories; retains all existing date ranges.
- Select teachers based on official `teamId`, seat, and activity `submissionId`; do not infer team identity by name.
- Opponent's older versions cannot bypass this team's range through matches against another team; `56414341` still excludes the entire game for any seat.
- Merge 19 duplicate records from mutual encounters between both teams, resulting in **2,427 games, 2,446 teacher trajectories**.
- 520 games directly read existing daily ZIP files; the remaining 1,907 games read the previously downloaded `.json.gz`, with no duplicate downloads.

Using the world seed hash division based on root seed 62001, consistent with existing BC partition rules,
the same world and both parties in the same game are always located in the same partition. No filtering by rating, cash, or match outcome.

| Partition | Game | Trajectory | Supervised Turns |
| --- | ---: | ---: | ---: |
| Training | 2,181 | 2,198 | 1,580,358 |
| Validation selection | 124 | 124 | 89,156 |
| Confirmation | 122 | 124 | 89,156 |
| Total | 2,427 | 2,446 | 1,758,670 |

Use the existing `grounded-production-context-v4` features, `complete-turn-seat-v1` complete trajectory, and q100 action interface. Retain 1,758,674 context turns; 4 turns with unexpressible actions are masked for supervision loss but not removed from context. 673 turns contain more than 100 quantity requests, maintaining the existing truncation encoding. No full game exclusions. Total array size: **78,365,686,734 bytes (approximately 73.0 GiB)**.

Data entry: [manifest.json](../outputs/datasets/agronomy-v4-watch2-20260922-q100/manifest.json).
SHA256: `324d0dfcf076be6ab06f50bd06aad9887b0ef30ebf759ab5e7c7d63760ad9173`.
A fixed copy of the original data collection list is stored in the same directory `source-manifests/`; source identity is referenced in `sources.json`.

All 7,281 arrays have passed verification of SHA256, size, type, and supervision count; 2,427 world seeds.
No leakage across partitions. Random sampling covers 31 complete games across ten dates, two teachers, and all partitions,
reconstructed encoding and masking are consistent, and all 44,640 observations in the official environment are identical.
See [Data Verification](../outputs/analysis/watch2-bc-20260922/data-verification.json).

Conversion, Verification Entry Point:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMPY_MADVISE_HUGEPAGE=0 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.datasets.sequences.prepare \
  --config-name sequences_watch2_20260922
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMPY_MADVISE_HUGEPAGE=0 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.datasets.sequences.verification \
  --config-name sequences_watch2_20260922
```

## New BC Operation

Run: `outputs/learning/agronomy-v4-m384-u2902-watch2-bc100-20260922-s77001`.
**11:36:22 UTC** Started, initial parent process PID 937498.
Configuration: [learning_agronomy_watch2_bc_20260922.yaml](../configs/learning_agronomy_watch2_bc_20260922.yaml).

| Project | Setting |
| --- | --- |
| Initial Weight | Latest U2902 Actor at termination, retain full checkpoint copy with source identity preserved |
| Model | 16 × 384, 384 turn memory, full v4 features |
| Budget | 100 full epochs, no early stopping, complete automatic termination |
| Device and Precision | GPU0 + GPU1, BF16 computation, FP32 parameters and Adam |
| Learning Rate | Fixed at 1e-4, new BC Adam |
| Batch | Global 8 full trajectories, 4 per card, 5,752 context turns |
| Update per Round | 275 Adam steps, cumulative 27,500 steps |
| Training Budget | 158,035,800 supervised turns |
| Validation | Full selection set per round; full confirmation set after round 100 |
| Save | Every 16 batches and at epoch boundaries, full Adam, dual rank RNG, cursor, and data identity |

`pretraining_only=true`, this run only executes BC, without automatically entering PPO. BC uses the supervision NLL from the effective action field, without using the reward function. A new independent run with seed 77001 is initiated, and the parent PPO optimizer and RNG are saved in the parent checkpoint; the new BC does not inherit them.

See [Startup Log](../outputs/analysis/watch2-bc-20260922/launch.json),
[Configuration Parsing](../outputs/analysis/watch2-bc-20260922/resolved-training-config.json).

After normal shutdown, restore from archive:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-u2902-watch2-bc100-20260922-s77001
```

8 tests, Ruff, and full mypy (933 source files) passed.

Formal **Batch 112 / 642,785 turns** checkpoint verified and fully preserved in the analysis directory.
The initial Actor's **347 tensors** match exactly those of parent U2902; the BC Adam has advanced exactly 112 steps,
with updates occurring in the encoder, memory, and action head. All checkpoint tensors are finite, with full double-precision CPU/CUDA RNG support,
reconstructed in batch order and precisely aligned with the cumulative turn count from the supervision mask. This RL update is 0,
and the parent ledger and U2902 file hashes remain unchanged. Warm training median time is **0.738 seconds per batch**, excluding save and end-of-epoch validation.

The monitoring interface has been confirmed to be running with type BC, status running, displaying correct parent weights, data identity, two teachers, 100 epochs, learning rate, and GPU0+GPU1. Run ID: `07ef5b8493fc42c8a3bb2399f29ba126`.
See [Initial Weights Verification](../outputs/analysis/watch2-bc-20260922/initial-verification.json),
[Official Checkpoint Verification](../outputs/analysis/watch2-bc-20260922/formal-verification.json),
and [Monitoring Audit](../outputs/analysis/watch2-bc-20260922/monitor-response.json).
