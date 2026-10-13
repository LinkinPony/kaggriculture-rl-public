# Experimental Boundaries of the Single-Turn Action Interface

`policy/grounded` is a new experimental interface starting from random parameters, configured as Hydra `configs/learning_grounded.yaml`. It still reuses the entity encoder, PPO, and the native transmission format of work, and the migration of shared modules from `production/` is not yet complete.

## Diagnostic Rationale

`outputs/analysis/scratch-work-behavior/behavior.json` conducted 8 sampled mirror matches with the same seed for the initial and update 32 of two work-v1 random root experiments. Approximately 96.9% of the credited job fields belong to absent units; none of the four models executed WATER or HARVEST.
These fields still influence market latent states in the older models and cannot be simply regarded as mathematically inactive variables.
Sales revenue remained nearly unchanged; cash improvement primarily stemmed from purchasing less. The results do not support expanding the original configuration.
The audit used old native binaries, which are retained alongside the report with their SHA256 values recorded, and contain no weights.

## Expression and Credit

Each official turn is decided independently; each existing unit chooses PASS, move to an adjacent cell, or perform an action in the current cell.
All original unit actions remain expressible. Movement is represented by an adjacent target cell; on-site actions have their own distinct categories and quantities.
Units not hired, the second queued task, and release time set to zero are no longer sampled.
The market hidden state aggregates only the choices of existing units, and PPO credit is also based on current observations, excluding absent units.

Native observation extension adds `[units, 44]` table, version `grounded-unit-support-v1`.
The support table uses official unit rules and the observable state of this entity to indicate whether a single-operation execution quantity of 1 is valid.
Larger quantities and multi-unit shared inventory conflicts are still handled by official rules. The market retains full order sequence and quantity.
There is currently no market-wide joint legal support table. This interface cannot be described as guaranteeing the legality of the entire joint action.

The old field name `harvestable_tile_turns` in this turn's behavior report actually only counts positive yield and does not represent harvest operations.
It is now legally valid; subsequent audit code has renamed this field to `positive_yield_tile_turns`. Harvest count comes directly from actual HARVEST operations and is separate from this coverage statistics.

Initialize using a learnable low-frequency market STOP bias, diminishing quantity bias, and stochastic output layer; no teacher parameters, fixed time-action tables, or specific crop trajectories. The model and all random evaluation anchors are generated from a newly created random root following this instruction. Training utilizes only the current self-play and in-run historical pool.

## Completed Verification

- `tests/test_grounded_policy.py` checks sampling and conditional re-computation probabilities, effective gradients, and isolation of missing fields, and performs step-by-step comparisons across official execution support for empty land, weeds, plants, animals, and empty buildings.
- Under the same random strategy, observations and terminal states are consistent between native batch execution and per-turn `ContractSession`.
- After recompilation, 64 official replays and 92,160 observations were rechecked for consistency, as shown in `outputs/analysis/daily-20260906-grounded-native-audit/report.json`.
  These tests do not replace final model export, official end-to-end closure, or time budget eligibility.
- `scratch-grounded-qualification-v1` completes 2 × 8 full-season training runs from a random root, without compilation, width 64, actor learning rate 1e-5. All 24 runs confirm identical results to the initial model.
  In 4 behavioral audits, the initial and final states each seed 41/42 once, with 4 waterings each and no harvests; absence of work credits is 0; the average final cash balance is 510.375. This only verifies interface functionality; operational issues remain unresolved.

## Subsequent State Course Constraints

The daily state index only saves the original replay member, seed, turn of entry, and the corresponding state statistics at that time, without generating imitation labels.
Replays involving both sides and identical environment seeds are grouped into the same stable 80/10/10 partition. Display names do not equate to independent strategy versions; positive yield in the index does not equate to the legal harvest available at that moment.

The future loader must exactly replay the action prefix from the original seed, restore the complete engine and public history, and verify the entry state;
Reconstructing training snapshots solely from recorded observations is insufficient. Only actions sampled by the new policy after entry can be incorporated into PPO.
A complete initial state evaluation must be maintained to avoid treating intermediate state returns as zero-start operational capability; additional handling of the constant win/loss signals caused by initial wealth disparities between the two players is also required. Currently, the index is used only for coverage analysis and is not employed in any model training.

`datasets.states` has established 19,198 daily boundary candidate states for the 662 complete games on September 6.
Training/selection/confirmation each have 521/69/72 games, checked for no cross-region overlaps by environment seed, and content hash has been verified.
Among the 15,109 states in the training region, 11,345 satisfy the condition that the cash difference between both sides does not exceed `0.2 * max(3000, cash0, cash1)`, and both sides already have plants; this coverage statistics has not applied future revenue filtering.
The training region covers 36 display names, which is still not considered as the number of independent strategy versions.
It provides a research starting point for subsequent courses, without proving the effectiveness of course training.
The persistent source index is located at `data/external/kaggriculture-restart-candidates-2026-09-06-v1/`,
and the coverage and verification report is located at `outputs/analysis/daily-20260906-state-coverage/`.
