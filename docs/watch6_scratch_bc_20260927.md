# Six-Party Old Data Plus Latest Replay: Reinitialize BC with Random Weight

**Next State:** As requested by the user, normally stopped at
Round **16,608 / 95,333,278 supervision turns** on **2026-09-27 04:55:36 UTC**, full state preserved.
Latest Actor used for [new RL, historical pool inheritance, and cash difference rewards](watch6_bc_to_rl_20260927.md).
The original data, startup, and verification records are retained below.

Stopped normally as per user request, RL `derived-v5b-m384-watch6-ppo50-20260926-s91001` at **2026-09-27 00:52:11 UTC** at **U2137 / 273,536 games**.
The supervision process recovery exit code is 0; checkpoint hash, full optimizer, dual rank RNG, and parameter boundedness verification passed.
390 active historical strategies and original PFSP records are retained.
See [Checkpoint Verification](../outputs/analysis/watch6-scratch-bc-20260927/stop-verification.json).

## Frozen Data

Based on the previous six-party BC s90001's **1,874 games / 2,078 trajectories** as the base set,
five continuous collectors' collected replays up to **9/27 00:43:47–00:52:18 UTC** are appended.
All previous teacher seats, submitted identities, and environment seeds are retained, and the original manifest and arrays remain unchanged.
Among them, 1,868 fully identical encodings are reused after hashing; 1,462 new or seat-changed games are re-encoded.

Extend the original scope: five opponents use the union of "currently publicly active submissions" or "official submissions with submission time from Beijing Time **9/25 00:01** onward"; our side, Unknown Mother-Goose, uses existing games starting from that time.
Monitor only valid seats, deduplicate within the same game, retain two trajectories when both sides are valid, and exclude submission `56414341` entirely.
No additional filtering by win/loss, score, or current amount; no extra download of match replays.

Final: **3,330 games / 3,853 trajectories / 37 submission versions**, excluding zero-length games.
Compared to last time, added **1,456 games / 1,775 trajectories**.
Training: **3,157 games / 3,657 trajectories / 2,628,976 effective supervised turns**;
Validation: **173 games / 196 trajectories / 140,905 effective supervised turns**.
Retain full 719-turn context per trajectory; only mask loss for 426 unsupervised turns.
Partition seed remains **62001**; samples from the same environment seed are not cross-partitioned.

| Teacher | Trajectory Count |
| --- | ---: |
| DSM | 1,076 |
| M & M & P & Q | 512 |
| DECEM | 798 |
| Boey | 702 |
| Vadim Vasilenko | 587 |
| Unknown Mother-Goose | 178 |

Data entry point is
[manifest.json](../outputs/datasets/derived-v5b-watch6-expanded-20260927-train-val-q100/manifest.json),
SHA256: `254ebdb3b892a5b4c294d7f528bf79e2962c0c6e5ffdf84b37cdc700a19241c7`.
See [Scope Verification](../outputs/analysis/watch6-scratch-bc-20260927/scope-verification.json),
[Five-Party Freeze Selection](../outputs/datasets/derived-v5b-watch6-expanded-20260927-train-val-q100/source-manifests/selection.json) and
[Our Side Selection](../outputs/datasets/derived-v5b-watch6-expanded-20260927-train-val-q100/source-manifests/own/selection.json).

9,990 array hashes passed; independent spot-checks covered six teachers, 37 submission versions, and two partitions, totaling 39 games, 33,793 lines of code, and **56,160 official observations**, all consistent.
See [Data Acceptance](../outputs/analysis/watch6-scratch-bc-20260927/data-verification.json).
Current data aligns with the BC module's Ruff and mypy passing for 47 source files; no modifications to the training implementation are required.

## New BC Protocol

**2026-09-27 01:01:33 UTC** Started
`derived-v5b-m384-watch6-scratch-bc100-20260927-s92001`,
run ID **`9aca70e1512748d3bd8c5beeece89583`**.
New random seed **92001**, `initial_weights: null`, `resume: false`,
using standard random initialization with original fixed exploration bias, create new BC Adam.
Complete v5b, 27,915-dimensional input, 384-turn memory; two-GPU BF16, FP32 parameters,
learning rate **1e-5**, **100 epochs, no early stopping**, equal weighting across five action groups.
Global batch size of 8 full trajectories, 4 per GPU, 48-turn gradient blocks; 458 training batches and 25 validation batches per epoch.
Save full state every 16 batches and at epoch boundaries; terminate after BC completion.

[Training configuration](../configs/learning_watch6_scratch_bc_20260927.yaml) inherits the previous recipe,
[Difference record](../outputs/analysis/watch6-scratch-bc-20260927/protocol-changes.json) contains only new directories,
new seeds, expanded data, and random starting points.
The collector continues running, and subsequent added data does not alter the current frozen input.

**01:02:01 UTC** Random start validation passed: 351 Actor tensors and seed 92001
The regenerated model matches bit by bit; 339 tensors differ from the RL weights at the point of stopping, but the model structure is identical.
The ledger clearly records `initialization: random`, empty `input_weights`, with no evidence of weight migration.
See [Startup Log](../outputs/analysis/watch6-scratch-bc-20260927/launch.json),
[Random Start Validation](../outputs/analysis/watch6-scratch-bc-20260927/initialization-verification.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-watch6-scratch-bc100-20260927-s92001/learning-progress.json).

**01:05:16 UTC** Turn **80 / 455,054** of supervision fully saved checkpoint accepted:
BC Adam consists of 80 steps, actual LR **1e-5**, 339 Actor tensor updates completed.
Floating-point model parameters are FP32; model and optimizer are both finite, double rank RNG is complete;
Two training readers completed array hash verification, two GPU workers are running normally.
Original RL ledger hash unchanged; during verification, the new BC has completed turn 82 and continues training.
See [verification run](../outputs/analysis/watch6-scratch-bc-20260927/running-verification.json).

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -u -m kagg_revue.learning.cli \
  --config-name learning_watch6_scratch_bc_20260927
```

After normal termination, use archived source code and full state recovery:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-watch6-scratch-bc100-20260927-s92001
```
