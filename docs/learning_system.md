# Scope of Completion and Future Boundaries of Reinforcement Learning Reconstruction

The goal is to achieve reproducible competitive performance gains from additional reinforcement learning investments, while not restricting strategy capabilities to a specific version of the teacher model.
2026-09-07 All model weights generated prior to this instruction are excluded, including those from training, initialization, recovery, and evaluation.
Future models must be traceable back to this experiment starting from random parameters; daily raw data can be reused,
previously trained BC, PPO, and search models are not reusable.

The mainline refactoring and pre-declaration of two random roots with 512-round experiments are complete, see [Delivery Results](learning_results.md).
The 128→512 revenue gains from internal and EcoBot family have been independently confirmed; the failure of the route family is retained separately.
Here, "completion" refers to runnable engineering and empirically measured finite-budget revenue, not including infinite monotonic growth, overall leaderboard advantage, or unexecuted Kaggle submissions as achieved results.

## Results That Must Be Proven

| Requirement | Authoritative Evidence | Current Status |
| --- | --- | --- |
| Fresh weights, no teacher dependency | Random root and end-to-end source tracing; training entry does not accept external weights or teachers | New learning configuration, initialization, and ledger have been implemented; source isolation tests passed |
| Environment and execution reliability | Consistency of actions in official replays and model closed-loop | 64 official replays are consistent; two new roots (0/16/32/64/96/128 rounds) show 138,240 observation consistency in official observation-driven closed-loop |
| Exploration can reach effective operating state | Full season, production/investment/sales behaviors, and final match evidence | After multiple date initializations, PPO maintains and increases actual production; average cash at 128-round endpoint mirror is about 66,000, independent fixed opponent cash is about 83,000–85,000 |
| Opponent continuously updates | Frozen historical pool generated during this run, actual sampled identities, and recovery | Historical pool has been sampled with new checkpoints during the run; deterministic FP32 full state recovery is bit-by-bit consistent; mature population and multi-source coverage remain insufficient |
| Optimizer learns terminal reward | Fixed-seed full game, causal credit, and effective gradient verification | Two new roots complete 65,536 PPO games each; internal 128→512 independent confirmation improves by 30.96/28.71 percentage points, paired intervals remain above zero |
| Increased investment leads to improvement | Multiple budgets, multiple RNG seeds, fixed evaluation, late external opponents, and intervals | Both roots pass internal and EcoBot 128→512 independent confirmation; route families fail, some adjacent intervals cross zero |
| No overfitting to four old scripts | New data sources, time leave-out, and mature opponent from multiple sources | 512-round experiments completed do not use old scripts; 100k runs introduced 25% of existing native scripts as per September 8 user instruction; further testing required for generalization against unseen opponents |
| Clear project architecture | Environment/action/policy/data/learning/evaluation/deployment interfaces and default entry points | New training entry and independent native core have detached from versioned teachers; network, contract, data, learning, evaluation, and deployment are now domain-separated; legacy workflows still retain compatible entry points |
| Deployment equivalence and local budget | Export consistency of the same new model, official timing, and full match | 512-round trajectories are consistent across two Python/PyTorch combinations; official timing including cold import and additional budget checks pass; Kaggle host did not execute |

## Current Experiment Boundaries

New learning entrypoint bypasses BC fallback via production.train. Shared Learner, PrefixCritic, terminal objectives, temperature, and update protection have been migrated to `learning/optimization/`; CUDA Graph strategy inference resides in `policy/inference.py`, sampling and historical seat routing in `learning/collection/`.
Network components are located in `policy/spatial/` and `policy/grounded/`, action contracts in `policy/contracts.py`, native batches and features in `native/`, neural combat and pairing statistics in `evaluation/`. `learning/adapter.py` only constructs `learning.settings.RuntimeSettings`, no longer requiring fictional BC data paths or old workflow mode/checkpoint.
Model semantics are defined by `policy/settings.py`, shared immutable schema in `configuration/`.
The old production workflow inherits runtime configuration and appends its own data and workflow validation.
Default `learning_mainline` uses a confirmed fixed multi-date initialization with online PPO recipe, generating a new random root and independent output directory each time. Source code recovery is documented in [learning_recovery.md](learning_recovery.md).
Default native builds and neural self-play use independent `_revue_core`; when explicitly configuring script populations, full C++ opponent components are reused, with protocol and recovery boundaries detailed in [Script Opponent Access](learning_script_population.md).
The full extension of the old workflow and the minimal observation extension of deployment are both preserved. The new core performs official replay, complete neural trajectory, new random root training, and archived state recovery verification, as described in [learning_native.md](learning_native.md). All long-budget experiments that have concluded use their original archived runtime. Engineering qualifications and completed expanded-budget experiment evidence are retained; the old workflow's compatibility entry remains, but future research scope does not imply dependency on the default training for old teachers.

Sparse market initialization sets only the initial distributions unrelated to time, state, or specific scripts: market STOP probability, quantity decay, and slight random output layer weights. All parameters are learnable, with no frozen schedules or predefined crop management trajectories. Initialization is an exploration of hypotheses, requiring comparison with different exploration structures, and it cannot be assumed that action expression limits have already been overcome.

