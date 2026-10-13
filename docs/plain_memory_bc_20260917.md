# Old Residual Block + Time Memory: September 17 BC

User requests to pause the current GTrXL training, revert to the old Block, retain time memory, download the latest three complete daily dates, then perform a BC. This operation will only execute the BC; after completion, save and stop, with RL not automatically starting.

## Stopped Execution

`gtrxl-m384-bc100-3d-20260916-s71001` received SIGTERM and exited normally.
Final save: **U965 / 123,520 games**, checkpoint `checkpoints/update-000965.pt`,
SHA256 `68d0eac5ecf47c0ea38b42e9ac8f4d04f65dd2c0786ffaacdd32d8400388dcac`.
Model, dual optimizers, dual-card RNG, and history pool retained; all tensor limits enforced, training lock released.
Evidence: [Stop verification](../outputs/analysis/plain-memory-20260917/old-stop-verification.json).

## Architecture and Budget

- Actor entity encoder **16 × 384**, Critic entity encoder **6 × 320**, both using old
  `Block`: pre-LN, standard residual addition, no branch output ReLU, output projection uses
  `1 / sqrt(2 × depth)` initialization scaling.
- Actor and Critic each retain independent **2 × 256** time modules; four summaries per turn, memory retains 384 turns. Time module and memory fusion continues to use existing gating; entity encoders remove gating.
- Actor **24,880,538**, Critic **9,648,962**, total **34,529,500** parameters.
  BC trains only the Actor; Critic is randomly initialized when RL is later launched independently.
- Random seed 72001, fully random initialization. Dual H200, BF16, compilation enabled.
- BC global **8 full trajectories / 5,752 context turns**, 4 per card; 48 turns continuous per segment, memory preserved across segments, gradients truncated, full trajectory processed before Adam update.
  Learning rate 1e-4, maximum 100 epochs, early stopping on validation NLL with patience 10 / min_delta 0.001.
- After each round, record validation NLL, 4 self-play games' operational statistics, and 16-game evaluations against two fixed random models (double-seat). Random model diagnostics do not equate to competitive strength, and cannot be directly compared across different opponent pools.
- `pretraining_only: true` explicitly prohibits automatic transition from BC to RL; no cash rewards are used.

Official configuration: [learning_plain_memory_bc_20260917.yaml](../configs/learning_plain_memory_bc_20260917.yaml).

## Data

The latest three complete dates of the newly acquired daily index are **2026-09-14 / 15 / 16**, with 654 / 652 / 639 games respectively, totaling **1,945 games**. The original index, compressed package, and source list are permanently stored in `data/external/kaggriculture-plain-memory-20260917/raw/daily/`; reusable downloads are retained with their original paths. The historical top ten teacher filtering criteria from prior periods are continued, rather than claiming a re-grab of today's top ten rankings.

Complete observations are used for causal memory; actions that cannot be supervised are only masked in loss; quantity follows q100.
Splitting is performed by environment seed to isolate training, validation, and confirmation. After encoding, hash all arrays and verify them; from each date, extract three games for complete official replay and item-by-item encoding consistency verification.

Configuration: [sequences_20260917.yaml](../configs/sequences_20260917.yaml).
Encoding completed: Training 1,606 games / **2,456 trajectories / 1,764,824 supervised turns**;
Validation 81 games / 129 trajectories / 92,695 supervised turns; confirmation 80 games / 121 trajectories / 86,951 supervised turns. Each training epoch involves **307 Adam updates**, with a maximum of **30,700 updates** over 100 rounds. Observed context is retained for masked action frames.
The complete manifest SHA256 is
`6ea86052a53d795160680b918cad31febcfb7076664b7d2370fedf11552b90c2`.
All **5,301 array hashes** passed; 9 full official replays were cross-verified against **12,960 observations**, and an additional **12,223 encoded lines** were found to be exactly equal. Environment seeds show no leakage across the three data splits and do not collide with the retained training/evaluation seed ranges of new runs. The new official seed ranges have been cross-checked against the reserved intervals of 97 historical runs.

## Acceptance

Regression tests with consistent encoder weights and outputs have passed; segmental consistency and gradient finiteness of the gated entity block and causal memory have passed. Ruff and full-scale src mypy (814 files) have passed.
12 related tests have passed. Replay of 719 turns in full size with BF16, cache eviction of 384 turns, and new game clearing have passed, with an average prefix KL of 4.998e-6 under the invariant policy.
The two-GPU BC has completed Round one and saved the stop state normally; after restoring from archived source code, it completed Round two, with Adam steps increasing from 1 to 2, totaling 4,314 supervised turns. The model and Adam tensors are finite; the entity encoder, time module, and fusion parameters have all been updated upon restoration, and the two-GPU RNG is fully preserved. Both rounds of operational diagnostics and random opponent cash panels have been generated; the final state is complete, RL update count is 0, and the BC has been confirmed before normal termination.

Evidence: [Dual-card acceptance](../outputs/analysis/plain-memory-20260917/qualification.json),
[Data verification](../outputs/analysis/plain-memory-20260917/data-verification.json),
[BF16 memory consistency](../outputs/analysis/plain-memory-20260917/consistency.json),
[Parameter and seed check](../outputs/analysis/plain-memory-20260917/architecture-seeds.json).

## Official Operation

`outputs/learning/plain-m384-bc-3d-20260917-s72001` has passed configuration
`learning_plain_memory_bc_20260917` started, using frozen manifest hash and shared compilation cache.
Run ID `3cfaedf1df45404e85b8e26509dce8db`. Formal Step **88** checkpoint has been individually confirmed:
704 distinct trajectories, 505,871 supervised turns, data order and valid mask counts match, model and Adam finite, encoder, time module, and fusion parameter updates, dual-GPU RNG complete. Median batch inference time **0.866 seconds**, median loading time **0.035 seconds**.

Execution resumed from the original source archive. The parent hash of the **step 96 / 551,870 supervised-turn** checkpoint points exactly to step 88. Adam advanced from 88 to 96, all modules continued updating, and model and optimizer tensors remained finite.
Formal BC continues on two GPUs. The first validation pass has not finished, so these training-batch losses do not establish whether terminal cash has recovered. Save and stop when BC finishes.

See [first official checkpoint](../outputs/analysis/plain-memory-20260917/formal-checkpoint.json),
[archive continuation verification](../outputs/analysis/plain-memory-20260917/formal-verification.json),
[startup log](../outputs/analysis/plain-memory-20260917/formal-launch.json),
and [real-time progress](../outputs/learning/plain-m384-bc-3d-20260917-s72001/learning-progress.json).
