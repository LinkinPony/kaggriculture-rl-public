# 2026-09-21 Public Notebook Update and Native Opponents

Formal training continues during investigation, compilation, and CPU verification.
Retrieve the current publicly available list from Kaggle `kaggriculture`, and separately extract the first 100 items for `dateRun` and `scoreDescending` from page one of the sorted list. This is not a complete exhaustive survey of all publicly available notebooks. Sorting and titles are not official proof of score or strength.

Download 12 notebooks, statically unpack, and deduplicate the submitted source code by SHA-256 to obtain 9 candidate entries.
Retain the original notebooks, metadata, compressed submission package, source code, and extraction records; do not execute notebook cells.
Recursively inspect the literal strategy source code in `exec`. Do not set optional research variables `V92_SELL_LIB` in the test environment.

Source and complete download records see
[`data/external/kaggriculture-notebook-survey-20260921/`](../data/external/kaggriculture-notebook-survey-20260921/).
The version source code published by Nathan Pipe16 and three other authors is identical, with no redundant addition to the training pool.

## Independent Dual-Seat Screening

In each random world, both parties swap seats, fully executing 719 actions. The entry rules are adopted from the last callable on Kaggle. Ahmed V53's official entry is `_e363_agent`, not the old `agent` within its module.

| Candidate | Initial Screening: 4 worlds / 8 games, vs. V45 | Confirmation: Another 16 worlds / 32 games, vs. V45 |
| --- | --- | --- |
| Ahmed V51 | 8 wins, 0 losses | — |
| Ahmed V52 | 8 wins, 0 losses | — |
| Ahmed V53 | 8 wins, 0 losses | 32 wins, 0 losses |
| Thomas Metav4 | 7 wins, 1 loss | 32 wins, 0 losses |
| Nathan Pipe16 | 7 wins, 1 loss | 32 wins, 0 losses |
| One More Wheat | 7 wins, 1 loss | — |
| Guru Master V4 | 7 wins, 1 loss | — |
| Hybrid 2965 | 7 wins, 1 loss | — |
| Idle Seller | 7 wins, 1 loss | — |

