# September 15: Latest Two Days 2-epoch BC → Official RL

## Current Status

User requested to halt the current training, add it to the historical PFSP pool, perform 2 epochs of BC on the latest two-day data with new weights, then initiate formal RL. The old run has been stopped, and both new data and startup procedures have passed confirmation; two rounds of formal BC have been fully completed, and the formal dual-GPU RL is now running continuously, with U8 checkpoint verified.
User has explicitly confirmed that the new model will be randomly initialized, followed by 2-epoch BC, with the old weights used only for freezing historical opponents.

## Stop and Historical Pool

Old run `outputs/learning/budget-q100-top10-2d-20260913-s68001` stopped normally on U5629.
Final checkpoint `checkpoints/update-005629.pt` has SHA-256:
`5700c91c41e6198b444ae5aa540e08f03f51ad6cb3444f57c0a8601d0370bef6`.
Both optimizers accumulated 118,114 steps for Actor and 118,209 steps for Critic; all checkpoint tensors are finite.
Dual-card RNG is independent. Process exited, run lock released, and parent process exit code 0 is restored.
See [Stop Verification](../outputs/analysis/top10-training-20260915/old-stop-verification.json).

Retain the original 57 external models, add 39 self-version instances from the pool when old runs were stopped, plus the final U5629:
BC endpoint, 38 historical snapshots, and the final weights, totaling 40 versions.
Total external models: 97, capacity expanded to 136, retaining 39 historical self-positions.
Sources of state hashes and explicit checkpoint lists are available at
[Historical Selection](../outputs/analysis/top10-training-20260915/historical-selection.json).
All lineage, hashes, architectures, and finite numerical validations for the 97 models have passed, see
[Historical Source Verification](../outputs/analysis/top10-training-20260915/historical-preflight.json).

## Data Scope

This refresh of the official index covers the two most recent complete dates: 2026-09-13 and 2026-09-14, each with 654 games.
Date, number of games, uncompressed volume, and original ZIP hash have been confirmed. Permanent original source available at
[daily manifest](../data/external/kaggriculture-top10-2d-20260915/raw/daily/manifest.json).

Use the mainline selection criteria: two days of daily-replay seats from verifiable historical top-ten teams, plus all available public games from public submissions whose own score is strictly above 2900 and whose teams are currently in the top ten. Supplemental replays have no lower date bound and are deduplicated by episode ID. Historical ranking coverage remains incomplete; retain the exclusion list of unverified seats.
Quantity classes range from 1–100. Use seed 62001 for the 90% / 5% / 5% split and traverse every row with equal weight.

The leaderboard snapshot is fixed at 2026-09-15 07:27:14 UTC, with 17 versions meeting the criteria.
3,506 games in the API list overlap with daily games in 622 cases; the remaining 2,884 games have all been supplemented,
with no download failures or server rate limiting. The historical top ten of four verifiable leaderboard snapshots collectively cover 30 team IDs,
name mapping has passed verification. 4,137 candidate games are selected for consolidation; full-frame auditing excludes two games (108447638 and 108275644),
as well as 3 demonstration slots; original files are retained.
The final set consists of 4,135 games and 5,102 demonstration slots, including 1,252 daily games and 2,883 publicly supplemented games,
which have been encoded into 519 fragments.

| Partition | Game | Demonstration Seat | Valid Decision Rows | Unsupported Unit Action Rows | Rows with Quantity Truncation |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 3,705 | 4,565 | 3,279,967 | 2,268 | 2,400 |
| selection | 229 | 285 | 204,796 | 119 | 102 |
| confirmation | 201 | 252 | 181,056 | 132 | 137 |

The training set consists of 464 shards, and a complete traversal of 2 epochs yields **6,559,934 rows and 26,216 optimization steps**.
The data manifest is [manifest.json](../outputs/datasets/grounded-v2-top10-20260913-14-q100/manifest.json),
SHA-256 is `f89c5a7a5de59342d7bb453c05708406d2ef652cbf82eafd5cb26a303faf7268`.
All hash, shape, finite value, quantity range, and seat checks for the 2,076 array files have passed,
with no duplicate episodes or decision rows across partitions and no cross-partition seed conflicts. 28 API metadata identity verifications have passed.
30,240 observations and model features from 21 full replays are consistent, and the labels retained have finite likelihood.
See [Array Acceptance](../outputs/analysis/top10-2d-20260915/dataset-verification.json) and
[Full Replay Acceptance](../outputs/analysis/top10-2d-20260915/replay-verification.json).

