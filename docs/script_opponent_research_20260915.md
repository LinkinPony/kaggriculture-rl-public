# Self-developed Script: Revue Revenue Lead R1

## Conclusion and Scope

Developed a candidate **`revenue_lead_r1`** that is clearly stronger than the currently available public script pool.
It adds our own sell timing and sell order control mechanism on top of Ahmed V43's frozen source code.
The inherited route selection, unit control, and public strategy retain the original author's ownership; it is not a completely rewritten strategy from scratch.

Frozen independent confirmations using **64 uninvolved world seeds, and both sides' seats**:
vs. V43: **125 wins, 3 losses**;
vs. six public scripts collectively: **749 wins, 19 losses**.
Under identical seeds and opponents, the comparison against V43 yields **543 wins, 188 draws, 37 losses**.
The six opponents include strategies from closely related families, and thus do not represent six completely independent opponent distributions.

**Does not support upgrading the training pool for neural model results**: For the currently frozen U5312, R1, and V43, all have 0 wins and 32 losses, with R1 showing a worse average return difference. The current conclusion is a targeted enhancement for public scripts, not a proven general upgrade that increases neural training pressure.

Deliverables include a standalone Python `agent`, native C++ build artifacts and isolated compiled libraries, research tools, frozen recipes, and per-game evidence. The official training pool has not yet adopted R1. The native batch interface has been validated; population registration, archival recovery, and continuation migration for formal training are not within the scope of this delivery acceptance.

## Freeze Identity

- [Independent Script](../outputs/opponents/research-20260915/revenue-lead-r1/main.py)
  SHA-256: `385024f8fa6419b237a49f47f161937362e71776ea99b824e911b3d89ff72505`.
- [Origin and Recipe](../outputs/opponents/research-20260915/revenue-lead-r1/provenance.json),
  [Selection Freeze Record](../outputs/opponents/research-20260915/revenue-lead-r1/selection.json),
  [License](../outputs/opponents/research-20260915/revenue-lead-r1/LICENSE).
- Parent Strategy: [Ahmed V43](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v43-recovering-lost-harvests),
  Frozen Source Code SHA-256: `919fc1d61050cd96f799979e49177ae3ac7bce98ec9835724238bea73f4a08ed`.
- [Native Asset](../outputs/opponents/research-20260915/revenue-lead-r1/native/revenue_lead_r1.json.zlib)
  SHA-256: `605ec5cd6f0007196e7fa1e0553928fb20e2f901b42fe60b167a014a676c9cec`.
- [Native Build Record](../outputs/opponents/research-20260915/revenue-lead-r1/native/build.json),
  Compilation Library SHA-256: `f9edfab5b7265aa8bf721bea9e4a8356962161179400ca59acd8f52ec23c7ac3`.
  This library is stored in the candidate directory `native/`, targeting a native Linux / CPython 3.11 environment.

`selection.json`'s `not_yet_confirmed` describes the frozen state at that time and is retained.
Final confirmation is based on this document and the complete game record linked herein.

## Algorithm

The controller only reads official observations, its own inventory, and its selected trajectory, not the engine's hidden state.
In step **216–695**, when the current product price is at least **2**:

1. Calculate the expected warehouse inventory after the current farmer and worker actions.
2. For up to **6 steps** ahead in its own trajectory that are already scheduled for sales, attempt early sales of existing inventory.
   Do not cross the next 72-step route switch boundary; avoid selling wheat, fertilizer, goods involved in current sell orders, and goods required by current or pending PICKUP actions.
3. Record the early sale quantities in the parent strategy's existing sale reservation ledger to prevent reprocessing the same inventory batch when the plan expires.
4. Remove empty sell orders and sell orders that cannot execute based on expected inventory; within consecutive sell order segments, sort them according to the parent strategy's price exposure function.
   Buy operations remain in their original relative positions and are not repositioned across buy order reordering.

