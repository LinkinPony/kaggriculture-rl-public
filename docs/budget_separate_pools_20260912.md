# Budget Model: Independent Script Pool and Historical PFSP

2026-09-12, change the game target of `budget-26m-20260911-s66001` to
**30% self-play, 20% native script, 50% historical model PFSP**.
Operate officially on U1864, save and stop normally; the new phase takes effect from U1865.

## Sampling and Quota

Each round still consists of 128 physical matches. For each opponent, two GPUs are paired according to the seat positions on both sides, resulting in a global count in units of 4; the script's cumulative allocation uses deterministic rounding, reaching the target exactly every 5 rounds:

| Turn from effective point | Self-play | Independent script | Historical PFSP |
| --- | ---: | ---: | ---: |
| 1 | 40 | 24 | 64 |
| 2 | 36 | 28 | 64 |
| 3 | 40 | 24 | 64 |
| 4 | 36 | 28 | 64 |
| 5 | 40 | 24 | 64 |
| Total | 192 (30%) | 128 (20%) | 320 (50%) |

In each turn, one script and one historical model are randomly selected, taking on respective game quotas.
Five scripts—`router_95`, `farming_v4`, `kaito_v58`, `shop_router_0908`, `shop_router_0909`—are drawn from the script pool using adaptive sampling based on recent match outcomes: the lower the learning side's score, the higher the script's priority. The script pool is allocated 80% of the time via normalization based on `(1 - score)^2`, with 20% reserved for uniform exploration; each of the five scripts has at least a 4% sampling probability within the pool, corresponding to at least 0.8% total game sampling probability.
Here, `score` uses a prior with exponential decay, incorporating half a draw rate. The evidence half-life is 128 turns, the prior is based on 8 matches, and the maximum number of effective evidences is 256 matches; scripts do not apply the "latest version override" from historical models.
Script sampling and historical PFSP use separate, randomly seeded streams indexed by update number; neither the number of historical models nor changes in win rates affect script sampling outcomes. Script match scores only influence weights within the script pool and do not participate in the probability normalization of historical PFSP. No guarantee exists that each short time window will have equal allocation among the five scripts.

Based on the existing match records of U1864, the initial probabilities in U1865's script pool are sequentially as follows:
Router **22.84%**, Farming **18.49%**, Kaito **13.07%**, Shop 0908 **22.00%**, Shop 0909 **23.60%**; subsequent updates will be made according to the new complete game results. See
[Initial Probabilities](../outputs/analysis/budget-separate-pools-20260912/initial-script-probabilities.json).

The historical pool retains all original members and match evidence, with a capacity of 64, and 32 external versions are permanently preserved.
A snapshot is taken every 64 turns. The decay parameter PFSP, uniform exploration, and latest model coverage parameters remain unchanged.
The native script continues to execute in the C++ batch environment.

## Continuation Boundary

U1864 checkpoint SHA-256:
`6ce0f00c4e1bcff83d7471540e19c51bb87c4cbcfb0d7f1ad68c622021b2ba6e`.
Migration only modifies the recipe fields of `population` and `script_population`; original weights, two optimizers,
dual-GPU RNG, training seed, 100k total budget, BC source, T=1, learning rate, and logical batch 5,760 /
micro-batch 2,880 are retained. The CUDA Graph exclusive stream fix is also retained.
New quota rounding begins to be calculated from U1865; historical PFSP evidence continues from U1864.

The WebUI displays historical PFSP probability tables and independent script tables; U1865 marks changes in opponent composition. Each turn of 24/28, whether the field is balanced or a different script is drawn, does not result in additional segmentation of the statistical phase.

Configuration: [learning_budget_separate_change.yaml](../configs/learning_budget_separate_change.yaml).
Stop recording: [stopped.json](../outputs/analysis/budget-separate-pools-20260912/stopped.json).

## Dual-card Continuation Acceptance Inspection

Independent replica `budget-separate-adaptive-qualification-20260912` starting from formal U1864,
completed U1865–1872, a total of **8 rounds, 1,024 games**, including normal termination at U1868 and recovery from archive.
The first five rounds accumulated **192 self-play games, 128 scripted games, and 320 historical PFSP games**.
Five types of scripts were all drawn during these eight rounds, with script weights adjusting according to match outcomes.

Both Actor and Critic are updated, with each optimizer advancing **168 steps**, no KL rejection;
All checkpoint tensors are finite, and PFSP sampling replay, saved statistics, and model lineage are consistent.
Random states on both GPUs are advanced and remain independent. Peak memory usage is **95.95 GiB per card**.
The three preheated samples U1867, U1868, and U1870 take **28.19–28.97 seconds per turn**;
There is additional overhead in the first compilation, restart, or first loading of a historical model with a different shape.
These are engineering acceptance results and do not represent opponent strength assessment.

15 related Python checks, 3 PFSP frontend checks, full Ruff and mypy (723 files) passed.
See [Acceptance Report](../outputs/analysis/budget-separate-pools-20260912/qualification.json) and
[Additional Verification of Random Streams, Quotas, and Timing](../outputs/analysis/budget-separate-pools-20260912/qualification-additional-checks.json).

## Formal Migration

Formally migrated and archived under `population-revisions/0002`, with source code identity as
`8a9dba5ce8dc92d0783f3f07ae13b09343b531f0211081a540087d5f004f5e36`.
Only the formula fields have changed for `population` and `script_population`; the checkpoint byte check of U1864, all historical members and evidence, and the source code summary of the original CUDA Graph exclusive stream fix are completely consistent with before migration.
Training has been formally resumed with two GPUs through the archival entry. See
[Migration Verification](../outputs/analysis/budget-separate-pools-20260912/transition-verification.json) and
[Formal Launch](../outputs/analysis/budget-separate-pools-20260912/formal-launch.json).

Formal **Checkpoint U1868 has passed verification**: 512 new games and 664 new learning trajectories added for U1865–1868.
The Actor/Critic optimizers each advanced 84 steps with no KL rejections; all tensors are finite, PFSP replay and checkpoint statistics are consistent, and both GPU random streams have progressed independently. Checkpoint SHA-256:
`8d9d7b8744e35c76ac656b4df2491a0d83fac01b881c0292e7fa3734bab6d9d4`.
Formal training has passed the evaluation boundary after this checkpoint and continues to U1870.
The WebUI has confirmed "training in progress", 30% / 20% / 50% targets, 64 pure historical entries, and 5 dynamically normalized script entries with separate normalization. See
[Formal checkpoint verification](../outputs/analysis/budget-separate-pools-20260912/formal-verification.json) and
[WebUI verification](../outputs/analysis/budget-separate-pools-20260912/webui-formal.json).

Subsequent fixes addressed the issue of WebUI incorrectly hiding historical details between two save operations: changes in opponents or 24/28 field quotas during real-time updates no longer cause the win rate from the previous save point to become invalid; historical pool and script pool statistics are still displayed even when a new phase has not yet been saved. Only truly cross-training-phase past win-draw-lose records are isolated.

15 frontend checks, quota changes in browsers, new phase pending save, and three real-time page scenarios have passed;
64 historical entries and 5 script entries are all visible. The monitoring service has been updated, and training processes remain uninterrupted.
See [Browser Verification](../outputs/analysis/budget-webui-history-20260912/browser-verification.json) and [Service Update Verification](../outputs/analysis/budget-webui-history-20260912/deployment-verification.json).
