# This Early Diagnosis and Failed Experiment from Scratch Research

This file retains evidence from the exploration and state course experiments that have already concluded in this instruction. The current mainline, execution, and decision are based on
[CURRENT_MAINLINE.md](CURRENT_MAINLINE.md). The following records experiments in chronological order, where "next experiment" describes the decision at the time, not the current default command. All models originate from this fresh random root.

### Completed Diagnosis

- `outputs/learning/scratch-qualification-v1`: Random initialization, terminal WDL, 2 × 8 game training.
  Uniform exploration of action space in the original work led to all players having 0 final cash, all draws, and 0 actor updates; this approach fails.
- `outputs/learning/scratch-qualification-v2`: Uses trainable market STOP bias and decaying quantity bias,
  no teacher, no time-action table, still retains full quantity with finite probability support.
  4 × 32 game training all achieve non-constant WDL,
  actor updates are 4, 6, 6, 6 respectively.
  24 independent confirmed games show no measurable score improvement; only demonstrate recovery of training signals,
  not evidence of strength or scaling laws.
  Full results available at [confirmation.json](../outputs/learning/scratch-qualification-v2/confirmation.json).
- 256 games/update compilation configuration has completed three consecutive updates,
  steady-state around 8.8 seconds per turn, peak memory usage approximately 4.6 GB.
  See [technical qualification](../outputs/learning/scratch-compiled-qualification-v1/qualification.json).
  RNG and evaluation match in BF16 interruption recovery, but parameters are not guaranteed bit-level consistency.
  Bit-level deterministic FP32 verification has passed:
  actor, critic, two optimizers, and RNG match bit-for-bit after recovery compared to continuous training, see [recovery verification](../outputs/learning/scratch-resume-deterministic-challenge-v1/resume-verification.json).
  This verification requires `torch.use_deterministic_algorithms(True)` and `CUBLAS_WORKSPACE_CONFIG=:4096:8`,
  and does not extend to guarantee bit-level reproducibility of default BF16 execution.

Two completed learning curve experiments are `outputs/learning/scratch-work-s41001` (cuda:0) and `outputs/learning/scratch-work-s41002` (cuda:1), both with new random roots, 32 updates, and 256 games per update. Both groups completed 32 turns and exited, resulting in a total of 16,384 games trained. `launch.json`, `run-status.json`, and `state.json` record configuration, process, and complete training ledger. The source code fingerprint is identical at `545b982943ebdef925396f938e53a09d50649bb88d272847f9eb34ae6077e2c8`. Selection is fixed every 4 turns, and confirmation is only applied at the end of training. All groups started from scratch.

| Training random seed | Number of training games | Confirmation of score change | 95% interval by environment seed |
| --- | ---: | ---: | --- |
| 41001 | 8,192 | +5.21 percentage points | [+2.08, +8.33] |
| 41002 | 8,192 | 0.00 percentage points | [-1.56, +1.56] |

Each group consists of 192 games, 32 independent environment seeds, three random neural opponents, and dual slots. Complete budget curves, actual historical pool sampling, optimizer steps, and terminal identities are available in [comparison.json](../outputs/analysis/scratch-work-baseline/comparison.json), reconstructible via `python -m kagg_revue.learning.report`. An improvement on a single seed cannot prove stable gains across RNGs, and results on random opponents cannot confirm current game strength. Neither group achieved model advancement or submission.

Behavior audit has confirmed that approximately **96.9% of the operation credit fields for work-v1 belong to absent units**, with neither initial nor post-training operations carrying out watering or harvesting; cash improvement primarily stems from reduced procurement. Report available at [work behavior audit](../outputs/analysis/scratch-work-behavior/behavior.json).

### Single-turn Action Interface and Second Round from Scratch Experiment

The new `grounded-v1` selects adjacent moves or on-site supported unit actions during each official turn, preserving all original units. Operational expressiveness is maintained, with absent units and queued fills no longer selected randomly; the market operates only based on the actual presence of units. Native support for unit augmentation guarantees only executability when the number of isolated units is 1; shared inventory, large quantities, and market dynamics remain subject to official rules. Technical boundaries and testing are detailed in [grounded_policy.md](grounded_policy.md).

Two new random roots `scratch-grounded-s42001` and `scratch-grounded-s42002` have both been completed.
16 × 128 training rounds terminated, totaling 4,096 games; no retrieval of the previous round or old mainline model.
The training archive source code fingerprint is `821e01b3d65d178bb60c5004bdbed7f136a7cb7b6441325d3ee8c661a228bc63`.
384 actor updates per group, no KL rollback, learning rate maintained at 1e-4 throughout, with a steady state of approximately 16 seconds per update.

