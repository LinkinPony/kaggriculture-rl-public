# Budget Feature Main Line: 35% self-play and 65% unified PFSP

2026-09-12 As per user request, switch `budget-26m-20260911-s66001` from pure self-play to unified opponent pool PFSP. Formal operation has been normally halted at **U1028**, with a complete checkpoint saved at `checkpoints/update-001028.pt`. Both optimizers have accumulated **32,896 steps**; all model and optimizer tensors are finite, the dual-GPU RNG is complete and distinct, and the training lock has been released. See [halt verification](../outputs/analysis/budget-unified-pfsp-20260912/stopped.json).

Configured as [learning_budget_pfsp_change.yaml](../configs/learning_budget_pfsp_change.yaml).
This change only modifies `population` and `script_population`, preserving the current learning agent's weights, BC source,
both optimizers, dual-GPU RNG, root seed, training environment seed range, 100,000 update budget,
T=1, Actor/Critic learning rates, global logic batch size of 5,760 and micro-batch size of 2,880.

## Proportional and Uniform Sampling

Each round still consists of **128 games**. The target ratio is **35% self-play / 65% opponent pool matches**.
For each frozen opponent slot on dual-GPU setups, the learning seats are paired and balanced such that the total match quotas are rounded to the nearest integer:
The self-play game count every 5 rounds is **44 / 44 / 48 / 44 / 44**, and the frozen opponent match count is **84 / 84 / 80 / 84 / 84**. Every 640 games contains exactly **224 / 416 games**.
Balancing begins counting from the first round of this change, and phase resets are preserved upon recovery.
Each round generates **172 or 176 learning trajectories**; both self-play participants have equal weight of 0.5, while frozen opponent matches only train the learning side, with the total weight per physical match being identical.

All scripts, current history, and external history share the same PFSP probability distribution.
In each turn, a frozen opponent is sampled, and both cards use the same selection, with it handling the entire batch of frozen opponents for that turn.
Dense model inference is retained without loading the model per game. Scripts continue to use the existing C++ implementation,
and training does not include per-turn Python opponent callbacks.

PFSP uses `(1-p)^2` difficulty weighting, 20% uniform exploration across the full pool, 10% coverage based on the most recent historical runs,
8 prior games, 128 update half-life, and 256 as the upper limit of effective evidence.
Uniform exploration and difficulty weighting are normalized across all opponents; the script has no independent quota or minimum number of games per turn.
Evidence for scripts not selected in a turn is retained. External models do not inherit the win rate statistics from previous learners.

## Opponent Identity

At switch, there are **60 opponents**:

- Current budget feature run: BC endpoint and all 22 still registered PPO checkpoints, totaling 23.
- `context-26m-3d-20260910-s65001`: BC endpoint and all 26 still registered PPO checkpoints, including the final **U3575**, totaling 27.
- The above context run has imported prior history:
  `context-26m-20260908-s62001`'s **U512 / U1536 / U2560 / U3584 / U4302**, totaling 5.
- Native scripts: `router_95`, `farming_v4`, `kaito_v58`, `shop_router_0908`, `shop_router_0909`, totaling 5.

Neural history pool upper limit **64**, with 32 external versions fixedly retained; currently running retains up to 32 versions, adding snapshots every 64 turns, retaining BC endpoint, the latest 4 snapshots, and earlier training stages.
5 scripts always have sampling eligibility, making the total pool upper limit **69 opponents**.

All external sources bind the original ledger SHA256, checkpoint SHA256, and run ID;
After copying, register them into the current run `historical/manifest.json`, and archive recovery using a local copy.
BC only allows importing authenticated `rl_initial` from the source run, and does not accept any intermediate shard.
The model retains its own vocabulary table and internal budget feature switches, separately constructing frozen inference graphs;
Numbering mappings are applied only at native action execution boundaries, and original logits and sampling distributions are preserved.
Public observations, environment, clock, and other network semantics must still match.

## Verification and Official Switching

34 related Python checks, Ruff, mypy (717 files), and two PFSP frontend checks passed.
Regression coverage across joint probability across types, continuous 200 turns with dual-GPU seed partitioning, statistical recovery replay,
script evidence retention upon non-selection, native script batching, compatibility with old budget models and quantity-numbered execution,
and batch size caching across different batch sizes of the same frozen model.

Five-script completion of 10 official environment matchups, 14,400 observations, and 7,190 script actions all matched exactly.
Independent replicas completed **Round U1029–U1040, totaling 12 rounds, 1,536 games, and 2,072 learning trajectories**,
after normally stopping at U1032, restored from archived source code to U1040.
Actor/Critic both advanced **264 steps**, with no KL rejections, all tensor bounds satisfied;
dual-GPU RNG is complete, PFSP replay sampling and checkpoint/ledger statistics are consistent.
Both full 5-round windows consist of 224 self-play games and 416 pool-vs-play games.

Samples with six inference graphs preheated took between **27.13–30.04 seconds**, with a median of **29.64 seconds**;
peak allocated GPU memory reached **96.11 GiB per card**. The initial compilation for the two batch sizes took approximately 345 / 311 seconds, respectively, and there were preheating overheads during archive recovery and the first inference of the old model.
See [Official Environment Comparison](../outputs/analysis/budget-unified-pfsp-20260912/official.json),
[Complete Acceptance](../outputs/analysis/budget-unified-pfsp-20260912/qualification.json),
[Acceptance Summary](../outputs/analysis/budget-unified-pfsp-20260912/qualification-summary.json), and
[WebUI Verification](../outputs/analysis/budget-unified-pfsp-20260912/webui-qualification.json).

The formal update has been applied to **`population-revisions/0001`, effective from U1029**.
Field-by-field verification confirms that only two population configurations have been modified; all originally registered assets, checkpoint bytes, and historical records are preserved.
Formal **U1032 complete checkpoint passed verification**: U1029–1032 comprises 512 games, 692 learning trajectories,
the first three rounds play against current history, and the fourth round consists of 44 self-play games and 84 Kaito v58 games.
Each optimizer advances 88 steps, both Actor and Critic are updated, with no KL rejections; all tensors are finite,
PFSP replay and checkpoint/ledger statistics are consistent, and both dual-GPU RNGs continue progressing independently.
Actor learning rate is 7.5e-6, Critic learning rate is 1e-4. Training continues.
See [Formal Checkpoint Verification](../outputs/analysis/budget-unified-pfsp-20260912/formal-verification.json).
The formal WebUI now displays 35% / 65% of target progress, all 60 opponents, and two generations from external sources, with no script errors.
The unified pool probability table is retained even when match results have not yet been saved.
See [Formal Interface Verification](../outputs/analysis/budget-unified-pfsp-20260912/webui-formal.json).
See [Migration Verification](../outputs/analysis/budget-unified-pfsp-20260912/transition-verification.json) and
[Official Launch](../outputs/analysis/budget-unified-pfsp-20260912/formal-launch.json).

Use the original recovery entry after normal stop:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/budget-26m-20260911-s66001
```
