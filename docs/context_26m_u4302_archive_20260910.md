# Context 26M: U4302 Stop, Performance, and BC Source

2026-09-10 Stop `context-26m-20260908-s62001` as per user request, retain for baseline of the next stage of research.
This record will separately cite online feedback, training statistics, and independent evaluation.

## Fixed Version and Stop Verification

| Item | Record |
| --- | --- |
| Git annotated tag | `context-26m-20260908-s62001-u4302` |
| Commit containing training implementation | `1889ac0`; tag points to a subsequent commit containing this archive document |
| Run ID | `9d3a7fd343984da084c72d65a681198e` |
| Stop time | 2026-09-10 07:55:15 UTC; recovery entry at 07:55:16 UTC exit |
| Final complete update | **4302 / originally 100000**, status `stopped` |
| Cumulative physical games | **551,040**; U1 is 512 games, the rest 128 per round |
| PFSP phase | U3781–4302, **522 rounds / 66,816 games** |
| Actor / Critic parameters | 20,618,508 / 5,845,442, total **26,463,950** |
| Cumulative optimization steps for Actor / Critic | **102,063 / 102,064**, consistent with sum from round-by-round ledger |
| Final actual learning rate | Actor **3.75e-6**; Critic **1e-4** |
| Final sampling | T=1, 32 self-play games + 32 historical PFSP games + 64 native script PFSP games |

Send a SIGTERM to the parent process that has passed process identity verification, complete the current PPO update according to the existing stop protocol, save the last two updates U4301/U4302 that have not yet been committed to disk, then exit. The exit code of the recovery entry is **0**.
The parent process, the training main process, and the two-GPU worker processes have all exited; `run.lock` and `recovery.lock` can be reacquired.
The WebUI continues to provide service on port 8765, returning HTTP 200 for both health checks and operational details, with details showing `phase=stopped` and `update=checkpoint_update=4302`, see
[WebUI Status](../outputs/analysis/context-stop-20260910/webui.json). No retraining has been restarted.

The original restore point is
[`checkpoints/update-004302.pt`](../outputs/learning/context-26m-20260908-s62001/checkpoints/update-004302.pt).
To prevent the rolling retention policy from eliminating this non-periodic snapshot during future training sessions, separate, independent
[fixed checkpoint](../outputs/archives/context-26m-20260908-s62001-u4302/update-004302.pt),
[ledger at stop](../outputs/archives/context-26m-20260908-s62001-u4302/state.json), and
[fixed asset inventory](../outputs/archives/context-26m-20260908-s62001-u4302/manifest.json)
are retained.
This directory preserves the final weights and the ledger; full PPO restoration still uses the historical pool, source code, and native assets from the original run directory.
Git tag stores the source code and this document, linked to the weights via the following SHA256; large files remain in the gitignored `outputs/`.

| Asset | SHA256 |
| --- | --- |
| U4302 complete checkpoint | `2be6014c0a43701be311f0795cc5d10365e5c65339f88a8f59c1a801e6014082` |
| Executable source code content | `a96851f251faf732d8304aa39244152441dd374393f3b01feea638d07b259d9a` |
| Native module | `2b947f38e5c18cda8ab03ca5c109998940feb90e6695621fc7ddd79514c4f5a3` |
| BC endpoint `pretraining/shard-001504.pt` | `a4a72675ea8778a7865cc689dd6c02b01fae692d497229039b84fd7ae9cfdaec` |

Re-verified all **39 registered members**, hashed native and script-execution assets; final checkpoint
includes Actor, Critic, two optimizers, CPU/CUDA RNG per two GPUs, PFSP state and parent chain, with all tensors finite.
The two GPUs have distinct RNGs, PFSP state matches the ledger, and `metrics.jsonl` is exactly consistent with the ledger.
Verification entry is the existing `learning.state.restore`, not validated through restarting PPO.
See [Stop Request](../outputs/analysis/context-stop-20260910/stop-request.json) and
[Stop Verification](../outputs/analysis/context-stop-20260910/stopped.json).

## Range of Performance and Evidence

### User's Online Performance Report