Implemented see [market.py](../src/kagg_revue/opponents/research/market.py).
Reserved and anticipated inventory belong to strategy judgment and cannot guarantee that each advance order will execute under the expected conditions.
Advantage is measured based on complete game results.

### Revenue Mechanism

Under the same world, seat, and opponent, replacing V43 with R1 improves the cash margin relative to V43 by an average of **2,199.3**.
R1 earns **697.5** more, while the opponent earns **1,501.9** less.
The main advantage therefore comes from competitive timing in the shared market; the full 2,199 cannot be attributed to increased production or higher own earnings.

## Research Design and Exploration

[Pre-defined phase division](../outputs/analysis/script-research-20260915/research-protocol.json):

| Stage | Seed | Purpose |
|---|---|---|
| Development | 1860916001–1860916004 | Diagnostics, early sale attempts, sorting, opening moves, and internal switches |
| Selection | 1860916101–1860916132 | 5 candidates × 6 opponents × 32 seeds × 2 seats, totaling 1,920 games |
| Independent Confirmation | 1860916201–1860916264 | Freeze R1 versus V43 comparison, 768 games each, totaling 1,536 games |
| Final Neural Comparison | 1860916501–1860916516 | Freeze U5312; V43 versus R1, 32 games each |

All complete games are 719-move games where both sides react based on actual observations.
Seeds are statistical resampling units; the two player seats are combined, using a fixed random number for 10,000 bootstrap samples.
Intervals describe variation in sampling from this distribution, not guarantees of rankings on the game leaderboard or generalization across opponents.

Main exploration results:

- In 32 terminal diagnosis cases, no warehouses, carried items, or unharvested value were found remaining in the test worlds, prompting a shift to market timing; this is not a conclusion for all worlds.
- Broad liquidation, longer advance windows, or disabling feed/fertilizer workers are less effective than maintaining the original route with short-window adjustments.
- On 32 selection seed variants, a standalone advance of 6 steps yielded 62 wins and 2 losses for V43, with an average lead of 1,491.8; after sorting, it improved to 63 wins and 1 loss, with an average lead of 2,133.1.
- An advance of 8 steps with sorting yielded comparable gains for V43, but lost two more games on Shop Router; ultimately, the strategy of advancing 6 steps with sorting was selected across the entire panel. R1 achieved a total of 380 wins and 4 losses across the selection panel.
- The seed repair toggle showed no observable benefits in a small number of development worlds and was not adopted.

[Development Follow-up Results](../outputs/analysis/script-research-20260915/market-followup/summary.json)、
[Selection Results](../outputs/analysis/script-research-20260915/market-selection/summary.json).

### Failure Records and Invalid Interventions

- The initial `market-screen` stalled after 128 games due to an issue with creating worker processes in the process pool during Python 3.11's loop; an interruption has been recorded, and it is now modified so that each process handles only one game. Duplicate games cannot be counted as independent new samples.
- The name `market-screen-complete` containing "complete" does not imply successful completion: in reality, 212 games were retained before an exception occurred when processing sell orders due to empty orders. The empty order handling has been fixed and regression tests have been conducted; this directory is not considered a complete selection panel.
- Early opening experiments only modified constants that had already been consumed at import time, thus no changes to actions were made. These draws cannot serve as evidence for the claim that "opening variations are ineffective." The research runner has now been modified to simultaneously update the current game's trajectory.
- The initial C++ candidate encountered a `bytes` unsupported issue during initialization in the V43 Python copy optimization. After adopting the following exact source code binding with copy adaptation normalization, it was recompiled and fully validated.
- The batch acceptance initially misinterpreted the "learner / opponent" column of `cash()` as fixed player 0 / 1; the acceptance script has been corrected and passed. Failure logs are retained, and no changes to the game or strategy have been made to eliminate discrepancies.

## Independent Confirmation Result

Each row contains **64 new seeds × 2 seats = 128 matches**; a draw counts as half a point.

