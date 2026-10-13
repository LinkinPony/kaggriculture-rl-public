# v4 Latest BC Weighted Mixed RL: 2026-09-17

User requests to halt the current BC, and instead initiate an RL using the latest weights, incorporating a script opponent and the PFSP historical pool.
This supersedes the previous arrangement of stopping after a full 100 epoch BC; it retains the same run ID and save directory.

## BC Continuation Point

`agronomy-v4-m384-bc100-3d-20260917-s73001` saved normally and stopped at
`pretraining/shard-004187.pt`, SHA256:
`d2d4948bec400fbfaeaa487dff0cff301564f3bde0aebbd5d64617a6e3f69da5`.
Completed **13 full epochs + Round 14, 196 batches**, Adam **4,187 steps**,
cumulative **24,069,461 supervised turns**. The validation NLL of the final complete epoch 13 is
**0.2687714**, which does not represent the full validation result after partial training in Round 14.
Model, BC Adam, dual-GPU RNG, historical checkpoints, and original source code are preserved.
See [Validation Verification](../outputs/analysis/agronomy-v4-rl-20260917/stop-verification.json).

## RL Configuration and Historical Compatibility

Continue using v4 **22,003-dimensional** observations, standard residual Block Actor **16 × 384**,
Critic **6 × 320**, each with **2 × 256 / 384 turn** time memory.
Dual H200, BF16, compilation cache, native C++ game; **128 games per round**, **28 full trajectories per GPU**, 48-turn segments, Actor LR **7.5e-6**, Critic LR **1e-4**.
KL **0.05**, only early stopping, no rollback; reward is **pure terminal WDL (+1/0/−1)**,
funds are used only for observations and diagnostics. BC Adam is saved from the original BC checkpoint, PPO uses new dual optimizers.

Mixed ratio is **20% script / 50% PFSP history / 30% self-play**.
Five scripts are `ahmed_v45`, `metacounter_r1`, `shop_router_0913`,
`rayk_v38_low_pressure`, `farming_v4_0914`, executed directly via native batch processing extension.
Retain the previous mixed configuration's **137 external historical models**, sourced from s65001 (27),
s62001 (5), s67001 (25), s69001 (29), s68001 (51); initial pool plus current BC totals **138 members**.
Each 64 turns adds a current run snapshot, pool capacity reaches 177.
PFSP power 2, uniform 0.2, latest 0.1, prior 8 games, half-life 128 turns;
scripts perform independent PFSP sampling, one script is selected per turn and seats are balanced between both sides.
Rounded to cumulative quotas, each script plays either 24 or 28 games per turn, history fixed at 64 games, the rest are self-play.

The old historical model uses v2 features. Importation of historical weights with original ledgers, weight hashes, and source code identities is allowed only after full replay verification has passed between the old native core and the current core. Both feature sets are batch-encoded from the same native engine state, with v2 fields that retain their original values extracted for use by the historical model; routing buffers are reused without modifying the historical weights. A total of 9 complete replays, comprising **12,960 observations** of v2 arrays, actions, supervision masks, and full engine trajectories, have been individually hashed to ensure consistency. See [Native Compatibility Verification](../outputs/analysis/agronomy-v4-throughput-20260917/native-compatibility.json).

Original batch script binary declaration v2 has been parallelly rebuilt into v4 using existing build entry points;
C++ code generated via compiler, with no manual editing or modification of third-party source files.
After throughput optimization, five scripts with two seats each account for **10 games**.
Full official consistency passed: **14,400 official observations**, **7,190 learner feature rows**, and
**7,190 script actions** matched, taking 58.3 seconds. This time represents the official consistency check,
not the RL update throughput conclusion.
See [Script Official Consistency](../outputs/analysis/agronomy-v4-throughput-20260917/official.json).

## Throughput Optimization and Current Status

Original four-round acceptance U4 sampling: 56.0 seconds, optimization: 23.8 seconds, opponent/inference graph preparation: 14.9 seconds, update total: 94.8 seconds, formal RL not yet activated. The formal target is a complete update of 30–40 seconds including sampling, optimization, and saving; add `cycle-timing.jsonl` to record the full round time after saving.

C++ code adds runtime-selectable AVX/F16C float→half, AVX-512 FP16 double→half conversions, preserving original rounding; reuses board encoding and thread-private buffers, merges prediction decay turns, and caches daily unchanged planting returns. Fixed to single core, 60 real states, 3,840 encodings per contract: v4 0.670→0.321 seconds, v2 0.166→0.120 seconds. Full replay maintains consistent new and old features, actions, masks, and trajectory hashes. See [Encoding Timing](../outputs/analysis/agronomy-v4-throughput-20260917/encoding-isolated-after.json), [v4 Full Consistency](../outputs/analysis/agronomy-v4-throughput-20260917/encoder-compatibility.json).