Added native selection of two distinct strategy branches:
[Ahmed V53](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v53-opening-signature)
and [Thomas Metav4](https://www.kaggle.com/code/thomastschinkel/the-metav4-farm-submission-v13).
This result indicates their superiority over the existing V45 on this panel, but does not reflect official rankings nor the win rate against current neural strategies.
Pipe16 remains as a filtered candidate and was not compiled or added to the training pool this time.

Results see [Initial Screening](../outputs/analysis/notebook-survey-20260921/screen-v45/summary.json),
[Confirmation](../outputs/analysis/notebook-survey-20260921/confirm-v45/summary.json).

## Native Implementation and Performance

Reuse the frozen source code to C++ compiler, `create_native_opponent_session`,
`create_batch` and the GIL release `ParallelBatch.advance_programs`.
There are no turn-by-turn Python script callbacks during training.

Complete the loop for `else`, static data compression and alias import, binary byte indexing, offset, diagnostic mapping, string operations, list deletion, and decimal rounding. The deduplication function's asset package now includes its actual dependency constants, preventing loss of data when functions are shared across different scripts. V53 uses a separate official entry binding, retaining the old `agent` for internal strategy chain calls. Read-only prediction data is shared across games, while cached dictionaries and controller states remain independent.

The original five compressed strategy assets maintain byte consistency. Existing running source code, binary, checkpoints, and logs are preserved.
The current script optimizes local variable overwriting, built-in function caching, and temporary allocations during dictionary lookups.
For 16 games, 4 work threads, and 2 repetitions, the CPU time ratios are:
Ahmed V45 **1.053×**, Metacounter **1.054×**, Shop Router **1.008×**,
Rayk **1.061×**, Farming **1.042×**. All terminal cash values are identical; the single-core complete trajectory actions and state hashes are identical.
This is the script's computed baseline, not the full-round PPO acceleration factor.

The sales forecasting function of the new script has a dedicated C++ implementation bound to the complete AST hash; it maintains the original scoring, stable sorting, and tie-breaking priority, without caching game-dependent win/loss information.

Performance original records see
[`compact-script-throughput-20260921`](../outputs/analysis/compact-script-throughput-20260921/)
and [`notebook-survey-20260921`](../outputs/analysis/notebook-survey-20260921/).

## Training Access Constraints

Target runtime remains `compact289-v4-selected8-ppo-restart-20260921-s74001`:
1024 games = 820 self-play games + 204 unified PFSP pool matchups, script has no independent quota.
Retain the original five scripts, add two native opponents; do not modify pure terminal WDL, γ=λ=1, model,
three Actor/Critic updates, and learning rate warmup.

Manifest update verifies source code hash, dependency files, and entry point, and migrates existing PFSP statistics for the same script. Historical strategy statistics, previous script win/loss counts, valid samples, and decay time are preserved unchanged; new strategies start from prior knowledge. The complete pre-change state and migration mapping are archived, and the model, optimizer, and dual-card RNG in the original checkpoint remain unmodified.

## Actual Integration and Verification

U155 / 158,720 games saved, registered `population-revisions/0002`, effective from U156 onward.
06:23 UTC, initial recovery failed due to mismatch between old checkpoint PFSP key name and new ledger; no new update was executed.
Subsequently, recovery process was fixed: only replay registered identity migrations at identical save boundaries, field-by-field verification of statistical values, without rewriting original checkpoints. Added recovery regression tests and real U155 checkpoint replay verification passed.
Registered `source-revisions/0001`; at 06:27 UTC, initiated dual-GPU recovery again, current source code identity `19ccd51b8ae704d71bb397ce154843f2d4d808a377379ab88b70ab28dcf1f173`, native script binary `9ef75eb57ef06ab6836ac4b74c6be7eea9b68e5d43f9315ebc359dfeb01a4312`.
Script manifest is `data/external/kaggriculture-public-native-20260921/manifest.json`.

The new prediction, before and after optimization, shows consistency across **18 games / 25,884 actions**, complete states, cloned controller behaviors, and diagnostics;
Final version passes round-by-round verification against the original script. The current branch fixes the U128 strategy and passes **4 games** with both sides' seats through official runner validation, showing consistency in **5,760 observations, 2,876 script actions, and learner feature lines**, asynchronous native script prefetch path execution is realized. The complete action trajectory hash of this neural panel is also consistent before and after optimization.

The new script achieves CPU throughput of **1.396×** for V53 and **1.268×** for Thomas within the same 16-game / 4-thread / 2-repetition benchmark. The wall-clock ratios are **1.283×** and **1.182×**, respectively. Final cash remains unchanged. RSS stays stable after repeated session creation, cloning, and destruction. Passed **25 items** of compiler, session, recovery, unified PFSP, and evidence migration tests; Ruff and mypy pass.

This does not include duplicate standalone GPU qualification branches. The binding report explicitly records `separate_gpu_qualification_updates=0`.
Based on completed CPU full-game matches, real checkpoint neural interfaces, checkpoint finite bounds, and per-rank RNG verification,
the formal training updates are subsequently checked. Offline qualification is not described as an unexecuted GPU training experiment.

Formal **U164 / 167,936 games** checkpoint has been copied, archived, and SHA-256 verified. U156–U164, nine rounds
Replaying from the migrated U155 state, sampling probability, opponent selection, final PFSP statistics, and historical pool are fully consistent.
Actor/Critic weights have both been updated; all parameters of the two Adam optimizers have advanced **27 steps**;
All checkpoint tensors are bounded, double rank RNG is complete, and the original U155 checkpoint bytes remain unaltered.
Each round completes three optimization steps on two GPUs, still operating under pure WDL, γ=λ=1, and 820/204 game allocation.
U157's V53 group actually completed 204 games, with the learning side achieving **102 wins, 0 draws, 102 losses**.
As of the saved U164 checkpoint, Thomas has not been randomly selected; both new opponents are drawn from the same PFSP distribution,
with no additional guaranteed quotas. Logs have been verified up to U166, and the recovery process is still running.

Evidence: [Final Source Code Comparison](../outputs/analysis/notebook-survey-20260921/conformance-forecast/report.json),
[Official Neural Game](../outputs/analysis/notebook-survey-20260921/official-forecast.json),
[Throughput Comparison](../outputs/analysis/notebook-survey-20260921/performance-summary.json),
[Binding Eligibility](../outputs/analysis/notebook-survey-20260921/population-qualification.json),
[Migration Verification](../outputs/analysis/notebook-survey-20260921/transition-verification.json).
Recovery and Repair Evidence: [Actual Checkpoint Validation](../outputs/analysis/notebook-survey-20260921/restore-qualification.json),
[Lossless Source Code Revision](../outputs/analysis/notebook-survey-20260921/restore-verification.json).
Formal Continuation Training Evidence: [U164 Checkpoint and Nine-Round Replay](../outputs/analysis/notebook-survey-20260921/formal-verification.json).