| Training random seed | Number of training games | Independent confirmation of score change | 95% interval by environment seed |
| --- | ---: | ---: | --- |
| 42001 | 2,048 | +48.44 percentage points | [+42.19, +55.01] |
| 42002 | 2,048 | +46.88 percentage points | [+39.58, +53.65] |

Each group still consists of 192 games, 32 independent environment seeds, three randomly generated neural opponents from the same experiment run, and dual seats.
Complete curves and identity verification are available at
[grounded comparison](../outputs/analysis/scratch-grounded-baseline/comparison.json).
This is not a budget-constant ablation study compared to work-v1, nor does it prove the competitive strength against mature opponents.

**Decision: Do not consider the significant increase in random opponent usage as production capacity, nor continue to expand this configuration alone.**
In 8 mirror behavior audits, the total procurement costs for the two models decreased from 37,589/37,772 to 5,944/6,523,
revenue dropped from 414/406 to 146/144, sowing decreased from 63/68 to 11/11, and harvesting remains at 0.
Absence of job credits is indeed 0, but the models have learned local optima of spending less.
Reports are available at [Behavior 42001](../outputs/analysis/scratch-grounded-s42001-behavior/behavior.json) and
[Behavior 42002](../outputs/analysis/scratch-grounded-s42002-behavior/behavior.json).
A multi-source state curriculum with precise prefix replay has been integrated subsequently; currently, no models have advanced or submitted.

### Completed Multi-Source State Course

`datasets.restarts` and native `replay_prefixes` now support restoring the current daily state from the original seed, field-by-field state verification between both sides, and confirmation of the public history reconstructed from official observations as well as all actor features.
PPO only collects new policy actions occurring after the entry point; original replay actions are not used as training labels.
Restoration source, partitioning, reward, and budget rules are detailed in [restart_curriculum.md](restart_curriculum.md).

`scratch-curriculum-qualification-v2` Completed 32 technical qualification games, with harvest, watering, and fertilization appearing in independent source suffixes, yet no operational improvement was measured. Deterministic FP32 true SIGTERM/recovery comparison has been verified, including source sampling, complete model, optimizer, RNG, and cash results, see [Course Recovery Verification](../outputs/learning/scratch-curriculum-resume-challenge-v1/resume-verification.json).

Two new random roots `scratch-curriculum-s43001` and `scratch-curriculum-s43002` have been completed and exited.
Each group consists of 64 × 128 games; source code fingerprint is
`87fd06468b04fd4285f2927f99505f4c5b58d91f3fde87f2fe4493654c6667e5`.
The first four phases start at turns 576, 384, 192, and 48, respectively, with each fourth round restarting from turn 0; the final 32 rounds begin entirely from turn 0. Each group completes 5,120 full games, 3,072 suffix games, and 4,968,448 online policy transitions.
Auxiliary rewards use `(terminal cash - cash at entry) / 1000`, retaining the direct WDL term; the reward from this auxiliary objective does not equate to competitive ability. A full initial state selection is performed every 8 rounds, followed by an independent confirmation.
Each group completes 1,308 actor updates, with no KL rollback; the learning rate remains at 1e-4.

| Training Seed | Confirmation of Score Change | 95% Interval by Environment Seed | Mean Terminal Cash Confirmation |
| --- | ---: | --- | ---: |
| 43001 | +55.73 percentage points | [+49.15, +61.98] | 2,995.52 |
| 43002 | +52.60 percentage points | [+46.35, +58.85] | 2,999.01 |

Confirmation that coverage is limited to random neural opponents, with 192 games per group and 32 independent environment seeds. See
[Comprehensive Budget Report](../outputs/analysis/scratch-curriculum-baseline/comparison.json).
**This course does not address the problem of starting from zero.** In 8 mirrored audits with identical seeds, both terminal models showed no seeding, no harvesting, and no sales; total purchases were only 1 and 0, with average cash balances of 2,999.9375 and 3,000.
See [43001 Initial State Behavior](../outputs/analysis/scratch-curriculum-s43001-full-behavior/behavior.json) and
[43002 Initial State Behavior](../outputs/analysis/scratch-curriculum-s43002-full-behavior/behavior.json).

After 576 turns of source retention in the suffix evaluation, the terminal cash per game is approximately 828.26 and 781.95 higher than the initial model, with intervals of [627.86, 1034.66] and [576.26, 986.62], respectively; the average net cash is only 73.45 and 57.36. This demonstrates that local gains achieved after inheriting existing resources cannot prove the viability of autonomously establishing a farm. The curves are shown in [43001 Source Selection](../outputs/analysis/scratch-curriculum-s43001-source-selection/curves.json) and [43002 Source Selection](../outputs/analysis/scratch-curriculum-s43002-source-selection/curves.json).

