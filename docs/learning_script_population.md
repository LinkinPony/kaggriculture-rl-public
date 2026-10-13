# 100k turns of native script opponent integration

2026-09-08 User requests to directly halt the current training, add script opponent, and resume afterwards, without performing algorithm ablation;
subsequently explicitly requires reusing the existing C++ opponent implementation. This change only modifies the opponent composition, without reinitializing the network or optimizer.

Each update still consists of 128 complete initial-state games, with two H200s synchronously training a strategy:

| Opponent | Total Games | Games per GPU | Trainable Trajectory |
| --- | ---: | ---: | ---: |
| Current Strategy Self-Play | 64 | 32 | 128 |
| Historical Model of This Run | 32 | 16 | 32 |
| Kaito v39 | 8 | 4 | 8 |
| Kaito v48 | 8 | 4 | 8 |
| Mugundh v21 | 8 | 4 | 8 |
| Boatlee v21 | 8 | 4 | 8 |

Each card and each frozen opponent balances the positions of both sides, with seeds not repeated. Each side's trajectory accounts for half the weight in the game;
In frozen opponent games, only the learner's trajectory enters PPO, and the total weight per game remains one.
Script actions are not used as demonstration or supervision labels; the four-round demonstration initialization has already ended and is not rerun.

Integrate and continue using `opponents/batches.py::create_batch` and `opponents/native_batch.py::create_native_opponent_session`.
`_revue_native.ParallelBatch.advance_programs` directly calls a C++ session after releasing the GIL, shares the existing route assets, and maintains an independent state per game. No new script strategy porting is added, and there is no per-turn Python opponent or observation dictionary conversion. Self-play and historical neural opponents continue to use `_revue_core`.

Script source uses the existing public notebook list (../data/external/kaggriculture-public-notebooks-2026-08-28/manifest.json),
with list SHA256 of `a1500b7318a3437c452dde547d449ce5f9086f97a29244b31be645a3f96c3811`.
Pre-training verification includes original script identity, registration of existing native implementations, and compression trajectory assets; archival runs additionally save the script's extended binary and four trajectory assets, and subsequent recovery also checks these files.

Training originally stopped after round 318 without continuing; stop requests failed to complete. The process ultimately terminated unresponsive workers.
The latest verifiable recovery point is round 316, SHA256 `b15bc3c055e815ba575c2e93ca1142c589d8a968461dce8c602311e0edc29dbc`.
Unsaved updates from rounds 317–318 are recomputed from this point. Diagnostics are available in [stop.json](../outputs/analysis/script-population-20260908/stop.json).
Added abnormal log entries for new workers and an immediate exit path to prevent a single rank from getting stuck during NCCL cleanup, which would otherwise cause other ranks to wait excessively for collective operations.

The entry point is `learning.recovery.population`, configured as
[learning_population_change.yaml](../configs/learning_population_change.yaml).
A separate instance is used for full game correspondence and checks for stopping/resuming with two GPUs of the same size, without performing algorithmic performance comparisons.
`population-revisions/0001` is registered only after successful verification, retaining the original source code, all checkpoints, optimizers,
dual-GPU RNG, and the original historical pool, continuing under the same UUID with a 100,000-update budget.

These scripts, after the switch, have become observed training opponents, and their win rate only reflects performance against training opponents.
Shop/Pasture and EcoBot still do not enter training; route strategies may share design, and thus cannot be claimed to be completely independent in family.
The previous conclusions and deployment choices from the two random roots over 512 rounds remain valid; this engineering review does not constitute a new proof of model capability.

Reproducibility further localizes to Turn 213 of Round 319: non-local work instruction `[0, 1, 0, 0]`
Contains masked movements. CPU and GPU actions are consistent, with limited input features.
The compiled exponential sampling uses `-log(uniform)`; zero endpoints result in positive infinity; if the only valid option draws infinite noise, the Gumbel score becomes negative infinity, thereby losing to invalid options within finite masks.
Now, before taking the logarithm, we simultaneously impose a positive lower bound and a finite upper bound on the exponential noise, without consuming additional random numbers.
Regression testing enforces both zero and infinity endpoints and covers both fixed and dynamic temperatures; detailed diagnosis is available in [sampling-failure.json](../outputs/analysis/script-population-20260908/sampling-failure.json).

Full verification passed, see [qualification.json](../outputs/analysis/script-population-20260908/qualification.json).
Copy completed 316→320 normally stopped → 328 resumed, totaling 12 updates of the same size; except for two startup warm-up instances,
the median update duration was 4.165 seconds. Each update was a 64/32/8/8/8/8 game session, with no missing or duplicated logical updates,
complete optimizer, dual-GPU RNG, and parent checkpoint hash chain. 32 related tests, Ruff and mypy passed.

The original run has been restored from turn 316 via `learning.recovery.cli`, and the current source code identity is `dd2ff85f28ae192eb40c0c3ac19ea2454513a0a81aff1f3e779e4347a8356374`.
[Startup log](../outputs/learning/long-100k-20260908-s61001/population-launch.json) saves exact parameters;
[recovery-status.json](../outputs/learning/long-100k-20260908-s61001/recovery-status.json)
records the isolated source code process and real-time log paths.
