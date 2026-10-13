# Three Experts BC and Mutual Combat RL

Reduce the current model parameter count to approximately one-quarter, and train three independent models using A, B+C, and SpaTaro data, each for 6 epochs of BC. Then, conduct 100,000 turns of mutual combat training between GPU0 and GPU1. In each turn, each of the three models performs one PPO rollout update.

2026-09-09 Following user requirements, starting from Round **55**, three models will participate in self-games:
32 games of mutual combat among the three models, and 32 games of self-combat for each model, totaling 192 games per round.
Original weights, optimizers, RNG, BC endpoint, and 100k total budget are carried over; the display name is uniformly set to SpaTaro.
Current configuration and acceptance details are available in [Self-Game Revision](league_selfplay_20260909.md).

## Data and Splitting

Source is the latest index from the official daily episodes, from 2026-09-06 to 09-08, totaling 1,988 games.
Download source, fingerprint, and behavior explanations are available at [Three-Day Analysis](daily_behavior_20260909.md).
Training, selection, and confirmation are divided by complete environment seed; the seats for both players always belong to the same partition.
Shared grounded-v2 encoding and a number vocabulary table determined solely by the training partition.

| Training Role | Train Decision Count | Selection | Confirmation |
| --- | ---: | ---: | ---: |
| A | 713,972 | 32,168 | 40,476 |
| B+C | 1,869,683 | 88,594 | 113,378 |
| SpaTaro | 162,492 | 7,190 | 9,347 |

A defines a window of 24 consecutive decisions: a complete unit action sequence must be repeated in at least three other training episodes, with market requests aligning with the mode of these reference trajectories at least 90%, and the average mode share at least 80%.
When classifying a training episode, exclude the positions of both sides involved; reserve the data to not participate in template fitting or market mode computation.
The last window has 23 decisions.

B+C are the remaining representable decisions. This is an operational classification of the degree of behavioral repetition, and one cannot conclude from this that
the author uses RL. The fragment rules allow the same author or different stages of a game to be assigned to different categories.

SpaTaro only includes its own seat position, preserving the complete representable trajectory; all instances in this case fall into B+C, thus resulting in intentional overlap with the second model. The six epochs sequentially traverse their respective datasets, with different numbers of optimization steps. Holding actions from opponents with different names are not mixed into SpaTaro's labels.

The data view shares immutable tensors via hard links, adding only row-selection masks; both standard loaders and GPU resident loaders enforce the mask. Verification covers all shards, with A being mutually exclusive and exhaustive against B+C, and SpaTaro is checked per seat with no overlapping seed partitions, see [Data Verification](../outputs/analysis/league-20260909/data-audit.json).
Base manifest SHA256: `e03b80c39d7265b7b7d2fda278b29cc2117669583da12bbe74f218fcc33c631f`;
Layer manifest SHA256: `7681a3fb111fc7a423a385ddba811fc25b1252d142d1e8abd9ab6e25cb46abd4`.

## Model and Execution

Actor: width 192, 15 layers, 4 attention heads, expansion factor 2, 5,002,434 parameters.
Prefix critic: width 160, 6 layers, 1,565,282 parameters.
Total **6,567,716**, which is **24.82%** of the original 26,463,950 parameters.
Input remains 13,316 features per step, sharing the same 153-item vocabulary and native action ABI as before.
The network architecture is reduced and reinitialized without scaling the original weight values or loading previous model parameters.
Three actors use identical random initialization; models, optimizers, data progress, and subsequent critic are saved separately.

BC global batch 1,024, per-card 512, learning rate 1e-4. Run in order: A, B+C, SpaTaro, each for six full epochs. Training for each model simultaneously uses two GPUs.
Each selected row of each shard is transmitted once to the GPU; subsequent batches are indexed on the GPU, reducing repeated transfers.
Record out-of-sample NLL per epoch, but fixedly use the endpoint of the sixth epoch for RL.