The native script uses ahead-of-time C++, with no Python strategy callbacks during training; there are still overheads from generic dynamic values and call frames. Two independent MetaCounter runs total 1,438 decisions, with strategy CPU time of 6.615 seconds and observation construction time of 0.312 seconds, involving 4,008,384 dynamic calls. Precise AST matching with field/integer fast paths that check rebindings has been added, redundant dictionary calls have been eliminated, and the input beam search has been changed to a fixed-type C++. Search width of 8, depth of 8, stable sorting, and all final decision rules are preserved, with function AST identity binding; original generation code is executed when type or auxiliary function checks are not satisfied. MetaCounter strategy CPU time has dropped to 4.725 seconds (−28.6%), Ahmed's time reduced from 8.369 to 6.357 seconds (−24.0%), and Shop's time decreased from 0.0168 to 0.0150 seconds. The action and state hashes from full two-seat games for all three scripts are consistent. See [Script Staged Baseline](../outputs/analysis/agronomy-v4-throughput-20260917/native-policy-before.json), [Script Optimization Timing](../outputs/analysis/agronomy-v4-throughput-20260917/native-policy-inputs.json). Native script decisions overlap with encoding of immutable current state and GPU inference execution.

Batch per GPU optimized from 16 to 28, keeping 128 games per round and one full trajectory traversal per training pass;
Each GPU's 82/84 trajectory batch count reduced from 6 to 3 batches with decreased fill rate; fixed real sampling per GPU.
Preheat time reduced from 22.03 to 18.76 seconds, peak GPU memory at 107.2 GB; full six-round validation passed on dual-GPU setup.
Old binary and validation records retained; new binary must pass complete v4 replay verification to be integrated into BC.

## Acceptance and Operation Entry Point

Original handover source code and configuration submission `eb1ce3c`; `acd900b` will bind the handover proof to the actual script runtime identity.
Throughput optimization submission `19a1f80`, Ruff, full-scale mypy (829 files), and 30 related tests passed.
The new six-round dual-GPU acceptance directory is `outputs/learning/agronomy-v4-optimized-rl-qualification-20260917`,
including normal save, stop, and archive source code recovery, with the original four-round acceptance artifacts retained.

```bash
.venv/bin/python -m kagg_revue.learning.pretraining.handoff_qualification
.venv/bin/python -m kagg_revue.learning.pretraining.handoff
.venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001
```

The first two entry points are used for this one-time handover, to check the current stop status and acceptance binding, and cannot be reactivated.
Subsequent restarts will use only the archived recovery entry point. Configuration see
[learning_agronomy_rl_20260917.yaml](../configs/learning_agronomy_rl_20260917.yaml).


## GPU Real-world Testing and Sampling Pipeline (Subsequent Optimization)

`19a1f80` passed six-round dual-GPU acceptance, including normal save and stop, archiving and recovery, 137 external histories, PFSP exact replay, BC parent chain, and pure terminal WDL. Post-warm-up full updates (including save) for U5/U6 were respectively **52.362 / 47.712 seconds**; U6 sampling took 22.507 seconds, optimization took 18.950 seconds, and save took 5.700 seconds. See [Six-Round Acceptance](../outputs/analysis/agronomy-v4-throughput-20260917/qualification.json).

A 200-millisecond GPU sampling indicates that with fixed real-world 64-game single-GPU sampling, GPU utilization is approximately **42–43%**, and the optimizer reaches approximately **99–100% / 670–685 W**. Thus, further optimization of CPU/GPU handoff idle time is continued. Geometric feature precomputation using Manhattan distance, merging workers at the same location, and combining repeated shed distance loops; the v4 encoding on a single core is further reduced from 0.321 to 0.237 seconds per 3,840 iterations, i.e., approximately 61.7 microseconds per line. The v4 and historical v2 features, actions, masks, and engine hashes are completely identical across nine full replays. See [Geometric Optimization Full Consistency](../outputs/analysis/agronomy-v4-throughput-20260917/encoder-geometry-compatibility.json).

Modify the sampling implementation to use two independent native environments and causal memory, alternately launching GPU inference and CPU advancing the other group;
Each group's script continues with asynchronous pre-computation in C++. The original game rounds, seat pairing, PFSP sampling, and sample weights are preserved,
and the complete training tape is written back via explicit indexing. Independent entry points perform bitwise verification of overlaps in execution and serial execution under the same group or random order, checking features, actions, log probabilities, returns, weights, and terminal outcomes.
The initial version measured 14.844 seconds, but repeated measurements ranged from 22 to 24 seconds, making it unsuitable as a stable throughput conclusion.
Final adoption and training startup records will be determined based on subsequent full dual-GPU validation.


## Asynchronous Checkpoints and Page Cache Pressure