2026-09-10 User feedback: The current model's trajectory has reached approximately **rank 10** level; previous operations have largely stabilized.
It notes that the rank 1 opponent has a win rate of about **100%** against us, and this opponent exhibits more flexible behavior.
Reference: [submission 56114097 / episode 107395930](https://www.kaggle.com/competitions/kaggriculture/leaderboard?submissionId=56114097&episodeId=107395930).

The above serves as the user observation record. The replay provided could not be read, the ranking was not independently verified, nor were the match samples statistically analyzed. The assumption that "the opening is fixed by BC" was not confirmed as an established causal relationship. At the time of termination, the most recently recorded submission by our side was
**U3364 / submission 56133717**, see
[Submission Acknowledgment](../outputs/analysis/kaggle-context-s62001-u3364-20260910-once/submission-receipt.json).
This submission predates the PFSP switch at U3781; user feedback cannot be directly used as evidence for PFSP improvement or for the online strength of U4302. No submission of U4302 was made at termination, and no independent matchup evaluation against this top-ranked player was conducted.

At the same time **11:51:09 UTC**, the archived submission **U4302** was submitted as requested by the user, with Kaggle acknowledgment number **56143582**, and initial verification code **`PENDING`**. The submission used the same checkpoint and full source code. It passed two eager sampling consistency checks, as well as two official full-game matches under Python 3.11/3.12, each including cold-start conditions. See [Deployment Qualification](../outputs/analysis/kaggle-context-s62001-u4302-20260910/qualification.json), [Submission Acknowledgment](../outputs/analysis/kaggle-context-s62001-u4302-20260910/submission-receipt.json), and [Kaggle Status](../outputs/analysis/kaggle-context-s62001-u4302-20260910/submission-status.json).

### Training Statistics for Fixed Scripts

Weighted by actual game count, compare the last 128 turns of PFSP's **U3653–3780** with the last 128 turns of **U4175–4302** prior to stopping. The seeds of the two windows are different; the latter window uses dynamic opponent matching and belongs to online training observation.

| Opponent | Win Rate (Games) Before Switch | Win Rate (Games) Before Stop | Change |
|---------|-------------------------------|-------------------------------|-------|
| router_95 | 93.90% (2,048) | 93.33% (1,544) | -0.57 percentage points |
| farming_v4 | 96.53% (2,048) | 96.63% (1,128) | +0.10 percentage points |
| shop_router_0909 | 87.89% (2,048) | 88.10% (3,252) | +0.21 percentage points |
| shop_router_0908 | 90.53% (2,048) | 91.05% (2,268) | +0.52 percentage points |

Script performance has remained basically stable. The historical PFSP score before stopping was **57.97% / 4,096 games**, and the last 32 rounds achieved **52.83% / 1,024 games**; scores are calculated as win = 1, draw = 0.5, loss = 0. The historical opponent pool has evolved with training, so these values cannot be considered as fixed opponent ability curves or as standalone evidence of performance degradation.

### Fixed Assessment and Throughput

| Fixed selection checkpoint | Opponent | Win / Draw / Loss | Average terminal cash |
| --- | --- | ---: | ---: |
| U3584 | BC endpoint + two random strategies, each 64 games | 192 / 0 / 0 | 139,996.70 |
| U4096 | Same panel and seed | 192 / 0 / 0 | 143,329.52 |

The panel is already saturated; cash increases cannot alone demonstrate an improved win rate against strong opponents. U4096 is the most recent fixed assessment at the time of stopping. U4302 has no independent fixed assessment yet. The next phase should retain U4302 and the deployed U3364 as separate baselines.

Over the 128 rounds before the stop, the median time per round was **25.88 seconds/turn**, with P10–P90 ranging from **25.83 to 26.48 seconds**.
Before the switch, it was **29.38 seconds/turn**. Based on the median, throughput improved by **13.5%**.
The recorded update duration does not include checkpoint or additional evaluation overhead. This improvement accounts for the reduction in per-turn learning trajectory from 192 to 160.
The median time for sampling/optimization per turn was **6.11 / 19.74 seconds**, with peak allocated GPU memory reaching **95.24 GiB per GPU**.
All 522 PFSP rounds had no KL rejections or Actor early stops; the historical pool remained consistently at 16 agents, with each of the four scripts having at least 4 games per turn.
See [complete statistics and window definitions](../outputs/analysis/context-stop-20260910/performance.json).

## What specific dates did BC actually use?

The sources are the five official Kaggle daily replay packages dated **2026-09-03, 09-04, 09-05, 09-06, and 09-07**.
These are replay creation dates. The run started on **09-08**, which does not mean it used demonstrations from 09-08.
The SHA256 hashes of all five ZIP files were recalculated and exactly match the original archived preparation configuration and provenance manifest. The creation dates of `manifest.csv` inside the packages also match each respective date.

Read the environment seed from each game replay in the original `source.tar.gz` using `demonstrations_context.yaml` and the group code, and reconstruct the results using the split seed **62001** as follows:

| Replay Date | Original Game | Actual Training | Validation Selection | Final Holdout Confirmation |
| --- | ---: | ---: | ---: | ---: |
| 2026-09-03 | 669 | 602 | 30 | 37 |
| 2026-09-04 | 668 | 590 | 40 | 38 |
| 2026-09-05 | 664 | 590 | 34 | 40 |
| 2026-09-06 | 662 | 601 | 27 | 34 |
| 2026-09-07 | 663 | 602 | 27 | 34 |
| **Total** | **3,326** | **2,985** | **158** | **183** |

The unit of division is a complete environment seed, and both players remain in the same group during a game; they contribute training data for five consecutive days.
In the configuration, each source's `split: train` will be deterministically grouped under `partition: episode-seed`,
thus not all 3,326 games are used for gradient training. This reconstruction is consistent with the total number of games in the original document, with no duplicate episode IDs.

Based on the retained consumption ledger, each training epoch uses **4,292,256** valid decisions, with a validation set of **227,196** samples; the originally planned holdout set was **263,147** samples.
Fixed training for **4 epochs**, accumulating **17,169,024** training decisions and **67,172** BC optimization steps.
Global batch size 256, with 128 per GPU on two GPUs, BC learning rate **1e-4**, and fixed entry into PPO at the end of the fourth epoch.

| BC epoch | Training NLL | Validation NLL |
| --- | ---: | ---: |
| 1 | 0.24846 | 0.18116 |
| 2 | 0.14699 | 0.14998 |
| 3 | 0.12513 | 0.13184 |
| 4 | 0.11233 | 0.12245 |

Demonstrates coverage of source replay for both sides across all phases, with preparation process not filtered by win/loss or cash labels.
This is not limited to learning data from the top-ranked or winning positions. Subsequent script replacements, self-play, and PFSP all involve PPO opponent changes, and no new BC dates have been added to this run; the data from 09-06 to 09-08 used by another small model league does not belong to this run.

**Cache Status:** The original encoding list `outputs/datasets/grounded-v2-20260903-07/manifest.json`
and its feature cache are no longer present in the original path. Its registered SHA256 remains
`789bcd28991222a9b98e04c969be4ba5b4fff97c61dc4ad6a2d51be4cf05c953`, consistent with the BC ledger.
This verification included the original ZIP, original archived configuration/group codes, and training consumption records. No claims were made regarding re-validation of missing feature arrays or line-by-line re-encoding. Continuing PPO can directly use the saved BC endpoint and final complete checkpoint;
when re-running BC, re-encoding must be performed from the preserved original replay.

See [Original Five-Day Source List](../data/external/kaggriculture-episodes-2026-09-03_2026-09-07/raw/manifest.json),
[Archived Configuration and Source Verification](../outputs/analysis/context-stop-20260910/bc-provenance.json),
[Game-by-Game Group Reconstruction](../outputs/analysis/context-stop-20260910/bc-partition-reconstruction.json) and
[Original Data Preparation Record](learning_20m_proposal.md#section-7227fe909594).

## Analysis Boundaries of Initial Solidification

The current PPO's BC retention coefficient is **0**, with the most recent metric `bc_retention_loss=0`.
The BC might persist due to initialization bias, but existing evidence cannot distinguish between initialization bias, subsequent RL convergence, insufficient coverage of the historical pool, and the influence of reasonable repeated opening patterns under identical initial conditions.
The source statistics confirm the data window and coverage range; it does not measure the frequency of opening strategy types, and thus cannot assert that a specific date or player's template caused fixation.

The actual reward at termination remains `sign(own cash - opponent cash) + own cash / 10000`,
the actual learning rate of the Actor is `3.75e-6`. These are conditions that should be recorded in subsequent controlled experiments,
this termination did not alter the reward, exploration, model architecture, or training ratios.

Need to continue the original runtime, use the archive recovery entry, do not re-BC:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-20260908-s62001
```
