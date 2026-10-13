# 2026-09-14 PM Native Opponent Upgrade

Integrate the stronger version from the new investigation natively, retire the corresponding old version, and apply it to the current training.
Selection and intensity comparison across 896 games are available in [Afternoon Public Notebook Investigation](public_notebook_survey_20260914_refresh.md).

## Change Scope

- `ahmed_v42` replaces `ahmed_v41`, source SHA-256 `728fdfb4405ba313f8b14ffb3e0f8eceaddcaa0de49e4835928d89aaf71467e9`.
- `farming_v4_0914` replaces `farming_v4_0912`, source SHA-256 `03e263f1a20db29d6aa3404e978b97549bdac7f81d2b7f8dea5b36a3d6e91edc`.
- The source code and asset bytes of MetaCounter R1, Shop Router 0913, and Rayk V38 Low Pressure remain unchanged.

A new source is bound to [manifest](../data/external/kaggriculture-public-native-20260914-v2/manifest.json), SHA-256 `9c07d9b47f52f6e8d1e2bcddae2a140865cb6074f97421bbf532c4af07fe716f`. The farming date denotes the date when the source code was obtained; the list `lastRunTime` does not reflect the actual source code changes in this instance.

Reuse `opponents/compilation/` to generate C++ code for frozen functions and control flow in advance, resulting in 213 shared functions/initialization units. The existing compiler already supports two source code versions, requiring no modification to its strategies or extension of Python callbacks. The training entry remains `create_native_opponent_session` → `create_batch` → `ParallelBatch.advance_programs`, with the opponent executing within C++ that releases the GIL.

New configuration and trusted registry reject two retired IDs; the archiving protocol can still read them, and the original source files and assets are retained. The old generation implementation is preserved through training archiving and Git history retention; to reproduce the old version, the corresponding archived runtime must be used. The default mainline and native league configurations are updated to the new five IDs.

## CPU and Native Acceptance

- 100 complete and properly paired games: 143,800 actions, complete observation trajectories, control layer diagnostics, and fork consistency.
- 25 games with DIG interference injected every 37 turns: 35,950 actions and trajectory consistency.
- 10 games with official interpreter cross-verification covering five opponents and dual seats: 14,400 observations, 7,190 script actions, and numeric batch, `advance_programs`, and step 360 fork passes.
- 31 related tests passed; covering source integrity protection, new-old identity isolation, duplicate calls, reset, fork, quota, PFSP, and historical retention.
- Ruff, 744 source files passed mypy and `git diff --check`.

The above does not represent all possible game scenarios exhaustively. Verify native binary SHA-256 `5c9c6b46c6e86f070af328a71688fc9f87b5ac1db66311f6ded92a466e5e3b32`. The core rule `_revue_core` hash remains `2b947f38e5c18cda8ab03ca5c109998940feb90e6695621fc7ddd79514c4f5a3`.

8 games per batch, 8 CPU workers, two full PASS training sessions: V42 takes 3.28–3.30 seconds, the new Farming version takes 3.38 seconds; the other three take 2.84, 0.16–0.17, and 2.82–2.87 seconds. Includes session creation/cloning/destroys and RSS logging. This is not a GPU training throughput test per turn or a strict pre- and post-change performance comparison experiment.

Evidence Directory `outputs/opponents/public-20260914-v2/`:
[Normal](../outputs/opponents/public-20260914-v2/conformance/report.json), [Disturbance](../outputs/opponents/public-20260914-v2/perturbed/report.json), [Official Batch](../outputs/opponents/public-20260914-v2/training/training-parity.json), [Throughput and Memory](../outputs/opponents/public-20260914-v2/throughput.json).

## Current Running Migration

Operation in production remains `outputs/learning/budget-q100-top10-2d-20260913-s68001`. Use [Migration Configuration](../configs/learning_public_20260914_v2_change.yaml) to maintain 128 games per turn, a total budget of 100k, 30% self-play / 20% independent dynamic scripts / 50% historical PFSP, and constant learning rates for the Actor LR `7.5e-6` and Critic LR `1e-4`.

The script statistics of the new manifest are re-established from prior knowledge according to existing rules; the original learning model, two optimizers, dual-GPU RNG, historical model pool, external models, and historical PFSP are carried over. Migration must bind to a complete checkpoint and undergo dual-GPU updates through an isolated replica, followed by archival recovery.

Formally running on **U3959** normally stopped, checkpoint SHA-256
`c9988b0251f2f3330fcfb93d934476b79d89a01d2671c253b0192db0e9bd27ca`.
The original two Adams accumulated 83,102 / 83,139 steps; the migration did not alter any byte of this checkpoint.

The current model conducts an additional 10 official interpreter comparisons, involving 14,400 observations and 7,190 learner feature instances matching script actions.
Isolated replica `outputs/learning/public-native-qualification-20260914-v3` completes **12 turns / 1,536 games**:
U3963 normally terminates, then restores from archived source code to U3971. All five current scripts actively participate; each optimizer advances 252 steps, with both Actor/Critic components updated, all tensors finite, and both dual-GPU RNGs progressing while remaining independent.
Constant LR, 96 historical members, 57 external models, and existing training records are preserved; PFSP replay sampling and saved statistics are consistent.
This constitutes integration and continuity verification, and no training intensity gains are claimed based on this.

[Qualification Report](../outputs/opponents/public-20260914-v2/qualification.json) SHA-256
`1419b21009bd74753bd4379903532e69583b053fd01d3ced1475793c55422f17`,
bound formal U3959, complete original state, new protocol, new native runtime, and source code hash
`3767462c3eb3ede0a0d04ae68028de91b5837d0f81322f706b0098c7a8f40d13`.
See [Additional State Verification](../outputs/opponents/public-20260914-v2/qualification-verification.json).

Migration has been written into the official runtime `population-revisions/0002`, **effective from U3960 onwards**.
The only protocol change before and after migration is `script_population`; original checkpoints, models, optimizers, RNG, historical pool, PFSP, and training records remain unchanged. New script statistics are established from prior knowledge based on manifest identity, and the initial turn clears old script statistics.
See [Migration Verification](../outputs/opponents/public-20260914-v2/migration-verification.json) and
[Official Recovery Startup](../outputs/opponents/public-20260914-v2/formal-launch.json).

**Official U3964 checkpoint verified**, SHA-256
`40d05e2e983a2ce64ed93aac78fbb923269e0443c4b888b2cdcc215cab6b748f`:
Added 5 rounds / 640 games; all five current scripts actively participated. V42 executed 24 games in U3961, and the new Farming version executed 28 games in U3964. Each optimizer advanced 105 steps, with no KL rejections; both Actor/Critic were updated.
All checkpoint tensor limits are finite; dual-GPU RNG progressed independently; PFSP replay and saved statistics match exactly.
The parent hashes from U3959 → U3960 → U3964 are continuous; original U3959 bytes are preserved. Previous records, protocols, and external models remain intact; the new training records and script statistics no longer contain the two retired IDs.
The binary of the newly loaded scripts on both GPUs and the original rule core hashes have also been verified.

See [formal continuation verification](../outputs/opponents/public-20260914-v2/formal-verification.json).
Dual-card formal training continues to run; real-time progress is available in the run directory under `learning-progress.json`.
