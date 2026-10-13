# Context 26M: Recent Three Days BC → Self-play + PFSP

Future update: This run paused PFSP after U124 as per user request, and switched to pure self-play starting from U125;
See [switch log](context3d_selfplay_20260910.md). The following records the initial data and training phase.

2026-09-10 Following user requirements, continue using the archived U4302's 26M main trunk and training workflow, and perform a **4 epoch BC** from random parameters using the latest three complete-date replays. Then automatically transition into **self-play + historical PFSP**.
This run does not include script opponents and does not load weights from previous runs or engineering acceptance models.

## Source and Fixed Data Partitioning

2026-09-10 Real-time download of [Kaggle Official Daily Index](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index)
Latest complete date is **2026-09-09**, thus the freeze window is **2026-09-07 to 09-09**.
The original ZIP file 09-07/08 is reused after verification; the 09-09 download is newly obtained and retained in `data/external/`.
Verify daily date, number of games, uncompressed volume, and SHA256. Source details are available at
[Original Data List](../data/external/kaggriculture-context3d-20260910/raw/manifest.json).

Retain group and division by seed `episode-seed`, group **62001**. Players with the same environment seed and both sides in the same game remain in the same group;
The data from five days ago overlapping with 09-07 follows the same grouping rules.

| Replay Date | Original Games | Training | Validation Selection | Final Holdout Confirmation |
| --- | ---: | ---: | ---: | ---: |
| 2026-09-07 | 663 | 602 | 27 | 34 |
| 2026-09-08 | 663 | 594 | 30 | 39 |
| 2026-09-09 | 662 | 582 | 40 | 40 |
| **Total** | **1,988** | **1,778** | **97** | **113** |

| Data Set | Candidate Decisions | Unexpressible Unit Actions | Coverage Gap in Quantity Table | Available Decisions |
| --- | ---: | ---: | ---: | ---: |
| Training | 2,556,764 | 2,277 | 0 | **2,554,487** |
| Validation | 139,486 | 155 | 0 | **139,331** |
| Final Holdout | 162,494 | 171 | 1 | **162,322** |

Covers both sides and all stages, without filtering by final outcome or cash. Full training consists of **224 training shards × 4 epoch**, consuming **10,217,948** training decisions and **40,012** BC optimization steps. The final held-out set retains only the data, not used for vocabulary fitting or BC gradient computation; the vocabulary is composed of training labels and pre-specified exploration values, totaling **183** symbols, with **13,316** observations preserved.

Data preparation entry point is [demonstrations_context_3d.yaml](../configs/demonstrations_context_3d.yaml),
Generating 252 shards, taking **185.90 seconds**. Encoding manifest is
[manifest.json](../outputs/datasets/grounded-v2-20260907-09/manifest.json), SHA256:
`2ac6d5b961f771fa298e522e76ef5ada537febb78897f54fcb4e9aa4fb4b7700`.
Grouping, coverage, and interface verification are available in [data-verification.json](../outputs/analysis/context3d-20260910/data-verification.json).

## New Model and Training Recipe

Configured formally as [learning_context_3d.yaml](../configs/learning_context_3d.yaml).
New random seed **65001**, run directory `outputs/learning/context-26m-3d-20260910-s65001`.
Actor: 384-dimensional, 16 layers, 8 heads, FFN 768; Critic: 320-dimensional, 6 layers, 8 heads, FFN 640.
The output head count is established based on 183 symbols from the current training dataset; the main backbone, action interface, and native environment remain unchanged.
Actor has **20,663,448** parameters, Critic has **5,863,362** parameters, totaling **26,526,810**, see
[Parameter Verification](../outputs/analysis/context3d-20260910/parameters.json). The minor differences from the previous model arise from
the increased output head and critic embedding sizes due to expansion of the training vocabulary, while the backbone depth and width remain unchanged.