Retrieve and prepare configurations for [ranked_acquisition_20260915.yaml](../configs/ranked_acquisition_20260915.yaml)
and [demonstrations_ranked_20260915.yaml](../configs/demonstrations_ranked_20260915.yaml).

## New Startup Fix and Acceptance

Existing regression tests have revealed that `transition(config, state, config)` returns prematurely during the first import.
Although the external models have been authenticated and replicated, they do not immediately enter the PFSP pool.
The original pool is now retained only when all external models are already in the pool; the full pool initialization is still performed during the first import.
The existing behavior for script/configuration migration of established pools remains unchanged.
27 related tests, Ruff, and full mypy (771 files) have passed.
Using the mainline model size, 97 external models, and five official native scripts, a small data BC (2-epoch, dual-GPU) → 8-round RL acceptance has been achieved, including normal shutdown and archival recovery from U5 to U8.
All models have been updated; the Actor and Critic optimizers for U5 → U8 have each advanced by 21 and 63 steps respectively, with all tensor bounds satisfied.
Dual-GPU RNGs are independent. All 97 external members have entered the pool from U1, and all 8 rounds of PFSP sampling and statistical replay have passed.
The first 5 rounds consist of exactly 192 self-play games, 128 script-based games, and 320 historical matchups.
See [complete engineering acceptance](../outputs/analysis/top10-training-20260915/qualification.json).

Official recipe retains 100,000 updates, 128 games per turn, 30% self-play / 20% independent dynamic scripts / 50% historical PFSP, Actor LR 7.5e-6, Critic LR 1e-4 constant, fully saved every 4 turns.

## Official Operation

Working directory: `outputs/learning/budget-q100-top10-2d-20260915-s69001`.
Random seed **69001**, run ID `7d29cd58baca4ee286e8a8e27f8deb3b`, `input_weights: []`.
Hydra configured as [learning_top10_2d_20260915.yaml](../configs/learning_top10_2d_20260915.yaml).
Data, historical sources, training code, and acceptance code consistency, as well as full seed range verification, have passed, see
[Pre-launch verification](../outputs/analysis/top10-training-20260915/preflight.json).

The formal process has been initiated, with a 2-epoch BC execution using two GPUs, followed by automatic import of 97 historical models and entry into RL.
The training seed range is `[3,850,000,000, 3,862,800,000)`; selection, confirmation, and BC behavior checks begin at 3,870,000,000, 3,871,000,000, and 3,872,000,000, respectively.
It has been verified that there is no overlap with existing data or ongoing training/evaluation intervals locally.
The initial BC checkpoint confirms a new random root, no input of old weights, actual Actor updates, complete optimizer state, and dual-GPU RNG.
See [BC Startup Verification](../outputs/analysis/top10-training-20260915/formal-bc-start-verification.json).

**2 BC epoch completed and verified**: 3,279,967 rows per turn, total 6,559,934 rows,
26,216 optimization steps. Training NLL over two turns is 0.35898 / 0.24490, selection NLL is
**0.27483 / 0.23945**. Final SHA-256 of terminal `pretraining/shard-000928.pt` is
`3c7531d0368b4572a119e6bfbfabd16238cf4d89a6f6df775495dfaaa1964188`.
Data identity, full budget, optimizer, two-GPU RNG, and finite tensors have passed, see
[BC Completion Verification](../outputs/analysis/top10-training-20260915/formal-bc-complete.json).
**Formal RL has started, and the complete U8 checkpoint has passed verification.**
In the first eight turns, totaling 1,024 games, both the Actor and Critic optimizers accumulated 168 steps each. Both U4 → U8 networks were updated, with each optimizer continuing for 84 steps; zero KL rejections, Actor LR at 7.5e-6 and Critic LR at 1e-4 remained constant.
All checkpoint tensors are finite, and both GPU random streams have progressed and remain independent.

97 external models have entered the U1 pool, bringing the total to 98 models including this BC model. The previously stopped U5629 has been officially registered into the pool; the U3328 from this source has actually participated in the first eight rounds of gameplay. All eight rounds of PFSP sampling and statistical replay have passed verification; the first five rounds consisted of 192 self-play games, 128 scripted games, and 320 historical matchups.
The U8 checkpoint SHA-256 is
`15e4a3a3162766a7c93e7ac32f772311005393d5cb6165c45696da76125257ec`.
See [Formal RL Verification](../outputs/analysis/top10-training-20260915/formal-rl-verification.json).
Formal training is ongoing; these checks validate the correctness of the operation, not independent conclusions on competitive strength.
See [Startup Log](../outputs/analysis/top10-training-20260915/formal-launch.json) and
[Real-time Status](../outputs/learning/budget-q100-top10-2d-20260915-s69001/learning-progress.json).