| Opponent | V43 Benchmark: Win / Draw / Loss | R1: Win / Draw / Loss | R1 Average Revenue Difference | Improvement in Revenue vs. V43 Benchmark |
|---------|-------------------------------|------------------------|----------------------------|------------------------------------------|
| Ahmed V43 | 8 / 112 / 8 | **125 / 0 / 3** | +2,199.3 | +2,199.3 |
| Current Ahmed V42 | 69 / 54 / 5 | **125 / 0 / 3** | +2,305.0 | +2,202.8 |
| Farming 0914 | 93 / 22 / 13 | **122 / 0 / 6** | +3,141.4 | +1,436.6 |
| MetaCounter R1 | 128 / 0 / 0 | **128 / 0 / 0** | +28,735.6 | +1,429.3 |
| Rayk V38 | 120 / 0 / 8 | **124 / 0 / 4** | +3,831.7 | +1,257.1 |
| Shop Router 0913 | 125 / 0 / 3 | **125 / 0 / 3** | +10,545.4 | −63.4 |
| Total | 543 / 188 / 37 | **749 / 0 / 19** | +8,459.7 | +1,410.3 |

- The average revenue difference against V43 for 95% seed bootstrap interval is **[+1,871.6, +2,548.4]**;
  After averaging across both sides of 64 worlds, all results are positive.
- The total scoring rate increased from **82.94%** to **97.53%**, an improvement of **14.58 percentage points**.
- The overall panel's pairing revenue difference improvement interval is **[+1,172.8, +1,662.2]**.
- On Shop Router, the average self-revenue decreased by **254.2**, with a revenue difference improvement interval of **[−149.1, +21.7]**.
  The original script should be retained as a complementary baseline, and it cannot be claimed that R1 improves revenue against all opponents.

[Full confirmation](../outputs/analysis/script-research-20260915/revenue-lead-r1-confirmation/summary.json),
[Pairing changes](../outputs/analysis/script-research-20260915/revenue-lead-r1-confirmation/paired-improvement.json).

## Neural Opponent: No Improvement

Using the frozen **U5312** from this training checkpoint, both the model weights and the exported TorchScript actor retain identity records.
Inference is performed on CPU with FP32 precision, temperature set to 1, and a fixed random seed of `2 * world seed + neural-policy seat` per game.
Each script engages in 32 games (16 new worlds × 2 seats) against the same reference model.

| Script | Win / Draw / Loss | Average Revenue Difference |
|---|---:|---:|
| Original V43 | 0 / 0 / 32 | -9,006.4 |
| Revenue Lead R1 | 0 / 0 / 32 | -9,455.0 |

R1's relative pairing return difference compared to V43 is **−448.6**, with a 95% seed bootstrap interval of **[−735.3, −128.8]**; in 16 worlds, 13 show worse performance and 3 show better performance.
These results do not support the claim that it is more suitable as a training opponent for the current neural model.
Simply adjusting the timing of selling public routes is insufficient to compensate for the return gap of approximately nine thousand in neural strategy.

Previously, there were only early sales without sorting, and `lead_6` achieved 0 wins and 8 losses across 4 development worlds;
This small sample was neither the final R1 nor used in the above final comparison selection.
Saved neural actions and observations can be utilized for subsequent analysis of production pathways, resource utilization, and strategy adaptation.

Evaluation increases CPU worker processes from 4 to 16 after completing 24 games; full records are preserved, with only missing tasks replayed. Original declarations, execution changes, per-game random seeds, and AST consistency checks for individual game inference functions are archived. An additional replay of an old task is performed for validation of parallel setup changes, and this does not count toward the 64 independent comparisons.

[Model Source](../outputs/opponents/research-20260915/neural-reference/manifest.json)、
[Final Result](../outputs/analysis/script-research-20260915/neural-r1-confirmation/summary.json)、
[Pairing Changes](../outputs/analysis/script-research-20260915/neural-r1-confirmation/paired-improvement.json)。

## Official Environment and Native Acceptance

