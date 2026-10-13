# compact289: Eight Teams, Five-Day Data, Dual H200 BC100

**Subsequent changes: User requested early termination of BC and transition to PPO.** BC was completed for 47 full epochs +
Epoch 48, batch 100 saved and stopped; latest weights integrated into [official dual-GPU PPO](compact_ppo_20260921.md).
The original BC100 protocol and startup records are retained; full 100 epochs and final confirmation set evaluation were not performed.

After throughput optimization, the old formal PPO is discontinued, the selected model is frozen, and a new BC operation is established.
The runtime directory is `outputs/learning/compact289-v4-selected8-bc100-20260921-s74001`,
Startup time **2026-09-21 03:03:46 UTC**. The following are the startup and early validation logs.

## Fixed Specifications

| Item | Fixed Value |
| --- | --- |
| Actor | 256-width, 3 layers, 4 heads, expansion 2; 2,507,162 parameters |
| Prefix Critic | 128-width, 1 layer; 380,546 parameters |
| Total Parameters | **2,887,708** |
| Observation and Attention | Full v4's 22,003 features, all 286 scene tokens |
| Memory | No learned memory; public historical features of observations are retained |
| Precision | BF16 mixed precision, FP32 parameters and Adam states |
| Action | Original 276-column ABI; only omitting fixed zero-padding intermediate computations |

Model entry: [compact289.yaml](../configs/model/compact289.yaml).
Training preset: [learning_compact_20260921.yaml](../configs/learning_compact_20260921.yaml).
Current configuration: [learning_compact_bc_20260921.yaml](../configs/learning_compact_bc_20260921.yaml).
This round optimizes only the Actor's supervision objective; the Critic configuration is reserved for future PPO.
Performance experiment conclusion is available in [throughput report](throughput_scale_20260921.md).

## Data and Training Agreement

Reusing the verified [eight-team five-day data](selected8_five_day_bc_20260921.md):
From 2026-09-16 to 09-20 UTC, 2,777 games, 4,189 teacher trajectories, and 3,011,489 supervised turns.
Entry point is `outputs/datasets/agronomy-v4-selected8-5d-20260921-q100/manifest.json`,
SHA-256 is `8def06dbcad7881bcb4b3c2fbc2049c702cb050a1a8aaeb8121dac66088c34eb`.
At startup, each rank verifies the hash of all arrays and the data protocol, without modifying the dataset.

| Partition | Supervised Turns | Usage Method |
| --- | ---: | --- |
| train | 2,742,636 | Traverse completely once per epoch |
| selection | 130,124 | Complete validation once per epoch, without updating parameters |
| confirmation | 138,729 | Perform complete evaluation once after the 100th epoch |

- **100 epoch, no early stopping**; total training sample budget **274,263,600 turns**.
- GPU0 + GPU1, distributed gradient averaging; root seed 74001, learning rate `1e-4`.
- Each group contains 16 complete trajectories, 8 per card, totaling 11,504 context turns;
  padding and unsupported teacher rows are only masked out in loss, without sampling or discarding supervised turns.
- 239 groups per round, totaling **23,900 global Adam updates**. The final group is normalized by global effective turns.
- BC loss uses per-turn effective action field average NLL, then averaged over global effective turns.
  For memory-free models, trajectories are flattened for computation, while original observations and conditional teacher prefixes are preserved.
- Every 16 groups and at epoch boundaries, optimizer, dual rank RNG, cursor, and data identity are saved.
- `pretraining_only=true`: terminate upon budget completion, do not automatically enter PPO; do not replace the 100th round with the validation-best round.

Full coverage of training/validation splits in Round one, training NLL **1.08537**, validation NLL **0.85133**.
After 10 rounds of training, training NLL **0.42814**, validation NLL **0.42603**.
Round one includes compilation; subsequent training phases take approximately **52 seconds/epoch**, validation takes about **1.4 seconds**, with additional overhead for saving and publishing. These metrics measure teacher action fitting and do not represent match win rate.

## Old Training Stopping and Recoverability

Old `agronomy-v4-m384-bc100-3d-20260917-s73001` received normal stop signal,
Completed saving and exit in **U7820 / 1,000,960 games**, exit code 0.
Original runtime retained; final weights and ledger saved to
`outputs/analysis/compact-bc-selected8-20260921/previous-training-*`.

A new run starts from random initialization with source code identity
`d7e89a8370005bb0d496351470408be8499493a6fff688e8a9ebefb78b921bae`.
The run directory saves `source.tar.gz`, `source.json`, native binaries, parsed configuration, and a standalone ledger.
Subsequent WebUI fixes will not alter the implementation already loaded in this training process.

If a new run is unexpectedly stopped, use the archive recovery entry; do not restart during runtime:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/compact289-v4-selected8-bc100-20260921-s74001
```

## BC WebUI

Open [this run](http://127.0.0.1:8765/?run=learning%2Fcompact289-v4-selected8-bc100-20260921-s74001).

- Complete epoch progress, real-time/saved batches, supervision turn budget, learning rate, throughput, and ETA.
- Training/validation NLL, five-action NLL and accuracy, as well as training and validation time curves.
- Action space effective field count, per-epoch details, gradient norm and load time for the last 12 batches.
- Three data partitions, number of teacher trajectories per partition, data hash verification, and final confirmation results.
- Automatic synchronization of expanded/collapsed state, table scroll position, and keyboard focus; separately preserve state when switching BC runs.

Write the BC curve to an independent `pretraining/metrics.jsonl` to avoid mixing with PPO update.
The accuracy under conditions is based on the teacher's action prefix and is not marked as complete plan accuracy or game win rate.

Verification includes full-parameter gradient and complete ABI reference comparison, existing BC recovery/sequence loading tests, API and curve monitoring tests, Ruff/mypy checks, as well as actual Chromium automatic refresh interaction validation.
Evidence is stored in [Migration Verification](../outputs/analysis/compact-bc-selected8-20260921/transition-verification.json) and [Refresh Interaction Verification](../outputs/analysis/compact-bc-selected8-20260921/webui-reading-state-verification.json).