| Project | Setting |
| --- | --- |
| GPU | GPU0 + GPU1, two H200 |
| BC | Fixed 4 epoch; global batch size 256; 128 per card; learning rate 1e-4 |
| BC Saving | Save model, optimizer, and dual-card RNG every 4 shards, at the end of epoch, and upon normal termination |
| BC Selection | Enter RL at the endpoint of the 4th epoch; validate NLL and 4 independent behavior measurements per epoch |
| RL Total Budget | 100,000 updates |
| Game per Turn | **64 current-model self-play games + 64 historical PFSP games** |
| Learning Trajectory | 192 trajectories per turn; self-play sides each with weight 0.5, historical game learning side with weight 1 |
| PPO | Global logical batch size 5,760; execution micro-batch size 2,880; 24 steps per actor/critic per turn; actor with KL protection |
| Sampling and Precision | T=1, BF16, concurrent historical inference, CUDA Graph, native batch environment |
| Initial RL Learning Rate | Actor 3e-5, Critic 1e-4; retain KL fallback protection |
| Reward | `sign(own cash - opponent cash) + own cash / 10000` |
| BC Loss Retention | Coefficient 0 during RL phase |
| Script Configuration | `script_population: null`; no script quota or script model tag |
| Checkpoint | Save every 4 turns and upon normal termination; retain the last 8 checkpoints and protect historical pool members |
| Fixed Evaluation | Every 512 turns, evaluate 64 games at the current BC endpoint and at two random anchor points |

The history pool comes solely from this round's random root: it starts with only the BC endpoint, and a snapshot is added every 64 updates, up to a maximum of 16.
Retain the BC endpoint, the last 4, and representatives from earlier stages; allocate according to decayed win/loss estimates as: **20% uniform + 10% latest + 70% square of loss probability**. Evidence half-life is 128 turns, prior is 8 games, and effective sample cap is 256. When there is only one member at the beginning, the sampling probability of that historical member is naturally 1.
The historical match participants are evenly distributed across the two GPU slots; sampling statistics are saved with each complete checkpoint and verified upon recovery.

The new training seed range is `[4,150,000,000, 4,162,800,000)`; the selection start point is 4,170,000,000,
confirmation is 4,180,000,000, and BC behavior measurement is 4,190,000,000; the random evaluation anchor points are 150001/150002.
The data loader simultaneously checks that the replay seed does not overlap with these role ranges.

## Acceptance and Operational Status

Before official launch, conduct a 4 epoch BC → 4 turn complete PPO engineering acceptance test using a single latest full training shard and an independent validation shard under identical backbone, batch, micro-batch, and two-GPU settings. Perform a normal mid-PPO stop and restore from archive. Shorten the historical snapshot interval to 2 to verify new pool member addition; the official setting remains at 64. Use acceptance random seed 65002, separate from the official run.

The acceptance has been passed, see [qualification.json](../outputs/analysis/context3d-20260910/qualification.json).
4 epoch small-data BC contains 45,944 decision entries, followed by 4 rounds of PPO totaling 512 games. After U3 normally stops, it is restored from archive to U4, with each optimizer advancing 24 steps; the model, optimizers, and dual-GPU RNG are complete and all tensors are finite; PFSP sampling replay and checkpoint/ledger are consistent, with the final pool consisting of this BC, U2, and U4.
The initial small-data policy triggers KL protection and pauses the Actor at U1, and U2–U4 each complete 24 steps for both Actor and Critic.
The first and remaining shape compilations occur at U1 and U2; restart preheating happens at U4; the only fully stable sample at U3 takes **31.44 seconds**, with peak allocated GPU memory reaching **95.82 GiB per card**. This acceptance is not used to evaluate model performance or to determine the learning rate for formal training.
11 related tests, full Ruff and mypy (690 files) pass, see [inspection record](../outputs/analysis/context3d-20260910/checks.json).

