# s73001 U7820: Eight Teams, Five-Day Data BC100

**Future Changes: Users requested to prematurely terminate BC and initiate a new RL using the latest weights.**
This run has completed **10 full epochs + Round 11, batch 164**, and was saved to
`pretraining/shard-004934.pt` before being normally terminated. The latest weights have been integrated into
[Dual-GPU Unified PFSP PPO](agronomy_selected8_ppo_20260921.md).
The original BC100 startup protocol is retained below; the full 100 epochs and final confirmation evaluation were not executed.

Initialize independent BC run from `agronomy-v4-m384-bc100-3d-20260917-s73001`'s latest complete weights
**U7820 / 1,000,960 turns RL**: `outputs/learning/agronomy-v4-m384-u7820-selected8-bc100-20260921-s75001`.

Parent checkpoint is `checkpoints/update-007820.pt`, SHA256: `ee5964120b3f6ed427d289e83539975513cc9f2ed2485e0c2688829236a468dc`.
The new run preserves a complete copy of the parent checkpoint, the source ledger hash, the parent run ID, source identity, and protocol;
Initial actor parameters inherit the parent weights tensor by tensor, retaining the 16 × 384 network and 384 turn time memory.
The new BC uses a separate run ID and seed 75001, reinitializes Adam; all outputs from the parent run are retained.

## Fixed Training Protocol

Configuration: [learning_agronomy_selected8_bc_20260921.yaml](../configs/learning_agronomy_selected8_bc_20260921.yaml).
Data: [Eight-Team Five-Day Data Description](selected8_five_day_bc_20260921.md), dated
2026-09-16 to 09-20 UTC, manifest SHA256:
`8def06dbcad7881bcb4b3c2fbc2049c702cb050a1a8aaeb8121dac66088c34eb`.

| Project | Setting |
| --- | --- |
| Budget | 100 full epochs, no early stopping |
| Device | GPU0 + GPU1, two H200, synchronized gradient averaging |
| Precision | BF16 mixed precision computation, FP32 parameters and Adam states |
| Learning Rate | Fixed `1e-4` |
| Global Batch | 8 complete trajectories, 4 per card, 5752 context turns |
| Time Segments | 48 turns; Adam updated after full trajectory processing |
| Per Training Turn | 3,815 trajectories, 2,742,636 supervised turns, 477 updates |
| Total Training Budget | 274,263,600 supervised turns, 47,700 updates |
| Per Validation Turn | Complete selection set, 130,124 supervised turns |
| Final Confirmation | After turn 100, complete confirmation set, 138,729 supervised turns |
| Save | Every 16 batches and at epoch boundaries, including Adam, dual rank RNG, cursor, and data identity |

Training uses the average NLL of effective action fields per turn, then averages over all effective turns globally.
Context is retained, padding, and unexpressible teacher turn losses are masked. Training automatically stops upon completion,
`pretraining_only=true`, and does not automatically enter PPO. The current BC does not use a reward function.

## Run and Recovery

Startup time: **2026-09-21 08:07:02 UTC**, parent process PID **3507065**.
Run ID: `5a989e787597401fb2d54a5856fc1a05`; Source code identity:
`df8338ef21d659042ebcc901ca9268917b966f27a24bed789c7654a6d098c99c`.
Complete command, environment, and acceptance identity see
[Startup record](../outputs/analysis/agronomy-u7820-selected8-bc-20260921/launch.json).

```bash
.venv/bin/python -m kagg_revue.learning.cli \
  --config-name learning_agronomy_selected8_bc_20260921
```

New run includes complete source code archive and fixed native binaries. After stopping, use the archive recovery entry to restore:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-u7820-selected8-bc100-20260921-s75001
```

Resume using the parent weight copy saved during the new run, without depending on the parent directory's continued existence. The runtime ledger is explicitly labeled as
`checkpoint-root-league-v1` / `initialization=checkpoint`.
The serialized identity of the original random initialization protocol is maintained for compatibility.

## WebUI

[Open this BC run](http://127.0.0.1:8765/?run=learning%2Fagronomy-v4-m384-u7820-selected8-bc100-20260921-s75001).

Reuse independent BC epoch curve, complete round progress, real-time/saved batch, supervision turn count, throughput, and ETA.
Memory model completes five action types with NLL, teacher prefix condition accuracy, and gradient norm;
Display initial weight source, three data partitions, teacher coverage, and final confirmation set results.
Automatically refresh while preserving existing expanded state and scroll position.

Acceptance and official launch evidence writing
`outputs/analysis/agronomy-u7820-selected8-bc-20260921/`.

Two-GPU engineering subset completes two rounds, 4 Adam updates; after the first round's checkpoint is saved, the archived codebase is restored for the second round.
Training proceeds for 14,380 supervised turns, with 2,156 turns validated per round, and final confirmation on 2,876 turns.
The model, Adam, dual rank RNG, and supervision cursor have all been confirmed; the encoder, temporal memory, and action head have been updated.
All five action metrics are outputting normally; these small-data metrics are solely for engineering acceptance.

During the initial archival recovery, it was found that the script migration module requires an unused `_revue_native` extension when imported.
The module is now loaded only when script migration is required, and the issue has been fully fixed and retested for archival recovery prior to formal operation.
Logs from the initial acceptance and failed recovery are retained. 28 related tests, Ruff, and full mypy (906 files) have passed.
Chromium real-world weight source visibility and BC panel visibility with auto-refresh preserving expanded state, no JavaScript errors.
See [Acceptance Report](../outputs/analysis/agronomy-u7820-selected8-bc-20260921/qualification.json) and [Browser Report](../outputs/analysis/agronomy-u7820-selected8-bc-20260921/webui-qualification.json).

Formal checkpoint verification: `pretraining/shard-000048.pt` has been validated, with a complete audit copy retained:
**48 Adam updates, 276,051 supervision turns**, batch order and supervision mask counts match when reconstructed from seed.
Initial parameters are exactly equal to U7820 on a per-tensor basis; after 48 steps, the encoder, time memory, and action head have all been updated.
All checkpoint tensors are finite, and both rank RNGs are complete. Parent run ledger and U7820 original file hashes are preserved.
Dataset array hash passes; actual learning rate is `1e-4`; RL update for this run is zero.
Warm-up training median time per batch: **0.753 seconds/batch** for 56 batches, excluding checkpoint publishing and end-of-turn validation.
See [Formal Checkpoint Validation](../outputs/analysis/agronomy-u7820-selected8-bc-20260921/formal-verification.json) and [Formal WebUI Check](../outputs/analysis/agronomy-u7820-selected8-bc-20260921/webui-formal.json).
