# From-Scratch Training and Budget Expansion Experiment: Delivery Results

Mainline restructure, 512 rounds of training with two random roots, complete pre-declaration evaluation, and local portable package verification have been completed.
Online training budget increases have been independently confirmed on internal fixed neural opponents and the public EcoBot family; stronger route families have not yet achieved reliable win rates. This conclusion is limited to the actual tested budget and opponents, and does not guarantee improvement for every subsequent budget segment.

## Quadruple the online budget after fixing initialization

51001/51002 both start from random parameters following this instruction, with no parent weights from previous models. Initialization is performed using daily actions from multiple sources on September 3–4, fixed over four epochs, then demonstration targets are disabled and the full season PPO training is run. Online opponents are self and the frozen historical pool of this run; neither of the two public families enters training, reward computation, or fallback.

For each increase from 16,384 games over 128 turns to 65,536 games over 512 turns, a total of 47,120,384 strategy transfers are accumulated.
The following are independent confirmations with reserved environment seeds; intervals are clustered by seed, preserving the positions of both sides and the relevance to opponents.

| Fixed Evaluation Panel | Training Seed | Game Scores (128 → 512 turns) | Increment and 95% Confidence Interval |
| --- | --- | --- | --- |
| Four newly trained neural opponents | 51001 | 62.01% → 92.97% | +30.96 percentage points [27.73, 34.08] |
| Four newly trained neural opponents | 51002 | 57.42% → 86.13% | +28.71 [25.59, 31.84] |
| Public EcoBot rule family | 51001 | 63.28% → 91.41% | +28.13 [19.53, 36.72] |
| Public EcoBot rule family | 51002 | 42.97% → 96.88% | +53.91 [44.82, 62.50] |
| Public route/rule family | 51001 | 0.00% → 1.56% | +1.56 [0.00, 3.91] |
| Public route/rule family | 51002 | 0.00% → 0.00% | 0.00 [0.00, 0.00] |

Each internal budget point has 512 games, and each public family budget point has 128 games, all consisting of 64 independent environment seeds.
Two public families report separately; the number of displayed names, repeated trajectories, and different budgets are not counted as additional independent strategies or seeds.
Complete protocol, per-game results, identities, and cash increments are available at
[Unified Conclusion Index](../outputs/analysis/scratch-scaling-conclusion/report.json).
All nine selection budgets are retained, see
[Individual Opponent Curves](../outputs/analysis/scratch-scaling-common-arena-512/figures/opponent-curves.png).
The 384→512 score range of the second family crosses zero, and thus the later overall gains cannot be explained as monotonically guaranteed in segments.

## Runnable Mainline and Model

By default, `python -m kagg_revue.learning.cli` and the installed `kagg-revue` generate a new random root. A fixed initialization and 512 × 128 turns of PPO are executed. Hydra manages the budget, devices, and output directories; `learning_demonstrations` retains the original 128-round recipe, while `learning_grounded` retains the pure RL ablation. Architecture separation and installation are described in [README](../README.md), and recovery is detailed in [learning_recovery](learning_recovery.md). New training and default C++ builds use `_revue_core` without versioned teachers; the old workflow preserves explicit compatibility entry points. The entire long experiment runs using its original archived runtime, and evidence of equivalence between the new core and the old runtime is preserved separately. Ruff, type checking of 603 source files with mypy, four default Hydra/Pydantic configurations, and documentation link checks have all passed, as seen in [Final Engineering Check and Source Code Archive](../outputs/analysis/mainline-delivery/report.json).

The two complete training records and their final weights are
[51001](../outputs/learning/scratch-scaling-s51001/state.json) / [weights after 512 updates](../outputs/learning/scratch-scaling-s51001/checkpoints/update-000512.pt),
and [51002](../outputs/learning/scratch-scaling-s51002/state.json) / [weights after 512 updates](../outputs/learning/scratch-scaling-s51002/checkpoints/update-000512.pt).

The locally default portable package uses a pre-fixed first 512-turn endpoint:
[submission.tar.gz](../outputs/deployment/scratch-scaling-s51001-u512-portable-v1/submission.tar.gz),
SHA256 `b3c22b47f70e607ce77de6f6cceef2bfeb6c2cdf5cff7c163e20f8551d362c85`.
It completes two official timed loops under both Python 3.11/Torch 2.13 and Python 3.12/Torch 2.12, with identical full action trajectories across both runtimes. Cold start includes PyTorch import; maximum first action takes 2.191 seconds, maximum subsequent action takes 0.118 seconds, and the official extra time allowance remains at least 58.809 seconds, with peak RSS below 589 MB.
See [exact package eligibility](../outputs/analysis/deployment-scaling-s51001-u512/qualification.json) and
[deployment procedure](learning_deployment.md). This is local validation; not yet uploaded or executed on Kaggle host.
The actor inside the package matches exactly with the forward code and all frozen constants from four publicly available evaluation exports, as seen in
[evaluation and model identity delivery](../outputs/analysis/mainline-delivery/evaluated-deployment-identity.json).

## Boundaries Still Need Research

Trajectory family independent confirmation shows only 2/128, 0/128 wins, with no reliable winning gain from cash improvement; broader coverage against mature opponents, gains beyond 512 turns, and true leaderboard strength still require new experiments. Current delivery supports reproducible scalability gains within limited budgets, without claiming breakthrough performance against all opponents, achieving leaderboard rankings, or realizing infinite monotonic growth.
