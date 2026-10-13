# BC with Normalization of Five Types of Actions

The new `learning_grouped_bc` pipeline uses `domain_mean` to supervise loss: calculate the average NLL separately for unit target, unit operation, unit quantity, market operation, and market quantity, then combine them explicitly by weight.
This makes the direct loss coefficient of market decisions no longer determined by the number of worker fields in the same turn.

Let the global effective batch of one Adam update be B, and the effective field set of category d be F_d:

```text
L_d = sum(-log p(teacher_field | observation, teacher_prefix), F_d) / |F_d|
L   = sum(weight_d * L_d) / sum(weight_d)
```

Default weights for all five categories are 1. Weights are relative values, allowing a single category to have a weight of 0, with the total sum being finite and greater than 0.
If a category does not exist in a complete batch, it contributes 0; its weight is not reallocated to other categories.
This is neither a turn-by-turn averaging nor an averaging per sequence block.

`normalization: field_mean` Interpret the same set of weights as multipliers for each field, sharing a single denominator across the entire batch:

```text
L = sum(weight_d * sum(NLL, F_d), d) / sum(weight_d * |F_d|, d)
```

The proportion of each domain changes with field frequency; sparse domains are not amplified; validation and early stopping use the same formula.
The initial usage and multiplier derivation are seen in [Intensity Selection Version BC](strength_canonical_bc_20260928.md).

## Valid Batches, Masks, and Memory

- The cyclic model normalizes over a complete trajectory group from a single update; the memoryless complete trajectory model is identical.
  Standard row-by-row BC normalizes over a single Adam mini-batch.
- Before neural forward computation, use existing `field_weights` statistics to count the number of valid fields of each type.
  For two-GPU setups, merge the counts first; all sequence blocks and micro-batches share the same denominator, then gradients are accumulated and averaged according to the original procedure.
  When a category has only one global sample and all fields on a particular GPU are padding, the correct coefficient is preserved.
- Fields that are absent workers, fixed padding fields, market slots after STOP, and quantity-less operations are excluded from counting.
  STOP itself remains a learnable market decision. Context-specific turns retain memory effects but do not incur supervision loss.
- Teacher prefixes, full historical context, truncated memory gradients, and Adam update boundaries maintain their existing semantics.
  Statistical pre-traversal computes only masks and involves no additional neural forward pass.

## Configuration and Entry Points

[Default weights](../configs/bc_loss/grouped.yaml) are managed by Hydra.
[Complete configuration](../configs/learning_grouped_bc.yaml) inherits the fixed data, parent weights from watch2 BC, 100 epochs, a learning rate of 1e-4, and a dual-GPU setup, using an independent output directory; this facilitates comparison of loss schemes only.
It is a runnable research configuration; this code implementation does not initiate training, nor does it switch the currently running PPO.

View full configuration:

```bash
.venv/bin/python -m kagg_revue.learning.cli --config-name learning_grouped_bc --cfg job
```

New runtime entry point (output directory must be independent and unused):

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" \
  .venv/bin/python -m kagg_revue.learning.cli --config-name learning_grouped_bc \
  experiment.output_dir=outputs/learning/agronomy-v4-m384-watch2-grouped-bc
```

Can cover weights such as `experiment.demonstrations.loss.weights.market_operation=2.0`.
New datasets must simultaneously cover the manifest path and SHA256; parent weights must also be bound according to the existing protocol.
Adding `+bc_loss=grouped` to existing BC configurations enables the same target, supporting only
`grounded-v2` for single-turn actions. `experiment.demonstrations.loss=null` can perform old loss comparisons.

## Verification, Recovery, and Comparison

Train log retains five categories' NLL, accuracy, and effective field counts. For selection/confirmation, aggregation is performed first.
The total sum and count of NLL across all categories in the entire partition are computed, followed by weighted target calculation, without averaging category means across batches of different sizes.
Early stopping is enabled using this selection target to select checkpoints; training epoch metrics are aggregated based on category counts across the full epoch, representing the error measured online during that epoch, not a re-evaluation of the final weights.

The original `train_nll`, `selection_nll`, `action_nll` fields are retained, with their meanings explicitly identified by the `loss` configuration in the log. The scalar values of old and new losses cannot be directly compared as the same metric; only metrics with identical definitions, such as various NLLs, accuracy rates, and fixed-game evaluations, can be compared.

Weights and normalization methods are simultaneously parsed in the configuration, runtime protocol, BC checkpoint progress, and logs. Mid-game recovery is supported.
Changes to the loss function will be rejected; modifications to the target require the creation of an independent run. Historical configurations are omitted only when `loss` is specified, but the original settings are still used.
A per-turn effective field average is maintained, the original protocol identity is preserved, and historical training outputs are not overwritten.

This change balances five action domains and does not individually increase the weight of the `BUY_LAND` or SE categories.
It also cannot infer SE usage rate or win rate improvements solely based on loss performance. Subsequent comparisons should simultaneously examine market classification metrics, SE unlocking and production utilization in autonomous games, and win rate; the reward protocol remains unchanged from the current mainline.

## Validation Implementation

Against the target formula, native observations, and all parameter gradients, covering historical/new loss, recurrent/non-memory models, masked turns, sequence tail padding, uneven counting across dual processes, and fully padded tail rank.
Additionally, covering compiled graph capture, validation partition aggregation, rejection of invalid weights, and optimizer/RNG/ledger recovery.
These are implementation and recovery checks, not comprehensive training throughput or strategy gain conclusions.