For rounds 1–54: 64 games each of A–B+C, A–SpaTaro, and B+C–SpaTaro; from round 55 onward, mutual matches begin.
Revised to 32 games each of A–B+C, A–SpaTaro, and B+C–SpaTaro, plus an additional 32 self-play games each for A, B+C, and SpaTaro.
Total remains 192 games, 384 trajectory entries; each model collects 64 trajectory entries per GPU.
In self-play, each side's trajectory is assigned half weight; in mutual matches, the self-trajectory weight is 1, with all matches treated equally as in physical competition.
First freeze the three strategies to complete all sampling, then update the actor/critic for each strategy separately, using only their own actions, behavior likelihoods, and rewards. Gradient synchronization across two GPUs; no use of training script opponents or shared optimizers.
Retain current PPO's prefix credit, reward, and KL rollback protection.

Three CUDA Graphs share a native C++ SelfPlayBatch; a CUDA synchronization is performed once per turn, then actions are distributed back to their respective seats. RL logic batch size is 5,760, with global micro-batch execution of 5,760.
The original run reappeared NaN during the 4th BC epoch of B+C, and disabling cuDNN attention and BF16 low-precision accumulation did not fully resolve the issue. The root cause has been identified as the decoder fusion LayerNorm reading uninitialized temporary data, and native operator boundaries have been added independently for both forward and backward passes.
No exception retry or eager fallback is implemented; network compilation and CUDA Graph remain intact.
Previous BC results are not considered valid endpoints; after the fix, three independent 6-epoch BC runs are restarted from the same initialization. See [Root Cause and Fix](decoder_numerics_20260909.md). The compilation cache is stored in repository `tmp/`.
Training seed range is `[3700000000, 3719200000)`, with a total pre-allocated budget of 19,200,000 games.
Every 512 turns, three pairwise matches and three self-play games are evaluated on independent fixed seeds, and three independent actors are exported; each of the six match types consists of 64 games, executed in two batches, preserving the original pairwise evaluation seed. A separate confirmation seed is used at the end. This evaluation measures relative performance and cannot be used solely to infer absolute progress from pairwise win rates.

Every 4 turns and upon normal termination, submit three models, six optimizers, and GPU RNG atoms from both sides to the same joint checkpoint, retaining the initial point and the most recent eight restore points. Restore strict source code, native libraries, configurations, data, and BC lineage, while repairing the tail end of unsubmitted metric logs.

## Entry

Official configuration: [learning_league.yaml](../configs/learning_league.yaml).
Official output directory: `outputs/learning/league3-20260909-s63001-fixed`.
Process status available at `run-status.json`, `league-progress.json`; BC details in
`a/learning-progress.json`, `bc/learning-progress.json`, `spataro/learning-progress.json`.

After training stops, restore using the frozen run archive:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.league.recovery
```

The initial pipeline acceptance used an independent small data view to complete 6 turns and stop recovery, with records retained in [Original Acceptance Report](../outputs/analysis/league-20260909/qualification.json). This short test did not cover the later-occurring fused kernel faults, and therefore cannot be used to validate the original BC weights in operation.

Fixed verification uses original fault shards and trained weights; the final source code passes all 18 batch forward/backward NaN checks and 2 rounds of 384 real-game matchups. All three actor/critic models are actually updated, with finite parameters, optimizers, and sampled tensors. Ruff, mypy full checks, and 10 test cases pass.
After preheating, **41.13 seconds per turn**, peak **94.16 GiB per GPU**; at this short-term speed, approximately 47.6 days for 100k turns, though actual speed may vary. See
[Fixed Verification](../outputs/analysis/league-failure-20260909/repair-qualification.json).

The restored official run has been initiated; see
[Startup Log](../outputs/learning/league3-20260909-s63001-fixed/launch.json) and
[Initial Configuration Confirmation](../outputs/learning/league3-20260909-s63001-fixed/restart.json).
Three complete BC phases and the first 3 rounds of official RL have all been verified. Subsequently, round 4 was successfully submitted by restoring from the archived run of the same execution, continuing with the original 100k total budget. See
[Official Run Verification](../outputs/learning/league3-20260909-s63001-fixed/formal-verification.json).
The latest stage is governed by the progress file in the run directory.