Pipeline six-round dual-GPU acceptance passed, including archival recovery and full BC/PFSP/WDL status checks.
U6 sampling and optimization and other front-end tasks took 38.425 seconds, with 4.878 seconds for saving, resulting in a complete round time of 43.305 seconds.
However, saving times for U1–U5 showed fluctuations between 22.8 and 72.5 seconds, preventing the claim that end-to-end stability has been achieved.
See [Pipeline Acceptance](../outputs/analysis/agronomy-v4-pipeline-20260917/qualification.json).

Diagnosis shows that local file writes consume a large amount of kernel CPU and are accompanied by container memory pressure. A standalone CPU checkpoint write takes 41.4 seconds, a 16 MB buffer write takes 36.5 seconds, and a full block ordinary write takes as long as 146.9 seconds.
Complete CRC32 serialization to memory takes only 0.53–0.57 seconds, ruling out CRC32 as the primary cause.
With the same serialization content preserved, a 4 MB-aligned direct I/O write of 399 MB takes just 0.180 seconds, and the full SHA256 before and after the write is consistent. Retaining CRC32, full file SHA256, and atomic temporary file replacement; when the filesystem does not support direct I/O, falling back to ordinary writes, actual I/O errors are propagated, and the old checkpoint is preserved.

The RL checkpoint further adopts a single background thread with at most one independent host snapshot.
On the training CUDA stream, each original storage is asynchronously copied while preserving aliases and views; the background thread waits for the copy event, then serializes, writes directly to disk, and computes SHA256; the next training round continues using the real-time model.
The main thread receives the save result before appending the next round of PFSP/metrics and publishes the corresponding ledger; the background thread never accesses real-time weights.
New historical pool snapshots, evaluations, normal shutdown, and all submissions prior to training termination are added; if a write fails, the recovery point is not advanced.
`cycle-timing.jsonl` records the full round including snapshots and backpressure from the foreground; `checkpoint-timing.jsonl`
Additionally, the background completion time and ledger publication time are logged to avoid equating asynchronous queuing with persistent storage.

True and complete RL checkpoint comparison conducted twice: initial fixed snapshot at 0.807 seconds, post-warmup at **0.055 seconds**; background serialization, disk writing, and hashing each take approximately **1.032 seconds**. After submission, the GPU model was immediately modified, and the saved model, Adam, RNG, PFSP, and all metadata were verified to be identical to the original content, with file SHA256 read back confirming consistency. See [Checkpoint Verification](../outputs/analysis/agronomy-v4-async-20260917/checkpoint-profile.json).
Ruff, full mypy (841 files), and 15 tests related to save/recovery/historical pool passed.
Six rounds of dual-GPU asynchronous save and archival recovery using the current source code still need to be verified before formal activation.


## User requirements for the initial formal state upon startup

The user subsequently explicitly requested, "That's enough, just start the formal training." The remaining verification has been canceled; round 3 completed during shutdown. Therefore, the actual verification scope is **U1–U3**, including U2's normal stop, archival recovery, and U3's continued updates. All saved weight hashes, finite tensors, dual-GPU RNG, Adam progress, PFSP sampling and statistics, BC parent chain, and pure WDL have been verified. The report clearly marks that the originally planned six rounds were not fully completed.

Steady-state U2 full front-end turn: **35.038 seconds**, dual-GPU sampling: **14.794 / 14.777 seconds**, optimized to **18.898 / 18.994 seconds**, each performing 3 actor and critic updates. The front-end checkpoint overhead for this turn is **0.071 seconds**, and the background save takes **0.825 seconds**, with normal shutdown waiting for completion. GPU utilization over a 200-millisecond sampling interval for the entire turn is **95.32% / 96.56%**, reaching approximately **100%** during the optimization phase.

Formal handover written into `bc-completion/0001`; original BC checkpoint and status preserved. Formal dual-GPU RL
Started at **2026-09-17 09:12 UTC**: restoring entry PID 1739471, training PID **1739565**.
Continuing with original runtime directory `agronomy-v4-m384-bc100-3d-20260917-s73001`; initial weights SHA256
are `d2d4948bec400fbfaeaa487dff0cff301564f3bde0aebbd5d64617a6e3f69da5`.
Checkpoint saved every 4 turns, 128 games per turn; asynchronous checkpointing and two pipeline groups have been activated; five scripts and 137 historical models have been registered. Formal training has started; the first formal optimizer checkpoint has not yet been individually confirmed.
Code commit `d31714d`; user's original `pyproject.toml` modifications were not committed or altered.
See [Startup Log](../outputs/analysis/agronomy-v4-async-20260917/formal-launch.json) and
[Startup Configuration Verification](../outputs/analysis/agronomy-v4-async-20260917/formal-launch-verification.json).
