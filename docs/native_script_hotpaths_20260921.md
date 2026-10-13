# 2026-09-21: Recompute Hotspot Handwritten C++ Script

The goal is to reduce the time during which the current compact289 training is blocked by script computations. During investigation, compilation, and offline verification, formal training continues to use the archived implementation. All strategy source assets remain unchanged in bytes, and the sampling and evidence procedures of PFSP are preserved unchanged.

## Bottlenecks and Parallel Scale

GPU0/GPU1 each have two sampling groups, with each group using 8 C++ OpenMP threads per script batch,
up to 32 script worker threads running simultaneously. Script execution overlaps with encoding/GPU inference, with native calls releasing the GIL.
Each round consists of 204 script matches, corresponding to 146,676 complete script decisions. Different games can be executed in parallel,
but the next turn of the same game still depends on the observations resulting from the current actions of both players.

Before optimization, the median update times in the official logs of U157–U172 for historical model opponents were 32.69 seconds, 47.43 seconds for V45, 45.83 seconds for Farming, and 63.81 seconds for V53; Shop Router took 32.12 seconds. Not all scripts slow down training, and the CPU computation of the heavier scripts is not covered by inference time. The sample sizes are not equal, and there is no consistent learner weight across samples, so these cannot be used alone as a basis for optimization acceleration ratio.

## Achieved Computation Trajectory

The compiler first changes the binding of local variables and ordinary positional parameters to static slots, preserving the semantics of dynamic globals, keyword parameters, closures, None/undefined distinction, and session cloning.

Then perform C++ function-level dissection and manually rewrite the following hotspot function:

- `_View.__init__`: Directly construct the observation view to reduce calls to generic functions and intermediate dictionaries.
- `_projected_shed`: Use fixed-length inventory array to compute PICKUP, DROP, and PLACE, maintaining capacity constraints and item order.
- `_clone_state`: Directly copy mutable containers required by the plan, preserving the original shallow copy boundary.
- `_r51_input_forecast`: Use 100-cell direct indexing, coordinate arrays, and daily bitsets to execute four-day route prediction, retaining watering deduplication, harvesting, worker birth positions, and end-of-day reset order.
- `_v92_p_forecast`: Reuse integer indices from frozen event streams to perform score computation via time-window scanning; support original episode odd-even filtering, maintaining stable sorting and tie order.

Each replacement binds the complete source code AST hash. Non-expected inputs and re-binding auxiliary functions use the preserved original generation path.
Cache only immutable source event streams; each game's observation, win/loss, and predicted scores are recomputed. Caching is verified with weak references and ownership identity, with capacity limits to prevent address reuse, data corruption, or infinite retention.

These are the specialized C++ implementations of hot functions; the surrounding strategy control flow is still generated from the frozen original source code.
Training continues to use `create_native_opponent_session`, `create_batch`, and
`ParallelBatch.advance_programs`, without introducing turn-by-turn Python opponent callbacks.

## Verifiable Evidence

All data is at
[`outputs/analysis/compact-script-throughput-round2-20260921/`](../outputs/analysis/compact-script-throughput-round2-20260921/).

Function profiling is enabled only when `KAGG_NATIVE_FUNCTION_PROFILE`'s independent process is explicitly set; throughput testing and formal training do not enable timing probes.
CPU benchmark uses 16 games, 4 threads, and 2 repetitions, saving the final results of each game.
GPU sampling benchmark uses a fixed configuration of U164 learner, world seed, sampling RNG, two groups, and a scale of 512 games per rank, with 102 games being scripted matches, recording the hash of complete observations, actions, rewards, weights, and cash.
Performance benchmark shares hardware with formal training and reports retained original timing values.

## Final Verification and CPU Throughput

Final binary script:
`c32aabb0169caed3d7996dd6aeae8c70b48864117a53b6c1a25cd0087b95cb6d`.
Original official binary is `9ef75eb57ef06ab6836ac4b74c6be7eea9b68e5d43f9315ebc359dfeb01a4312`;
Compare the process directly loading a standalone copy of this file to avoid pollution of identity records due to file replacement during build.

| Opponent | Original CPU seconds / 16 games | Hand-written optimization | CPU throughput multiplier |
| --- | ---: | ---: | ---: |
| Ahmed V45 | 36.01 | 23.37 | 1.54× |
| Farming V4 | 35.23 | 22.99 | 1.53× |
| Ahmed V53 | 63.82 | 38.57 | 1.65× |
| Thomas Metav4 | 61.26 | 39.97 | 1.53× |

Here, two repeated process CPU time averages are used, including native rule execution, not the full-round PPO acceleration multiplier.
The final cash values across all four panels are individually consistent. The official report only adopts
[`cpu-comparison-final.json`](../outputs/analysis/compact-script-throughput-round2-20260921/cpu-comparison-final.json)
and its original records of `throughput-baseline-final.json` / `throughput-final.json`;
the early `baseline.json` ended during the replacement build phase, and its trailing disk binary hash cannot represent the loaded image,
thus it is not used as a basis for the final acceleration ratio.