Behavior auditing of work-v1 has confirmed a large number of absent unit selections, as well as localized optima that only reduce procurement without improving production.
The new grounded-v1 interface selects adjacent moves or operations supported by the current agent's on-field state, with the market conditioned only on the existence of units; unit support, probability re-computation, gradients, and gradual native closed-loop have passed verification. Specific scope and limitations are detailed in [grounded_policy.md](grounded_policy.md). Larger quantities, shared inventory conflicts, and market dynamics remain handled by the official executor.
If the new interface still only learns to spend less, further zero-shot experimentation should proceed via multi-source replay-state curricula, state coverage, or more effective exploration; it cannot circumvent the issue by restoring old teacher weights.

Daily data can serve as material for state coverage and multi-source supervision research. Training/selection/confirmation must be separated by complete games, seeds, and time; display names do not equate to independent strategy versions, and diversity cannot be overstated based on name count.
Data from September 6 has been used for environmental auditing, state coverage indexing, and curriculum environment recovery, and also serves as a likelihood diagnostic partition for a later-date independent opponent; this opponent was parameterized only with September 5 labels. Candidate models were parameterized only with labels from September 3–4.
State indexing is partitioned by complete environment seeds; all used bank roots have undergone precise prefix replay, double-seat state verification, and public history feature validation. The curriculum has completed two full budget experiments but has not achieved initial state operation, see [restart_curriculum.md](restart_curriculum.md). 128-round paired experiments exploring earlier investment phases and sales volume have concluded; improvements in scores on an internal neural opponent include minor commodity trading, yet still lack autonomous planting and have not been reproduced across multiple training RNGs. Multi-date demonstration initializations followed by online RL budgeting have received internal confirmation on two new roots; specific source boundaries and zero-budget controls are detailed in [demonstration_initialization.md](demonstration_initialization.md).

Two new seeds 51001/51002 have completed 512 rounds of experimentation, with fixed initialization followed by 65,536 games of training, using unchanged learning recipes. Four neural opponents containing two strong endpoints were pre-fixed, with 9 selection budgets, independent 0/128/512 confirmations, and the primary focus on late-stage gains from 128→512. The two new runs do not load the initial 128-round models as initialization. The protocol is available at [scaling protocol](../outputs/analysis/scratch-scaling-common-arena/protocol.json).

The gain in total score during the first 128 rounds was primarily driven by two weaker opponents, while the stronger panels still lag significantly. The current curve now retains observed scores and pairing intervals for each opponent, avoiding the misinterpretation of mixed total scores as uniform strength improvements.

The 128→256 round experiment yielded an internal gain of +14.06/+7.03 percentage points, with all pairing intervals above zero; this increase came from two stronger neural opponents. See [256-round results](../outputs/analysis/scratch-scaling-common-arena-256/curves.json).

The 3,072 previously recorded game-by-game entries from the new core have been retested and are consistent with the original expansion. Training and internal independent confirmations at 512 rounds have now concluded:

- The score improvement from 128→512 is 30.96/28.71 percentage points, with a 95% interval of [27.73, 34.08]/[25.59, 31.84], see [internal confirmation](../outputs/analysis/scratch-scaling-common-confirmation/curves.json).

- The 256→384 round experiment further improved by 15.23/17.19 percentage points, with pairing intervals of [10.94, 19.92]/[12.11, 21.88].

The two new roots now show observed scores exceeding 50% against both original strong mainline endpoints, see [384-round selection](../outputs/analysis/scratch-scaling-common-arena-384/curves.json).

A publicly available route/rule strategy currently under download and review has completed external selection/confirmation, see [external evaluation](learning_public_arena.md). The selection for 0/64/128 and independent confirmations for 0/128 both resulted in complete losses; cash gains did not translate into wins. This strategy is only for evaluation and belongs to a family of strategies, not generalizable to the entire leaderboard.

Another publicly available family, EcoBot v7, which operates based on observed valuation and daily planning, has completed a pre-fixed supplementary evaluation. In independent confirmations, the two 128-round models each increased from 2.34%/0.78% to 82.03%/73.44%, with both pairing intervals above zero.
This result provides additional external evidence of victory; the failure of the original route family is retained; neither family enters training.
The 512-turn independent confirmation of EcoBot has also concluded, with a score improvement of 28.00 13/53.91 percentage points, over the interval [19.53, 36.72]/[44.82, 62.50]. The route family achieved only 2 wins out of 128 and 0 wins out of 128, failing the late-stage criteria.
The unified agreement, per-game identity, and per-panel results are available at [Conclusion Index](../outputs/analysis/scratch-scaling-conclusion/report.json).

## Completion Discipline

Save source archive, parse configuration, random seed, full optimizer/RNG, historical pool, opponent hash, and pairing evaluation after each training turn.
Algorithm progress is only recognized after independent confirmation and with support for larger budgets or multiple random seeds, ensuring sustained returns; strength and scalability must be proven by evidence covering the relevant scope. Technical qualifications, single small experiments, documentation migration, or old submissions do not substitute for complete objective achievement.
Training results are stored in outputs, external raw data in data/external, temporary resources in tmp; do not modify third_party.