- Official `kaggle-environments==1.32.7` confirmation for 48 games: full action sequences (SHA-256 hashed), final rewards, outcomes, and move counts match exactly with the local game execution.
- Original standalone Python, normalized Python for C++, and native C++ implementations completed 96 game-by-action comparisons, including 48 perturbed games with intentionally skipped actions. **All 69,024 candidate actions are identical**.
- **480 session replicates, 96 cross-game resets** show perfect consistency; the 48 unperturbed games also fully match independent verification records.
- A new script and the original 5 native scripts executed 12 games via the same `ParallelBatch.advance_programs`, with both sides' rewards at each step matching the original Python; additionally, five replicated branches remain consistent for 503 consecutive steps.
- The original five compressed native assets remain byte-for-byte identical; the training library installed in the root directory was not replaced by this isolated library.
- 3 new regression checks added for empty sell orders, reservations, trajectory boundaries, and replication identity adaptation; combined with existing checks, a total of 22 checks pass. Full Ruff and mypy (758 source files) passes.

The container replication optimization for V43 is Python performance tuning, including Python introspection not supported by the native runtime.
[normalization.py](../src/kagg_revue/opponents/compilation/normalization.py)
Only accepts the exact hash of 7 reviewed AST nodes, replacing them with existing native graph replication behavior;
overflow handling from the parent strategy and the optimized route planning are preserved.
The semantic equivalence of this step is verified by the above complete action comparison and cannot be inferred solely from "compilation success."

Cumulative call duration per game: Python candidate 38.6 seconds, native step-by-step invocation 288.9 seconds, the latter including overhead from copying specified steps; this dynamic C++ runtime is not optimized for Python's single-game speed.
A hybrid native batching and branch advancement approach takes approximately 9.4 seconds, offering an execution path without requiring Python callbacks per turn.
These are native, panel-specific measurements, not the full neural training throughput.
Official and native duplicate checks do not include the count of independently confirmed samples.

Evidence: [Official Comparison](../outputs/analysis/script-research-20260915/revenue-lead-r1-official/native-comparison.json),
[Per-action Native Verification](../outputs/analysis/script-research-20260915/revenue-lead-r1-native/summary.json),
[Batch Verification](../outputs/analysis/script-research-20260915/revenue-lead-r1-native/batch-verification.json).

## Reproduction Entry Point

All research implementations are located at `src/kagg_revue/opponents/research/`.
The original public source is located at gitignored `data/external/`, and the results are located at gitignored `outputs/`.
Ensure that the provenance list and frozen source code exist before running the commands.

```bash
# Export a standalone script; the destination directory must not exist.
.venv/bin/python -m kagg_revue.opponents.research.export

# Rerun independent confirmation in a new directory using the frozen recipe.
.venv/bin/python -m kagg_revue.opponents.research.cli --config-name script_research_confirmation research.output=outputs/analysis/revenue-lead-r1-confirmation-repeat

# Check each action using the distributed isolated C++ library.
.venv/bin/python -m kagg_revue.opponents.research.qualification panel.output=outputs/analysis/revenue-lead-r1-native-repeat

# Execute the same library at the native batch boundary used in training.
.venv/bin/python -m kagg_revue.opponents.research.batching panel.output=outputs/analysis/revenue-lead-r1-native-repeat

# Compare the final candidate with the fixed neural reference; the protocol verifies the reference directory and actor hash.
.venv/bin/python -m kagg_revue.opponents.research.neural --config-name script_neural_confirmation panel.output=outputs/analysis/revenue-lead-r1-neural-repeat panel.workers=16
```

[Independent Script Re-export](../outputs/opponents/research-20260915/revenue-lead-r1-reproduced/reproduction.json)
Byte-by-byte consistency verified. Native re-generation entry point is
`python -m kagg_revue.opponents.compilation.cli --config-name native_revenue_lead_r1`;
This configuration is output to `tmp/revenue-lead-r1-build/` and should be compiled within a fully isolated source code copy,
then used with `kagg_revue.native.build build.target=legacy`, and the native assets must be verified against the generation record.
The generated source code and build parameters are stored in the candidate `native/` directory.