The 7×7 ordered pairings of seven strategies, totaling **49 games / 70,462 actions**, have been verified against the original source code, while simultaneously cross-checking controller diagnostics, full engine state, and session forks. All seven original strategy asset hashes remain unchanged.
This panel uses a fixed world and does not represent an exhaustive enumeration of all game states.
**21 test cases, Ruff, and 22 Python modules (mypy)** have all passed.
See [`validation-final.json`](../outputs/analysis/compact-script-throughput-round2-20260921/validation-final.json).

For the fixed U164 learner, the V45 / V53 two full sampling panels maintain identical observations, actions, log-probabilities of actions, WDL rewards, sample weights, and cash hashes compared to the original bit-by-bit. Additionally, log-probability tensors are saved, and it is confirmed that all tensors for each `662918×276` are finite with a maximum absolute error of **0**.
See [`pipeline-likelihood-verification.json`](../outputs/analysis/compact-script-throughput-round2-20260921/pipeline-likelihood-verification.json).

Complete GPU sampling original durations (seconds):

| Opponent | Original Implementation | Optimized |
| --- | --- | --- |
| Ahmed V45 | 39.25, 24.99 | 23.00, 22.29 |
| Ahmed V53 | 51.10, 40.18 | 28.53, 43.10 |

V45 shows a second reduction of approximately 10.8%; V53 exhibits significant volatility and cannot be claimed as stable based on two shared hardware samples for the full-round PPO acceleration multiplier. The first round includes the effect of cold start, and all original timing values are retained, not reporting only the fastest sample. See [`pipeline-comparison-final.json`](../outputs/analysis/compact-script-throughput-round2-20260921/pipeline-comparison-final.json).

## Formal Integration and Checkpoint Verification

Currently running compact289 on **U241 / 246,784 games** completed and terminated with exit code 0.
Registered `source-revisions/0002`, restarted GPU0+GPU1 at **07:31:58 UTC**;
source identity is `906b4a5ced48ef741e69480ddb9797b9483f377fd897ae8da331c348ed4dfd16`.
Boundary checkpoint SHA256 is
`dde481e464fe8e62d058c879425292c6d1a7c7f5b67ea24ac8c395269b5bd11a`.
The ledger only modifies source identity, source directory, repair history, and archive script runtime library; all checkpoint bytes, configuration, optimizer, dual rank RNG, PFSP evidence, historical model pool, and full records are preserved.

The binary of the aforementioned `c32aabb…` script has been loaded for both rank process mappings, with function timing probes disabled.
The native rule core remains `aebde8e8d84bddf732f3d4af1dcd48fb4897a7c4a1678f2fee34c5fbd4c6655f`.

**U244 / 249,856 games** checkpoint verified: PFSP sampling and statistical full replay consistency between U242–U244,
Actor/Critic Adam both advanced **9 steps**, with weights updated for both, all tensors finite, and both rank RNGs fully intact.
All formal rewards remain pure terminal WDL, γ=λ=1, cash reward weight is 0.

| Turn | Opponent | Sampling Seconds | Full Update Seconds | Notes |
| --- | --- | ---: | ---: | --- |
| U242 | V45 | 21.37 | 129.67 | Restore first turn, including runtime initialization |
| U243 | Historical Model | 12.21 | 55.14 | First load of this historical opponent, each rank takes about 22 seconds |
| U244 | V45 | 20.36 | 40.94 | Opponent loading takes about 0.05 seconds each, normal sampling |

U244 is below the median of 47.43 seconds of the optimized prior V45, but with variable world, learner, and concurrency loads.
Only observed results are listed here, not as a strictly controlled acceleration ratio. The new implementation still uses multiple OpenMP work threads;
future update times under different opponents and cold loads will still vary. Proceed with training after verification; subsequently, as requested by the user,
completely save and normally terminate at **07:49:05 UTC / U265**, exit code 0.
Final checkpoint, dual rank RNG, and PFSP integrity are available at
[Stop Verification](../outputs/analysis/compact-stop-commit-20260921/verification.json).

Evidence: [Binding eligibility](../outputs/analysis/compact-script-throughput-round2-20260921/repair-qualification.json),
[Status retention](../outputs/analysis/compact-script-throughput-round2-20260921/transition-verification.json),
[Initialization](../outputs/analysis/compact-script-throughput-round2-20260921/launch.json),
[Dual rank runtime library](../outputs/analysis/compact-script-throughput-round2-20260921/loaded-runtime-verification.json),
[Formal checkpoint verification](../outputs/analysis/compact-script-throughput-round2-20260921/formal-verification.json).