**Next experiment adjustment: Add the initial investment phase and distinguish between sales and procurement quantity exploration.**
The current source code introduces
learnable quantity biases categorized by market operations; when enabled, the initial sales quantity distribution no longer inherits the large-quantity penalty from procurement.
The original quantity vocabulary and official inventory constraints remain unchanged. This switch is fully written into the model layout, and is disabled by default to preserve the existing semantics of new models.
A new source index adds turns 1, 3, 6, and 12, resulting in 21,846 candidate states.
Technical qualifications have been passed for turn 3 and turn 1.
The first pairing switch for `learning_reverse.yaml` is as follows:
`scratch-reverse-volume-s45001` and `scratch-reverse-shared-s45001`, each branch with 128 × 128 games,
shared initialization seeds and source sampling, with all common initial tensors being bit-identical.
Source code fingerprint is `06c092c55d1e794657ed3bfd555e2eb5843f2ba46a30c31258aa601a3b05d752`.
These represent two configurations under the same initialization seed, not two independent RNG reproductions. Both failed and exited after completing 48 rounds:
At turn 12, 6 out of the 128 source roots exhibited inconsistent backpack item ordering, thus no data was collected for round 49.
The root cause is that the JSON items in daily data, sorted by name, were mistakenly interpreted as insertion order in the environment, while the native state values themselves remained consistent.
Failure evidence is available at [diagnosis.json](../outputs/analysis/restart-feature-mismatch/diagnosis.json).
Neither used the full budget confirmation, and thus are not complete ablation results. Full mirror audits of round 48 yielded no insights; each was only seeded once, with 3/2 times.
Reports are saved in their respective incomplete-behavior paths pointed to by `qualification.json`.

Fixes the behavior starting from an empty initial backpack, ensuring that insert, delete, and restore operations follow the correct insertion order per turn, without referencing future frames or native state as a reference label. All course entry points are validated before the first PPO update in new training runs.
The official interpreter, native engine, and normalized replay have undergone triple auditing across 64 games, 92,160 observations, including backpack insertion order, see [order audit](../outputs/analysis/daily-20260906-inventory-order-audit/report.json).
The v2 branches have been launched from new random roots, with paths `scratch-reverse-volume-v2-s45001` and `scratch-reverse-shared-v2-s45001`. Each branch has been verified across all 10 entry points, totaling 1,040 training roots, with actual training source code fingerprints of `c69da90c279d2b8ad90f9a6e8a03917c88795753a1dc47a4c9281c84c3169e82`.
The initial parameters shared between both branches are bit-by-bit identical, see [v2 initialization comparison](../outputs/analysis/scratch-reverse-v2-ablation/initialization-control.json).
Both branches have completed and exited, each running 128 × 128 games: 8,704 full games, 7,680 suffix games, and 10,749,440 policy transitions. The on/off quantity bias has completed 2, 826/2, and 586 actor updates respectively, with no KL rollback observed, and learning rate maintained at 1e-4. The confirmed score change on the own random anchor is +51.04/+51.56 percentage points, with 95% intervals [43.75, 57.81]/[44.79, 58.33].
See [full budget](../outputs/analysis/scratch-reverse-v2-baseline/comparison.json).

In the 8 full-start mirror audits, neither endpoint had any seeding or harvesting. In the opened branch, 46 units of wheat were bought and 33 units sold; the average terminal cash was 2,972.19. In the closed branch, there were no purchases or sales, and cash remained at 3,000. See [Full Behavior](../outputs/analysis/scratch-reverse-v2-full-behavior/behavior.json).

A pre-fixed unified opponent consists of the two models from the 64th round of the random root curriculum, serving as an internal neural control with retained cash. With 128 trials, 32 environment seeds, and dual seats, the endpoint win rates were 69.53%/50.39%, and the average cash was 2,992/3,000; in the opened branch, 79 trials had cash above 3,000, but the mean remained unprofitable. The win rate difference between closed and opened branches falls within the interval [-26.56, -12.11] percentage points. The intermediate budget and original results are shown in [Unified Opponent Curve](../outputs/analysis/scratch-reverse-v2-common-arena/curves.json).

This is a pair of initialization ablation studies, with no cross-training RNG reproducibility or mature external opponent evidence yet. Design and evidence are provided in [reverse curriculum](restart_curriculum.md); no new models have advanced at this time.
