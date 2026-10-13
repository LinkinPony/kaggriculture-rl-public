# Supplementary for Three-Model Self-Gameplay

The user requests to check and complete the self-games for the A, B+C, and SpaTaro models, while unifying the display name to **SpaTaro**. The internal member ID `spataro` and existing checkpoint names are kept stable.

The original league only included three types of matches: A–B+C, A–SpaTaro, and B+C–SpaTaro, with 64 games of each type. There was indeed no training match where the same model controlled both sides. After the complete preservation of Round **54**, independent replica acceptance was completed and the system was resumed from the same recovery point; starting from Round **55**, the following new match ratios are adopted.

## Sampling and Optimization

| Game | Total Games per Turn | Games per GPU |
| --- | ---: | ---: |
| A–B+C | 32 | 16 |
| A–SpaTaro | 32 | 16 |
| B+C–SpaTaro | 32 | 16 |
| A Self-play | 32 | 16 |
| B+C Self-play | 32 | 16 |
| SpaTaro Self-play | 32 | 16 |

The total remains at **192 games / 384 seat trajectory entries**, with each model still collecting 64 trajectory entries per GPU.
Physical matches consist of 50% mutual gameplay and 50% self-play. Each model participates in 96 games: 32 self-play games and 32 mutual games against each of the other two models. In self-play, trajectories from both sides are retained, each with a weight of 0.5; in mutual games, only the trajectories from the current model are retained, with a weight of 1. Thus, each model's optimization weights for the three opponents are each assigned to 1/3, avoiding double-counting a match due to two seats in self-play.

Still first freeze three strategies to complete sampling, then update the three Actor/Critic independently. Native batch size, three sets of CUDA Graph, inference batch size, optimization logic batch and micro-batch, as well as GPU0 + GPU1 remain unchanged. The total budget remains at 100,000 turns. The training seed continues to increment by 192 games per turn, with no reuse of seeds from previous turns.

## Statistics and Evaluation

Each round records six types of matches; physical field count is counted only once. Mutual match outcomes are statistically derived from the left-model's perspective in the pairing name; self-play outcomes are fixedly derived from seat 0, without merging both sides, resulting in approximately a 50% win rate.
Self-play outcomes are separately displayed with field counts, average terminal cash per side, absolute cash difference per match, and draw rate.
The overall cash of each model is weighted by physical field count, with self-play first averaging the cash of both sides; the mutual win rate of a model uses only the number of mutual matches as the denominator.
The UI's historical window breaks at points where match composition changes; the self-play curve starts from the actual introduction round and does not artificially fill in prior data.

Evaluate with fixed seed, retaining three mutual games of 64 matches each along with their original seeds, and adding three self-play games of 64 matches each, totaling **384 matches**. Mutual games and self-play games are executed in two batches in sequence, reusing the original inference batch size. The self-play seeds follow immediately after the 192 mutual game seeds and do not enter the training seed stream. A baseline evaluation is performed once at the boundary switch, and thereafter the rules of evaluation every 512 turns and confirmation at budget end are followed.

## Same Run Continuation Training and Data Dependency

Switch to retain three models, six optimizers, mutual RNG, BC endpoint, and original 100k total budget.
Source recovery point is `checkpoints/update-000054.pt`, SHA256:
`2c50ae09c31d6079ce709830461c9a967abac63a92968492a2e479922e68c9d2`.
Old source code, configuration, and recovery points are retained in revision archive; official weights do not use updates from acceptance copies.

The initial acceptance test revealed that the original BC data list path no longer exists during replica preparation:
`outputs/datasets/league-v2-20260906-08/views/strata.json`.

The original implementation relied on the original demonstration list for PPO recovery after BC completion. The current approach now reads the original data only when BC has not been completed. For PPO recovery after BC completion, verification and archiving now include: the original demonstration configuration, path information for each role, hashes, six epoch records, registered BC endpoints, and model, native library, and source code fingerprints.

The identity of the original data is preserved, with no modification to the BC data source or re-execution of BC.

Acceptance includes CPU routing and weight testing, three rounds of true dual-GPU PPO, and recovery from the same source code archive after mid-game interruption. All six networks are actually updated, with all models, six optimizers, and both RNGs fully finite.
Stable turn: **40.46 seconds**, peak approximately **94.1 GiB per card**. First launch and archive recovery for the initial round include compilation warm-up, taking 89.92 and 89.55 seconds, respectively. 33 Python tests, 10 frontend tests, Ruff, and mypy checks on 673 source code files all pass.
See [`qualification.json`](../outputs/analysis/league-selfplay-20260909/qualification.json).

Official source code SHA256:
`26ae31ed96752fd87caa4ed1b8c83440553798226b7525c6baf8ea7c740fecff`.
Revision history and previous recovery points are retained in the runtime directory `population-revisions/0001`;
The BC subdirectory retains the previous state for each and references their internal latest source code archives.
See [Startup Activation Record](../outputs/analysis/league-selfplay-20260909/formal-launch.json).
The recovery command remains `python -m kagg_revue.learning.league.recovery`, without reprocessing BC.

Formal operation has verified checkpoint Round 56: all three Actor/Critic models have been updated, all six optimizers and both RNGs are finite, BC member identities remain consistent; since Round 55, each of the six match types has consisted of 32 games per round. WebUI testing returned 203 scalar values, six rows of training statistics, six rows of evaluation tables, and SpaTaro self-play filtering all function normally, with no browser script errors. See
[Formal Recovery Point Verification](../outputs/analysis/league-selfplay-20260909/formal-verification.json) and
[Formal Page Verification](../outputs/analysis/league-selfplay-20260909/formal-browser.json).