Formally launched at **2026-09-10 08:44:37 UTC**, run ID is
`9040df0f976046c0bf3ca581b500a0c4`, see
[Launch Record](../outputs/analysis/context3d-20260910/formal-launch.json).
Random initial checkpoint SHA256 is
`65df01ebbfbcfaebc7a55b7ff55a366405d5b9ba83da07e2841cf73b8da6702f`,
and its model tensors have been individually verified against the randomly reconstructed model kernel seeded with 65001.
Formal BC fragment savepoint #60 has been confirmed: model updates, optimizer, and two-GPU RNG are complete, all tensors are finite,
all formal data array hashes have passed loader verification, the old run ledger remains unchanged and is still marked as stopped.
See [Formal BC Verification](../outputs/analysis/context3d-20260910/formal-bc-verification.json).

Formal **4 epoch** has been fully completed, with an actual consumption of 896 training data shards, 10,217,948 decision records,
40,012 optimization steps, and training phase timing of **1,667.97 seconds** (including held-out validation and behavior measurement).

| Epoch | Training NLL | Validation NLL | Accumulated Optimization Steps |
| --- | ---: | ---: | ---: |
| 1 | 0.341225 | 0.253543 | 10,003 |
| 2 | 0.208686 | 0.218760 | 20,006 |
| 3 | 0.181674 | 0.200281 | 30,009 |
| 4 | 0.165333 | 0.188679 | 40,012 |

BC endpoint is `pretraining/shard-000896.pt`, SHA256 is `60b5d12dfe15cdcf32e8603579564618b7499036d9c659ec6a07257a33f1e1da`.
Complete consumption records, optimizer 40,012 steps, dual-GPU RNG, data, and parent chain identity have been confirmed; all tensors are finite;
Four behavioral measurements have been completed. The same entry has automatically switched to `reinforcement_learning`; the historical pool initially contains only this BC endpoint. See [Complete BC Verification](../outputs/analysis/context3d-20260910/formal-bc-complete.json).
Validate NLL as a measure of fit to the held-out demonstration actions; no evaluation of online ranking or opening adaptability has been performed this time.

Formal RL U4 complete checkpoint has been verified, see
[formal-rl-verification.json](../outputs/analysis/context3d-20260910/formal-rl-verification.json).
In the first 4 rounds, 64 self-play games and 64 historical PFSP games were sampled per round, totaling 512 games and 768 learning trajectories.
Both Actor and Critic were updated, with each optimizer completing 96 update steps; the model and optimizer tensors in the complete checkpoint are limited in size.
The CPU/CUDA RNG with two GPUs is fully implemented and distinct. The PFSP replay sampling per round matches the round-wise sampling, and the checkpoint/ledger statistics are consistent.
The historical pool consists solely of this BC; script allocation across all rounds is empty. U64 has only been introduced in the online historical snapshot for the first time.
The U4 checkpoint SHA256 is
`2fdcbf611f258d8c094834c998630013b3f472d0c1a974173d489c0e3a8675ab`.
This early PPO file will be cleaned according to the original recent checkpoint retention policy; the verification report will retain its hash and consumption records.

U1 preheating took 109.42 seconds, and after two KL rejections, it still completed 24 steps for both Actor and Critic, with the Actor learning rate automatically reduced to **7.5e-6**. U2–U4 had no rejections and each completed 24 steps; the times were **31.19 / 31.26 / 31.80 seconds**, with a median of **31.26 seconds** and a peak of **95.81 GiB per GPU**. These are three steady-state throughput samples from the early formal run; RL continues to run, and subsequent metrics are based on the run directory.

The WebUI operation page, real-time PPO progress, 50% self-play / 50% historical PFSP ratio, and historical pool are all visible; submitted metrics load normally, with no JavaScript errors in the browser, see
[Page Verification](../outputs/analysis/context3d-20260910/webui-formal-rl.json).
Runtime entry: <http://127.0.0.1:8765/?run=learning/context-26m-3d-20260910-s65001>.

The running status and actual completion progress are based on the current `run-status.json`, `learning-progress.json`.
The old `context-26m-20260908-s62001` continues to remain at U4302, with the original tag and fixed weights retained.

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.cli --config-name learning_context_3d
```

Recovery entry after normal stop:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-3d-20260910-s65001
```
