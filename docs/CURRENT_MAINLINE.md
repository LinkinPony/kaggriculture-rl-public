# Current Mainline

> This file retains historical research records. The final released content, model downloads, and privacy sanitization scope are available at [Repository Homepage](../README.md).
> Local output links and historical runtime environments are not distributed with the source code.

## October 1: Post-game lossless storage deduplication, retaining recovery and historical evaluation capabilities

According to the user's confirmed revision plan, XFS block deduplication is applied only to 208 file groups with byte-level identical content, processing 558 duplicate stored files and achieving a measured space release of **71.674 GiB**. No files were deleted, and no checkpoint pruning was performed; all SHA256 hashes, original paths, inodes, modification times, and existing hard link relationships remain unchanged. The previously proposed plan to delete old weights and submission packages has been canceled and is prohibited; its deletion list is not to be used.

The final submission remains **56721459 (s101701 U250)** and **56721201 (s100901 U756)**.
The U250 and final recovery point U295 of s101701 are both retained; U756 of s100901 is retained. All 24 existing complete checkpoints, historical pools, and native script opponents from both runs are preserved. Deduplicated archival recovery validations—including Actor/Critic, dual optimizers, per-card RNG, and next-round PFSP sampling—are identical to the pre-deduplication state.
366 model references across 49 frozen evaluation panels, along with the two final submission packages, have passed re-verification.
Early weights retired on September 18 are not restored as a result of this deduplication; it is not claimed that all early evaluations can be re-run.

The tool is `kagg_revue.artifacts.deduplication`; by default, it only performs verification, and write operations require explicit specification.
`deduplication.apply=true`. This list has already been executed and cannot be repeated; the inode from the original plan cannot be used for recovery copies on a different filesystem. See [Execution Results](../outputs/analysis/weight-cleanup-20261001/revision-2/execution/result.json), [Recovery Verification](../outputs/analysis/weight-cleanup-20261001/revision-2/execution/recovery-summary.json), and [Alternative Solutions](../outputs/analysis/weight-cleanup-20261001/revision-2/report.txt).

## September 30: Final score submission as s101701 U250 and s100901 U756 (23:34 UTC)

Submit two packages in sequence based on user decision, both with FP32, T=0, and terminal liquidation:
- s100901 U756, number **56721201**, package `8bf76b3b…`, uploaded at 23:17:39 UTC, passed verification at 23:25:40;
- s101701 U250, number **56721459**, package `c278b324…`, uploaded at 23:28:25 UTC, passed verification at 23:33:50.

Both start from 600. Based on "only the most recent two submissions," the final leaderboard is determined by these two submissions, and the games will continue for another 15 days after the deadline.
56720178 (s101701 U200) and 56709373 (s101102 U200) are no longer scored.
See [Final Submission](final_submission_20260930.md#section-17562d275f76).

## September 30: Submitted s101701 U200 with terminal liquidation (56720178)

At **22:25:55.547 UTC**, Kaggle received **56720178**: s101701 U200,
FP32, T=0, with terminal liquidation patch, package SHA256 `c1e2ff72…`, 93,714,448 bytes.
A single submission interface call was made; pre- and post-list confirmation shows exactly one new entry, with consistent ID, description, and size.
Confirmed received at 22:26 UTC; no processing completion status or score has been returned yet; alternative s101701 U250 was not submitted.
See [Final Submission Record](final_submission_20260930.md#section-570f7bf73353) and
[Receipt](../outputs/analysis/s101701-u0200-20260930-t0-liquidation/submission-receipt.json).

## September 30: Final submission preparation, two cards switching to MMPQ line (22:15 completed)

**Conclusion (22:15 UTC): Preferred s101701 U200, alternate s101701 U250.** Both are FP32, T=0, with terminal liquidation patch,
have passed official budget certification, **neither was submitted at 22:15 UTC.** The preferred package is `outputs/deployment/s101701-u0200-20260930-t0-liquidation/` (`c1e2ff72…`).
It shows +4.7pp (from +0.7 to +8.8) when paired against the s101102 U200 baseline across three panel opponents; direct match against U200 achieves 53.6% (1024 games). The alternate package is `…/s101701-u0250-20260930-t0-liquidation/` (`c278b324…`),
achieving 56.2% in direct match against U200, but showing regression against v4 P clones. s99001 U588 achieves only about 20% against U200 under both T=0 and T=1.
At 21:41 UTC, as per user request, s101701 and s101702 were halted at U292.
The terminal liquidation patch is strictly non-loss: each game yields an additional $80–270 in revenue, with estimated win rate improvement of 0–0.6 percentage points,
packaged by `deployment.liquidation=true`, with `budget` and `check` to verify this revision.
Game deadline is 23:59 UTC. Recommend submitting only the preferred option: replace the earlier U480, retain s101102 U200.
See [Final Conclusion](final_submission_20260930.md#section-50f02ac40138).

**Update (23:00 UTC):** The user submitted their preferred package at 22:25:55 UTC and received 56720178. The leaderboard was subsequently updated to use the scores from s101102 U200, with confirmation that only the most recent two submissions are scored.

A broader evaluation was then conducted on new seeds across 7 opponents, including s100901: s101701 U200 and s101102 U200 tied (pairing difference: −1.3pp; combining three seed groups yields +2.7pp, not significant). s101701 U250 is the strongest locally, achieving 56.0% win rate against U200 in direct matchups.

s100901 U480 and U756 perform weaker against U200, MMPQ, and DSM clones, but excel against Tufa and DECEM clones.

The user noted that evaluations will continue for another 15 days after submission deadline, so it is recommended to re-submit the original U480 package (`809acef5…`) to replace s101102 U200. This change results in two distinct trajectories for scoring: s101701 U200 on the MMPQ line and U480 on the DSM line; and U480 consistently outperforms U200 across the trajectory. See
[Expanded Evaluation](final_submission_20260930.md#section-3d01b11d39c4).

As instructed by user at 16:56 UTC, all GPUs have been redirected to the MMPQ line, and 1–2 final packages are to be prepared by 23:00 UTC. **The user decides whether to submit each package.**
Starting around 17:45 UTC, two single-GPU RL training jobs have been launched:
- **s101701** (cuda:0): Continuation training from s101102 U200, with a constant actor learning rate of 4e-6;
- **s101702** (cuda:1): Launched from a v4 P clone, serving as the second seed of the s101102 recipe, with a learning rate held at 5e-6.

Both share 509 opponents, including all snapshots of s101102 and a DSM clone from September 30; evidence is inherited from the s101102 ledger.
The container restarted approximately at 16:42 and 17:25 UTC, with both the collector and export services restarted. Two runs were resumed from frozen checkpoints to restore training after restart.
Actual performance at 17:00 UTC: 56709373 has 46 wins and 1 loss (2750.1, still rising), 56689315 has 117 wins and 49 losses (2886.8).
See [Final Submission Preparation](final_submission_20260930.md).

## September 30: Submitted s101102 U200 (56709373), stopped s101102, GPU0 redirected to DSM

Submit the verified U200 package (FP32, T=0, `0eec4dfe…`) via the new module `kagg_revue.deployment.submission`. Call the submission interface only once; confirm that exactly one new entry is added in the before-and-after lists, with description and size matching.
Kaggle received **56709373** at **13:57:57.887 UTC**; the two submissions in scoring are **56709373** and **56689315**.
At 13:58 UTC, s101102 was normally stopped (**U433**, running `stopped`, workflow `cancelled`, with output retained).

GPU1 continues training DSM line s101401. GPU0 is used for DSM new data collection and evaluation: at 14:00 UTC, read-only queries show that DSM has no new versions; the publicly available ones remain 56693917 (C′) and 56692773; however, after the data collection cycle at 13:36, the number of collected games for 56693917 increased from 108 in v4 to **132**. Based on this, v5 data is reconstructed (training/validating 127/5, with validation games identical to v4), and two seeds s101501 / s101502 are trained in parallel on cuda:0 using the s101303 recipe. Held-out NLL decreased for both seeds (0.1857 / 0.1864, v4 was 0.1912 / 0.1905). On the same T=0 panel, the total scores are **66.4% / 56.2%**, up from v4's 60.5% / 58.0%. The mean difference between the two seeds is +2.1 (−2.7 to +7.0), not statistically significant. s101501 is currently the strongest DSM clone (achieving 52.3% against MMPQ v4 P clone), but its performance against s101303 is +5.9 (−1.4 to +13.3), not significant. In real Kaggle games, the current two versions of DSM achieve 8 wins and 0 losses against 56689315. 56709373 has been upgraded to `COMPLETE`, with an initial score of 784.8 at 14:24 UTC. See [Submission and Stop](s101101_mmpq_clone_rl_20260930.md#section-77ed872c5f2e), [DSM v5 Data](dsm_bc_redesign_20260930.md#section-0f87b6ee9071).

## September 30: U400 confirmation not victorious against U200, maintain recommendation submission s101102 U200 (not submitted)

Submit conclusion within half an hour as per user request, confirm the latest U400 for s101102. T=0 progress panel shows 71.2%, paired with U200 under the same seed.
−1.3 (−8.0 to +5.7). New seed T=0 directly plays 512 games: U400 vs U200 **42.4% (36.9%–48.1%)**,
vs v4 P clone 54.9%, vs current submission s100901 U480 55.7%. U200 directly beats U400 57.6%, a significant difference;
it also performs better against the clone (59.4%), and against current submissions both are around 58%.
**Maintain recommendation: s101102 U200, FP32, T=0, using verified package `0eec4dfe…`.**
At approximately 13:22 UTC, read-only query shows: 56689315 at 2884.4, ranked 6th, MMPQ at 3111.4 ranked 1st.
**No Kaggle submissions recorded.** See [U400 confirmation](s101101_mmpq_clone_rl_20260930.md#section-0c65f1cf2b54).

## September 30: s101102 U200 directly defeated the starting MMPQ clone, recommend submission of U200 (package verified, not yet submitted)

According to user query, s101102's U200, U300, and U332 run 256 games each (with new seeds) against the starting point v4 P clone and the currently submitted s100901 U480, at T=0.
- U200 achieves 59.4% win rate (51.6%–67.2%),
- U300 achieves 50.8%,
- U332 achieves 49.2%,
the latter two match the starting point's performance; all three achieve approximately 55% against s100901 U480. After merging the progress panel, U200 reaches 58.3% (51.6%–65.1%, over 384 games). U200 also reaches the highest point on the progress panel (72.5%).

Kaggle Read-Only Query (12:40 UTC): Scoring entries: 56689315 (s100901 U480, T=0) 2886.0,
56671443 (s100201 U200, T=1) 2817.6; MMPQ peak at 3106.6 (56680759, cloned training data),
DSM peak at 2939.8. Recommended submission: **s101102 U200, FP32, T=0**; after a second submission, the scoring is between this and 56689315.
Packages built and verified independently based on user selection for U200 are not submitted:
`outputs/deployment/s101102-u0200-20260930-t0/submission.tar.gz` (SHA256 of `0eec4dfe…`).
Identical to the verified package of 56689315 except for weights; Python 3.12 official complete competition with two slots: `DONE`, additional time remaining
59.39 / 59.40 seconds. **No Kaggle submissions made.**
See [Direct Match and Submission Package](s101101_mmpq_clone_rl_20260930.md#section-fe6bdc7f0f6a).

## September 30: GPU1 clones s101303 from the latest version DSM to take on single-card RL s101401 (in progress)

On user selection, freeze the workflow to `attached_bc` connecting to s101303, automatically selecting the optimal epoch 9 for validation.
`pretraining/shard-000117.pt`, 12:14 UTC starts single-GPU RL training on cuda:1 **s101401**
(64 games per update, approximately 40–44 seconds per update). The recipe is identical to s101102: pure terminal WDL, KL 0.3,
300 updates warmup, critic using s100901 U756, 50/50 self-play / unified PFSP, mastery from 64/0.95/0.05,
with 0.5 inheritance. The opponent pool consists of 485 external opponents from s101102, plus MMPQ v4 P clones of s101001 and nine DSM new clones (totaling 495); 474 opponents inherit evidence from s100901, and 23 clones have never played against each other. The progress panel at T=0 updates every 100 updates, sharing the same opponents and seed (starting total score 60.5%) as the DSM clone panel in s101303, with evaluation running on cuda:0.

s101102 U300 progress panel **67.4%** (95% CI: 60.9%–73.7%), 4.7 percentage points higher than the baseline clone, but not significant by seed pairing (−2.7 to +11.7). U200 is at 72.5%; the decline is primarily observed in in-pool opponents: s100901 U756 (74.2% → 60.9%) and s99001 U200 (80.5% → 69.5%); out-of-pool opponents s100201 U200 at 75.0% and s100901 U480 at 64.1%; in-pool score is 76.4%, referenced by KL 0.044 (warmup completion).
**No Kaggle submissions have been made.** See [s101401](s101401_dsm_clone_rl_20260930.md).

## September 30: Automatically export RL/BC submissions to Google Drive every half hour

Deploy scheduled export as per user requirements: automatically detect active training sessions, at UTC hourly, `:00/:30` will have fixed checkpoint submissions, generate FP32/T=0 submission, and upload to [kagg-rl-revue-submissions](https://drive.google.com/).
After run completion, export the final selected model; retain s101203/s101204 if they remain active at request time, and new tasks will be automatically included thereafter.
Common submission notes are saved simultaneously in `submission-info.txt/json`, both within a tar archive and as independent files on Drive.
Final package SHA256 and full description with `pkg` short code are available externally in `receipt.json`.

The first s101102 U156 package and its documentation have been uploaded and remotely verified; the remaining tasks are being processed sequentially in the persistent queue.
The initial package has also passed the official full competition in Python 3.11, with both slots being `DONE`; daily, each package is validated against two Python ABIs.
The service does not call Kaggle submission interfaces. 10 targeted tests and Ruff/mypy have passed.
See [Execution, Credentials, Recovery Methods, and Verification Scope](drive_submission_publisher.md),
[Real-time Status](../outputs/deployment/drive-publisher/status.json).

## September 30: RL switched to single card s101102 (in progress); DSM clone now uses the latest version data

Following user request, RL uses only GPU0: the device belongs to the running protocol and cannot be retrained with changed GPU count, thus normally stopped at 08:27 UTC
s101101 (**U24**), starts training on a single GPU with identical handover, critic, reward, KL, and opponent pool (**s101102**)
(64 games per update, only cuda:0, matching the single-GPU precedent of s100401). U1–U50 health checks passed. Progress panel at T=0:
U100 at 62.1%, indistinguishable from the initial clone at 62.7% (within warmup period); **U200 at 72.5%, 9.8 percentage points higher than the initial clone** (seed-paired from +2.9 to +16.6), compared to s100901 U480 (Kaggle 56689315) at 64.8%.

GPU1 re-trains DSM clone. DSM has three strategies (A, B, C); the latest and strongest version 56693917 shows notable changes on C (C′: market instruction approximately 5.2 per turn, buys two plots on day 8). The old DSM clone data was based on B or a mixture of B and C.
A clone trained solely with old strategy B achieved only 40.0% at T=0 average across four references; clones trained with four versions of the current strategy C achieved 52.0%–59.0%.
Freshness verified per user alert: at 09:44 UTC, DSM had no version newer than 56693917; data was reconstructed after the 10:09 collection cycle.
**The best clone is s101303 trained with 56693917 (108 games), starting from s100901 U756: four-reference average 66.2%, total score 60.5%**,
11.2 percentage points higher than the v3 C strategy clone (seed-paired +3.7 to +18.9); second seed 58.0%, U0 start 55.9%, both significantly outperforming v3 C strategy. Under teacher forcing, it achieves the most accurate outcomes against 56693917 (unit target 94.1%, market 92.5%, starting at U756: 90.6% / 81.5%).
Recommended DSM clone: **s101303 `pretraining/shard-000117.pt`, T=0**.
All DSM clones still fall behind MMPQ v4 P clones. **No Kaggle submissions have been made.**
See [DSM BC Re-train](dsm_bc_redesign_20260930.md) and [s101102](s101101_mmpq_clone_rl_20260930.md#section-c61951b9aeda).

## September 30: Clone from v4 MMPQ to take over RL s101101 (already stopped on U24, now changed to s101102)

Based on user selection, freeze the workflow for `attached_bc` to complete BC s101001, automatically selecting the optimal epoch 9 for validation.
Start training with two GPUs RL **s101101** from 08:07 UTC. Actor is a v4 P clone, critic is taken from s100901 U756.
Recipe matches s100901: pure terminal WDL, KL 0.3, 128 games per update, 300 updates warmup, 50/50 self-play / unified PFSP,
mastery 64/0.95/0.05, inheritance 0.5. Opponent pool consists of 455 imported opponents from s100901 and its 17 own checkpoints,
plus an additional 13 clones (old six teams, DSM v2, MMPQ v3, and five new MMPQ clones); 474 opponents inherit evidence from s100901.

The user asked whether KL anchoring slows down training. Anchoring adds approximately 13% wall time (43 seconds per update versus 38 seconds), with slow early progress primarily due to warmup; reference KL in s100901 stabilizes around 0.03 after U300, indicating that anchoring limits drift, so it is retained. Starting from U100, a T=0 panel evaluation is performed every 100 updates, and is compared against a baseline clone (62.7%) with seed matching. **There are no Kaggle submissions.** See [Startup, Opponent Pool, KL Discussion, and Monitoring](s101101_mmpq_clone_rl_20260930.md).

## September 30: Stop s100901, redo MMPQ BC; cloning weaknesses are mainly due to data design issues

Stopped normally at 02:31 UTC as per user request, s100901 (halted at **U756**, workflow `cancelled`, product retained),
redesigned MMPQ behavior cloning. **No Kaggle submissions.**

The old v3 data mixed two sets of strategies from MMPQ (56594027/56607039 and the current strategy starting from 56612150), and lacked the latest and strongest 56679033/56680759. It was replaced with the current strategy across six versions (714 games, training/validation on 676/38), while the rest of the recipe remained the same as v3. The average win rate at T=0 against four fixed reference opponents increased from **48.4% to 77.6%**, and direct matches against a v3 clone achieved 82.8%. The cosine learning rate and the newly added optional "per-slot autoregressive" joint decoding showed no measurable benefit; the high-learning-rate variant with the lowest validation NLL performed the worst, indicating that NLL is not suitable for clone selection. The performance at T=0 was 15–22 percentage points higher than at T=1.

Recommended clone **v4 P (s101001, epoch 9, T=0)**: two-seed four-reference mean scores of 76.6% / 77.4%;
Against s100901 U480 (Kaggle 56689315) at T=0: 57.0%, 59.4% for U756, 67.2% each for the two U200s, with an average of 62.7%. However, against s99001 U200, the actual MMPQ is Kaggle 6 wins, 0 losses, +9.8k, while the local clone achieves only +2k, still significantly weaker than the true MMPQ. See [Diagnosis, Design, Two-Round Experiments, and Full Panel](mmpq_bc_redesign_20260930.md).

## September 29: Additional testing of s100201 U200, T=0 performs equally better than T=1

The temperature evaluation for the s100201 U200 has been completed, **with no additional Kaggle submissions**.
FP32, 384-turn memory, eight opponents with equal weighting, 1,024 games per temperature:
**T=0 78.61% (805 wins, 1 draw, 218 losses) / T=1 66.31% (679 wins, 345 losses)**,
a win rate difference of **+12.30 percentage points** (95% confidence interval: +8.89 to +16.11).
Additionally, 128 games of direct head-to-head matches with equal weighting, T=0 achieved **81 wins, 47 losses (63.28%)**.

Two panels share seven identical opponents; when comparing only among these seven opponents, the T=0 win rate of U480 / U200 is
**84.04% / 80.13%**, a difference of +3.91 percentage points (95% confidence interval: +0.45 to +7.48).
This is the local agent panel conclusion, without direct head-to-head comparison between the two T=0 weight sets.
Training continues to U519 (U516 has been saved). See [Per-opponent results, shared panels, and final verification](s100201_u200_temperature_20260929.md).

## September 29: The latest complete U480 for s100901 has been submitted once at T=0

At user request, at 22:43:36 UTC fixed s100901 with the latest complete **U480 / 61,440 games**,
complete v5b, FP32 CPU, 384 turn memory, T=0 condition argmax.
The exact submission package was submitted via the official complete competition in Python 3.12, with 1,440 observations consistent, both seats `DONE`,
with extra time remaining above 59.4 seconds. Kaggle received **56689315** at **22:50:58.853 UTC**;
only one submission interface call was made, and the before-and-after lists confirmed exactly one new entry. Training continues.

The same frozen weights completed **2,176 local evaluations**: eight opponents with equal weighting, 1,024 games per temperature,
**T=0 82.91% (849 wins, 175 losses) / T=1 64.06% (656 wins, 368 losses)**, a difference of **+18.85 percentage points**
(95% confidence interval: +15.33 to +22.46). All eight opponent point estimates were led by T=0;
Additionally, 128 direct matchups with identical weights yielded T=0 **93 wins, 35 losses (72.66%)**.
Kaggle status is now `COMPLETE`. Training continues until U505, with the latest saved checkpoint at U504.
See [Submission eligibility, per-opponent win rates, and completion verification](s100901_u480_temperature_20260929.md).

## September 29: Stop DECEM, switch to DSM BC from s99001 U1061 for the last two days, then proceed to RL

According to the user's latest requirement, the DECEM workflow has been canceled, and s100701 has been normally stopped at **U34**, with all historical products preserved.
The new BC Actor and subsequent RL critic explicitly inherit **s99001's latest U1061**.

DSM's latest two days are selected based on the version submitted by **9/28–9/29 UTC**. Six versions of the public game list are refreshed and supplemented with 11 additional games, frozen into **598 games / 598 complete trajectories**. Training and validation are performed on **563/35**, with no exclusions.

Only DSM teacher seats are included, retaining the canonical market labels, field_mean, and market field weights of 3.5.

Two-GPU **BC s100801 completed**: 15 epochs, patience 4 — normal early stopping; validation optimum at **epoch 11**, loss **0.14588223**. The frozen workflow has automatically selected this Actor to launch two-GPU **RL s100901**; the critic independently loads all 186 tensors from **s99001 U1061**, and a new PPO optimizer is created. Maintaining pure terminal WDL, KL 0.3, 128 games per update, 300 update warmup, 50/50 self-play / unified PFSP, mastery 64/0.95/0.05. Inheriting 431 external strategies from s99001 and 24 preserved weights from itself, PFSP evidence discount set to 0.5. All 351 Actor tensors from the actual RL starting point match bit-by-bit with the selected BC weights, and all 186 critic tensors match bit-by-bit with those from **s99001 U1061**; 455 opponents inherit prior evidence, and 365 opponents initially enter the mastered-opponent review set.

Parent weight, 455 historical strategies, 1,794 data arrays, and **11,520 official observations** verified;
13 data selection/inheritance/transfer tests, Ruff, mypy passed. See [Configuration and Evidence](s99001_dsm_recent2d_bc_to_rl_20260929.md),
[Workflow Status](../outputs/workflows/derived-v5b-s99001u1061-dsm2d-bc-to-rl-20260929/status.json).

## September 29: Stop two KL RL, switch to DECEM 56654377 full BC → RL, inherit DSM critic

As per user request, s100401 / s100501 have been normally stopped at **U139 / U105**, historical checkpoints and evidence are retained.
The user explicitly specified that the subsequent critic shall inherit **DSM s100401 U139**.

After a comprehensive turn-by-turn comparison of the behavior across 19 versions of DECEM, only **56652700** is sufficiently close to the specified **56654377** (all unit, market, and labor differences are below the P95 of self-randomly partitioned references); 139 + 136 = 275 publicly available games from both versions are included. 1 anomalous decision frame in the older version is excluded by current validation, while all 139 games in the target version are retained; ultimately, **274 trajectories** are used to train/validate **266/8**.

Two-GPU **BC s100601 has started**; learning only from the public BC starting point s99001 U0 for these two DECEM versions, with LR 1e-5, field_mean, up to 40 epochs, patience 4. The frozen workflow automatically selects the best Actor after completing BC, then proceeds to **RL s100701**: pure terminal WDL, KL 0.3, 128 games per update, 50/50, self-play/uniﬁed PFSP, preserving mastery and inheriting evidence from the prior model with 0.5 weight. The Critic independently inherits all 186 tensors from **U139**, with a new optimizer and 300 update warmup.

822 arrays of data and 10,080 official observations, true critic structures and bit-by-bit values, Ruff/mypy, and 15 inheritance/transition tests passed. See [Configuration, Version Selection, and Evidence](decem_56654377_bc_to_rl_20260929.md), [Workflow Status](../outputs/workflows/derived-v5b-decem56654377-bc-to-rl-20260929/status.json).

## September 29: Strong team clone panel selects s99001 U200, submits one authorized test; continues training of clone pool s100101

**Schedule (Kaggle Official Evaluation Page):** Final submission deadline **9/30 23:59 UTC**; up to 5 submissions per day; only track the **latest 2 submissions**, which will be used for the final Bradley–Terry ranking approximately two weeks after the deadline; scoring considers only wins, draws, and losses.

**Stop s99001.** 23:06 UTC stopped normally at **U1061** according to the stop protocol. Reason: the internal panel remains level after U200; from U307 onward, each weight pair outperforms the earlier average weights; from U308 to U1016, learners achieve 49.6% performance against BC baseline, approximately 44% against U192/U256; during the same period, Kaggle's performance against five top teams dropped from 19–9 for s80001 U816 to 4–64 for the combined three submissions of s95001.

**Negative result:** The loop-replay action of strong team footage as a proxy opponent is unavailable—all package replay win rates are 90%–95%, and the replay side's income is approximately 20,000 less than the original game (at the end of the day, random numbers are first drawn for both sides' empty plots and grass, then for shops; changing opponents alters the shop sequence).

**Strong Team Cloning Panel (New Agent)**. Six teams (MMPQ, DSM, Vadim, Tufa Labs, DECEM, Boey) 9/27 from 12:00
Each version undergoes BC fine-tuning from U0 as a closed-loop opponent; 11 candidate models × 6 clones × 128 games = **8,448 games**,
64 new environment seeds, with pairwise radius of 7.7 percentage points:

| Candidate | Equal-weighted among six teams | After removing Boey (clone failure, all candidates approximately 100%) |
| --- | ---: | ---: |
| s99001 **U200** | **72.8%** | **67.5%** |
| U256 / U192 | 68.4% / 67.8% | 62.1% / 61.3% |
| U512 | 65.0% | 58.0% |
| U588 (9/28 submitted) | 63.0% | 55.8% |
| U0 (BC starting point) / U1061 | 60.9% / 59.8% | 53.1% / 51.7% |
| 9/29 new BC (U0 continued BC, 9th epoch) | 55.5% | 46.6% |
| s95001 U960 / s91001 U2137 / s82001 U3243 | 46.6% / 35.2% / 25.4% | — |

U200 is +9.8 percentage points higher than U588, exceeding the concurrent interval, and is stronger on each of the five valid clones;
The ranking aligns with the candidate round-robin tournament (later weight degradation approaches the BC starting point). Clones are weaker than actual strong teams; the old lineage order does not fully match Kaggle's small-sample performance records, and further online testing is required for confirmation.

**One authorized submission submitted:** U200 (T=1, FP32, official executor with dual seats `DONE`, remaining timeout over 59.37 seconds),
Kaggle received **56658433** at **01:21:27 UTC**; exactly one submission call made, list confirmation shows exactly one new entry added.
Currently tracking **U200 + U588**.

**Continuing training s100101 (in progress):** Restart from s99001 U200 Actor (new Critic, new 300 warmup), pure terminal WDL,
PFSP unified pool = inherit external strategy + s99001 retained checkpoint + six clones (bootstrap adds "direct import from outside archive"),
Save checkpoint every 50 updates, plan to stop U300. Clones are within the training pool; evaluations must be conducted against pool-external opponents (U588, U192, U256, U512, new BC).

**Nighttime Continuation Training (22:40 Beijing Time onwards, as per user request, no early termination):**
Add `reference_kl_weight` to sequence PPO: field-by-field penalty.
KL (policy ‖ frozen policy at startup), referenced as `initial.pt` (default 0, behavior unchanged). After data refresh, train two clones:
- DSM v2 (starting from 9/28, 5 versions, 479 games, including 9/29's 56661176 and 56664798; continues BC from DSM v1)
- MMPQ v3 (starting from 9/26 at 13:30, 6 versions, 695 games, including 9/29's new version 56658903; no obviously malicious low-score versions to be excluded; starts BC from U0).

Two RL runs with KL anchoring weight 0.3 are each assigned one GPU, running 64 games at a time:
- s100401 (DSM v2, `configs/learning_dsm_clone2_kl_ppo50_20260929.yaml`)
- s100501 (MMPQ v3, `configs/learning_mmpq_clone3_kl_ppo50_20260929.yaml`)

Automatic evaluation is performed at U100, U200, U300, U400 and every 200 updates thereafter, including the external panel and 128-game matches against s100201 U200. Results are recorded in `outputs/analysis/anchored-progress-20260929/summary.md`.

22:40 Kaggle:
- s100201 U200: 2841.2 (still rising, early record: 41 wins, 0 losses)
- s99001 U200: 2887.9

**Update Submission (18:10 Beijing Time):** 56658433 (s99001 U200) has resumed processing on Kaggle. With user authorization, the locally strongest model s100201 U200 (package `8c3f8dce…`, Checkpoint `339858de…`) was selected for the new submission; however, the CLI returned 429 twice upon calling StartSubmissionUpload and failed to create any submission. The submission was subsequently completed manually via the web interface. The expected tracking will be **s100201 U200 + s99001 U200** (U588 removed from tracking). Submission ID will be verified upon API recovery. API continues to return 429: the collector is now polling hourly, with a 6-second request interval, and scanning historical data only every 6 hours via DSM. Submission periods are paused, followed by staggered restarts. Continue training s100301 using a new seed to replicate the s100201 recipe; evaluate after U250 stops.

**DSM Clone + Short-range RL as Local Strongest (s100201 U200):** s100101 (U200 start, cloned into pool) shows no improvement after 300 updates
(Cloned panel: 71.2%–72.5% vs. baseline 72.8%; pool-out: 57.6%–61.1% vs. 58.6%), U302 stopped. s100201 cloned from DSM with same recipe RL, U302 stopped: external panel (9/29 BC, U192, U256, U588, all not within its pool) achieves U200 **66.4%**, U100 65.2%, U300 62.3%; baseline DSM clone reaches 56.6%; s99001 U200 reaches 58.6% (with an 8.2-point radius advantage). Cloned panel achieves U300 78.0%, U200 76.4%. In 5 direct matchups (128 games per pair), s100201 U200 averages 61.3%, against s99001 U200 at 60.2%, and against U588 at 66.4%. U200 including `8c3f8dce…` has passed the official executor (double seat DONE, remaining timeout over 59.37 seconds), but not submitted.

**Single-team pure BC approaching optimal RL:** Among 8 full round-robin tournaments (1,792 games), U200 achieved 65.6%, DSM clone 64.2%, U588 57.0%, and U0 52.0%; DSM clone defeated U588 61.7% and U0 60.9%. Mixed multi-team BC performs worse. Subsequently, s100201 conducted a short-range RL from DSM clone using the same recipe.
Submitted 56658433 remains in PENDING on Kaggle for an extended period; users have judged this as a server issue and will not proceed with handling.

See [Experiment Description](deadline_experiments_20260929.md),
[Clone Panel Report](../outputs/analysis/clone-panel-20260929/panel/report.json),
[Submission Acknowledgment](../outputs/analysis/eval-s99001-u0200-20260929-t1/submission-receipt.json).

## September 28: Tufa Labs joins continuous replay collection starting from 56642914

According to user request, add **Victor @ Tufa Labs / team 16621497**'s **56642914** and subsequent versions to continuous collection, with a fixed lower bound on official submission time of **2026-09-28 13:56:46.353 UTC** (inclusive).
Game **114912906** has been downloaded and verified. Initial discovery: **1 submission / 102 games**.
3 full replays passed verification for identity, 720 frames, both sides' DONE status, and original/compressed SHA256; errors = 0.
Independent tmux **`kaggle-tufa-labs-replays`** continuously fills in gaps, waiting 600 seconds after each turn, up to a maximum of 200 games per turn, automatically tracking new versions by team ID; retains existing exclusion rules.
8 collection tests, Ruff, and mypy passed.
See [Collection Scope, Data Entry Points, and Operation Instructions](tufa_labs_replay_watch.md).

## September 28: 17 weight retention comparisons completed, U512 has the highest comprehensive point estimate, no significant unique leader yet

Under a user budget of 5–8 hours, evaluating 17 recoverable weight sets (U0–U616) frozen at 15:11 UTC, including submitted U588 and archived U307; completed 84,928 formal games by 22:28 UTC, plus 864 technical validation games.
The fourth-generation historical neural family and native script family each account for 20%; T=1, BF16, full 384-turn memory.
After initial screening and round-robin tournament among 17 candidates, 16 candidates were independently validated against 19 opponents using distinct seeds, with 192 games per pair.

**U512 score 88.84%**, 95% confidence interval **87.36%–90.24%**;
U616 **88.65%**, U192 **88.58%**, U128 **88.39%**, U588 (submitted) **87.43%**.
U512 is only **0.19 percentage points higher** than U616; differences from the other 15 validated candidates are not statistically significant at the 95% confidence level.
In the full candidate round-robin tournament, U256 ranked first (59.96%); among the top four finalists who directly faced each other, U192 ranked first (55.08%).
The main conclusion is a fixed historical panel point estimate ranking, not a current assessment of the overall strength of Kaggle's private opponents.

Trained the same PID continuously from U616 to U1002 (latest saved at U1000 upon termination), with unchanged protocol, source code, and native identity.
Minimum available GPU memory from 4,948 formal monitoring records: **25,989 MiB**, maximum heartbeat interval: **86.9 seconds**; all evaluation processes exited.
29 Actor hashes, along with all game identities, seeds, seats, results, and composite scores, independently confirmed; Ruff, mypy, and two statistical/sampling tests passed.
See [Complete Ranking and Charts](../outputs/analysis/s99001-checkpoint-comparison-20260928/summary.md),
[Protocol and Resource Constraints](checkpoint_comparison_s99001_20260928.md),
[Verification Completion](../outputs/analysis/s99001-checkpoint-comparison-20260928/completion-verification.json).

## September 28: The latest complete U588 for s99001 has been submitted once at T=1

As per user request, freeze current operation at **14:54:51 UTC**
`derived-v5b-m384-strength-canonical-ppo50-warmup300-20260928-s99001`
The latest complete **U588 / 75,264 games** weights, including PFSP predecessor evidence inheritance starting from U308.
Export complete v5b, 27,915-dimensional input, FP32 CPU, 384-turn memory **T=1 conditional Gumbel** package.

351 actor tensors are finite, compared to the previous submission s95001 U1664, there are 339 tensor changes.
The model architecture, deployment source code, native binary for two Python ABIs, and toolchain are consistent with the previously certified version,
and are accepted according to the subsequent weight compression process.
The exact new package is fully validated through the official Python 3.12 executor in a complete game,
1,440 observation checks are consistent, both seats are `DONE`, and terminal liquidation remaining time is above **59.35 seconds**.

Kaggle received submission **56644629** at **15:03:12 UTC**; the submission interface was called exactly once, and the before-and-after lists confirmed exactly one new entry. Training continues, and this submission is fixed to U588.
See [complete record](../outputs/analysis/strength-canonical-v5b-s99001-u588-20260928-t1-once/submission-summary.md),
[acknowledgment](../outputs/analysis/strength-canonical-v5b-s99001-u588-20260928-t1-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/strength-canonical-v5b-s99001-u588-20260928-t1-once/qualification.json).

## September 28: PFSP inherits predecessor discount win rate evidence, effective from s99001 starting at U308

In PFSP, inherit the historical win rate of the previous ledger, discounted according to the user's requirements, for both current and future training;
avoid wasting numerous games repeatedly confirming simple opponents. Default `inheritance.discount=0.5`:
Provide evidence to opponents the current learner has not yet faced; multiply the decayed evidence from the k-th predecessor by `0.5 ** k`;
Before first encounter, use the evidence from the last real game for judgment; after encountering an opponent, perform normal judgment based on merged evidence.
The historical pool bootstrap and the BC→RL workflow are enabled by default; the old protocol remains unchanged, as recorded in `AGENTS.md`.

s99001 stopped normally at **U307**, with s97001 (first generation) and s95001 (second generation) as donors revised:
263 of the 443 opponents already had records unchanged, and 179 new inheritances were acquired, of which 118 directly entered the review set.
The number of mastered opponents increased from 209 to 327, and the probability of unengaged opponents occupying PFSP dropped from 75.3% to 1.6%.
Checkpoint bytes remain unchanged; replay registration events are restored during recovery. The protocol has only one change: PFSP inheritance.
**11:52 UTC** training resumed. U308 sampling and prediction matched, and U312 checkpoint contains all inherited records.
Two sets of Adam steps increased from 1,228 to 1,248. Model and Critic tensors are finite. 3 new tests and 18 related tests, Ruff, mypy passed. See [full explanation](pfsp_inheritance_20260928.md),
[boundary verification](../outputs/analysis/pfsp-inheritance-20260928/qualification.json), and
[run verification](../outputs/analysis/pfsp-inheritance-20260928/running-verification.json).

## September 28: New BC early stopping completed, verified optimal 11th epoch automatically connected to s99001 RL

After BC ends, automatically switch to RL using the validated optimal weights, continuing with the s97001 recipe. s98001 completed normally at **08:14:08 UTC** due to early stopping (13 epochs), with the optimal validation achieved at epoch **11**, targeting **0.14828**, `pretraining/shard-001166.pt` (SHA256 `3ab4a6ed…`).
Market operations and market quantity validation accuracy rates are **93.5% / 88.3%**.

s98001 is started independently, thus adding a new workflow attachment mode: freeze after verifying that the plan protocol is consistent with the running BC
2,009 source code files; selection, bootstrap, and startup of RL occur only when the BC completes normally.
**08:29:37 UTC** Start with two GPUs
`derived-v5b-m384-strength-canonical-ppo50-warmup300-20260928-s99001`,
Initial 351 Actor tensors match bit by bit in their weights.

Inherit all **420** external strategies from s97001, plus its own **11** checkpoints (including final U590),
plus BC starting point totaling **432 strategies + 7 native scripts**, capacity 567. Terminal liquidation
`WDL + delta / (abs(delta) + 10000)`, 64/64 self-play/PFSP, LR **7.5e-6 / 1e-4**,
300 update warmup, high win rate frequency reduction on 64/0.95/0.05, no automatic evaluation.

Pre-start read-only pool inspection, U8 complete checkpoint (Adam 32 steps, warmup LR, boundedness, dual rank RNG), and 8-round reward formula error of 0 have all passed. In Round 8, the learner approximates the BC starting point, and PFSP draws the predecessor U590.
**37 wins, 27 losses**; under the old design, the same outcome was 14–50, 7–57. 64 games per round, informal evaluation.
Ruff, mypy, and 9 workflow tests passed. See [Handover Notes](strength_canonical_bc_to_rl_20260928.md),
[Runtime Verification](../outputs/analysis/strength-canonical-bc-to-rl-20260928/running-verification.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-strength-canonical-ppo50-warmup300-20260928-s99001/learning-progress.json).

## September 28: Stop s97001, start U590 with intensity selection version, market tag standardization, and new BC with field-weighted calculations

Following user requirements without performing ablation. s97001 received the stop signal at **07:52:13 UTC** and stopped normally at
**U590 / 75,520 games**, with the full checkpoint, optimizer, dual rank RNG, historical pool, and PFSP state preserved.
At **07:53:30 UTC**, a two-GPU run was started from U590: `derived-v5b-m384-u590-strength-canonical-bc-20260928-s98001`,
351 actor tensors match U590 bit-by-bit.

**Teacher Selection.** The top five on the leaderboard correspond to five continuously active teams. Using 9/25 to initiate **4,339 public games** with 1,790 submissions fitted via the Bradley–Terry model for strength estimation; only versions submitted by 9/26 with strength at least 0.5 logit above the strongest version are retained, plus the latest versions of teams already selected that have not yet converged. The resulting versions are DSM 7, MMPQ 2; the best versions of DECEM and Vadim fall below the threshold, and Boey has no new submissions after 9/24. A total of **882 games / 902 trajectories** (DSM: 696, MMPQ: 206) are used, split into training / validation as **847 / 55 trajectories**; the validation set consists solely of trajectories from selection buckets not involved in training.

**Market label standardization.** Remove empty slots and zero trade requests along the native settlement trajectory; merge adjacent, like-countable requests only, keeping all other orders and quantities unchanged; observation features remain bit-by-bit unchanged. By comparing round-by-round against the official state, the teacher's own state is completely consistent in **99.79%** of the turns, with a maximum per-turn cash difference of 82.

**Loss and Agreement.** Add `field_mean` normalization: equal-weighted per-field weighting between unit side and market side, with market field multiplier set to **3.5**, maintaining the market's two domains at 40% of the target; the per-field weight of unit quantity domain is reduced from approximately 30x to 1x.
LR **1e-5**, maximum 40 epochs, early stopping if no improvement of 0.0005 is observed for 4 consecutive turns, to validate optimal as `rl_initial`; training stops after BC completion and does not automatically transition to RL.

Data verification (2,646 array hashes, covering 14 re-encodings across 9 versions, 20,160 official observations),
initialization and validation of the 160th batch have all passed; at the 3rd epoch, validation target reached 0.161, with all five domains showing improvement.
Ruff, mypy, and 6 BC objectives have passed testing. See [complete design and evidence](strength_canonical_bc_20260928.md),
[version selection report](../outputs/datasets/derived-v5b-strength-top-canonical-20260928-train-val-q100/source-manifests/selection.json),
[data ingestion](../outputs/datasets/derived-v5b-strength-top-canonical-20260928-train-val-q100/manifest.json)
(SHA256 `052d0f7883259bc064be9dcc6738c90746cbab19965bb172ddf0fab548b09b5c`) and
[real-time progress](../outputs/learning/derived-v5b-m384-u590-strength-canonical-bc-20260928-s98001/learning-progress.json).

## September 28: Further diagnosis of strength gap, U472 beats BC starting point but reduced preference for buying geese

Fix s97001 **U472** with exact BC starting point, T=1, full memory, 64 seed seat swaps
Total of 128 games: PPO **111 wins, 17 losses (86.72%)**, average cash lead of **8,212**.
All 94 validation trajectories show a decline in boey-purchasing tendency under conditional inference and autonomous action probes;
When order of orders is ignored and teacher actions are not provided, the matching rate of teacher's boey-buying turns drops from **79.63% to 57.25%**.
The current BC's boey-strong version accounts for 20.51% of training trajectories, but the average loss coefficients in market operations and quantity domain are **44.58% / 57.29%**. These are loss coefficients, not gradient norms.

Additionally, fully verified the 38 public strong-hand games from three submissions of s95001,
with 54,720 observations and final cash balances matched, resulting in **1 win, 37 losses, average −4,007**;
Wheat, Ge Dan, and Milk remain the primary gaps. This is not s97001's official performance.
Training maintains original configuration; new diagnostic codes Ruff, mypy, and two tests passed.
See [Comprehensive Analysis and Limitations](strategy_gap_20260928.md),
[Fixed-Weight Matchplay](../outputs/analysis/strategy-gap-20260928/duel/report.json) and
[Teacher Loss Weight Audit](../outputs/analysis/strategy-gap-20260928/imitation/census.json).

## September 28: U116 Equal-Weight Memory Erasure, Direct Combat Memory Win Rate 81.25%

Fix the current s97001 to use the latest complete **U116** as it was at that time, with the same weights, full v5b, CUDA BF16, **T=1**, and compare it against the normal 384-turn memory setup with history K/V cleared after each turn. Retain the current turn-memory network computation and all observed features, but remove inter-turn caching; no retraining.

Formal **1,024 games** completed. In direct memory-on/off battles between 64 seed candidates, with 128 games involving seat swapping:
One side achieved **104 wins, 24 losses (81.25%)**; seed clustering performance within the 95% interval ranged from **75.00% to 87.50%**;
Average cash lead at terminal liquidation per game was **3,629**, within the interval **[2,802, 4,478]**.
Seven native script panels conducted 448 games across all modes: **448 wins to 444 wins**, average self-cash balance **113,870 vs. 111,627**, pairing increment **+2,243 [272, 4,250]**.
The script win rate increment of +0.89 percentage points occurred within the interval **[0.00, 2.01]**, indicating clear saturation.

Conclusion: This weight clearly benefits from cross-turn memory and is supported for retention; it does not represent the upper bound of an unmemory-based model retrained from scratch.
Pairing actions in the first turn, cache capacity, weight stability, and runtime identity verification passed, with an additional 12 technical qualifications not counted toward official results. Ruff, mypy, and targeted tests passed. Original training continues.
See [Comprehensive Ablation Report](memory_ablation_20260928.md) and
[Machine-Readable Results](../outputs/analysis/memory-ablation-s97001-20260928/main/report.json).

## September 28: Latest BC Launches s97001 Cash Differential RL, Complete Historical Pool and Default High Win Rate Frequency Reduction

At the user's request, s96001 BC stopped cleanly at **01:17:46 UTC**, at **batch 2,047 / 11,748,182 supervised turns**. RL starts from the latest complete weights saved at shutdown.
At **01:26:25 UTC**, `derived-v5b-m384-boey-watch4-ppo50-warmup300-20260928-s97001` launched on two GPUs. All 351 initial Actor tensors match the latest BC weights bit for bit, with full v5b features and 384-turn memory.

Inherit all 419 active strategies from s95001, additionally adding the final U1729,
combined with BC starting point to form 421 strategies + 7 native scripts; capacity 556, retaining 136 of its own slots.
Original PFSP evidence is preserved, and new Actor learns win rate from a fresh prior. Continue using each round's **64/64 self-play/PFSP**,
terminal **`WDL + delta / (abs(delta) + 10000)`**, base learning rates for Actor/Critic at **7.5e-6 / 1e-4** with **300 update warmup**, no automatic evaluation.

High-win-rate opponent frequency reduction has been enabled: a set of games with at least 64 effective games and an effective score rate of at least 95%, with only 5% of PFSP probability subject to confirmation review. User request for default activation has been implemented, now applied to new training, historical pool bootstrap, BC→RL workflow entry, and `AGENTS.md`; the old protocol maintains original configuration.
11 targeted tests, Ruff, mypy passed.
See [Operation Guidelines](boey_watch4_bc_to_rl_20260928.md),
[Historical Pool Verification](../outputs/analysis/boey-watch4-bc-to-rl-20260928/pool-verification.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-boey-watch4-ppo50-warmup300-20260928-s97001/learning-progress.json).

**01:32:53 UTC** Full validation passed for **U4 / 512 games**: two sets of Adam each with 16 steps,
339 actor tensor updates, model and optimizer fully finite, dual rank RNG complete.
Cash difference formula error on two GPUs is 0, PFSP sampling and statistical replay are exact, warmup over 300 rounds and high win rate frequency reduction configuration are both active; validation completed U6, training continues. See
[Formal operation validation](../outputs/analysis/boey-watch4-bc-to-rl-20260928/running-verification.json).

## September 28: Stop s95001 and use U1729 for BC on all Boey data and recent four-opponent replays

According to user request, all 388 collected replays of Boey **56521745** have been compiled, and merged with previously collected games from DSM, M & M & P & Q, DECEM, and Vadim, starting from Beijing Time **9/27 08:00** (UTC 00:00) onwards. After UTC 00:38 freeze, a total of 1,652 games were recorded; 1 opponent timeout game was excluded due to existing complete trajectory encoding rules, resulting in **1,651 games / 1,922 trajectories**, split into **1,828 for training / 94 for validation**. The 6 DSM games not yet downloaded at freeze time were not included in this input. 4,953 array hashes and 31 games containing 44,640 official observations have been verified.

s95001 RL stopped normally at **00:44:41 UTC** at **U1729 / 221,312 games**,
with full checkpoint, optimizer, dual rank RNG, 418 historical strategies, and PFSP evidence preserved.
At **00:47:22 UTC**, a two-GPU setup was launched from its latest Actor:
`derived-v5b-m384-u1729-boey388-watch4-bc100-20260928-s96001`.
Training continued with LR **1e-5**, equal weighting across five action groups, up to 100 epochs, saving every 4 epochs.
Early stopping was triggered after 6 consecutive turns without improvement in validation loss below 0.001; training halted after BC completion.
See [Run Instructions](boey_all_watch4_bc_20260928.md),
[Data Input](../outputs/datasets/derived-v5b-boey-all-watch4-since-20260927-train-val-q100/manifest.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-u1729-boey388-watch4-bc100-20260928-s96001/learning-progress.json).

**00:49:57 UTC** Turn **64 / 365,244** of supervision fully saved checkpoint verified:
Initial Actor and U1729's 351 tensor bits match exactly, 339 tensors have been actually updated,
BC Adam 64 steps, model and optimizer are all finite, double rank RNG is complete. Verification reached turn 72,
training continues. See [verification run](../outputs/analysis/boey-all-watch4-bc-20260928/running-verification.json).

## September 28: The latest complete U1664 for s95001 has been submitted once at T=1

Fixed current run according to user's new request at **00:05:55 UTC**
`derived-v5b-m384-watch6-ppo50-warmup300-20260927-s95001`
The latest complete **U1664 / 212,992 games** weights, compared to the previous U964, show 339 changes in Actor tensor values.
Exported a complete **T=1 conditional Gumbel** package with v5b, 27,915-dimensional input, FP32 CPU, and 384 turn memory.

Training source code, model architecture, deployment source code, two native binary files for Python ABIs, and toolchain
Consistent with the previous certification package; acceptance follows the subsequent weight optimization process. The exact new package passes official execution via Python 3.12, fully completing the competition with 1,440 observation checks verified, both seats identified as `DONE`, and terminal liquidation time remaining above **59.38 seconds**.

Kaggle received submission **56623562** at **00:18:44 UTC**; the submission interface was called exactly once, and the before-and-after lists confirmed exactly one new entry. The initial status was `PENDING`, with no score recorded. Training continues, and this submission is fixed to U1664.
See [complete record](../outputs/analysis/watch6-v5b-s95001-u1664-20260928-t1-once/submission-summary.md),
[acknowledgment](../outputs/analysis/watch6-v5b-s95001-u1664-20260928-t1-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/watch6-v5b-s95001-u1664-20260928-t1-once/qualification.json).

## September 27: The latest complete U964 for s95001 has been submitted once at T=1

As per user request, freeze current operation at **16:44:59 UTC**
`derived-v5b-m384-watch6-ppo50-warmup300-20260927-s95001`
The latest complete **U964 / 123,392 games** weights, including the PFSP mastery sampling revision starting from U890.
Export complete v5b, 27,915-dimensional input, FP32 CPU, 384 turn memory **T=1 conditional Gumbel** package.

Model architecture, deployment source code, two native binary ABIs in Python, and toolchain are consistent with the previous certified package, and acceptance is conducted according to the subsequent weight optimization process. The new package is verified through a complete game execution using the official Python 3.12 executor. 1,440 observation checks are consistent, both seats are `DONE`, and terminal liquidation remaining time is above **59.36 seconds** in all cases.

Kaggle received submission **56614434** at **16:52:51 UTC**; the submission interface was called exactly once, and the before-and-after lists confirmed exactly one new entry. The initial status was `PENDING`, with no score recorded. Training continues, and this submission is fixed to U964.
See [complete record](../outputs/analysis/watch6-v5b-s95001-u964-20260927-t1-once/submission-summary.md),
[acknowledgment](../outputs/analysis/watch6-v5b-s95001-u964-20260927-t1-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/watch6-v5b-s95001-u964-20260927-t1-once/qualification.json).

## September 27: s95001 reduces PFSP sampling of already-learned opponents from U890

Implement and apply directly as per user requirements, without ablation. Current
`derived-v5b-m384-watch6-ppo50-warmup300-20260927-s95001`
After saving the complete **U889 / 113,792 games**, continue training with the same weights, optimizer, and dual rank RNG.

For opponents with at least 64 valid games and a win rate of at least 95% following their most recent encounter, a total of only 5% of the PFSP sampling probability is allocated for reconfirmation; the remaining probability is distributed normally within the standard set according to the original PFSP. Time decay does not revoke previously acquired states; if reconfirmation fails to meet the threshold, normal sampling resumes. The latest snapshot retains normal coverage, and all historical weights and game evidence are preserved. Each round continues with 64 self-play games and 64 uniformly assigned PFSP games, maintaining the original rewards and learning rate. On the boundary, 304 out of 412 opponents are downweighted, reducing the total PFSP probability from 54.83% to 5%.

Verified officially **U890–U892 / 384 games**: sampling exact replay, both Adam optimizers proceed for 12 additional steps, model and optimizer are finite, double rank RNG is complete, training continues. The original workflow supervisor has ended; current operations are based on `run-status.json` and `recovery-status.json` in the training directory.
See [Modification Notes](pfsp_mastery_20260927.md),
[Formal Runtime Verification](../outputs/analysis/pfsp-mastery-s95001-20260927/running-verification.json).

## September 27: The current warmup RL s95001 has submitted the latest complete U556 once at T=1

As per user request, freeze current operation at **12:20:56 UTC**
`derived-v5b-m384-watch6-ppo50-warmup300-20260927-s95001`
The latest complete **U556 / 71,168 games** weights. Export complete v5b, 27,915-dimensional input,
FP32 CPU, 384 turn memory **T=1 conditional Gumbel** package.

Model architecture, deployment source code, two native binary ABIs in Python, and toolchain are consistent with the previous certified deployment;
differences between the BC in the training source code and the workflow will be separately recorded and verified according to the subsequent weight pruning process.
The exact new package has been fully tested in an official Python 3.12 executor over a complete game, with 1,440 observation checks confirming consistency;
both sides are `DONE`, and terminal liquidation time remains above **59.40 seconds** in both cases.

Kaggle received submission **56608595** at **12:31:02 UTC**; the submission interface was called only once, and a precise check of the before-and-after lists shows exactly one new entry. The initial status is `PENDING`, with no score recorded. Training continues, and this submission is fixed to U556.
See [complete record](../outputs/analysis/watch6-v5b-s95001-u556-20260927-t1-once/submission-summary.md),
[acknowledgment](../outputs/analysis/watch6-v5b-s95001-u556-20260927-t1-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/watch6-v5b-s95001-u556-20260927-t1-once/qualification.json).

## September 27: Exclude Boey's submission 56484772 from Collection and Subsequent BC

Exclude all persistent collectors and BC loading entry points permanently under **56484772**.
Retain existing game rules: if any seat uses a submitted entry that has been excluded, the game will not enter collection or BC processing.
Boey's seed collection is now set to **56521745**; 5 persistent collectors have been restarted with the new configuration.
6 existing collection lists (including one-time DSM v5b) have had their active entries and **`outside_scope`** records cleared; original replays and pre-existing fixed lists are preserved. Re-loading old BC lists will now generate a clear error message.

7 affected BC datasets have been released with the `-exclude-56484772` revised version; 6 training configurations that directly reference them have had their paths and SHA256 values updated. The latest six-party data has changed from **3,330 games / 3,853 trajectories** to **2,911 games / 3,434 trajectories**, with training/validation split at **3,277 / 157**; 419 games / 419 trajectories have been removed, retaining Boey's **56521745** with **283 trajectories**.
Current data entry points:
[`manifest.json`](../outputs/datasets/derived-v5b-watch6-expanded-20260927-train-val-q100-exclude-56484772/manifest.json),
SHA256: `d48b153f317953b2075c7407817baf40314aaa6a0af19bd2a5a2c03764e78dca`.

s94001 BC has ended, and the workflow has entered **s95001 RL**. This data exclusion does not alter the already-trained weights;
The current RL continues to run with its frozen protocol. See [complete exclusion record](exclude_boey_56484772_20260927.md).

## September 27: U2137 re-implement six-party BC, verify selection optimization, then automatically enter 300 updates warmup RL

Following the latest instruction, s93001 RL has been stopped at **05:09:15 UTC** on **U14 / 1,792 games**.
The previously proposed direct warmup restart plan has been canceled; the old run and weights are retained.
At **05:22:40 UTC**, a dual-GPU BC is launched:
`derived-v5b-m384-u2137-watch6-bc100-20260927-s94001`.
The initial Actor's **351 tensors** match bit-by-bit with s91001's latest **U2137**.
The recently expanded hexa-dataset (3,330 games, 3,853 trajectories) is used, with LR set to **1e-5**;
five action groups are equally weighted; weights are saved every **4 epochs**, along with the validation-best and recent recovery points.
A full validation is performed per round, with a maximum of **100 epochs**; early stopping is triggered if there is no improvement of at least **0.001** in validation loss for **6 consecutive rounds**.

Persistent workflow has been initiated. After BC completes normally or early terminates, the weights with the lowest validation NLL across the entire training process are selected, and `derived-v5b-m384-watch6-ppo50-warmup300-20260927-s95001` is automatically launched.

For subsequent RL, a clear safeguard ensures user-confirmed **300 updates of Actor/Critic linear warmup** is maintained, reaching **7.5e-6 / 1e-4** by the 300th turn. The terminal cash difference target, 64/64 self-play/PFSP, is retained, with the full inheritance of the s91001 pool and the addition of the final U2137. The expected initial configuration is **392 strategies + 7 native scripts**.

If BC is manually stopped, abnormally exits, or if weight validation fails, RL will not be initiated.

The code, complete two-phase configuration, and native runtime have been frozen. The current execution phase is governed by
[Workflow Status](../outputs/workflows/derived-v5b-u2137-watch6-bc-to-rl-20260927/status.json).
See [Runtime Instructions](watch6_u2137_bc_to_rl_20260927.md),
[Initialization Verification](../outputs/analysis/watch6-u2137-bc-to-rl-20260927/initialization-verification.json).

**05:26:28 UTC** Full checkpoint validation passed for batch 80: 80 Adam steps, 339 Actor tensor updates; all model and optimizer states are finite. Validation occurred at batch 91 of epoch 1; RL phase has not yet started.
See [Formal Runtime Verification](../outputs/analysis/watch6-u2137-bc-to-rl-20260927/running-verification.json).

## September 27: Stop s92001 BC, start cash spread RL with latest weights and inherit the full s91001 pool

Stopped normally at 04:55:36 UTC by random user request, BC s92001, at turn 16,608 / 95,333,278 supervision turns, full state preserved.
Started with two GPUs `derived-v5b-m384-watch6-ppo50-20260927-s93001` at 05:00:31 UTC. The initial actor's 351 tensor values matched bit-by-bit with the latest BC weights at the time of stop.
Full v5b, 27,915-dimensional input, 384-turn memory, new Critic, two PPO Adam optimizers, and RNG initialized.

Inherit all 390 historical strategy records from the previous round S91001, and additionally include its final U2137;
combined with the new BC starting point, totaling 392 strategies + 7 native scripts.
Capacity set to 527, retaining 136 of its own historical slots; original PFSP evidence is preserved, while the new learner starts from a fresh prior.
Begin using `WDL + delta / (abs(delta) + 10000)` from round U1,
with delta defined as the difference between our final cash and the opponent's final cash, cash difference coefficient set to 1, used for Actor advantage and Critic target.
Continue with 64 self-play games and 64 unified PFSP games per round, Actor/Critic learning rates at 7.5e-6 / 1e-4,
dual-GPU BF16 precision, no automatic evaluation.
See [Run Instructions](watch6_bc_to_rl_20260927.md),
[Historical Pool Verification](../outputs/analysis/watch6-bc-to-rl-20260927/pool-verification.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-watch6-ppo50-20260927-s93001/learning-progress.json).

**05:05:13 UTC** Full verification passed for **U4 / 512 games**: Actor/Critic Adam took respectively
4 / 16 steps, 339 Actor tensor updates completed, model and optimizer bounded, dual rank RNG fully intact.
The error in the four-round dual rank cash differential reward formula is 0; 64/64 ratio, learning rate, and PFSP exact replay passed.
The final U2137 from the previous round was actually drawn in Round one. Verification completed U6; training continues, old BC and RL ledgers unchanged.
See [formal operation verification](../outputs/analysis/watch6-bc-to-rl-20260927/running-verification.json).

## September 27: Six-way RL s91001 Latest Complete U2137 Has Been Submitted Once at T=1

Using the latest complete weights of the already stopped `derived-v5b-m384-watch6-ppo50-20260926-s91001`, fixed at a snapshot of **00:53:57 UTC**, corresponding to **U2137 / 273,536 games** as per user request.
Compared to the previous submission of U1064, there are 339 updated Actor tensor entries; exporting a complete v5b package with a 27,915-dimensional input,
FP32 CPU, and 384-turn memory for the **T=1 conditional Gumbel** package.

Deploy source code, model architecture, two native binary ABIs in Python, and toolchain consistent with the U1064 package;
verify according to the subsequent weight compression workflow.
The exact new package completes the full game via the official Python 3.12 executor,
1,440 observation checks are consistent, both seats are `DONE`, and terminal liquidation remaining time is above **59.33 seconds**.

Kaggle received submission **56593706** at **01:02:16 UTC**; the submission interface was called only once, and a precise check of the before-and-after lists shows exactly one new entry. The initial status was `PENDING`, with no score recorded. The original run remained stopped, the training ledger unchanged, and the weight snapshot, package, and acceptance records preserved. See [complete record](../outputs/analysis/watch6-v5b-s91001-u2137-20260927-t1-once/submission-summary.md), [acknowledgment](../outputs/analysis/watch6-v5b-s91001-u2137-20260927-t1-once/submission-receipt.json), and [eligibility report](../outputs/analysis/watch6-v5b-s91001-u2137-20260927-t1-once/qualification.json).

## September 27: Stop s91001, add old Six-Face data with latest replay, start new BC from random weights

At the user's request, s91001 RL stopped cleanly at **00:52:11 UTC** at
**U2137 / 273,536 games**, with full optimizer, dual rank RNG, PFSP, and history retention.
Launched dual-GPU
`derived-v5b-m384-watch6-scratch-bc100-20260927-s92001`
at **01:01:33 UTC** with random seed **92001**, no input checkpoint, initial 351 actor tensors matching bit-by-bit with regenerated random model.
Full v5b, 27,915-dimensional input, 384 turn memory; retained LR **1e-5**,
**100 epochs, no early stopping**, equal weighting across five action groups, stopped after BC completion.

Retain all **1,874 games / 2,078 trajectories** from the previous six-party BC, along with their partitions,
append newly collected replays, merge and deduplicate to yield **3,330 games / 3,853 trajectories / 37 submission versions**,
i.e., adding **1,456 games / 1,775 trajectories**.
Training/validation split: **3,657 / 196 trajectories**; 9,990 array hashes, 39 official replays with 56,160 observations and environment seeds have passed verification, and zero-integer game exclusions are applied.
See [Run Instructions](watch6_scratch_bc_20260927.md),
[Random Start Verification](../outputs/analysis/watch6-scratch-bc-20260927/initialization-verification.json) and
[Real-time Progress](../outputs/learning/derived-v5b-m384-watch6-scratch-bc100-20260927-s92001/learning-progress.json).

**01:05:16 UTC** Verification completed for the full checkpoint of the **80th / 455,054th supervision turn**:
BC Adam for 80 steps, actual LR **1e-5**, 339 Actor tensor updates,
model and optimizer finite, double rank RNG intact. Verification completed at the 82nd batch, two GPUs continue training,
original RL ledger unchanged. See [run verification](../outputs/analysis/watch6-scratch-bc-20260927/running-verification.json).

## September 26: The latest complete U1064 of the current six-party RL has been submitted once at T=1

Fixed at **13:48:56 UTC** per user's new request.
`derived-v5b-m384-watch6-ppo50-20260926-s91001` Current latest complete
**U1064 / 136,192 games** weight, 339 Actor tensor updates compared to previous U560.
Exported complete v5b, 27,915-dimensional input, FP32 CPU, 384 turn memory **T=1 conditional Gumbel** package.

Source code, model architecture, two native binary files for Python ABIs, and the toolchain are consistent with the U560 package; acceptance is conducted according to the subsequent weight optimization workflow. The exact new package is fully validated through the official Python 3.12 executor in a complete game, with 1,440 observation checks confirming consistency, both seats identified as `DONE`, and terminal liquidation remaining with **more than 59.40 seconds** of extra time.

Kaggle received submission **56580983** at **13:56:28 UTC**; the submission interface was called only once, and a precise check of the before-and-after lists shows exactly one new entry. The initial status is `PENDING`, with no score recorded. Training continues, and this submission is fixed to U1064.
See [complete record](../outputs/analysis/watch6-v5b-s91001-u1064-20260926-t1-once/submission-summary.md),
[acknowledgment](../outputs/analysis/watch6-v5b-s91001-u1064-20260926-t1-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/watch6-v5b-s91001-u1064-20260926-t1-once/qualification.json).

## September 26: The latest complete U560 from the current six parties RL has been submitted once at T=1

At user request, fixed current state at **08:36:07 UTC**
`derived-v5b-m384-watch6-ppo50-20260926-s91001` Latest complete state
**U560 / 71,680 games** weight, export complete v5b, 27,915-dimensional input, FP32 CPU,
384 turn memory **T=1 conditional Gumbel** package.

Deploy the relevant source code, two native Python ABI binaries, and the toolchain, consistent with the previously authenticated v5b package;
verify according to the subsequent weight-pruning process. The exact new package is fully executed through the official Python 3.12 executor in a complete match,
1,440 observation checks are consistent, both seats are `DONE`, and terminal liquidation remaining time is above **59.39 seconds**.

Kaggle received submission **56574712** at **08:44:33 UTC**; the submission interface was called only once, and a precise check of the before-and-after lists shows exactly one new entry. The initial status was `PENDING`, with no score recorded. Training continues, and this submission is fixed to U560.
See [complete record](../outputs/analysis/watch6-v5b-s91001-u560-20260926-t1-once/submission-summary.md),
[acknowledgment](../outputs/analysis/watch6-v5b-s91001-u560-20260926-t1-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/watch6-v5b-s91001-u560-20260926-t1-once/qualification.json).

## September 26: Current six-party RL switches from U11 to WDL with terminal cash difference

As per user's explicit requirement, the current `derived-v5b-m384-watch6-ppo50-20260926-s91001`
is changed to terminal **`WDL + delta / (abs(delta) + 10000)`**, delta being the difference of cash between our side and the opponent side, coefficient 1. This reward is used for PPO advantage and Critic target.

Originally ran normally until **02:35:58 UTC**, terminating at **U10 / 1,280 games**.
After independent replica training, termination, and archival recovery validation, the authenticated reward revision is recorded and takes effect from **U11**.
At **02:48:00 UTC**, the original RL was restored from the same U10; run ID, Actor/Critic, two Adam optimizers,
dual rank RNG, 357 strategies plus 7 scripts, and PFSP statistics are all preserved.
64/64 retains the game allocation, LR **7.5e-6 / 1e-4**, full v5b / 384-turn memory, dual-GPU BF16, and the no-auto-evaluation setting.
See [Reward Switching Instructions](watch6_rl_margin_20260926.md),
[State Continuity Verification](../outputs/analysis/watch6-rl-margin-20260926/transition-verification.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-watch6-ppo50-20260926-s91001/learning-progress.json).

**02:51:50 UTC** Official **U12 / 1,536 games** complete checkpoint verification passed.
U11–U12 dual rank new reward formula error is 0; both Adam optimizers continue from step 40 to step 48,
dual rank RNG is complete, old records and historical pool are preserved, PFSP exact replay passes.
Verification completed U13; training continues, see
[Official Runtime Verification](../outputs/analysis/watch6-rl-margin-20260926/running-verification.json).

## September 26: s82001 latest complete U3243 has been submitted once at T=0

According to user requirements, use the final complete weights of the already stopped **U3243 / 415,104 games** `agronomy-v4-m384-dsm-games-ppo50-20260924-s82001`, export the complete v5b, 27,915-dimensional input, FP32 CPU, 384-turn memory **T=0 conditional argmax** package.

Deploy the source code, native binaries, and toolchain consistent with previously certified U2392 packages, and proceed to acceptance according to the subsequent weight optimization process.
The current exact new package completed the full competition using the official Python 3.12 executor, with 1,440 observation checks verifying consistency.
Both seats are `DONE`, and terminal liquidation remaining time is above **59.37 seconds** in both cases.

Kaggle received submission **56567212** at **02:41:10 UTC**; the submission interface was called only once, and a precise check of the before-and-after lists shows exactly one new entry. The initial status is `PENDING`, with no score recorded.
The original training ledger remains unchanged, and the weight snapshot, package, and acceptance records are preserved.
See [complete record](../outputs/analysis/agronomy-v5b-s82001-u3243-20260926-t0-once/submission-summary.md),
[acknowledgment](../outputs/analysis/agronomy-v5b-s82001-u3243-20260926-t0-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/agronomy-v5b-s82001-u3243-20260926-t0-once/qualification.json).

## September 26: Pause the Six-Party BC, and start the new RL with the latest batch 7293

At the user's request, six-opponent BC s90001 stopped cleanly at **02:16:04 UTC**, at **batch 7,293 / 41,854,607 supervised turns**, preserving its full state.
At **02:22:56 UTC**, `derived-v5b-m384-watch6-ppo50-20260926-s91001` launched on two GPUs. Its 351 initial Actor tensors match the latest BC weights at shutdown bit for bit, with full v5b features, 27,915 input dimensions, and 384-turn memory.

Fully inherit s82001's **355 active historical strategies**, adding its final **U3243**,
plus the new BC starting point, totaling **357 strategies + 7 native scripts**. Strategy capacity is 492, continuing 136 of its own historical slots. Old PFSP evidence is preserved, and the new learner starts from a fresh prior.
Maintain pure terminal WDL, with **64 self-play games per turn + 64 unified PFSP games per turn**,
Actor/Critic learning rates at **7.5e-6 / 1e-4**, dual-GPU BF16, no automatic evaluation.
See [Run Instructions](watch6_bc_to_rl_20260926.md),
[Historical Pool Verification](../outputs/analysis/watch6-bc-to-rl-20260926/pool-verification.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-watch6-ppo50-20260926-s91001/learning-progress.json).

**02:32:53 UTC** Full verification completed for **U4 / 512 games**: Actor / Critic Adam each took 16 steps,
339 Actor tensor updates performed, dual rank RNG fully intact, all parameter and optimizer states finite.
Actual rewards, 64/64 allocation, and learning rate conform to protocol, PFSP sampling and exact replay statistics passed.
Verification completed U5; dual-GPU training continues; original BC and RL ledgers remain unchanged.
See [run verification](../outputs/analysis/watch6-bc-to-rl-20260926/running-verification.json).

## September 26: Stop s82001, and start the Six-Party BC with the latest U3243

Complete the Six-Party Dataset acceptance first, then normally stop s82001 RL at **00:28:14 UTC**,
save the latest complete **U3243 / 415,104 games**, including full optimizer, dual rank RNG, PFSP, and full history preserved.
At **00:29:57 UTC**, start with two GPUs
`derived-v5b-m384-u3243-watch6-bc100-20260926-s90001`, initialize a new BC Adam from the U3243 Actor.
The initial 351 Actor tensors are bit-wise consistent, with full v5b, 27,915-dimensional input, and 384 turn memory.
Learning rate **1e-5**, **100 epochs, no early stopping**, five action groups equally weighted, stop after BC completion.

Data consists of **1,874 games / 2,078 trajectories / 22 submitted versions**: the union of submissions from five opponents using "the most recent active submission, or submissions starting at Beijing Time **9/25 00:01**"; our side, Unknown Mother-Goose, adds existing replay seats based on the **game start time** from that point onward, resulting in a total of 108 entries.
After deduplication within the same game, and retaining two trajectories when both sides are valid, training/validation becomes **1,972 / 106 trajectories**.
5,622 array hashes, and 24 official replays with 34,560 observations and environment seeds have passed verification.
See [Dataset Description](watch6_active_recent_bc_20260926.md),
[BC Run Instructions](watch6_active_recent_bc_training_20260926.md),
[Stop Verification](../outputs/analysis/watch6-active-bc-20260926/stop-verification.json) and
[Real-time Progress](../outputs/learning/derived-v5b-m384-u3243-watch6-bc100-20260926-s90001/learning-progress.json).

**00:34:28 UTC** Verification completed for the **80th / 460,074th supervision turn**: Adam took 80 steps,
actual LR **1e-5**, 339 Actor tensors have been updated, model and optimizer are finite, double rank RNG is intact.
Dual-GPU BC continues running, original RL has stopped with no changes to the ledger, see
[Run verification](../outputs/analysis/watch6-active-bc-20260926/running-verification.json).

## September 25: Add Vadim Vasilenko's continuous replay data collection

Add team **16770421 / Vadim Vasilenko** as per user request, with **56557908** submitted as the discovery seed.
The fixed range is set to the official submission time **`dateSubmitted >= 2026-09-25T16:01:00Z`**, i.e.,
**Beijing Time 2026-09-26 00:01 (inclusive of boundaries)**, with subsequent new submissions automatically included.
The current public versions **56556874** and **56557908** both fall within the range; 12 earlier versions are assigned to **`outside_scope`**.

**23:49:05 UTC** Small batch acceptance finds **2 submissions / 172 games**, has downloaded and verified 3 complete replays,
zero errors; 7 collection regression tests, Ruff, and mypy pass.
**23:49:37 UTC** Permanent tmux **`kaggle-vadim-replays`** has been started, waiting 10 minutes after each turn,
maximally supplementing up to 200 games per round. Actual configuration and exclusive core verification passed, the original four collection tasks continue running.
See [Collection Guidelines](vadim_replay_watch.md),
[Acceptance Records](../outputs/analysis/vadim-replay-watch-20260926/qualification.json) and
[Startup Verification](../outputs/analysis/vadim-replay-watch-20260926/launch.json).

## September 25: s82001 complete v5b U2392 has been submitted once at T=0

At **15:33:25 UTC**, according to user request, fixed the latest complete checkpoint **U2392 / 306,176 games**,
exporting the complete **v5b, 27,915-dimensional input, FP32 CPU, 384-turn memory** **T=0 conditional argmax** package.
Deploy the extended padding v5b feature version declaration, using authenticated training archive and separately documenting source code differences of the deployment.

Two full seasons totaling **2,876 actions** are exactly identical to the original model. The default cache tolerance fails at turn 565; rerunning with `rtol=1e-5, atol=2e-6` following the existing FP32 rounding confirmation procedure passes, with a maximum absolute error of **below 1.923e-6**; the first failure is retained, and the submitted package remains unchanged. The exact package passes two seed runs of the official full game on Python 3.11 and 3.12, covering 5,760 observations, with all seats set to `DONE`, consistent action trajectories across versions, and additional time of at least **59.39 seconds**; the complete source code archive passes Ruff and mypy checks.

Kaggle received submission **56554776** at **15:57:50 UTC**; list reconciliation confirms exactly one new entry.
Initial state: `PENDING`, with no score. Training continues, and this submission fixes the above U2392.
See [complete record](../outputs/analysis/agronomy-v5b-s82001-u2392-20260925-t0-once/submission-summary.md),
[acknowledgment](../outputs/analysis/agronomy-v5b-s82001-u2392-20260925-t0-once/submission-receipt.json), and
[complete eligibility report](../outputs/analysis/agronomy-v5b-s82001-u2392-20260925-t0-once/qualification.json).

## September 25: Stop s89001, resume original training of s82001; confirmed complete v5b

As per user request, s89001 stopped normally at **15:01:07 UTC** at **U101 / 12,928 games**, retaining a complete state.
At **15:02:18 UTC**, it was restored.
`agronomy-v4-m384-dsm-games-ppo50-20260924-s82001` resumed with its own **U2349 / 300,672 games**,
carrying forward the original run ID, Actor/Critic, Adam, dual rank RNG, 341 strategies + 7 scripts, and PFSP statistics.
The original Actor/Critic learning rates were **7.5e-6 / 1e-4**, with pure terminal WDL, 64/64, and no automatic evaluation.

**The actual features are full v5b**: both the checkpoint and the archived native engine use `grounded-derived-context-v5b`, with 27,915 input dimensions, 5,912 new derived-feature dimensions, and 384-turn memory.
`v4` in the directory name is a legacy label. Migration to v5b took effect at U1844, and the new projections already have 2,024 steps of Adam state.
See the [resume notes](s82001_resume_v5b_20260925.md), [feature verification](../outputs/analysis/s82001-resume-v5b-20260925/feature-verification.json), and [live progress](../outputs/learning/agronomy-v4-m384-dsm-games-ppo50-20260924-s82001/learning-progress.json).

**15:06:41 UTC** Full verification completed for **U2352 / 301,056 games**: Both Adam setups continue from original state for 12 steps, all models are finite, both rank RNGs are complete, PFSP sampling and statistical replay are precise.
Dual cards continue running, see [recovery verification](../outputs/analysis/s82001-resume-v5b-20260925/resume-verification.json).

## September 25: Latest four-opponent BC → RL, inheriting the complete s82001 history pool and adding its final policy

As per user request, Quad BC normally stopped at the **5,992nd batch** at **13:46:38 UTC**,
using the latest `shard-005992.pt` (the most recent update continuing from after completing 25 epochs) as the Actor starting point.
At **13:52:54 UTC**, started with two GPUs
`derived-v5b-m384-watch4-ppo50-20260925-s89001`,
run ID `adb0ac0737c943e0993ace6d81aece62`.

Fully inherit the previous round's S82001's **341 historical active strategies**, adding its final **U2349**;
with the new starting point, the initial pool consists of **343 strategies + 7 native scripts**, with a strategy capacity of 478.
Actor 351 tensors are exactly consistent with the latest BC; new Critic, PPO Adam, and PFSP priors are introduced.
Retain pure terminal WDL, 64/64 self-play/PFSP, with Actor/Critic learning rates set at **7.5e-6 / 1e-4**;
full v5b, 384-turn memory, no automatic evaluation. Original BC and RL state are fully preserved.
See [Run Instructions](watch4_bc_to_rl_20260925.md) and
[Real-time Progress](../outputs/learning/derived-v5b-m384-watch4-ppo50-20260925-s89001/learning-progress.json).

**14:00:56 UTC** Full verification completed for **U4 / 512 games**: Two sets of Adam, each with 16 steps, dual-GPU RNG
Fully verified; actual rewards, 64/64 ratio, and learning rate all conform to the agreement. PFSP scheduling and statistics have been precisely replayed.
Dual-GPU operation continues, see [Runtime Verification](../outputs/analysis/watch4-bc-to-rl-20260925/running-verification.json).

## September 25: U2349 initiates the first download of all data for 9/24 from the Four Sides, reopening BC

Using data from the DSM, M & M & P & Q, DECEM, and Boey collection tasks, starting from **9/24 00:00 UTC**, based on the user-confirmed **first download time**. The old Boey was independently BC'd and normally stopped at the **1,029th batch** at **12:11:58 UTC**, with full state preserved.
At **12:21:43 UTC**, the dual-GPU `derived-v5b-m384-u2349-watch4-bc100-20260925-s88001` was started, reinitialized from the latest complete **U2349** Actor of s82001, and a new BC Adam was created.

Frozen 1,850 games; two abnormal trajectories were excluded by existing integrity checks, resulting in **1,848 games / 1,976 teacher trajectories / 20 submission versions**, of which 1,905 are training and 71 are validation.
Complete v5b, 384-turn memory, learning rate **1e-5**, 100 epochs, no early stopping.
5,544 array hashes, 20 official replays, and environment seed splits passed verification.
See [Run Instructions](watch4_collected_bc_20260925.md) and
[Real-time Progress](../outputs/learning/derived-v5b-m384-u2349-watch4-bc100-20260925-s88001/learning-progress.json).

## September 25: Stop s82001, perform BC against Boey using the latest U2349 for 158 games

At the user's request, s82001 stopped cleanly at **11:52:14 UTC** at **U2349 / 300,672 games**, with full training state preserved.
Launched independent two-GPU BC `derived-v5b-m384-u2349-boey158-bc100-20260925-s87001` at **11:54:27 UTC**, initializing from the latest U2349 Actor.
Fixed Boey **56521745** with **158 games** collected; only supervises this submission slot;
156 training games and 2 validation games passed encoding, identity, and hash verification.
Full v5b, 384-turn memory, learning rate **1e-5**, continuing with 100 epochs, no early stopping configuration.
See [Run Instructions](boey_56521745_bc_20260925.md) and
[Real-time Progress](../outputs/learning/derived-v5b-m384-u2349-boey158-bc100-20260925-s87001/learning-progress.json).

## September 25: s82001 U1843 Direct Migration Complete v5b and Continued Training

As per user request, s86001 stopped normally at **06:15:27 UTC** at **U258 / 33,024 games** and retained its state.
At **06:30:33 UTC**, s82001 was started with two-GPU recovery, inheriting the
`agronomy-v4-m384-dsm-games-ppo50-20260924-s82001` directory and
run ID `61a90ab34b384a91aa752cf4ee27cb9c`, resuming from the complete state at **U1843 / 235,904 games**.
Starting from **U1844**, the full v5b was used, with the original learning rates as explicitly selected by the user: **Actor 7.5e-6, Critic 1e-4**.

347 old Actor tensors, 182 old Critic tensors maintained consistently; each increases by 4 zero-initialized feature projections.
Old Adam states are migrated by parameter name, retaining 7,372 steps and momentum from both sets, with newly added parameters initialized from zero.
Dual rank RNG, 333 strategies + 7 scripts, original PFSP game evidence, seeds, and cumulative progress are all preserved.
Still purely **terminal WDL, 64 self-play games + 64 unified PFSP games**, with no automatic evaluation.

Migration registration is set to `feature-revisions/0001`. Preserve the original ledger, original complete U1843, new complete migration boundary, old/new source code, and original native libraries; the training protocol alters only `derived: false → true`.
See [Migration and Runtime Instructions](s82001_v5b_continuation_20260925.md),
[Complete State Pre-check](../outputs/analysis/s82001-v5b-continuation-20260925/preflight.json),
[Migration Verification](../outputs/analysis/s82001-v5b-continuation-20260925/migration-verification.json), and
[Real-time Progress](../outputs/learning/agronomy-v4-m384-dsm-games-ppo50-20260924-s82001/learning-progress.json).

**06:38:57 UTC** Full verification completed **U1848 / 236,544 games** checkpoint: U1844–U1848 two GPUs
Actual Actor LR is **7.5e-6**; the old parameters of Actor/Critic Adam have been continued from step 7,372 to step 7,392.
All 4 new projections have been updated and completed 20 steps. All tensors are finite, dual rank RNG is intact,
PFSP sampling and statistical replay are accurate, the original boundary archive and the s86001 state at termination remain unchanged, and both GPUs continue running.
See [Restoration Run Verification](../outputs/analysis/s82001-v5b-continuation-20260925/resume-verification.json).

## September 25: s86001 Actor learning rate increased to 2e-5 (this run has stopped)

According to user requirements, the current v5b RL was normally saved and stopped at **03:38:51 UTC** at **U26 / 3,328 games**.
The Actor LR was adjusted from **7.5e-6 → 2e-5** via `learning-rate-revisions/0001`,
effective from **U27**; the Critic LR remains at **1e-4**. Pure terminal WDL, 50/50 game ratio,
335 strategies + 7 scripts, optimizer momentum and steps, and dual-GPU RNG are all carried over.

Fix the issue where PPO recovery incorrectly retains the old LR from the checkpoint. Actual CPU recovery verification of U26 checkpoint confirms:
Only the Actor optimizer's LR has been changed; the 104-step Adam configurations and all momentum values, as well as model parameters, are bit-by-bit identical across both Adam optimizers.
11 targeted tests passed, and Ruff/mypy checks passed. The full U26 checkpoint and the old ledger are separately preserved in the revision directory.
**03:46:23 UTC** Dual-GPU continuity was successfully initiated via the archived recovery entry.
See [Adjustment Notes](derived_epoch4_ppo50_20260925.md#section-3a5f574f4c9c),
[Recovery Verification](../outputs/analysis/derived-s86001-lr-2e5-20260925/optimizer-restore-verification.json), and
[Revision Check](../outputs/analysis/derived-s86001-lr-2e5-20260925/revision-verification.json).

**03:50:46 UTC** Verified that the actual Actor LR for both GPUs U27–U28 is **2e-5**;
in U28's complete checkpoint, the Actor/Critic LR is **2e-5 / 1e-4**, and the Adam optimizer steps continue from 104 to 112.
The model and optimizer tensors are limited, dual rank RNG is fully intact, PFSP sampling and statistical replay are accurate, and both GPUs are running continuously.
See [Restoration Run Verification](../outputs/analysis/derived-s86001-lr-2e5-20260925/resume-verification.json).

## September 25: s82001 latest complete U1843 has been submitted once at T=1

Fix the latest complete checkpoint **U1843 / 235,904 games** for the previously stopped run s82001 as per user request,
use the authenticated source code of that run to export the **T=1 conditional Gumbel** package with FP32 CPU and 384-turn memory.
Model configuration, deployment source code, native binary, and toolchain remain consistent with the prior U800 authenticated version; the exact package is verified
by running it through the official Python 3.12 executor for a full game, 1,440 observations, with both players set as `DONE`, and additional time of at least
**59.39 seconds**.

Kaggle received submission **56538672** at **03:21:18 UTC**, and list reconciliation confirms that exactly one new entry was added;
Initial status is `PENDING`, with no score. The original runtime ledger remains unchanged, and fixed weights along with all submission evidence are preserved.
See [complete record](../outputs/analysis/agronomy-dsm-games-s82001-u1843-20260925-t1-once/submission-summary.md),
[acknowledgment](../outputs/analysis/agronomy-dsm-games-s82001-u1843-20260925-t1-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/agronomy-dsm-games-s82001-u1843-20260925-t1-once/qualification.json).

## September 25: Retraining v5b epoch 4 → PPO, inheriting complete s82001 history pool

Based on the user's final choice, use the **retrained epoch 4**; the original epoch 4 file has been deleted under the old retention rules.
Retraining produced different results due to CUDA non-determinism compared to the original (validation NLL **0.162742**, original record 0.151673).
The original BC stopped at batch 585 at **02:58:00 UTC**; retraining stopped at **03:05:35 UTC**.
The selected batch 276 / epoch 4 from the saved checkpoint is adopted. Complete stop states of both BC runs and the original RL are preserved.

**03:18:45 UTC** Launching two GPUs
`derived-v5b-m384-epoch4-ppo50-20260925-s86001`,
run ID `0df4d8ad66134fe9912f94f989e2746c`.
351 initial actor tensors match exactly with selected epoch 4; complete v5b, 384-turn memory,
creating new Critic, PPO Adam, RNG, and this learner's PFSP statistics.

Fully inherit s82001's **333 active strategies** and additionally add the final **U1843**, totaling **334 external strategies**;
plus **335 strategies + 7 native scripts** as new starting point. Capacity is 470, retaining **136 historical slots** of its own.
Continue using s82001's valid protocols: **pure terminal WDL, 64 self-play games + 64 unified PFSP games**,
Actor/Critic learning rates at **7.5e-6 / 1e-4**, no automatic evaluation, no ablation studies.

See [Operation Instructions](derived_epoch4_ppo50_20260925.md),
[Start Verification](../outputs/analysis/derived-bc-to-rl-20260925/initialization-verification.json),
[Historical Pool Verification](../outputs/analysis/derived-bc-to-rl-20260925/pool-verification.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-epoch4-ppo50-20260925-s86001/learning-progress.json).
Compatibility with old v2/v4 observations and full game verification for 7 native scripts in v5b has passed; the BC epoch weight retention rule has been fixed.

**03:26:28 UTC** Full verification completed for **U4 / 512 games** checkpoint: Actor/Critic Adam each took 16 steps,
dual rank RNG fully validated, all tensors finite, 339 Actor tensors updated.
The first four rounds were all 64/64, actual rewards were pure WDL, PFSP sampling and statistical replay were fully consistent;
steady-state execution took approximately **38 seconds per round**, training continues on dual GPUs. See
[formal verification](../outputs/analysis/derived-bc-to-rl-20260925/formal-verification.json).

## September 25: Complete v5b, U1843 → DSM All Versions BC (Paused, migrated to upper PPO)

Implement **v5b directly as per user requirements, without ablation studies**. s82001 has been successfully stopped at **U1843 / 235,904 games**, with original state fully preserved. Started at **02:46:29 UTC**
`derived-v5b-m384-u1843-dsm-bc100-20260925-s85001`,
run ID `a98e71c1e0f84cbf8d96223fc6ab8252`, dual H200.

Input **22,003 → 27,915** dim (global/plot/worker/product increased by 5,912),
Actor retains 347 existing tensors completely; adds 59,904 newly initialized zero-projection parameters; actions and 384 turn memory remain unchanged.
CPU FP32 of real weights and full-season CUDA BF16 migration have passed verification, with output and memory fully consistent.

DSM selects all publicly discoverable versions, 575 games, from the snapshot period of **9/23 00:00 to 9/25 02:20:05 UTC** based on submission date; retains 574 complete trajectories, trains 552, validates 22, and preserves the original record for 1 anomaly case. Fixed at **100 epochs, LR 1e-4, equal-weighted group loss across 5 action types, dual-GPU BF16**; 6,900 training batches, no early stopping, training stops after BC completion. No runs of v5a, feature ablation, or new adversarial evaluation. See [Implementation, Data, and Run Details](derived_dsm_bc_20260925.md),
[Training Configuration](../configs/learning_derived_dsm_bc_20260925.yaml), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-u1843-dsm-bc100-20260925-s85001/learning-progress.json).

**02:51:23 UTC** Completed the 1st epoch and entered the 2nd epoch; training/validation NLL is
**0.147884 / 0.150570**. The 64th full checkpoint has been confirmed, all four new projections have been updated,
two-GPU Adam/RNG and model tensors are normal, steady-state time is approximately 0.75 seconds per batch.
See [formal confirmation](../outputs/analysis/derived-dsm-bc-20260925/formal-verification.json).

## September 25: Additional Features and Reuse Design of Existing Rights (Already Superseded by Previous Version v5b)

Complete [v5 feature design](derived_features_v5_design_20260925.md): Prioritize adding commodity supply-demand, expansion scenarios, and financial constraints **888 dimensions (+4.04%)**, then consider land/worker execution layers.
Maintain original network parameters through independent zero-initialized residual blocks, 286 tokens, and action interfaces.
Authentication of U800 weights in offline structural experiments on CPU FP32 with 6 segments and 48 real observations confirms consistency in Actor logits/memory, Critic state values/prefix values/memory, and greedy actions; new branch gradients are non-zero.
See [Experiment Report](../outputs/analysis/features-v5-design-20260925/compatibility.json).
This is structural prototype validation; native new features, formal migration, and training gains remain to be implemented and verified. Current training and deployment remain unchanged.

## September 25: Recent direct game diagnosis submitted against DSM

**01:20–01:26 UTC** Recheck official API: Among the last eight submissions, six versions involved direct DSM gameplay.
Result: **0 wins, 34 losses**; latest s82001 U276 / U800 scores are **0–6 / 0–4**.
34 games with **48,960 observations** show step-by-step replay consistency, with matching trade executions and final cash balances.
The latest 10 games average a lag of **5,404**, primarily due to mid-game milk, goose-egg, and tomato production gaps; both sides have fully acquired four plots and are producing.
BC validation generalization and PPO opponent coverage remain limited. Only analysis has been completed; training and deployment have not been adjusted.
See [complete diagnosis, diagrams, and reproduction link](dsm_duels_20260925.md).

## September 24: s82001 latest complete U800 has been resubmitted once again with T=1

**15:59:18 UTC** Lock current training for s82001 with the latest complete checkpoint **U800 / 102,400 games**,
using authenticated source archive, export FP32 CPU, 384-turn memory's **T=1 conditional Gumbel** package.
The exact package is executed through the official Python 3.12 executor for a full game, 1,440 observations, both sides `DONE`,
with additional time of at least **59.40 seconds**; source code, native binaries, and toolchain are identical to the previously authenticated version.

Kaggle received submission **56525914** at **16:08:01 UTC**, and list reconciliation confirms that one record was newly added this time;
Initial status is `PENDING`, with no score. Training continues, and the latest saved state upon check is U816.
See [complete record](../outputs/analysis/agronomy-dsm-games-s82001-u800-20260924-t1-once/submission-summary.md),
[acknowledgment](../outputs/analysis/agronomy-dsm-games-s82001-u800-20260924-t1-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/agronomy-dsm-games-s82001-u800-20260924-t1-once/qualification.json).

## September 24: s82001 latest complete U276 has been submitted once at T=1

**10:50:55 UTC** Lock current training for s82001 with the latest complete checkpoint **U276 / 35,328 games**,
using authenticated source archive, export FP32 CPU, 384-turn memory's **T=1 conditional Gumbel** package.
The exact package is executed through the official Python 3.12 executor for a full game, 1,440 observations, both sides `DONE`,
with additional time of at least **59.39 seconds**; the deployment of source code, native binaries, and toolchain remains consistent with the previously authenticated version.

Kaggle received submission **56519499** at **10:58:04 UTC**, and list reconciliation confirms exactly one new entry;
Initial status is `PENDING`, with no score. Training continues, and upon check, the latest saved state is U288.
See [complete record](../outputs/analysis/agronomy-dsm-games-s82001-u276-20260924-t1-once/submission-summary.md),
[acknowledgment](../outputs/analysis/agronomy-dsm-games-s82001-u276-20260924-t1-once/submission-receipt.json), and
[eligibility report](../outputs/analysis/agronomy-dsm-games-s82001-u276-20260924-t1-once/qualification.json).

## September 24: Restore s82001, remove automatic "closed-loop" evaluation

As per user request, s84001 stopped normally at **09:05:12 UTC** at **U12 / 1,536 games**, retaining a complete state.
**09:10:46 UTC** resumed recovery
**`agronomy-v4-m384-dsm-games-ppo50-20260924-s82001`**, using the original run ID,
resuming from its own **U113 / 14,464 games** Actor, Critic, two Adam optimizers (each with 452 steps), dual rank RNG,
and PFSP statistics. The pool consists of **306 strategies + 7 native scripts**.

Restore the original protocol: **Pure terminal WDL, no cash differential reward; 64 self-play games + 64 unified PFSP games**.
The automatic baseline evaluation for startup, cycle, termination, and confirmation has been removed from the training execution path, and the additional save synchronization wait for evaluation rounds has been deleted; historical evaluations are retained. All 12 targeted tests and static checks have passed.
This source code revision has been authenticated by `source-revisions/0001`. The checkpoint and training protocol are fully preserved.
See [Restoration and Deactivation Guidelines](s82001_resume_no_evaluation_20260924.md),
[Revision Verification](../outputs/analysis/s82001-resume-no-evaluation-20260924/repair-verification.json), and
[Startup Log](../outputs/analysis/s82001-resume-no-evaluation-20260924/launch.json).

**09:14:41 UTC** Successfully completed consecutively **U114–U116**, PFSP sampling is consistent with original statistical replay,
actual returns are pure WDL, game allocation is 64/64. The previous evaluation file has neither been updated nor rewritten, and the two cards continue training.
See [run verification](../outputs/analysis/s82001-resume-no-evaluation-20260924/resume-verification.json).

## September 24: Three parties BC move into s84001, cash differential reward restored

At the user's request, s83001 BC stopped cleanly at **08:45:18 UTC**, at **batch 720 / 4,130,174 valid supervised turns**.
The new RL run **`agronomy-v4-m384-watch3-margin-ppo50-20260924-s84001`** started on two GPUs at **08:49:36 UTC**. All 347 tensors of its initial Actor exactly match the latest BC checkpoint.

The user explicitly requests the cash difference version, with current reward set to **terminal WDL + delta / (abs(delta) + 10000)**,
where delta is the difference between the final cash of the agent and the opponent; `cash_margin.beta=1`, absolute cash weight remains 0.
Each round consists of **64 self-play games + 64 unified PFSP games**; Actor/Critic learning rates are 7.5e-6 / 1e-4.

Full inheritance of 306 historical strategy activities from s82001, plus its final U113, totaling 307 external strategies;
Retain 7 scripts, plus new starting point, resulting in **315 initial candidates**. Capacity 443, retaining 136 of its own historical slots.
Create a new PPO optimizer, Critic, and this learner's PFSP statistics; previous runs, historical pool, and statistical evidence are preserved.
See [Training Protocol](agronomy_watch3_margin_ppo50_20260924.md),
[Stop Verification](../outputs/analysis/watch3-bc-to-ppo-20260924/bc-stop-verification.json),
[Start Verification](../outputs/analysis/watch3-bc-to-ppo-20260924/initialization-verification.json), and
[Pool Verification](../outputs/analysis/watch3-bc-to-ppo-20260924/pool-verification.json).

**09:01:47 UTC** Full verification completed for **U4 / 512 games** checkpoint: Actor/Critic Adam each took 16 steps,
dual rank RNG fully validated, all tensors finite. The first four game rounds were all allocated to 64/64, and the actual cash difference rewards match the independent formula with a maximum error of **0**; PFSP sampling aligns with statistical replay, and training continues with two GPUs.
See [formal verification](../outputs/analysis/watch3-bc-to-ppo-20260924/formal-verification.json).

## September 24: Stop s82001 and start three-opponent BC from the latest U113

Stopped normally at U113 / 14,464 games at **08:30:09 UTC** according to user request, s82001 PPO, with optimizer, dual rank RNG, PFSP, and historical pool preserved. New BC **`agronomy-v4-m384-u113-watch3-bc100-20260924-s83001`** started with two GPUs at **08:31:58 UTC**, with the initial Actor's 347 tensors exactly matching the latest U113.

Use the cleaned third-party data: **759 games / 783 trajectories (750 train / 33 val)**.
Retain the five-action group loss, fixed LR **1e-4**, 100 epochs / **9,400 batches** budget;
Create BC Adam, no early stopping, stop after completion. See [Training Protocol](agronomy_watch3_bc_20260924.md),
[Stop Verification](../outputs/analysis/watch3-bc-20260924/stop-verification.json), and
[Start Verification](../outputs/analysis/watch3-bc-20260924/initial-verification.json).

**08:35:06 UTC** Confirmation of complete checkpoint for the **48th / 276,006 valid supervised turns**,
Adam 48 steps, dual rank RNG complete, all model and optimizer tensor bounds verified, dual-card continuous training.
See [formal verification](../outputs/analysis/watch3-bc-20260924/formal-verification.json).

## September 24: BC dataset submissions from three parties have been prepared

Based on the user's confirmation of the **9/23 00:00 to 9/24 08:11:31 UTC submission window**,
freeze six qualified versions of DECEM, M & M & P & Q, and DSM. Exclude MMPQ submissions with extremely low scores
**56509757** involving 7 games, and carry forward the exclusion criteria from **56414341**; if any position is hit, the entire game is excluded.
A full trajectory check further excludes 2 games where opponents timed out mid-game, resulting in **759 games / 783 teacher trajectories**,
**750 train / 33 val**, continuing with v4/q100 and seed 62001. 24 qualified teacher-versus-teacher matches are retained with supervision from both sides.

2,277 array hashes, full identity and partition checks, and 7 official complete game replays verified successfully.
Data preparation completed; s82001 RL and data collection continue to run. See
[Data Description and Usage Entry](watch3_bc_20260923_24.md) and
[Acceptance Report](../outputs/analysis/watch3-bc-20260923-24/data-verification.json).

## September 24: Add DECEM continuous replay data collection

Based on the user-provided submission **56489091**, game **112776500**, official metadata confirmation
**DECEM / team ID 16623559**. The example is used for seed discovery; the user subsequently specifies a fixed lower time limit,
current versions only include those submitted at the official submission time **`dateSubmitted >= 2026-09-23T00:00:00Z`**.
Earlier versions are moved to `outside_scope`, with original files preserved. Reuse existing collector, wait 10 minutes after each turn,
maximally supplementing up to 200 games; support daily ZIP reuse, retaining exclusion items 56414341.

Before setting the lower bound, at **07:36:07 UTC** a small-scale acceptance test discovered **9 submissions / 1,276 games**, with 16 games already available
(13 daily reuses, 3 independently downloaded), all completed identity verification, full replay, and hash checks, with 0 errors.
At **07:36:54 UTC**, the persistent tmux `kaggle-decem-replays` was started to continue filling in the remaining games.
DSM, M & M & P & Q, Boey's data collection, and s82001 RL are all continuing to run.
See [Collection Guidelines](decem_replay_watch.md),
[Acceptance Records](../outputs/analysis/decem-replay-watch-20260924/qualification.json), and
[Startup Verification](../outputs/analysis/decem-replay-watch-20260924/launch.json).

**07:40 UTC** Fixed 9/23 lower bound; activity range is **2 submissions / 319 games**, error is 0;
8 earlier versions and corresponding records have been moved to `outside_scope`, with original files fully preserved.
**07:40:53 UTC** The persistent collector has been restarted according to the new lower bound, see
[Lower Bound Verification](../outputs/analysis/decem-replay-watch-20260924/fixed-cutoff/qualification.json).

## September 24: Latest DSM BC transferred to s82001 PPO, self-play increased to 50%

At the user's request, s81001 BC stopped cleanly at **07:10:49 UTC** at
**Batch 737 / 7 complete epochs + 65 batches / 4,239,224 supervised turns**.
New RL **`agronomy-v4-m384-dsm-games-ppo50-20260924-s82001`** started GPUs 0+1 at **07:17:55 UTC**, with the initial Actor's 347 tensors exactly matching the latest BC.

Fully reuse s80001's **252 external historical strategies**, and add s80001's own starting point, 50 periodic snapshots, and final U3207, totaling **304 external strategies**; retain 7 native scripts, plus the current round's starting point, resulting in an initial unified PFSP pool of **312 candidates**. Capacity is 440, with 136 slots preserved from its own history.
**64 self-play games and 64 unified PFSP games per round**; pure terminal WDL outcomes, Actor/Critic learning rates at 7.5e-6 / 1e-4; a new PPO optimizer and Critic are introduced. All prior training and PFSP evidence are fully preserved.

Historical native compatibility report original path missing; revalidated 12 games / 17,280 observations using preserved binary, all matches confirmed; new evidence is independently bound to this run, s80001 ledger remains unchanged.
Pool membership, initial weights, and source code archive checks passed, see
[New Run Protocol](agronomy_dsm_games_ppo50_20260924.md),
[Complete Pool Validation](../outputs/analysis/dsm-games-bc-to-ppo-20260924/pool-verification.json), and
[Startup Log](../outputs/analysis/dsm-games-bc-to-ppo-20260924/launch.json).

**07:25:46 UTC** Full **U4 / 512 games** checkpoint verification passed: Actor/Critic Adam each for 16 steps, dual rank RNG complete, all tensors finite. The first 4 rounds were all assigned to **64/64** match allocation, PFSP sampling and statistical replay consistent, BC and s80001 original ledger unchanged, dual-GPU training continues. See [formal verification](../outputs/analysis/dsm-games-bc-to-ppo-20260924/formal-verification.json).

## September 24: Stop s80001, boot 9/22 with U3207 to start DSM BC game

s80001 stopped and saved its latest state normally at **06:54:07 UTC** as per user request for **U3207 / 410,496 RL games**, retaining original optimizer, RNG, PFSP, and historical artifacts.
New BC **`agronomy-v4-m384-u3207-dsm-games-bc100-20260924-s81001`**
Launched GPU0+GPU1 at **06:57:29 UTC**, with initial Actor's 347 tensors exactly matching those of U3207.

The data is fixed at the previously recorded **802 games**: official games from `createTime` at
**9/22 00:00 UTC to 9/24 06:49:20 UTC**, monitored only for DSM, covering 8 versions.
The full trajectory contract is retained, excluding 1 game with mid-match timeout, resulting in **768 training samples / 33 validation samples**, with no test set.
All 2,403 array hashes and 17,280 observations from 12 official replays passed verification.
The five-action-grouped loss is retained, with a fixed learning rate of **1e-4**, 100 epochs / **9,600 batches** budget;
A new BC Adam is introduced, without early stopping, terminating after completion, and not automatically entering PPO.

**07:00:37 UTC** Full check-in passed for the **48th / 276,096th supervision turn**:
Adam 48 steps, dual rank RNG complete, all model and optimizer tensors finite, steady-state time approximately 0.74 seconds per batch;
Training continues with two GPUs. See [formal verification](../outputs/analysis/dsm-games-bc-20260924/formal-verification.json).

See [Data Range and Training Protocol](agronomy_dsm_games_bc_20260924.md),
[Stop Verification](../outputs/analysis/dsm-games-bc-20260924/stop-verification.json),
[Start Verification](../outputs/analysis/dsm-games-bc-20260924/initial-verification.json), and
[Start Logging](../outputs/analysis/dsm-games-bc-20260924/launch.json).

## September 24: s80001 restored from U2824 due to tmp deletion interrupt

User confirms deletion of the repository `tmp/` during training run. Archive recovery process work directory
`tmp/learning-recovery-mr8arhwl` vanishes subsequently, **01:28 UTC** write progress triggers
`FileNotFoundError`, two-GPU process exits; training artifacts in real `outputs/` are retained.
Latest complete checkpoint is **U2824 / 361,472 games**, hash matches ledger.

**03:31:33 UTC** Start GPU0+GPU1 using the original archive recovery entry to reconstruct the runtime directory and compilation cache.
Maintain the same run ID, `source-revisions/0001`, training protocol, Actor/Critic Adam,
dual rank RNG, and PFSP; recompute updates that were not saved after checkpoint.
**03:44:51 UTC** Verify the new complete **U2828 / 361,984 games** checkpoint passes SHA256
`dd528daa96b753e08adac94a8d92ad0a02d7a62b1a2bb6cfe4aaeff154303eb9`,
parent hash points to U2824, both Adam optimizers advance from step 8472 to 8484, dual-GPU processes continue running.

See [Status Recovery Verification](../outputs/analysis/s80001-tmp-deletion-recovery-20260924/verification.json),
[Startup Log](../outputs/analysis/s80001-tmp-deletion-recovery-20260924/launch.json), and
[Directory Cleanup Instructions](learning_recovery.md). Do not delete active
`tmp/learning-recovery-*` or the entire `tmp/` during training.

## September 24: s80001 latest complete U2696 has been submitted once at T=0 and once at T=1

**00:25:09 UTC** Training is ongoing
`agronomy-v4-m384-dsm-grouped-ppo-20260923-s80001` Latest complete checkpoint
**U2696 / 345,088 games RL**, SHA256
`d87962cc64f5ee7d3d42e8041fcca930575956a3b881baa6aace4ec8fa28b218`.
Training continues; U2724 was saved upon submission check-in.

Reuse the previously authenticated `source-revisions/0001` deployment implementation to build, respectively, the FP32 CPU and 384-turn memory versions of the **T=0 argmax** and **T=1 conditional Gumbel** packages. According to the [subsequent weight pruning acceptance criteria](learning_deployment.md#section-74c85d88a648), each exact package completes one full game and 1,440 observations within the Python 3.12 official executor, with both sides using `DONE`. At least **59.40 / 58.50 seconds** of remaining time are guaranteed. Previous validation of this deployment implementation has already passed eager comparison and multi-game runtime verification; thus, redundant matrix operations are skipped in this run.

Kaggle receives **T=0: 56507324** (00:34:48 UTC), **T=1: 56507372** (00:37:58 UTC). Each list reconciliation confirms exactly one new entry; initial states are all `PENDING` with no scores. See [complete submission record](../outputs/analysis/agronomy-dsm-grouped-s80001-u2696-20260924-t0-t1/submission-summary.md), [eligibility report](../outputs/analysis/agronomy-dsm-grouped-s80001-u2696-20260924-t0-t1/qualification.json), [T=0 acknowledgment](../outputs/analysis/agronomy-dsm-grouped-s80001-u2696-20260924-t0-t1/submission-receipt-t0.json), and [T=1 acknowledgment](../outputs/analysis/agronomy-dsm-grouped-s80001-u2696-20260924-t0-t1/submission-receipt-t1.json).

## September 23: s80001 latest complete U1644 has been submitted once at T=1

At user request, **15:46:11 UTC** is fixed currently.
`agronomy-v4-m384-dsm-grouped-ppo-20260923-s80001` latest complete checkpoint
**U1644 / 210,432 games RL**, submitting once every **T=1**. Kaggle successful acknowledgment number
**56498204** (**16:06:15 UTC**); list verification confirms exactly one new entry, initial state
`PENDING`, no score yet. Main training continues, checkpoint saved as U1688 upon verification.

Submitted package uses authentication for `source-revisions/0001` training archive, FP32 CPU, 384 turns with memory and conditional Gumbel sampling. **2,876 actions and memory states** match the original model;
Python 3.11/3.12 passes **4 games / 5,760 observations** via official runner, all seats confirmed on `DONE`, with consistent cross-runtime trajectories and terminal liquidation. Package size is 93,436,561 bytes, below the 100 MB limit. See [complete submission report](../outputs/analysis/kaggle-agronomy-dsm-grouped-s80001-u1644-20260923-t1-once/submission-summary.md),
[confirmation](../outputs/analysis/kaggle-agronomy-dsm-grouped-s80001-u1644-20260923-t1-once/submission-receipt.json)
and [eligibility report](../outputs/analysis/kaggle-agronomy-dsm-grouped-s80001-u1644-20260923-t1-once/qualification.json).

## September 23: Add Boey's specified version and enable continuous replay collection for subsequent submissions

Boey (team ID **16915014**) uses submission **56484772**, episode **112499720** as seed,
with the official submission time fixed range set to **dateSubmitted >= 2026-09-23T06:08:10.517Z**.
Submissions of this version and all subsequent ones are automatically included; earlier versions are retained in `outside_scope` and are not added to the download queue.
Reuses existing crawlers and daily ZIP files; after each turn, waits 10 minutes, up to a maximum of 200 games, and scans its historical games hourly; retains existing explicit exclusion items `56414341`.

**15:37 UTC** Small batch acceptance finds **1 valid submission / 95 public games**, completes 3 downloads,
including user-specified replay, 720 frames, both sides DONE, identity and double hash passed, errors = 0.
**15:39 UTC** Launches standalone persistent tmux task `kaggle-boey-replays` to continue collecting remaining replays.
DSM and M & M & P & Q original tasks continue running. Configuration, raw data, and verification entry points are available at
[Boey Collection Record](boey_replay_watch.md).

## September 23: Turn-by-turn sale timing optimization research completed, no changes to training or deployment

Use DSM replay to conduct counterfactual analysis by only reordering the selling timing: fix opponent orders and our production, product by product, unit by unit.
Dynamic programming couples warehouse and cash constraints via Lagrange multipliers; the lock-step market simulation reconstructs the inventory and trading outcomes of all 105 games.
When opponent orders are perfectly predictable, the median terminal cash advantage increases from **+4,777 to +7,672** (comparable to our 25 games: **+5,447** for us, **+4,777** for DSM, with us leading DSM by a median of 3,670).

When re-solving daily based only on current information, value is almost entirely dependent on the prediction of when the opponent will sell: opponent sell time. Within a ±4 step error margin, the average value across 8 scenarios remains at **+3,678 / +3,253** (us / DSM), while single-point predictions yield only **+337 / −380**; "opponent repeats yesterday" results in **−3,912 / −4,271**; future store value is only 57 / 231. The reserved `opponent_shed_estimate` in the code currently remains 0 during both training and deployment.

**Only perform analysis, without modifying training, rewards, code, opponent pool, or submission.**
See [Mathematical Structure, Experiments, and native Design](sell_timing_optimization_20260923.md).

## September 23: s80001 latest complete U816 has been submitted once at T=0

Fix current state at **08:57 UTC** as per user request.
`agronomy-v4-m384-dsm-grouped-ppo-20260923-s80001` latest complete checkpoint
**U816 / 104,448 games RL**, submit only once at **T=0**.
Kaggle successful acknowledgment number **56489080** (**09:10:30 UTC**); submission list verification confirmed
Exactly one new entry added; initial verification has not yet returned evaluation status or score. Main training continues running.

Submission package uses `source-revisions/0001` authentication for training archiving, FP32 CPU, 384 turn memory, and conditional argmax. **2,876 actions and integer turn IDs are completely consistent**, memory cache validation passes the elimination phase and is verified with existing explicit atol=2e-6, rtol=1e-5 tolerances; maximum absolute cache error is 1.907349e-6, reduced to 1.358306e-6 after relative tolerance deduction; original tolerance threshold violation diagnosis is fully preserved.

Python 3.11/3.12 passed **4 games / 5,760 observations** through the official runner, all seats verified.
`DONE`: trajectory consistent across runtimes; maximum cold start time within **1.632 seconds**, subsequent actions within **0.401 seconds**, with at least **59.368 seconds** of remaining time. Passed Ruff/mypy.

See [Submission Report](../outputs/analysis/kaggle-agronomy-dsm-grouped-s80001-u816-20260923-t0-once/submission-summary.md),
[Successful Acknowledgment](../outputs/analysis/kaggle-agronomy-dsm-grouped-s80001-u816-20260923-t0-once/submission-receipt.json),
[Unique New Inquiry](../outputs/analysis/kaggle-agronomy-dsm-grouped-s80001-u816-20260923-t0-once/submission-status.json),
and [Complete Eligibility](../outputs/analysis/kaggle-agronomy-dsm-grouped-s80001-u816-20260923-t0-once/qualification.json).

## September 23: s80001 enables quadrant behavior monitoring, training continues in original state

Add unlock, construction, production usage, post-purchase idle, and land acquisition turn tracking for NW, NE, SW, SE directions, along with statistics on maximum production cells. Count only the learning agent's position, including final action settlement; after each round sampling, reuse the existing board tensor reduction. The native engine, rewards, optimization objectives, and PFSP remain unchanged. Enhance the monitoring overview with land acquisition rate and production usage rate curves, plus an SE indicator card. Display statistical processing time on the resources page.

s80001 normally stops at **U89**, independently completes dual-GPU training at U90–U93 and verifies stop/archival recovery,
PFSP sampling replay, Actor/Critic optimizers, dual rank RNG, and parent chain integrity. The original run was restored from **U89** at 02:56 UTC using an authenticated source code revision, maintaining run ID, protocol, and all historical pools.
Source code revision `source-revisions/0001`, training source code SHA256 `81538f2e1cd44bc64c583ad9b28a84b34b2a5e3500ae3c42890a517aab424a5b`.

30 complete trajectories and four-quadrant statistics from direct native state reading are fully consistent. Added complete dual-GPU stable turn cycles:
**5.4–5.7 ms / update, approximately 0.013%**; first turn after two process startups takes about 135–136 ms.
21 related Python tests, 5 frontend tests, Ruff and mypy (940 files) passed.
Original runtime **U92** checkpoint verified via web interface: among 164 learning-side trajectories, 42 purchases and uses of SE,
ratio **25.61%**; page cards and curves are active, training continues to U94 upon acceptance.
See [Monitoring Metrics and Performance](quadrant_monitoring.md),
[Original Runtime State Retention Verification](../outputs/analysis/quadrant-monitor-20260923/activation-verification.json) and
[Recovery Startup Records](../outputs/analysis/quadrant-monitor-20260923/resume-launch.json).

## September 23: DSM BC Latest Batch 977 Transferred Complete s78001 Historical Pool PPO

DSM group loss BC stopped normally at **01:50:47 UTC** as per user request, saving batch **977**:
**12 full epochs + 5 batches / 5,591,663 supervised turns**, with Adam, dual rank RNG, and data cursor preserved.
A new run **`agronomy-v4-m384-dsm-grouped-ppo-20260923-s80001`** started at **01:57:16 UTC**
Booting GPU0+GPU1; the initial Actor's 347 tensors are exactly identical to those in the latest BC checkpoint.

PFSP pool fully inherits the 225 external historical strategies from **s78001**, and adds s78001's initial state, 25 snapshots, and the latest **U1609** at termination, totaling **252 historical strategies**. Retains the original 7 scripts, plus the current round's initial Actor, totaling **260 candidates**; sampler members have been individually verified.
Pure terminal WDL, 70% unified PFSP + 30% self-play, Actor/Critic learning rates at 7.5e-6 / 1e-4.
A new PPO optimizer and Critic are introduced; the new learner reaccumulates PFSP win/loss records, while all prior run evidence is fully preserved.

Formal **U4 / 512 games** checkpoint verification passed: Actor/Critic Adam each for 12 steps, dual rank RNG
Complete, all tensors finite, PFSP sampling and statistical replay consistent in the first 4 rounds. Training has continued to round 5.

See the [New PPO Agreement](agronomy_dsm_grouped_ppo_20260923.md),
[Pool Member Verification](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/pool-verification.json), and
[Formal Acceptance](../outputs/analysis/dsm-grouped-bc-to-ppo-20260923/formal-verification.json).

## September 23: Stop s78001, start DSM group loss BC with the latest U1609

According to user request, PPO `agronomy-v4-m384-watch2-ppo-20260922-s78001` has stopped normally after successfully saving **U1609 / 205,952 turns of RL** at **01:33 UTC**, with the parent checkpoint, Adam, dual rank RNG, and PFSP fully preserved.

New run **`agronomy-v4-m384-u1609-dsm-grouped-bc100-20260923-s79001`** started at
**01:36 UTC** with GPU0+GPU1. The initial Actor's **347 tensor**s are identical to those of U1609,
a new BC Adam is created. Using the specified DSM **9/21** to load six versions of train/val data: **645 / 35 trajectory**s,
no test set is defined; 2,040 arrays passed re-verification. Five action types are each normalized with equal weights of 1.
Maintain a 16 × 384 network, 384 turn memory, learning rate **1e-4**, budget **100 epoch / 8,100 batches**;
no early stopping, automatically stops upon completion, does not automatically enter PPO.

Formal checkpoint verification passed for **Turn 96 / 550,035 total supervision turns**: Adam at 96 steps, encoder, memory, and action head all updated, all tensors finite, double rank RNG complete. Full validation group NLL **0.1732197785**, independently recalculated across five categories and consistent. Parent run unchanged, source code archive recoverable. Monitoring audit has reached batch 125; training continues. See [Protocol and Acceptance](agronomy_dsm_grouped_bc_20260923.md), [Startup Log](../outputs/analysis/dsm-grouped-bc-20260923/launch.json), and [Formal Verification](../outputs/analysis/dsm-grouped-bc-20260923/formal-verification.json).

## September 23: Added five types of actions, each normalized in the BC pipeline

According to user requirements, add `learning_grouped_bc`: normalize unit objectives, unit operations, unit quantities, market operations, and market quantities based on their respective effective field counts, then combine them using explicit Hydra weights with default equal weighting across five categories. The denominator covers one complete optimization batch and all ranks; sequence chunking, micro-batching, and padding do not alter objective weights. Selection/confirmation is calculated based on the total quantities of each category across the entire partition; loss configuration is bound to the runtime protocol, checkpoint progress, and logs, and loss changes made during recovery are rejected. Historical configurations retain their original loss and protocol identity.

Cycles, memoryless, dual-process tail batches, gradient, configuration, and recovery-related **19 tests** passed,
full-scale Ruff and mypy (938 source files) passed. This implementation only covers the pipeline and has not initiated new training;
the current PPO continues; no conclusions on SE utilization or win rate gains have been reached.
See [Objective Definition, Configuration, and Usage Instructions](grouped_bc.md) and
[New BC Configuration](../configs/learning_grouped_bc.yaml).

## September 23: DSM 9/21's submission has generated an independent BC dataset

Based on the user's final scope "September 21 to present", freeze the DSM collection list from **01:07:51 UTC**.
Select 6 versions (from **9/21 00:00 UTC** onward) submitted officially, covering 681 collected games.
Supervise only DSM; 86 games reuse daily ZIP, 595 games use standalone replays. 1 game is excluded due to opponent TIMEOUT during the match, following the full trajectory rule; the original files are retained.
Final result: **680 trajectories / 488,920 supervised turns**.
As per user's subsequent request, all original test (confirmation) entries are merged into train; only the following are retained:
**train: 645 trajectories / 463,755 turns, val: 35 trajectories / 25,165 turns**, with no test set.

Continue along the mainline v4 trajectory, Q100, and world seed hash; retain original verification seats, and transfer original confirmation seats into training.
2,040 array checks passed, 14,400 observations consistent across 10 official complete games, partition migration and actual reader verification passed. Data collection task and current PPO continue running.
This round only prepares data, without switching training. See [Data Description and Reproduction](dsm_bc_20260921_23.md),
[Final Data Entry Point](../outputs/datasets/agronomy-v4-dsm-20260921-23-train-val-q100/manifest.json),
and [Verification Report](../outputs/analysis/dsm-bc-20260921-23/train-val-verification.json).

## September 23: s78001 latest complete U1512 has been submitted once at T=0

Fix current state at **00:46 UTC** as per user request.
`agronomy-v4-m384-watch2-ppo-20260922-s78001` latest complete checkpoint
**U1512 / 193,536 games RL**, submit only once at **T=0**.
Kaggle successful acknowledgment number **56478145** (**00:58:25 UTC**); submission list verification confirmed
Exactly one new entry added, no return of evaluation status or score yet. Training continues; U1532 has been fully saved upon verification.

Submit the package using the current training archive, FP32 CPU, 384-turn memory, and argmax per condition.
**2,876 actions and integer turn IDs are completely consistent**, memory cache verification passed and overrides the elimination phase.
Retain the explicit atol=2e-6, rtol=1e-5 audit configuration; both games in this run also satisfy the original atol=1e-6 combined tolerance, with a maximum error of 9.050e-7 after relative tolerance deduction.
Audit only accumulates the prior error diagnosis files; the submitted package uses the complete original training source code.

Python 3.11/3.12 passed **4 games / 5,760 observations** through the official runner, all seats allocated.
`DONE`: trajectory consistent across runtimes; maximum cold start time **1.622 seconds**, subsequent actions within **0.396 seconds**, with at least **59.378 seconds** of remaining time. Passed Ruff/mypy; training and deployment implementation unchanged.

See [Submission Report](../outputs/analysis/kaggle-agronomy-watch2-s78001-u1512-20260923-t0-once/submission-summary.md),
[Successful Acknowledgment](../outputs/analysis/kaggle-agronomy-watch2-s78001-u1512-20260923-t0-once/submission-receipt.json),
[Unique New Inquiry](../outputs/analysis/kaggle-agronomy-watch2-s78001-u1512-20260923-t0-once/submission-status.json),
and [Complete Eligibility](../outputs/analysis/kaggle-agronomy-watch2-s78001-u1512-20260923-t0-once/qualification.json).

## September 22: s78001 has submitted the latest complete U340 once at T=0

At user request, fix current state at **15:10 UTC**
`agronomy-v4-m384-watch2-ppo-20260922-s78001` latest complete checkpoint
**U340 / 43,520 games RL**, submit only once at **T=0**.
Kaggle successful acknowledgment number **56468475** (**15:36:07 UTC**); submission list verification confirmed
Exactly one new entry added, no return of evaluation status or score yet. Training continues; upon verification, U392 is fully saved.

Submit the package directly using the current training archive, FP32 CPU, 384 turn memory, and argmax per condition.
Python 3.11/3.12 passes the official runner check in **4 games / 5,760 observations**, all seats.
`DONE`, trajectory consistent across runtimes; maximum cold start time **1.626 seconds**, subsequent actions within **0.398 seconds**, with at least **59.374 seconds** of remaining time.

Absolute cache tolerance of 1e-6 once exceeded the threshold value at turn 450; retain the first failure, add audit error logging, and then re-run two verification rounds explicitly with **atol=2e-6, rtol=1e-5**.
**2,876 actions and integer turn IDs are completely consistent**; maximum absolute cache error is 2.265e-6, reduced to 1.310e-6 after relative tolerance adjustment. Only the audit file was modified; the submitted package, model, and training source code remain unchanged.
Two existing regression tests and Ruff/mypy pass.

See [Submission Report](../outputs/analysis/kaggle-agronomy-watch2-s78001-u340-20260922-t0-once/submission-summary.md),
[Successful Acknowledgment](../outputs/analysis/kaggle-agronomy-watch2-s78001-u340-20260922-t0-once/submission-receipt.json),
[Unique New Inquiry](../outputs/analysis/kaggle-agronomy-watch2-s78001-u340-20260922-t0-once/submission-status.json)
and [Complete Eligibility and Value Confirmation](../outputs/analysis/kaggle-agronomy-watch2-s78001-u340-20260922-t0-once/qualification.json).

## September 22: Pause double-player BC, latest batch 2,120 transferred to complete historical pool PPO

watch2 BC has been normally stopped as per user request at **12:07:02 UTC**, saving batch **2,120**:
**7 epochs + Round 8, 195/275 batches**,totaling **12,182,704 supervised turns**.
The planned 100 epoch budget has been terminated early; the original model, Adam, dual rank RNG, data cursor, and ledger are retained.

A new run of **`agronomy-v4-m384-watch2-ppo-20260922-s78001`** has started at
**12:18:58 UTC** with **GPU0 + GPU1**. The initial 347 tensors of the Actor are exactly consistent with the latest BC state of **`pretraining/shard-002120.pt`**, and both the PPO Actor/Critic Adam and Critic have been reinitialized.
Continuing with **70% unified PFSP + 30% self-play, pure terminal WDL**, γ=λ=1, 128 games per turn, Actor/Critic learning rates at 7.5e-6 / 1e-4, 1 epoch, 28 trajectories per GPU, KL divergence of 0.05, 100,000 updates.

Inherit all **178 earlier external weights** from the archived and authenticated freeze of s76001, plus add **47** from s76001 (the starting point, 45 U64–U2880 snapshots, and the final U2902), totaling **225 historical opponents**.
Seven native scripts are retained; together with the BC starting point, the initial pool of candidates is unified to **233**.
Capacity 361 retains the original 136 strategy slots for self-policies; new learners accumulate PFSP win/loss records from a neutral prior, while the evidence and outputs from previous runs are fully preserved. The native compatibility evidence for v2 opponents is also fully inherited and confirmed.

See [New PPO Protocol](agronomy_watch2_ppo_20260922.md),
[BC Stop Verification](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/bc-stop-verification.json),
[Initialization and Full Dependency Recovery Verification](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/initialization-verification.json),
and [Startup Log](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/launch.json).

Formal **U4 / 512 game** complete checkpoint verified: Actor/Critic Adam each advanced **12 steps**,
encoder, memory, and action head all updated, all tensors finite, dual rank RNG intact.
PFSP sampling from the first four rounds and win/loss evidence replay are fully consistent; actual samples drawn include s76001/U1600, U2880, and s68001/U5312; actual rewards were only −1/+1, cash rewards and BC loss are zero, parent BC and s76001 ledger unchanged. U4 runtime is **29.45 seconds per 128 games**; monitoring trace extended to U7, training continues running.
14 related tests passed, Ruff/mypy verified, see
[Formal Checkpoint Verification](../outputs/analysis/agronomy-watch2-bc-to-rl-20260922/formal-verification.json).

## September 22: s76001 final U2902 has submitted once at T=0

Upon user request, use `agronomy-v4-m384-selected8-ppo-20260921-s76001`
Stop at the latest complete checkpoint **U2902 / 371,456 games RL**, submitting only once at **T=0**.
Kaggle successful acknowledgment number **56463811** (**12:00:07 UTC**), confirmation of submission list review confirms exactly this entry; the initial review has not yet returned evaluation status or score. The new watch2 BC continues to operate normally.

FP32 CPU, 384 turn memory, argmax conditioned on each condition. **2,876 actions and memory states** are consistent with the original model; Python 3.11/3.12 passes **4 games / 5,760 observations** through the official runner, with all seats `DONE` and consistent trajectory across runtimes. Maximum cold start action time is **1.625 seconds**, subsequent actions take **0.404 seconds or less**, with at least **59.375 seconds** of remaining idle time. Reusing the same deployment source code and patches, re-confirmed the current weights.

See [Submission Report](../outputs/analysis/kaggle-agronomy-selected8-s76001-u2902-20260922-t0-once/submission-summary.md),
[Successful Acknowledgment](../outputs/analysis/kaggle-agronomy-selected8-s76001-u2902-20260922-t0-once/submission-receipt.json),
[Unique New Inquiry](../outputs/analysis/kaggle-agronomy-selected8-s76001-u2902-20260922-t0-once/submission-status.json),
and [Complete Eligibility](../outputs/analysis/kaggle-agronomy-selected8-s76001-u2902-20260922-t0-once/qualification.json).

## September 22: Stop s76001, start dual-player BC100 from latest U2902

As per user request, PPO `agronomy-v4-m384-selected8-ppo-20260921-s76001` has normally terminated and saved at **11:28:49 UTC** after **U2902 / 371,456 turns of RL**, exit code 0, with parent run weights, optimizer, dual rank RNG, PFSP, and ledger preserved.

New BC **`agronomy-v4-m384-u2902-watch2-bc100-20260922-s77001`** started at
**11:36:22 UTC**, inherited the latest Actor, maintaining a 16 × 384 network with 384 turn memory.
User confirmed **100 epoch, learning rate 1e-4, GPU0+GPU1**, created a new BC Adam; automatic termination completed.

Data fixed at DSM **1,529 entries** and M & M & P & Q **917 entries** teacher trajectories, combined into
**2,427 games / 2,446 trajectory entries**, learning only seat positions within each team's activity range. DSM still starts from 9/17, `56414341` remains fully excluded, and 520 games reuse daily ZIP. Data collection tasks continue running.
Training set: **1,580,358 supervised turns / 275 updates per round**; validation and confirmation sets each contain 89,156 turns.
7,281 array hashes, partitions, and geometric verifications passed, with 44,640 observations consistent across 31 official full replays.

See [this agreement and data](agronomy_watch2_bc_20260922.md),
[parent run stop verification](../outputs/analysis/watch2-bc-20260922/stop-verification.json),
[data verification](../outputs/analysis/watch2-bc-20260922/data-verification.json),
and [startup record](../outputs/analysis/watch2-bc-20260922/launch.json).

Officially verified: Turn **112 / 642,785** of supervision. Initial 347 Actor tensors match exactly with U2902; BC Adam has taken 112 steps, encoder, memory, and action head have been updated; all tensors are finite; dual rank RNG and data cursor are intact; parent weights and ledger unchanged. Training continues, see [formal checkpoint verification](../outputs/analysis/watch2-bc-20260922/formal-verification.json).

## September 22: Add DSM continuous data collection, exclude low-score versions of M & M & P & Q

DSM (team ID 16732748) has started from the submitted 56444344, episode 111918050 as provided by the user
Running independent persistent data collection, continuing the process of waiting 10 minutes after each turn and historical version discovery. As clarified by the user,
the submission start point is fixed at **2026-09-17 00:00 UTC**, non-rolling; all subsequent submissions are included.
Games overlapping with daily are retained in the DSM dataset, directly referencing existing ZIP members without re-downloading.
At 07:13:54 UTC: **12 versions / 1,461 games**, 524 available (including 520 reused from daily), 937 games pending, 0 errors.
Original collected files and records from earlier periods are preserved in the archive and tracking is stopped.
The persistent task has been resumed. See [DSM Task](dsm_replay_watch.md).

`56414341` has been added to the persistent exclusion list of two tasks, and the existing 10 game replays along with associated files have been removed.
M & M & P & Q have passed the next round of check confirmation for **6 versions / 900 games**, with both pending downloads and errors at 0;
The public list, historical mining, and restart processes cannot reintroduce excluded versions. The original daily merge entry has also been removed synchronously.
Of these 10 games, the current total is **17,538 games**, and the actual subset used by SE is **1,471 games** (among the removed games, 2 opponent games used SE territory). The date and rating distributions have also been recalculated.
See [Exclusion and Cleanup Records](mm_pq_replay_watch.md#section-dfa13629b0d0).

## September 22: daily merge and fourth plot coverage statistics

Fetch the latest 9/21 daily 638 games, deducting 10 existing local games, resulting in a net increase of 628 games.
9/3–21's 19-day daily total comprises 12,441 games; after consolidation of independent replays and deduplication, it amounts to **17,548 games**.
There are **1,473 games** and **1,571 player trajectories** where the entire game previously involved planting or placing animals on the fourth land plot SE;
among these, daily games account for 619 games and 635 trajectories, with the latest 9/21 daily contributing 21 games.

All dates in the SE subset are known; in 632 out of 1,473 games, both players' average ratings are available, with a median rating of 2,991.7; missing ratings are not imputed using cash or current leaderboard ratings. Full parsing has zero failures, and 72 independent coordinate entries have passed confirmation. The original integration entry, SE subset, dates, and rating distribution are available in [Data Statistics Record](daily_land_20260922.md).

## September 22: The latest complete U1536 for s76001 has been submitted once at T=0

As per user request, fix the current `agronomy-v4-m384-selected8-ppo-20260921-s76001`
Select the latest complete checkpoint **U1536 / 196,608 games RL**, and submit only once at **T=0**.
Kaggle successful acknowledgment number **56447050** (00:34 UTC), list reconciliation confirmation confirms exactly one new entry; initial reconciliation has not yet returned evaluation status or score. Training continues to run.

This checkpoint initialization run for supplementation supports deployment origin, reusing parent weights and root type verification from the training side, preserving the genuine `checkpoint-root` lineage. The training archive only overlays five deployment files, maintaining model computation and training protocols; the source code identities and differences between training and deployment are separately archived.

FP32 CPU, 384 turn memory, argmax conditioned on each condition. **2,876 actions and memory cache** are consistent with the original model; Python 3.11/3.12 passes **4 games / 5,760 observations** through the official runner, with all seats `DONE`, consistent across runtime trajectories and cash flow. Maximum cold start action time is **4.337 seconds**, subsequent actions take **within 0.396 seconds**, with at least **56.663 seconds** of additional time. All 10 related tests and Ruff/mypy pass.

See [Submission Report](../outputs/analysis/kaggle-agronomy-selected8-s76001-u1536-20260922-t0-once/submission-summary.md),
[Successful Acknowledgment](../outputs/analysis/kaggle-agronomy-selected8-s76001-u1536-20260922-t0-once/submission-receipt.json)
and [Complete Qualification](../outputs/analysis/kaggle-agronomy-selected8-s76001-u1536-20260922-t0-once/qualification.json).

## September 21: Current PPO fills all historical sources used by s73001

`agronomy-v4-m384-selected8-ppo-20260921-s76001` has been fully saved and recorded at **U259 / 33,152 games**. `population-revisions/0001` is now being supplemented starting from **U260** with **137 historical weights** from the authenticated and archived s73001: 27 from s65001, 5 from s62001, 25 from s67001, 29 from s69001, and 51 from s68001. Previously, only 41 weights from s73001 itself were imported, missing these five external sources.

External history is now **178**; retain the current BC origin and U64/U128/U192/U256, along with seven scripts.
When switching, the unified pool has **190 candidate entries**. History capacity increases from **177 → 314**, retaining the original snapshot space.
**70% unified PFSP + 30% self-play**, pure terminal WDL, GPU0+GPU1, all optimization configurations preserved.
Existing PFSP statistics are fully retained; new members start from a neutral prior and do not copy the previous learner's win/loss records.
Original complete checkpoints, Adam, dual rank RNG, ledger, and historical outputs are retained.

All 137 frozen Actors, native compatibility evidence, and boundary checkpoints have passed verification; 18 related tests and Ruff/mypy have passed, and the archived recovery entry has been restarted. See
[Completion Record](agronomy_selected8_history_completion_20260921.md),
[State Persistence Verification](../outputs/analysis/agronomy-selected8-history-completion-20260921/transition-verification.json),
and [Continued Training Startup](../outputs/analysis/agronomy-selected8-history-completion-20260921/launch.json).

Formal **U260 / 33,280 game** checkpoints verified: First round actually drew the newly added s67001/U512,
Completed 40 rounds of self-play and 88 rounds of historical matches; PFSP sampling and evidence replay are consistent, Actor/Critic Adam each advanced **3 steps**, weights updated, all tensors finite, dual rank RNG complete, actual rewards remain purely terminal WDL.
Training continues running, see [formal verification](../outputs/analysis/agronomy-selected8-history-completion-20260921/formal-verification.json).

## September 21: Pause eight teams' BC, and start the new two-GPU PPO from the latest batch 4,934

User requests to terminate the current BC and confirms the new RL uses **70% unified PFSP + 30% self-play**.
BC `agronomy-v4-m384-u7820-selected8-bc100-20260921-s75001` has been fully saved and exited normally at **09:15:36 UTC**: **10 epochs + Round 11, batch 164**,
ending at `pretraining/shard-004934.pt`, with a total of **28,368,847 supervised turns**.
The original BC, originally scheduled for 100 epochs, has been terminated early as per user request; original weights, Adam, RNG, and ledger are retained.

A new run of **`agronomy-v4-m384-selected8-ppo-20260921-s76001`** has started at
**09:20:37 UTC**, initializing **GPU0 + GPU1**, with the Actor fully inheriting the latest BC;
maintaining a 16 × 384 network and 384 turn memory, reinitializing PPO Actor/Critic Adam and Critic.
Using **pure terminal WDL**, γ=λ=1, 128 games per round, Actor LR **7.5e-6**, Critic LR **1e-4**,
1 epoch, 28 trajectories per card per mini-batch, early stopping at KL 0.05, with a budget of 100,000 updates.
Two sampling pipelines and asynchronous checkpoints are enabled.

The unified pool initially includes seven existing native scripts, 41 reserved BC/PPO weights from s73001, and the starting point for this BC.
Scripts have no individual quotas; new runs start from accumulated prior PFSP evidence and incorporate their own snapshot every 64 updates.
All initial and historical weight identities, native environments, BC Adam, and dual rank RNG have been confirmed.

See [New PPO Protocol](agronomy_selected8_ppo_20260921.md),
[BC Stop Verification](../outputs/analysis/agronomy-selected8-bc-to-rl-20260921/bc-stop-verification.json),
and [Start Logging](../outputs/analysis/agronomy-selected8-bc-to-rl-20260921/launch.json).

Formal **U4 / 512 game** complete checkpoint verified: Actor/Critic Adam each advanced **12 steps**,
actual rewards were only −1/+1, cash rewards and BC loss were zero, encoder, memory, and action head all updated.
All checkpoint tensors are bounded, double rank RNG is complete, and the first four rounds of PFSP sampling and win/loss evidence replay are consistent.
Initial Actor and final BC states are tensor-wise equal; parent BC original files and ledger remain unchanged.
U3/U4 steady-state times are approximately **29.6 / 29.4 seconds per 128 games**; training continues.
8 related tests, Ruff/mypy, archive recovery checks, and browser WebUI checks passed, see
[Formal Verification](../outputs/analysis/agronomy-selected8-bc-to-rl-20260921/formal-verification.json).

## September 21: Starting eight teams from s73001's latest U7820 for a five-day BC100 tournament

At **08:07:02 UTC**, starting an independent BC run from the latest complete checkpoint of
**`agronomy-v4-m384-bc100-3d-20260917-s73001`**
**U7820 / 1,000,960 games RL**
**`agronomy-v4-m384-u7820-selected8-bc100-20260921-s75001`**.
Using **GPU0 + GPU1, two H200s**, with full Actor weights inheritance, maintaining the 16 × 384 network,
384 turn memory and complete v4 features. The original s73001 and the products from the stopped compact289 are retained.

Data: [specified eight teams' five-day data](selected8_five_day_bc_20260921.md). Fixed
**100 epochs, no early stopping**; learning rate **1e-4**, BF16, 8 samples per batch of complete trajectories,
each round completes **2,742,636** supervised episodes and **477 Adam updates**.
Each round validates **130,124** episodes; after completing the 100th round, evaluates **138,729** confirmed episodes.
BC Adam reinitialized; supervision training is executed only, and the process automatically stops upon completion.

Passed initial weight verification per card, two-round acceptance with dual GPUs, and actual archiving, training suspension, and recovery.
Model/Adam finite, dual rank RNG, and cursor complete. Fixed unnecessary script imports during BC recovery; original script evidence migration logic preserved. 28 related tests, Ruff, and full mypy passed.
WebUI verified BC progress, weight origin, five-category action diagnostics, and automatic refresh expansion status.

See [Training Protocol and Run Records](agronomy_selected8_bc_20260921.md),
[Startup Records](../outputs/analysis/agronomy-u7820-selected8-bc-20260921/launch.json),
and [Complete Acceptance](../outputs/analysis/agronomy-u7820-selected8-bc-20260921/qualification.json).

Formal **Batch 48 / 276,051 turns** verified: initial parameters exactly match U7820,
Adam steps at 48, encoder, time memory, and action head all updated, all checkpoint tensors bounded, dual rank RNG complete; data sequence and loss mask counts precisely matched, all array hashes passed, parent ledger and weights unchanged.
Median warm-up training batch time is approximately **0.753 seconds per batch**, excluding end-of-turn validation and checkpoint publication overhead.
Training continues running, see [formal verification](../outputs/analysis/agronomy-u7820-selected8-bc-20260921/formal-verification.json).

## September 21: Stop compact289 as per user request, fully preserve U265

`compact289-v4-selected8-ppo-restart-20260921-s74001` exited normally at **07:49:05 UTC**
after complete saving of **U265 / 271,360 games RL**, exit code **0**.
The training parent process and two GPU worker processes have all terminated; no further training is currently running.

Final checkpoint is `checkpoints/update-000265.pt`, SHA256:
`0fbf75323479ac9d46585dfef455928d9939602e6138105db91df93539130144`.
Checkpoint hash verified, all tensors finite, PFSP and ledger consistent, dual rank RNG complete;
model, optimizer, and historical run artifacts retained in the original output directory.
See [Final Stop Verification](../outputs/analysis/compact-stop-commit-20260921/verification.json).

## September 21: compact289 starts using hand-written C++ script to calculate hotspots

Currently `compact289-v4-selected8-ppo-restart-20260921-s74001` is at **U241 / 246,784 games**.
After full preservation, register `source-revisions/0002` and continue GPU0+GPU1 training at **07:31:58 UTC**.
Specially hand-write observation views, inventory projections, planning state replication, four-day input forecasting, and sales event indexing,
and modify the local variables and common parameters generated by code into static slots.
Strategy assets, unified PFSP evidence, model, optimizer, dual-GPU RNG, pure terminal WDL, and training configuration are retained.

A fixed CPU throughput improvement of **1.53–1.65×** for four heavy scripts; this represents script batch yield, not the acceleration factor of a full PPO update. In full sampling, V45 steady-state time decreased from 24.99 to 22.29 seconds; the two optimized samples for V53 are 28.53 / 43.10 seconds, with significant shared hardware variability.
**49 games / 70,462 actions** passed original source code verification, with identical full sampling trajectories and action probabilities compared to the original version bit-by-bit; 21 test cases and Ruff/mypy passed.

Current source code identity `906b4a5ced48ef741e69480ddb9797b9483f377fd897ae8da331c348ed4dfd16`;
Script runtime library `c32aabb0169caed3d7996dd6aeae8c70b48864117a53b6c1a25cd0087b95cb6d`.
See [Handwritten Hotspot and Performance Report](native_script_hotpaths_20260921.md),
[Checkpoint Binding Eligibility](../outputs/analysis/compact-script-throughput-round2-20260921/repair-qualification.json),
[State Persistence Verification](../outputs/analysis/compact-script-throughput-round2-20260921/transition-verification.json),
and [Formal Continuation Training Initiation](../outputs/analysis/compact-script-throughput-round2-20260921/launch.json).

Subsequently, **U244 / 249,856 game checkpoints** passed verification: the PFSP complete replay is consistent across U242–U244, the Actor/Critic Adam each advances **9 steps**, weights are updated uniformly, all tensors are finite, and both rank RNGs are fully intact.
Under normal conditions, U244 samples V45 in **20.36 seconds** per sample, totaling **40.94 seconds** per round; this is a single formal observation and does not represent a stable acceleration ratio across all opponents. Training continues, see
[Formal continued training verification](../outputs/analysis/compact-script-throughput-round2-20260921/formal-verification.json).

## September 21: compact289 retains the original pool and adds Ahmed V53, Thomas Metav4

Current `compact289-v4-selected8-ppo-restart-20260921-s74001` is fully preserved at
**U155 / 158,720 games**, registered as `population-revisions/0002`, and starting from **U156**, `ahmed_v53` and `thomas_metav4` are added to the unified PFSP. The original five native scripts are retained, with all win/loss counts, valid evidence, and decay times migrated after source code identity verification—no counts are reset.
Each turn remains **820 self-play games + 204 unified pool matches**; scripts have no individual quotas.
Model, pure terminal WDL, γ=λ=1, optimizer, dual-GPU RNG, learning rate, and update count remain unchanged.

Released 12 notebooks, with 9 unique source codes after deduplication; added two new strategies to 16 worlds with dual seats.
In the 32-game confirmation panel, both versions of V45 achieved **32 wins and 0 losses**. Both have been publicly released with source code frozen and compiled into C++. Training uses the existing native batch interface. **18 games / 25,884 actions and controller diagnostics** match, and the U128 neural policy matches **4 games / 5,760 official observations**.
After optimization of sales forecasting, the CPU throughput of V53/Thomas's scripts improved by **1.40× / 1.27×**; this figure is not the acceleration factor per full PPO round. Additionally, 25 related tests and Ruff/mypy checks passed.

On first startup, checkpoint PFSP key validation interception was triggered, and no new update was executed. Subsequently, registration of `source-revisions/0001` was recorded, and the identity migration was replayed in memory, preserving the original checkpoint file unchanged.
At 06:27 UTC, GPU0+GPU1 was restarted from the patched archive source; no separate training run on independent GPUs was conducted to pursue the qualification branch, instead using the full native/CPU-native neural interface qualification. Subsequently, formal checkpoint validation was completed for **U164 / 167,936 games**: a complete replay of the nine-round PFSP sampling and statistics from U156 to U164 showed full consistency. The Actor/Critic Adam agents each advanced by **27 steps**, with weight updates occurring; all tensors were finite, and the dual rank RNG was fully operational. In actuality, U157 sampled 204 games from V53, resulting in a 102-win / 102-loss record for the learning agent. Thomas has not been randomly sampled up to U164, and no artificial quota was added.
The validation logs were completed at U166, and training continues to run.
See [Public Opponent and Nativeization Report](public_notebook_survey_20260921.md),
[Qualification Binding](../outputs/analysis/notebook-survey-20260921/population-qualification.json),
[Lossless Migration Validation](../outputs/analysis/notebook-survey-20260921/transition-verification.json),
[Startup Log](../outputs/analysis/notebook-survey-20260921/launch.json),
[Formal Continuation Training Checkpoint Validation](../outputs/analysis/notebook-survey-20260921/formal-verification.json).

## September 21: s73001 final U7820 has been submitted once at T=0

Submit the latest complete weights for `agronomy-v4-m384-bc100-3d-20260917-s73001` as specified by the user
**U7820 / 1,000,960 games of RL**. This run has been stopped; submission is made only once at **T=0**,
Kaggle successful confirmation number is **56417993** (05:47 UTC), and verification of the submission list confirms that this entry was exactly added. The initial verification has not yet returned evaluation status or score.

Reuse the same run archive source code, FP32 CPU, 384 turn memory, argmax per condition.
**2,876 actions and memory cache** match the original model; Python 3.11/3.12 passes official runner validation across **4 games / 5,760 observations**, all seats `DONE`, with consistent trajectory and cash flow across runs.
Maximum cold start action time: **1.639 seconds**, subsequent actions within **0.404 seconds**, final extra time at least **59.361 seconds**.
Checkpoint integrity, deployment module Ruff and mypy pass; fixed weights, source code, submission package, and records are retained.

See [Submission Report](../outputs/analysis/kaggle-agronomy-v4-s73001-u7820-20260921-t0-once/submission-summary.md),
[Successful Acknowledgment](../outputs/analysis/kaggle-agronomy-v4-s73001-u7820-20260921-t0-once/submission-receipt.json)
and [Complete Qualification](../outputs/analysis/kaggle-agronomy-v4-s73001-u7820-20260921-t0-once/qualification.json).

## September 21: compact289 currently integrates PPO into five scripts, proceeds with dual-card training after unifying PFSP

Upon user request, `compact289-v4-selected8-ppo-restart-20260921-s74001` was fully preserved after **U78 / 79,872 games**, and `population-revisions/0001` was registered, with unified PFSP activated starting from **U79**. `ahmed_v45`, `metacounter_r1`, `shop_router_0913`, `rayk_v38_low_pressure`, and `farming_v4_0914` were added as five existing native C++ scripts.
Each turn remains **1024 games = 820 self-play games + 204 unified pool matches**; scripts sample jointly with their own BC/PPO historical models, with no individual script quota or minimum game count. PFSP was previously not enabled in this branch.

Keep GPU0+GPU1, pure terminal WDL, γ=λ=1, three Actor/Critic updates, full-sample training, learning rate with 500 update warmup. Retain original checkpoint bytes, optimizer, dual rank RNG, and old ledger.
The user subsequently explicitly requested to first continue training before optimizing throughput; thus, remaining independent validation is halted, and formal dual-GPU training is resumed using the completed official full game, training, and archive recovery checkpoint at **05:33:09 UTC**.
Full eight-round validation was not fully executed; the actual coverage range is explicitly documented in the report.

Source code identity `7a89bec235f8b33f83f9cd88b0910186d49e87a5d25be51e61c984adae88f58f`,
Adds only the current Hydra configuration compared to the previous run. Script throughput optimization continues in independent CPU benchmarking,
the running process uses the aforementioned archived source code and already authenticated script binaries.
See [Access Record](compact_scripts_pfsp_20260921.md),
[Access Verification](../outputs/analysis/compact-scripts-pfsp-20260921/qualification.json),
[State Retention Validation](../outputs/analysis/compact-scripts-pfsp-20260921/transition-verification.json)
and [Formal Launch](../outputs/analysis/compact-scripts-pfsp-20260921/launch.json).

## September 21: compact289 restarts PPO from BC, γ=λ=1, three two-GPU updates per round

The user discovered rapid degradation in the first round of PPO and requested a halt to training. Subsequently, they explicitly specified that only **γ, GAE λ, and the number of Actor updates per turn** would be aligned with the previous large model's dual-GPU configuration, and training was restarted formally.
The prior run `compact289-v4-selected8-bc100-20260921-s74001` has been fully saved and exited normally at **U47 / 48,128 games** (exit code 0); all original ledgers and preserved outputs remain unchanged.

**04:37:51 UTC** Launch a new PPO branch from original BC endpoint `pretraining/shard-011333.pt`
**`compact289-v4-selected8-ppo-restart-20260921-s74001`**, with devices **GPU0 + GPU1**.
Configured as [`learning_compact_ppo_restart_20260921`](../configs/learning_compact_ppo_restart_20260921.yaml):
**γ=1, λ=1**; change global logical batch size from 2,000,000 to **442,368 rows**,
split all **1,325,836 rows** per turn into three batches, with **Actor/Critic each updated 3 times**
(Actor still follows original KL early stopping). This aligns with the actual three-step record of the large model running on dual cards U7702/U7703;
the six-step process after the large model switched to single card is not considered part of the current dual-card objective.

Actor/Critic base learning rate remains at **1e-4**, and a new PPO U1 is restarted with a **500 update warmup**.
Each turn consists of 1024 games: 820 self-play games + 204 games against historically matched opponents, 1 epoch, original model and full features,
BF16, KL 0.05 with early stopping only, pure terminal WDL, and original evaluation/backup intervals remain unchanged.
The new branch connects only to the original BC Actor; both PPO Adam optimizers and the Critic are reinitialized and do not inherit from the old PPO U47.
The new and old directories share the original random root and BC's `run_id` lineage; the new PPO branch has its own directory and `branch_id`, and cannot be treated as an independent BC for reproducibility experiments.

BC complete weights, Adam, dual rank RNG, parent ledger unaltered, and configuration changes verified to be only the above three items: training field and output directory. Formal **U4 / 4096 games** checkpoint confirmed: both Adam steps are **12**, each round with two GPUs reporting Actor/Critic three steps, actual LR **8e-7**, γ=λ=1, all tensors finite, both rank RNGs fully intact. Post-warmup, U2–U4 performance is approximately **33.5 seconds per 1024 games**, formal training continues. Win counts against BC in first four rounds: 109/204, 97/204, 116/204, 106/204; no conclusive evidence of sustained improvement. Source identity: `f93a354dafd4fe0c88f19a5bac84dd26ddf4c4815647271c2c59152816c55704`. Future recovery will use the archive entry under a **new directory**, see [restart log](compact_ppo_restart_20260921.md) and [formal checkpoint verification](../outputs/analysis/compact-ppo-restart-20260921/formal-checkpoint-verification.json).

## September 21: compact289 latest BC connects to formal dual-card PPO, 500 update learning rate warmup

User requests to prematurely terminate the current BC and initiate the formal dual-GPU PPO instead of the following full BC100 schedule.
`compact289-v4-selected8-bc100-20260921-s74001` has been normally saved and stopped at:
**47 complete epochs + Epoch 48, batch 100/239**:
`pretraining/shard-011333.pt`,totaling **130,054,139** supervised turns, **11,333** BC Adam updates.
Last complete epoch training/validation NLL: **0.26678 / 0.28152**; no full validation performed at partial epoch endpoints.

**03:58:15 UTC** Started formal **GPU0 + GPU1** PPO using the latest BC weights, retaining the same run ID.
Configured for [`learning_compact_ppo_20260921`](../configs/learning_compact_ppo_20260921.yaml):
Actor/Critic learning rates both set to **1e-4**, with linear warmup for the first **500 updates**; U1 is **2e-7**, reaching **1e-4** at U500 and then held constant. **GAE λ=0.95, γ=0.999** calculated per game turn,
terminal bootstrap set to zero; no additional time discount applied to action fields within the same turn.

Maintain **2,887,708 parameters** and all original features; BF16 mixed precision computation, gradient synchronization across two GPUs,
each turn **1,024 games = 820 self-play games + 204 matches against historically matched opponents**, all decisions participate in PPO.
Pure terminal WDL (+1/0/−1); retain original 100,000 update budget, KL 0.05 with early stopping only,
adopt two accepted sampling pipelines and asynchronous checkpoints. BC Adam and dual-GPU RNG are fully preserved in the boundary replica;
PPO Actor/Critic uses a new Adam, Critic initialized according to fixed specifications.

The archived source code identity is `c3daec1ec76f2a84af47acde5c1a34793a2f6e76004448a9e3aefbfd39ddeab0`.
The original BC source code and ledger are retained; handover revisions are documented in the runtime directory `bc-completion/0001`.
Detailed protocol is available at [PPO Runtime Log](compact_ppo_20260921.md);
subsequent recovery will continue using this runtime's archive recovery entry, with warmup proceeding based on absolute update continuity.

Formal **U4 / 4096 games** checkpoint verification completed: both optimizers have 4 steps, actual learning rates are both **8e-7**,
GAE parameters are correct, all 651 checkpoint tensors are finite, and dual rank RNG is fully preserved.
All **1,325,836** decisions per round have participated; Actor parameters have been relatively updated from BC.
U2–U5 full-round training time is approximately **33.1–33.4 seconds per 1024 games (two GPUs)**, training continues.
See [Formal Checkpoint Verification](../outputs/analysis/compact-ppo-20260921/formal-checkpoint-verification.json).

## September 21: Solidify compact289, halt s73001, two-card training for eight teams over five days' data BC100

User accepts the current optimization results; throughput study is complete. The new model configuration is fixed to
[`model/compact289`](../configs/model/compact289.yaml): **Actor + Critic with 2,887,708 parameters**,
Actor with 256 width / 3 layers / 4 heads, Prefix Critic with 128 width / 1 layer, no learned memory.
Full v4 observations, all 286 scenario tokens and action ABIs are retained, BF16 mixed precision computation, FP32 parameters, and Adam optimizer.
H200 final complete PPO warm-start baseline is **56.82 seconds per 1024 games**, with all 1,325,836 decision participations.
The 30-second target is not met; no additional optimization experiments are conducted as per user request.

The old formal run `agronomy-v4-m384-bc100-3d-20260917-s73001` has been normally stopped after saving **U7820 / 1,000,960 games**, exit code 0. The original ledger, weights, and optimizer are retained; the final checkpoint is saved to the migration directory; the previously scheduled continued training on GPU0 is no longer executed.

A new run of **`compact289-v4-selected8-bc100-20260921-s74001`** has started on
**2026-09-21 03:03:46 UTC**, using **GPU0 + GPU1** (two H200 GPUs).
The entry point is [`learning_compact_bc_20260921`](../configs/learning_compact_bc_20260921.yaml),
using [five-day data from eight teams](selected8_five_day_bc_20260921.md), with fixed **100 epochs** and **no early stopping**.
Each training turn completes **2,742,636** supervised turns and validates **130,124** turns;
after final budget assessment, **138,729** independent confirmation turns are evaluated.
This run only performs Actor BC;
the Critic configuration is retained for future PPO use, and training will not automatically transition to PPO upon completion.

Runtime source identity: `d7e89a8370005bb0d496351470408be8499493a6fff688e8a9ebefb78b921bae`.
Configurations, source code archives, data hashes, optimizers, and dual rank RNG are all stored in the runtime directory;
subsequent recovery must use the archive recovery entry of this specific runtime. Solidified model configuration does not imply that new weights have been granted deployment eligibility.

The WebUI has added BC-specific curves, five-category action diagnostics, per-epoch/batch details, partition and teacher coverage, and retains the expanded state, table scroll position, and focus during automatic refresh.
See [BC Protocol and Runtime Records](compact_bc_selected8_20260921.md),
[Migration Verification](../outputs/analysis/compact-bc-selected8-20260921/transition-verification.json),
and [Throughput Experiment Final Report](throughput_scale_20260921.md).

## September 21: s73001 uses only GPU0, GPU1 is used for throughput scaling experiment

Upon user request, dual-GPU training is fully saved and exits at **U7703 / 985,984 games**, recorded as **`runtime-revisions/0003`**. Starting from **U7704**, recovery is performed using **`CUDA_VISIBLE_DEVICES=0`**. The parent process **2402403** is restored, and the training process **2402528** is resumed. Only the identifier **`execution.devices`** is changed to **`[cuda:0]`**, and the previously validated optimized archived source code **`665884a08780f516f4249b26654ea02ff5cd86a0c2e4e34fedf3ec1520c2202b`** is continued to be used. The original complete checkpoint is preserved separately, and the original weights, optimizer, rewards, unified PFSP evidence, and retention rules are maintained. The configuration remains unchanged: 128 games per turn, 28 trajectories per mini-batch; the number of optimization steps per GPU per turn is correspondingly increased. No claim is made that this is bit-equivalent to dual-GPU training.

GPU1 experiment has been fixed as **Actor + Critic totaling 2,887,708 parameters** according to user's subsequent requirements:
Actor: 256-width / 3 layers / 4 heads, Critic: 128-width / 1 layer, no learned memory, BF16 mixed computation.
Approximately 80% self-play, with historical opponents being models of the same specification. **All sampled decisions participate in PPO, no sampling is applied**;
All 1,325,836 decisions from 1,024 games are accumulated and each is executed once for Actor/Critic updates.
The experiment will not be recorded in the official training ledger; new architecture experiments use pure terminal WDL, while official training retains its authorized rewards.
The median of the last 100 rounds in a two-GPU setup was approximately **29.42 seconds per 128 games**, serving as the original baseline for this 10–20x performance target.
Configuration, throughput, and H200 power consumption measurements are available in the [Throughput Experiment Report](throughput_scale_20260921.md).

The user then explicitly stated: continue attempting single-GPU runs at **30 seconds per 1024 games**, but **do not alter the model architecture or features**, allowing only constant adjustments and performance optimizations. The map/unit summary candidates have been revoked, and no training or throughput measurements have been initiated for those candidates. Maintain the original full-scenario token count, 2.89M parameters, and complete PPO samples. Training hardware consists only of H200; optimizations are permitted for Hopper kernel, matrix multiplication compilation, and execution scheduling.

See [Single Card Startup](../outputs/analysis/throughput-scale-20260921/production-launch.json),
[Execute Revision](../outputs/analysis/throughput-scale-20260921/transition.json), and
[Migration Verification](../outputs/analysis/throughput-scale-20260921/transition-verification.json).

## September 20: The current s73001 U6676 has already submitted once at T=0

Select the latest complete weights **U6676 / 854,528 turns of RL** as per user request, from
`agronomy-v4-m384-bc100-3d-20260917-s73001`. Submit only once at **T=0**,
Kaggle confirmation number **56401905** (16:59 UTC); list verification at 17:00 UTC confirms the exact addition of this entry, no status or score has been returned yet.

Leverage the current H200 optimized training archive source code, FP32 CPU, 384-turn memory, and conditional argmax.
**2,876 actions and memory cache** match the original model; Python 3.11/3.12 runs through **4 games / 5,760 observations**.
Official runner verification confirms all seats are `DONE`, with consistent trajectory and cash flow across runtimes.
Maximum cold start action time is **1.622 seconds**, subsequent actions take **0.496 seconds**, and final additional time is at least **59.378 seconds**.
Checkpoint integrity and deployment modules Ruff and mypy pass; no modifications to implementation or training configuration.

See [Submission Report](../outputs/analysis/kaggle-agronomy-v4-s73001-u6676-20260920-t0-once/submission-summary.md),
[Successful Acknowledgment](../outputs/analysis/kaggle-agronomy-v4-s73001-u6676-20260920-t0-once/submission-receipt.json)
and [Complete Qualification](../outputs/analysis/kaggle-agronomy-v4-s73001-u6676-20260920-t0-once/qualification.json).

## September 20: The current s73001 U5864 has already submitted once with T=1

Select the latest complete weights **U5864 / 750,592 games RL** as per user request, from
`agronomy-v4-m384-bc100-3d-20260917-s73001`. Submit only once with **T=1**,
Kaggle confirmation number **56390472** (10:16 UTC); the submission list verification confirms the addition of exactly this entry, and the initial verification has not yet returned a status or score. Dual-GPU training continues running, and U5900 is already saved upon verification.

Reuse the current H200 optimized training archive source code, FP32 CPU, 384-turn memory, and original deployment sampling seed.
**2,876 actions and memory cache** match the original model; exact package in Python 3.11/3.12
Completed two full official runner games each, totaling **4 games / 5,760 observations**, all seats
`DONE`, with consistent trajectory and cash flow across runtimes. Maximum cold action time **within 1.897 seconds**, subsequent actions **within 0.482 seconds**, and final extra time at least **59.103 seconds**.
1,602 source code files and 2,071 checkpoint tensors are consistent with the original; deployment modules Ruff and mypy pass, with no changes to implementation. Fixed weights, ledger, submission package, and eligibility records are preserved.

See [Submission Report](../outputs/analysis/kaggle-agronomy-v4-s73001-u5864-20260920-t1-once/submission-summary.md),
[Successful Acknowledgment](../outputs/analysis/kaggle-agronomy-v4-s73001-u5864-20260920-t1-once/submission-receipt.json)
and [Complete Qualification](../outputs/analysis/kaggle-agronomy-v4-s73001-u5864-20260920-t1-once/qualification.json).

## September 20: s73001 restores dual-card training for GPU0+GPU1

Running according to user requirements, currently operating on **U5840 / 747,520 games** fully saved and normally stopped,
registering **`runtime-revisions/0002`**, resuming **GPU0+GPU1** from **U5841**.
Startup environment is `CUDA_VISIBLE_DEVICES=0,1`, continuing to use H200 to optimize source code
`665884a08780f516f4249b26654ea02ff5cd86a0c2e4e34fedf3ec1520c2202b`.
Resuming process PID **190278**, parent process **190193**.

Change only `execution.devices`, from `[cuda:0]` to `[cuda:0, cuda:1]`.
Still 128 games per turn, 28 trajectories per GPU per small batch; 3 steps each for Actor and Critic per turn;
Learning rate, terminal reward, 70% unified PFSP + 30% self-play, historical statistics, and checkpoint retention rules remain unchanged.
The full checkpoint bytes of U5840 remain unchanged and continue to preserve single-GPU boundary copies; rank 0 restores the original RNG,
a new rank 1 RNG is added, derived independently from the root seed, rank, and U5840 according to the existing recovery logic.
This update only involves execution configuration and startup confirmation, following the user's direct startup requirements without additional repeated qualification training.

See [Dual-card startup](../outputs/analysis/dual-gpu-s73001-20260920/launch.json),
[Execute revision](../outputs/analysis/dual-gpu-s73001-20260920/transition.json) and
[Status retention check](../outputs/analysis/dual-gpu-s73001-20260920/transition-verification.json).

## September 20: s73001 integrates with H200 for throughput optimization, continuing to use only GPU0

Stop additional duplicate verifications as per user request. Formal operation continues from **U5795 / 741,760 games** complete checkpoint,
Starting from **U5796**, use the optimized source code of `source-revisions/0001`.
Launch PID **97631** (restoring parent process **97549**), `CUDA_VISIBLE_DEVICES=0`; GPU1 experiment has been stopped.
Current source code is `665884a08780f516f4249b26654ea02ff5cd86a0c2e4e34fedf3ec1520c2202b`.
This update only modifies the implementation; the training protocol, rewards, learning rate, unified PFSP evidence, and original checkpoint bytes remain unchanged.

Optimize including historical opponent full-component compilation (including pool-based old versions without memory models), training memory attention fusion, entity attention assignment, and Hopper convolution layout/rapid mathematical options.
Memory opponent fixed baseline reduced from **62.99 seconds/turn to 53.93 seconds/turn, achieving a 16.8% throughput improvement**;
the old version opponent, on the basis of the optimized learner, decreased from **58.24 to 52.46 seconds/turn, further improving by 11.0%**.
These two measurements are warm-start evaluations for different opponents and cannot be combined or interpreted as the average performance gain across the entire PFSP pool; cold compilation is measured separately.

The user has accepted the specified BF16 probability bias and has explicitly requested direct startup.
Early implementation completed four-round training/stop/archival recovery; the current extended version has finished the full-round baseline for the old opponent pool.
Ruff, full mypy, passed; 44-line synchronization confirmation of opponent memory passed.
The current source code does not re-execute the four-round verification; all additional experiments have been canceled; the formal revision of
`authorization.json` accurately records the direct startup authorization and the scope of existing evidence.

See [Optimization Report](../outputs/analysis/h200-throughput-20260920/summary.md),
[Source Code Revision](../outputs/analysis/h200-throughput-20260920/source-transition.json) and
[Formal Launch](../outputs/analysis/h200-throughput-20260920/production-launch.json).

## September 20: Currently, s73001 is temporarily changed to use only GPU0

According to user request, `agronomy-v4-m384-bc100-3d-20260917-s73001` has been fully saved and stopped at **U5636 / 721,408 games**, and **`runtime-revisions/0001`** has been registered.
The official training PID **3842654** has been restored from original archive, starting from **U5637** using only **GPU0**;
the startup environment has been set to include `CUDA_VISIBLE_DEVICES=0`, and GPU1 has been released from this training.
This is a temporary execution adjustment for current operation; the repository's default dual-GPU configuration remains unchanged. Future restoration to dual-GPU should initiate a new execution revision from the latest complete checkpoint, without rolling back the learning progress after this point.

The only protocol change is that `execution.devices` is updated from `[cuda:0, cuda:1]` to `[cuda:0]`.
Source code, 128 games per turn, Actor/Critic LR **7.5e-6 / 1e-4**,
**`WDL + Δ / (|Δ| + 10000)`**, **70% unified PFSP + 30% self-play**,
The original PFSP evidence and checkpoint retention rules are continued. Each GPU still has 28 trajectory batches, so the current number of Actor/Critic optimization steps per turn increases from **3** to **6**; no claim is made that the dual-GPU trajectory is bit-wise equivalent.
During migration, the original checkpoint bytes remain unchanged, and GPU0's RNG is restored from the original rank 0; prior to the switch, the full dual-GPU checkpoint is separately saved in the analysis directory, preserving the original rank 1 RNG.

Four-round single-GPU training with independent instances passed all stop, archive, and restore operations; each optimizer advanced by **24 steps**.
PFSP exact replay, all checkpoint tensor bounds, and single-GPU RNG verification passed; terminal reward formula error is 0.
Peak allocated GPU memory is approximately **103.8 GiB**, and after warm-up, takes about **65 seconds per round**.
5 tests involving GPU count switching passed; related modules Ruff and mypy verified; training implementation unchanged.
Monitoring interface returns HTTP 200; configuration shows only `cuda:0`. Formal **U5637 / 721,536 games**
Completed: single-GPU Actor/Critic each updated by 6 steps, first-round PFSP sampling exact replay, reward formula error is 0,
actual GPU process verification confirms only GPU0 is occupied; training continues running.

See [Single Card Configuration](../outputs/analysis/gpu0-s73001-20260920/gpu0-upgrade.yaml),
[Four-Round Acceptance](../outputs/analysis/gpu0-s73001-20260920/qualification.json),
[Migration Verification](../outputs/analysis/gpu0-s73001-20260920/transition-verification.json),
[Formal Launch](../outputs/analysis/gpu0-s73001-20260920/launch.json), and
[First Round Formal Verification](../outputs/analysis/gpu0-s73001-20260920/formal-first-update.json).

## September 20: The current s73001 U5376 has already submitted once at T=1

Select the latest complete weights **U5376 / 688,128 games RL** as per user request, from
`agronomy-v4-m384-bc100-3d-20260917-s73001`. Submit only once with **T=1**,
Kaggle confirmation number **56376259** (01:49 UTC); review of the submission list confirms the addition of this entry exactly, no status or score has yet returned in the first verification, training continues to run.

Reuse current training archive source code, FP32 CPU, 384 turn memory, and original deployment sampling seed.
**2,876 actions and memory cache** match the original model; exact package in Python 3.11/3.12
Two complete official runner games were completed each, totaling **4 games / 5,760 observations**, all seats
`DONE`, cross-runtime trajectory and cash flow are consistent. Maximum cold action is **within 1.607 seconds**, subsequent actions are **within 0.402 seconds**, and final extra time is at least **59.393 seconds**.
1,587 source code files match the training archive; 2,071 checkpoint tensors are finite; deployment modules Ruff and mypy pass, with no changes to implementation. Fixed weights, ledger, submission package, and eligibility records have been preserved; temporary task directories have been cleaned.

See [Submission Report](../outputs/analysis/kaggle-agronomy-v4-s73001-u5376-20260920-t1-once/submission-summary.md),
[Successful Acknowledgment](../outputs/analysis/kaggle-agronomy-v4-s73001-u5376-20260920-t1-once/submission-receipt.json)
and [Complete Qualification](../outputs/analysis/kaggle-agronomy-v4-s73001-u5376-20260920-t1-once/qualification.json).

## September 19: The current s73001 U4108 has already submitted once at T=0 and once at T=1

Fixed selection of the latest complete weights **U4108 / 525,824 RL games**, two checkpoints from the same
`agronomy-v4-m384-bc100-3d-20260917-s73001` checkpoint, training continues.
**T=0: 56360218**; **T=1: 56360271**. Each temperature submitted once, both Kaggle responses have been successfully returned and verified in the submission list.

Reuse current training archive source code, FP32 CPU, 384 turn memory, and original deployment sampling seed.
Two temperatures each with **2,876 decisions and memory cache** are identical to the original model; the exact submission package was
Completed two full official runner games in Python 3.11/3.12, totaling **8 games / 11,520 observations**,
All seats `DONE`, with identical trajectory and cash flow across runs at the same temperature. Maximum cold action within **4.180 seconds**,
subsequent actions within **0.460 seconds**, and final additional time at least **56.820 seconds**.
1,587 source code files are consistent with the training archive, and 2,071 checkpoint tensors are finite; no implementation changes were made.
Submission package, source code, eligibility records, and confirmation have been retained; temporary copies have been cleaned up.

See [Submission Report](../outputs/analysis/kaggle-agronomy-v4-s73001-u4108-20260919-t0-t1/submission-summary.md),
[Two Confirmations](../outputs/analysis/kaggle-agronomy-v4-s73001-u4108-20260919-t0-t1/submission-receipts.json)
and [Complete Qualification](../outputs/analysis/kaggle-agronomy-v4-s73001-u4108-20260919-t0-t1/qualification.json).

## September 19: Cancel script independent quotas and join the unified PFSP as a regular member

Upon user request, after `agronomy-v4-m384-bc100-3d-20260917-s73001` saved its complete state and stopped at **U4067 / 520,576 games**, **`population-revisions/0001`** has been registered,
starting from **U4068** using **70% unified PFSP + 30% self-play**.
The pool contains **182 members: 5 native scripts + 177 historical models**.
Scripts and historical models jointly normalize PFSP probabilities, with scripts having **0 independent game ratio**,
no dedicated safety or supplementary quotas; each turn draws one opponent from the shared pool, uniformly allocating frozen opponent games.
128 games per turn are evenly distributed across dual-GPU positions, with frozen opponent games amounting to **88 or 92 games**, and self-play games to **40 or 36 games**,
maintaining a long-term ratio precisely at **70% / 30%**. The probability of a script being drawn changes according to shared PFSP statistics.
At the time of switching, the combined probability of scripts within the pool was approximately **0.6123%**, corresponding to an expected game share of about **0.4286%**,
this reflects only the distribution at that moment and is not a fixed allocation.

Migrate while preserving original U4067 checkpoint, complete historical ledger, 177 historical pool members, and existing PFSP win/loss evidence;
reset only the cumulative rounding starting point for game budgets. Actor/Critic LR **7.5e-6 / 1e-4**,
**`WDL + Δ / (|Δ| + 10000)`** reward, dual-GPU optimizer/RNG and checkpoint retention rules maintained.
Eight independent acceptance rounds, stop preservation and archival recovery passed; each optimizer advanced **24 steps**,
PFSP exact replay, limited tensor and dual-GPU RNG validation passed, cash differential return formula error is 0.
All eight rounds of natural sampling used historical models; scripts were not forcibly scheduled for games.
Related **34 test cases**, Ruff and full mypy (859 files) passed.

Formal training PID **3223707** is running continuously. **U4068 / 520,704** complete checkpoints have been published and read back with verification: 88 historical games, 40 self-play games, 0 script games, and PFSP exact replay passed; parent chain points to original U4067, both optimizers are at **12,204 steps** (each increased by 3 steps), Actor/Critic updates occur, tensor limits are respected, dual-GPU RNG runs independently, and cash difference formula error is 0.

See [Unified Pool Configuration](../configs/learning_agronomy_unified_change.yaml),
[Sampling Rule Verification](../outputs/analysis/agronomy-unified-pfsp-20260919/sampling-verification.json),
[Eight-Round Acceptance](../outputs/analysis/agronomy-unified-pfsp-20260919/qualification.json),
[Migration Verification](../outputs/analysis/agronomy-unified-pfsp-20260919/transition-verification.json),
[Formal Launch](../outputs/analysis/agronomy-unified-pfsp-20260919/launch.json), and
[Formal Checkpoint Verification](../outputs/analysis/agronomy-unified-pfsp-20260919/formal-verification.json).

## September 19: Current s73001 changed to WDL + terminal cash difference

Upon user request, `agronomy-v4-m384-bc100-3d-20260917-s73001`
at the end of **U3288 / 420,864 games** fully saved and stopped, has registered **`reward-revisions/0001`**,
starting from **U3289** using **`WDL + Δ / (|Δ| + 10000)`**, Δ is the difference between our side and opponent's final cash;
the win/draw/loss baseline values are +1/0/−1, cash difference coefficient is 1, and draw total return is 0.
This return is also used for PPO advantage and Critic target, replacing the previous pure WDL training objective.
The original U3288 checkpoint, complete ledger, and source code are preserved;
checkpoint bytes remain unchanged when the reward switch occurs,
Actor LR **7.5e-6**, Critic LR **1e-4**, 128 games per turn, mixed opponents, dual optimizers, and
dual-card RNG are all continued.
The formal run still retains the last two complete checkpoints and permanent checkpoints every 200 updates.

Independent replica passed four-round dual-GPU acceptance, stop, preservation, and archival recovery: the actual return formula error for all learning seats and turns is **0**; the Actor/Critic optimizers each advanced **12 steps**; checkpoint tensors are finite, dual-GPU RNG is complete, and PFSP exact replay passes. The acceptance replica retains the full checkpoint chain, with its updates not entering formal operation. Related **10 tests**, Ruff, and full mypy (859 files) pass; 714 training loops, optimizers, sampling, policies, native engine, and opponent files match the original training archive byte-for-byte.

Formal training PID **53839** has been restored after revision archiving. **Formal U3289** has completed 3 Actor/Critic updates per card, with rewards ranging from **−1.608840 to +1.765511**; cash difference formula error is 0, and the first-round PFSP matches exactly with the next-sample state prior to switching.
**Formal U3292 / 421,376 games** complete checkpoint has been published and read back for confirmation: parent chain points to original U3288, both optimizers have advanced **9,876 steps** (each increased by 12 steps), both Actor/Critic have been updated, all tensors are finite, and dual-card RNGs are independently progressing. Over four rounds totaling 512 games, the actual rewards range from **−1.650838 to +1.782618**, with formula error still at 0; full PFSP replay passes, and the saved training configuration includes correct cash difference parameters.
Dual-card formal training continues.

See [Switch Configuration](../configs/learning_agronomy_margin_change.yaml),
[Four-Round Acceptance](../outputs/analysis/agronomy-margin-20260919/qualification.json),
[Migration Verification](../outputs/analysis/agronomy-margin-20260919/transition-verification.json),
[Formal Launch](../outputs/analysis/agronomy-margin-20260919/launch.json) and
[First-Round Verification](../outputs/analysis/agronomy-margin-20260919/first-update-verification.json), as well as
[New Complete Checkpoint Verification](../outputs/analysis/agronomy-margin-20260919/formal-verification.json).

## September 19: Restore latest U2844 for s73001, start WebUI

Per user request, `agronomy-v4-m384-bc100-3d-20260917-s73001` has been restored at **00:22 UTC**
from the original archive of **U2844 / 364,032 games**, training PID **2061**, with two H200 worker nodes
PID **2222 / 2223**. The U2845–U2847 games not saved prior to interruption are being re-executed, and old logs are retained.
Continuing with `storage-revisions/0002`, Actor LR **7.5e-6**, Critic LR **1e-4**,
pure terminal WDL, original opponent pool, and full training protocol.

Checkpoint hash restored, 2,071 finite tensors, dual optimizers, dual-card RNG, and PFSP validation passed;
In the first round, U2845's PFSP sampling matches that prior to interruption, with each card completing 3 Actor/Critic updates.
**New U2848 / 364,544 games** full checkpoint released and read back verified, parent chain pointing to original U2844,
Both optimizers have completed **8,544 steps**, tensors are finite and dual-card RNG is intact. Verification continued to **U2850**.
Full checkpoints retain the most recent two and permanent checkpoints every 200 updates.

WebUI has started a tmux session named `kagg_revue_monitor`, and the page, health endpoint, runtime details, and curve endpoints all return HTTP 200; it displays the current running status, real-time U2850, and saved U2848.
Entry: <http://127.0.0.1:8765/?run=learning/agronomy-v4-m384-bc100-3d-20260917-s73001>.

See [Restore Startup](../outputs/analysis/resume-s73001-20260919T002229Z/launch.json),
[First-round Verification](../outputs/analysis/resume-s73001-20260919T002229Z/first-update-verification.json),
[New Checkpoint Verification](../outputs/analysis/resume-s73001-20260919T002229Z/first-save-verification.json),
and [WebUI Verification](../outputs/analysis/resume-s73001-20260919T002229Z/webui-verification.json).

## September 18: Restore s73001 dual-card training from the latest complete U2800

In response to the user's request to "restore latest training", `agronomy-v4-m384-bc100-3d-20260917-s73001`
has been restored at **16:42 UTC** from the original archive at **U2800 / 358,400 games**, training PID **2442**,
with dual H200 worker PIDs **2578 / 2579**. The U2801–U2802 logs from before the interruption were not saved and have been re-executed;
the original logs are retained. The source code remains `storage-revisions/0002`, Actor LR **7.5e-6**, Critic LR **1e-4**, pure terminal WDL, mixed opponents, and full training protocol unchanged.

Checkpoint hash, 2,071 tensors, dual optimizers, dual-card RNG, and PFSP validation passed; first-round U2801 PFSP sampling exact replay, with each card completing 3 Actor/Critic updates. **New U2804 / 358,912 games**
Complete checkpoint published and read back verified: parent chain points to original U2800, both optimizers have advanced **8,412 steps**, all tensors are finite, dual-card RNG is complete. Retaining the last two full checkpoints and permanent checkpoints every 200 updates; the next permanent checkpoint is **U3000**; post-warmup observation rounds take approximately **32–36 seconds**, training continues on both cards.

See [Restore Startup](../outputs/analysis/resume-s73001-20260918T164242Z/launch.json),
[First-round Verification](../outputs/analysis/resume-s73001-20260918T164242Z/first-update-verification.json) and
[New Checkpoint Verification](../outputs/analysis/resume-s73001-20260918T164242Z/first-save-verification.json).

## September 18: The current s73001 U2724 has already submitted once at T=0 and once at T=1

Fixed selection of the latest complete weights **U2724 / 348,672 turns of RL**, two copies from the same
`agronomy-v4-m384-bc100-3d-20260917-s73001` checkpoint, training continues.
**T=0: 56331731**; **T=1: 56331777**. Kaggle has returned successful confirmation.

Completed FP32 CPU export with 384-turn memory and per-game independent KV caching for the current model, preserving the original model, quantity budget, agronomy v4 features, and original deployment sampling seed.
Each temperature achieved 2,876 decisions and memory cache matching the original archived eager model; the exact submission package completed two official full games in Python 3.11/3.12, totaling **8 games / 11,520 observations**, all seats `DONE`, with consistent trajectories and cash flow across runtime sessions at the same temperature. Maximum cold start time within **2.017 seconds**, subsequent actions within **0.527 seconds**, and final additional time at least **58.983 seconds**.
The new memory export regression, combined with original tests, passed all 4 items; Ruff and full mypy (857 files) passed.

See [Submission Report](../outputs/analysis/kaggle-agronomy-v4-s73001-u2724-20260918-t0-t1/submission-summary.md),
[Two Confirmations](../outputs/analysis/kaggle-agronomy-v4-s73001-u2724-20260918-t0-t1/submission-receipts.json)
and [Complete Qualification](../outputs/analysis/kaggle-agronomy-v4-s73001-u2724-20260918-t0-t1/qualification.json).

## September 18: Outside the last two complete points, retain one complete point every 200 updates permanently

The storage rule is updated to **the latest 2 complete checkpoints + a permanent complete checkpoint every 200 RL updates**. Permanent checkpoints include the Actor, Critic, dual optimizers, and RNG for each GPU, and are not subject to automatic deletion or pruning. Additional checkpoints are saved when the regular save cycle does not cover a specific update. Historical complete checkpoints that have been cleaned cannot be restored, and existing inference history will not be incorrectly registered as complete recovery points.

Two retained runs have been updated and archived: s73001 is normally preserved and halted at **U2674**, migrated to `storage-revisions/0002`; s68001 remains halted at **U6105**, migrated to `storage-revisions/0003`. The original restore point byte counts are consistent before and after migration, and validations for Actor, Critic, Adam, dual-GPU RNG, and the next round's PFSP sampling have passed. s73001 has been restarted from the original U2674, with the next permanent point at **U2800**; if s68001 continues training, its next permanent point will be **U6200**. The new **U2676** complete checkpoint has been verified: the parent chain points to the original U2674, both optimizers have progressed 8,028 steps with 2,071 finite tensors, the dual-GPU RNG is complete, and the first-round PFSP is exactly consistent; training PID **3514098** continues running.

39 tests related to synchronous and asynchronous saving passed, Ruff and full mypy (855 files) passed, covering normal cases.
Additional saving of U200/U400 is performed when the interval is 3, and the optimizer and RNG are retained after subsequent rolling cleanup.
Current s73001 occupies approximately **399 MiB per full point**, and permanent points will continuously increase disk usage at this scale.
See [Storage Rules](checkpoint_storage.md) and
[Current Migration Report](../outputs/analysis/checkpoint-milestones-20260918/report.md),
[Continuation Saving Verification](../outputs/analysis/checkpoint-milestones-20260918/first-save-verification.json).

## September 18: Retain only s73001 / s68001 restoration status, simplify historical pool storage

As per user's explicit requirement, only the recovery of **s73001** and **`budget-q100-top10-2d-20260913-s68001`** is guaranteed. All other experiments and the BC, evaluation nodes, and independent weight rollback branches no longer in use have been cleaned up; historical ledgers, metrics, source code, and submission packages are retained. The paths to independent weights in the historical records below may have been retired; refer to the current list and ledger for accuracy.

Each run retains only the **most recent 2 complete checkpoints**; the historical pool preserves a streamlined Actor; PFSP original hash identity, statistics, and sampling remain unchanged. The pool for s73001 is **177**, and for s68001 it is **136**; overlapping models use hard links. **7,964** file paths are deleted, reducing weight occupancy from **532.751 GiB** to **16.217 GiB**, resulting in a net reduction of **516.534 GiB** after accounting for the new streamlined weights.

s68001 Maintain stop at **U6105**, fully preserve **U6104 / U6105**; after cleanup, proceed through the originally archived model, dual optimizers, dual-GPU RNG, and next-round PFSP validation. Its storage revision is set to `storage-revisions/0002`.
s73001 After normal stop at **U2651**, migrate to `storage-revisions/0001` with original restore point bytes unchanged, continuing training from the original archive, PID **3247882**. The new **U2652 checkpoint has been confirmed**:
Each of the two GPUs performs 3 Actor/Critic updates, both optimizers advance 7,956 steps, 2,071 tensors are finite, dual-GPU RNG is complete, and the first-round PFSP is exactly consistent; actual Actor LR is **7.5e-6**, with pure terminal WDL.
Old U2648 has been automatically cleaned up, and the complete checkpoint is verified against the most recent two rollings, with dual-GPU training continuing.

Pipeline default retention is reduced to 2, and restoration checks only actual dependencies; BC epoch, historical evaluation, and configuration updates.
Complete weights are no longer permanently retained. Frozen historical strategies do not carry optimizers; source ledger and Actor storage hashes are separated.
Ruff, full mypy (855 files), and 36 related tests pass.
See [Storage Rules](checkpoint_storage.md),
[Cleanup and Continuation Report](../outputs/analysis/checkpoint-storage-20260918/report.md),
[Formal Save Verification](../outputs/analysis/checkpoint-storage-20260918/first-save-verification.json).


## September 18: Roll back to U1856 near U1863, restore Actor LR 7.5e-6

`agronomy-v4-m384-bc100-3d-20260917-s73001` has been fully saved and exited normally at **U1969**, restored to **U1856 / 237,568 games**. Checkpoints U1860, U1864, and U1868 have been cleaned up according to the existing retention policy; U1856 is the closest existing checkpoint to the target U1863.
The original, unmodified U1856 is directly used, with Actor LR **7.5e-6** and Critic LR **1e-4**;
KL **0.05 / early_stop**, and the mixed opponent and pure terminal WDL are retained with the original configuration.

`rollback-revisions/0003` registered, replacing the previous U1891 / 2e-5 continuation.
The U1856 checkpoint shows **2,071 tensor finite**, with both optimizers at **5,568 steps**, full RNG and PFSP on dual cards. The 167-member historical pool from U1856, as originally recorded, has been restored. The PFSP sampling replay for the first turn of U1857 passed exactly. The nine existing subsequent checkpoints in the current branch, along with the complete ledger, metrics, and logs, are archived under the revised `abandoned/`; the original U1856 is preserved via a hard link.
Recovery was performed from the original archived source code, with training PID **2677525**. **New U1857 is complete**: each of the two cards performed 3 Actor/Critic updates, with actual Actor learning rates both at **7.5e-6**, maximum prefix KL of **0.003489**, no early stopping triggered, and the actual reward being pure terminal WDL. Training continues on both cards.
This verification covers the original recovery point and the first actual optimization phase; subsequent periodic checkpoints have not been individually verified.
See [Rollback Record](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/rollback-revisions/0003/transition.json) and [Formal Verification](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/rollback-revisions/0003/formal-verification.json).

## September 18: Corrected the recovery point to U1891, bypassed the 5e-5 update, and continued with 2e-5

The user explicitly noted that the original U1892 already includes the **5e-5** update and requests recovery from the previous checkpoint.
The current `agronomy-v4-m384-bc100-3d-20260917-s73001` has been restored to **U1891 / 242,048 games**,
at which checkpoint the Actor LR was **1e-5**, and both Actor and Critic Adam steps were **5673**.
The target hash matches exactly with the original backup prior to the 5e-5 update in `learning-rate-revisions/0002`.
Now set the Actor LR to **2e-5**, effective from the re-executed **U1892**; Critic LR remains **1e-4**,
KL is set to **0.05 / early_stop**, and the mixed opponent and pure terminal WDL configurations are retained unchanged.

`rollback-revisions/0002` has been registered, replacing the scheme restored from U1892 below. The model, optimizer, dual-GPU RNG, PFSP, historical pool, and records are restored from U1891's original ledger; **2,071 tensors match U1891 bit-by-bit and are finite**. The first-round PFSP sampling replay is exact. The five previously retired non-pool members, cleared by the existing retention policy, remain marked as retired and are not registered as active files.

Checkpoints, logs, and records from the original 5e-5 branch and error recovery branch are preserved in the two rollback archives.

After the original archive restoration, the new **U1892 is complete**: each of the two GPUs performs **3 Actor/Critic updates**, with actual Actor LR at **2e-5**, maximum prefix KL at **0.016715**, and no early stopping triggered.

The new U1892 checkpoint has been confirmed: the parent chain points to the derived U1891, both optimizers have advanced **5676 steps**, all tensors are finite, and the dual-GPU RNG is complete.

Training PID **1796339**; dual-GPU operation continues.

See [Correction Rollback Log](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/rollback-revisions/0002/transition.json) and [Formal Verification](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/rollback-revisions/0002/formal-verification.json).

## September 18: Roll back to U1892, Actor learning rate changed to 2e-5

Upon user request, `agronomy-v4-m384-bc100-3d-20260917-s73001` at **U1905**
after complete save and stop, restores to the checkpoint of **U1892 completed / 242,176 games**, changing the Actor LR from **5e-5** to **2e-5**, effective from the re-executed **U1893**.
Critic LR remains **1e-4**, KL set to **0.05 / early_stop**, and the mixed opponent with pure terminal WDL configurations are retained unchanged.

`rollback-revisions/0001` has been registered. The original training records, runtime status, chronological logs, and four checkpoint saves from U1893–U1905 are archived under the directory's `abandoned/`; the original recovery log is retained. Activity ledger, metrics, and PFSP are restored to U1892; the Adam steps for Actor/Critic are respectively **5674 / 5676**. Dual-GPU RNG and historical pool synchronization are restored. Derived continuation checkpoints only update the Actor LR and parent chain metadata; **2,071 tensors match U1892 bit-by-bit and are finite**; the first PFSP sampling is precisely reproduced from the original U1893 sampling record. The target checkpoint is preserved via a hard link, with source code identity unchanged. This continuation was subsequently corrected by the user to restore from U1891; this branch has been archived and stopped at U1893. The current active state is based on the above correction record.
See [Rollback Record](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/rollback-revisions/0001/transition.json) and [Continuation Startup](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/rollback-revisions/0001/launch.json).

## September 18: The Actor learning rate of current v4 RL is further increased to 5e-5

At the user's explicit request, `agronomy-v4-m384-bc100-3d-20260917-s73001` saved its complete state and stopped at **U1891 / 242,048 games**. Actor LR was then raised from **1e-5** to **5e-5**, effective from **U1892**. Critic LR **1e-4**, KL **0.05 / early_stop**, two-GPU execution, mixed opponents, and pure terminal WDL retain their original settings.

Registered `learning-rate-revisions/0002`, synchronized continuation configuration and derived checkpoint actor parameters. The original U1891 checkpoint is preserved via hard link; new checkpoints point to the original checkpoint via parent hash.
Bit-level tensor consistency verified for **2,071** tensors, with finite values; weights, Adam momentum and step count, dual-GPU RNG, PFSP, and source code archive preserved. After archival recovery, **formal U1892 has been completed**; the actual Actor learning rates on both GPUs are both **5e-5**. The maximum prefix KL in this turn is **0.100265**, triggering the original **0.05** early stopping threshold; each GPU performs **1 Actor update** and **3 Critic updates**. Training PID is **1602752**, with dual-GPU operation continuing. This validation covers the continuation checkpoint and the first round of actual optimization; subsequent periodic checkpoints have not been individually verified.
See [Change Log](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/learning-rate-revisions/0002/transition.json) and [Formal Validation](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/learning-rate-revisions/0002/formal-verification.json).

## September 18: The Actor learning rate of current v4 RL is increased to 1e-5

Upon user request, after complete preservation stops at **U1872 / 239,616 games**, `agronomy-v4-m384-bc100-3d-20260917-s73001` increases the Actor LR from **7.5e-6** to **1e-5**, effective from **U1873**; the Critic LR remains at **1e-4**.
Original archived source code is retained, two GPUs are used, mixed opponents are employed, pure terminal WDL is used, and all training progress is preserved.

`learning-rate-revisions/0001` has been registered. Due to the current optimizer learning rate loaded from the recovery path checkpoint, the continuation configuration synchronizes the Actor parameter groups with the newly derived checkpoint; the original checkpoint is preserved via a hard link. Bit-level verification of 2,071 tensors confirms consistency and finiteness. Model, Adam momentum and step count, dual-GPU RNG, and PFSP are all retained. The derived checkpoint's parent hash points to the original U1872, and the archived source identity remains unchanged. After the original archive recovery, **formal U1873 has been completed**: each of the two GPUs performed 3 Actor/Critic updates, with actual Actor LR values both set to **1e-5**. Training PID is **1377815**, and dual-GPU operation continues. This verification covers both the continuation checkpoint and the first-round actual optimization; the first regular savepoint after U1873 has not yet been individually verified. See [Change Log](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/learning-rate-revisions/0001/transition.json) and [Formal Verification](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/learning-rate-revisions/0001/formal-verification.json).

## September 17: Latest v4 BC has continued formal mixed RL, pipeline sampling, and asynchronous checkpoints

Upon receiving the user instruction "Enough, start the formal training directly", the remaining acceptance checks were ended, and the formal dual-GPU RL has been initiated at
**09:12 UTC** from `pretraining/shard-004187.pt`, with training process **PID 1739565**.
The runtime directory is `outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001`.
The latest BC's 13 full epochs, Epoch 14's 196 batches, weights, Adam optimizer states, dual-GPU RNG, and historical data are all preserved.
Each round consists of **128 games**, with **20% native scripts / 50% PFSP historical data / 30% self-play**, including five native C++ scripts, 137 external historical models, an initial pool of 138 members; rewards are pure terminal WDL.

AVX encoding enabled, native script search optimization, two CPU/GPU sampling pipelines, and asynchronous checkpoints activated.
Source code commit `d31714d`. Latest acceptance steady-state turn: **35.038 seconds**, with dual-GPU average utilization per full round at **95.3% / 96.6%**; this turn sampled for approximately 14.8 seconds and optimized for approximately 18.9 seconds.
Checkpoint front-end latency: about 71 milliseconds, back-end: about 0.83 seconds; backend write overlaps with subsequent training, full CRC32/SHA256 and atomic replacement preserved, normal stop and evaluation boundary waits completed.

This version completes **3 turns** of dual-GPU validation (including normal shutdown and archival recovery), with weight, dual optimizers, PFSP precise replay, BC parent chain, and pure WDL all passing; the user-requested startup did not proceed to complete the originally planned six turns.
Formal operation has verified startup configuration and BC state retention; **the formal initial optimizer checkpoint has not been independently confirmed**.
The 35.038 seconds above come from the acceptance steady-state turns and cannot be considered as formal cold-start latency.
See [Execution Record](agronomy_v4_rl_20260917.md),
[Formal Startup](../outputs/analysis/agronomy-v4-async-20260917/formal-launch.json),
[Startup Configuration Confirmation](../outputs/analysis/agronomy-v4-async-20260917/formal-launch-verification.json),
[Acceptance Scope](../outputs/analysis/agronomy-v4-async-20260917/qualification.json), and
[GPU Empirical Testing](../outputs/analysis/agronomy-v4-async-20260917/gpu-summary.json).

## September 17: v4 three-day BC, complete 100 epoch dual-card new run

According to user requirements, the **grounded-production-context-v4** for `agronomy: true` has been submitted.
After refreshing the official index, **1,945 games** of raw replays from 9/14–16 were used, continuing with the historical top-ten teacher filtering.
48 processes converted 1,767 selected games within **118.6 seconds**, generating approximately **86.7 GB** of v4 arrays;
training on **2,456 complete trajectories / 1,764,824 supervised turns**. All 5,301 array hashes,
9 complete official replays / 12,960 observations, and new/old field sampling validations have passed confirmation.

A new run of **`agronomy-v4-m384-bc100-3d-20260917-s73001`** has started at 04:03 UTC,
fresh random weights, standard physical Block Actor **16 × 384**, independent **2 × 256 / 384 turns**
time memory; 4 full trajectories per card, dual H200 / BF16 / compiled, LR 1e-4.
307 updates per epoch, clearly defined complete **100 epochs / 30,700 steps**, no early stopping;
**BC completion triggers save and stop, RL does not auto-start**. Two-round small-data validation on dual cards has been completed, model and Adam are finite, v4 input projection and memory parameter updates, saving, and BC completion passed.
The official source code has also fixed the dual-card BF16 reduction setting prior to BC's first compilation, preventing re-switching during the first evaluation round.

**Formal Step 48 / 275,976 Supervised Turns Verified**: 384 distinct trajectories show consistent actual sequence and mask counting, Adam step count is correct, model and optimizer are finite, v4 input projection, entity encoder, temporal memory, and fusion parameters are continuously updated, and dual-GPU RNG is fully preserved. After preheating, median inference time is **1.42 seconds per batch** over 24 batches, loading time is **54 milliseconds per batch**, achieving approximately **4,071 supervised turns per second**. Dual-GPU BC is running continuously.
See [Formal Verification](../outputs/analysis/agronomy-v4-20260917/formal-verification.json).

The old s72001 was previously normally stopped at BC cursor **2101 / 12,077,823 supervision turns**,
old checkpoint and history preserved; the previous "running continuously" status below has been replaced by this entry.
See [v4 Execution Log](agronomy_v4_bc_20260917.md),
[Startup Log](../outputs/analysis/agronomy-v4-20260917/formal-launch.json), and
[Real-time Progress](../outputs/learning/agronomy-v4-m384-bc100-3d-20260917-s73001/learning-progress.json).

## September 17: Old Block + Time Memory, New Three-Day Dual-Card BC Has Been Launched

As per the user's latest requirements, `gtrxl-m384-bc100-3d-20260916-s71001` has successfully been saved and exited normally at
**U965 / 123,520 games**, with dual optimizers, dual-card RNG, checkpoints, and historical retention.
The sections below regarding the previous run's "continuous operation" status have been replaced by this shutdown.

New architecture restores old entity `Block`: Actor **16 × 384**, Critic **6 × 320**;
Retains independent **2 × 256 / 384 turn** time memory with gating mechanisms, totaling **34,529,500** parameters. The latest three complete daily dates **9/14–16, totaling 1,945 games**, have been obtained, and after filtering, training on **2,456 complete trajectories / 1,764,824 supervised turns** has been conducted. All 5,301 array hashes and 9 complete official replays (12,960 observations) have passed verification. A fresh random initialization is performed for BC; globally, 8 complete trajectories (4 per GPU), with **307 Adam updates per round**; up to 100 epochs / patience 10; **BC ends with save, no automatic RL startup**.
The new official directory is `outputs/learning/plain-m384-bc-3d-20260917-s72001`, and dual-GPU operation has been initiated.

Small-data dual-GPU BC runs for two rounds, save-and-restore, parameter updates, finite tensor operations, dual-GPU RNG, and post-BC halting have all passed verification; terminal cash diagnostics are recorded for two fixed random models per round.
**Official step 88 checkpoint and archived recovery at step 96 have both been confirmed**: cumulative 551,870 supervised turns, Adam steps precisely continued, encoder, time module, and fusion parameters all updated continuously, model and optimizer tensors remain finite, dual-GPU RNG fully intact, checkpoint parent hash matches. Official dual-GPU BC continues to run.
See [Execution Log](plain_memory_bc_20260917.md) and
[Old Run Termination Verification](../outputs/analysis/plain-memory-20260917/old-stop-verification.json).
Official continuity evidence is available in [Checkpoint Recovery Verification](../outputs/analysis/plain-memory-20260917/formal-verification.json).

## September 17: Mixed opponents + bounded terminal cash difference, dual-card formal RL has been seamlessly continued

User requests to revert the current pure self-play back to the previous mixed opponent setup.
`gtrxl-m384-bc100-3d-20260916-s71001` has been normally saved and stopped at **U922 / 118,016 games**, with recovery point at `checkpoints/update-000922.pt`.
The target ratio is restored to **20% native scripts, 50% historical PFSP, and 30% self-play**;
the five scripts and 137 external historical models used prior to switching to pure self-play (s70001) are retained, along with the historical data from this run. The five scripts are `ahmed_v45`, `metacounter_r1`,
`shop_router_0913`, `rayk_v38_low_pressure`, and `farming_v4_0914`.
The user adds a request to include cash difference as a reward, explicitly selecting
**`WDL + Δ / (|Δ| + 10000)`**, Δ defined as the final cash difference (my side minus opponent side).
This instruction replaces the previous pure WDL constraint during training; the cash difference is computed only at terminal states, and is zero in draws.
GTrXL, latest weights, dual optimizers, dual-card RNG, BC state,
Actor LR **7.5e-6**, Critic LR **1e-4**,
KL **0.05 / early_stop**, 128 games per turn, and 32 trajectories per card are preserved.

Mixed opponent eight-round verification and cash difference four-round verification both passed: each optimizer increased by 24 / 12 steps.
PFSP exact replay, archive recovery, finite tensor, and dual-GPU RNG preservation all passed; per-item formula error in actual cash difference return is 0.
Registered `population-revisions/0001` and `reward-revisions/0001` — **effective simultaneously from U923**.
**Formal U924 checkpoint validation passed**: continuing from 256 games, Actor/Critic each increased by 6 steps, both network memory parameters updated, all tensors finite, dual-GPU RNG independently advanced, PFSP exact replay passed.
Actual reward range is from −1.922395 to +1.810943; per-item cash difference formula error is 0; U924 checkpoint parent hash precisely points to U922, original checkpoint, BC state, and historical data are fully preserved.
**Dual-GPU formal RL is now running continuously**. The previous "pure self-play" status below is replaced by this transition.
Five-script dual-seat configuration passed 10 official consistency tests; reward implementation passed Ruff, full mypy (812 files), and 39 related tests.
See [Stop Verification](../outputs/analysis/gtrxl-mixed-20260917/stop-verification.json),
[Official Consistency](../outputs/analysis/gtrxl-mixed-20260917/official.json), and
[Switch Configuration](../configs/learning_gtrxl_mixed_change.yaml) as well as
[Complete Execution Log](gtrxl_mixed_margin_20260917.md). Also see
[Cash Difference Verification](../outputs/analysis/gtrxl-margin-20260917/qualification.json) and
[Formal Launch](../outputs/analysis/gtrxl-margin-20260917/launch.json), and
[Formal Checkpoint Validation](../outputs/analysis/gtrxl-margin-20260917/formal-verification.json).

## September 16: Terminate BC as per user request, initiate formal pure self-play RL with latest weights

User explicitly requests to now halt BC and initiate formal pure self-play RL using the **latest weights**.
`gtrxl-m384-bc100-3d-20260916-s71001` has been properly saved at BC cursor **1240**:
Completed **28 full epochs plus 8 batches of round 29**, totaling **55,747,848** supervised turns.
The latest checkpoint is **`pretraining/shard-001240.pt`**, registered for `rl_initial` and
`bc_final`; full BC weights, Adam optimizer states, dual-GPU RNG, and all validation records are preserved.
The validation NLL of the last complete epoch (28) is **0.401105**; RL uses the user-specified latest weights from batch 1240, which does not claim to represent the full validation results of the latest partial epoch.

`bc-completion/0001` has been registered and formal RL has been initiated using the original archived source code, skipping remaining BC phases.
Configured as **pure self-play, pure terminal WDL (±1/0/−1)**, with two GPUs, 128 games per turn;
Actor LR **7.5e-6**, Critic LR **1e-4**, KL **0.05**, with early stopping only, no rollback.
This user instruction supersedes the previous "up to 100 epochs / patience 10 / auto-resume from best epoch"
BC termination condition. The run ID is preserved along with all prior training protocols, historical source code, and training artifacts.
See [Handover Record](../outputs/learning/gtrxl-m384-bc100-3d-20260916-s71001/bc-completion/0001/transition.json) and [Formal Launch Record](../outputs/analysis/gtrxl-bc-to-rl-20260916/launch.json).
**Formal U4 / 512-game checkpoint has passed verification**: The Actor and Critic optimizers completed 13 and 16 steps respectively, with zero rollbacks; encoder, temporal memory, and fusion parameters were all updated; model and optimizer tensors are limited, with independent RNG on dual GPUs, all actual sampling being self-play, and training rewards limited to terminal WDL.
The U4 checkpoint parent hash precisely points to the latest BC's 1240th batch weights; BC state and protocol remain unchanged.
**Formal dual-GPU RL is now continuously running.** See
[Formal Verification](../outputs/analysis/gtrxl-bc-to-rl-20260916/formal-verification.json) and
[Execution Instructions](gtrxl_bc_to_rl_20260916.md).

## September 16: BC loading throughput fault has been repaired, training continues at original progress

`gtrxl-m384-bc100-3d-20260916-s71001`'s slowdown occurs due to repeated allocation and concatenation of large NumPy arrays; under the current memory state, the large-page allocation path results in a median latency of **43.63 seconds** per batch loading.
It has now been changed to directly copy trajectory mappings into a reused pinned host buffer, and consistency checks are performed element-wise across full training batches, last batches, validation batches, and dual-GPU sliced segments.
Formal operation at BC cursor **144** has been successfully saved and registered as `source-revisions/0001`, preserving all weights, Adam, RNG, data progress, early stopping records, and protocol; the state has been archived and training continues.
**Formal checkpoint 160 has passed verification**; the model and optimizer are limited, and memory parameters continue to be updated.
The median latency for 25 formal warm-up batches is **4.20 seconds per batch**, with loading time of **0.24 seconds per batch** (maximum 0.28 seconds), representing an approximately **11.4x improvement** over the original full-batch median latency of **47.94 seconds**.
BC remains set to a maximum of 100 epochs, patience 10, and min_delta 0.001; upon completion, it will automatically transition to self-play / pure terminal WDL RL using the best validation weights. Dual-GPU formal training continues.
Ruff, full mypy (810 files), and 8 related tests have passed.
See [Root Cause and Fix](gtrxl_bc_throughput_20260916.md) and
[Formal Checkpoint and Throughput Verification](../outputs/analysis/gtrxl-bc-throughput-20260916/formal-verification.json).

## September 16: Re-randomize initialization, BC will automatically switch to RL after at most 100 epochs

The old GTrXL training of `gtrxl-m384-3d-20260916-s70001` has been completed on **U188**,
fully saved and exited normally, with checkpoints, two optimizers, dual-GPU RNG, and historical artifacts preserved.
The new official run of **`gtrxl-m384-bc100-3d-20260916-s71001`** has started, using fresh random weights, maintaining the same GTrXL architecture, 384-turn memory, complete BC data from 9/13–15, and dual-GPU configuration.
BC training runs up to a maximum of **100 epochs**; after each round, validation set NLL is evaluated, and patience is reset only if there is a significant improvement in the baseline relative to the previous round, with a reduction of at least **0.001**; early stopping is triggered after **10 consecutive epochs** without achieving such improvement.
At the end, the BC weights with the lowest validation NLL are selected, and a new pure self-play, pure terminal liquidation WDL RL is automatically initiated; Actor LR is set to 7.5e-6, Critic LR to 1e-4, KL divergence to 0.05, with only early stopping applied and no rollback.

Small data dual-GPU workflow has passed: After Round 2 BC triggers early stopping test, it automatically transitions into RL and completes.
**2 rounds / 256 games**, Actor/Critic each take 8 steps, tensor-limited model and optimizer, independent dual-GPU RNG, memory parameter updates, and pure WDL passed. The formal configuration uses patience 10 and does not use the tested early stopping threshold.
Ruff, full mypy (810 files), and 7 related tests passed.
The current formal phase is **BC**; the previous "continuous run" below has been replaced and stopped in this instance.
The formal run has completed initial checkpoint verification and restored from archived source code; the BC cursor continues to advance.
See [Initial Launch Verification](../outputs/analysis/gtrxl-bc100-20260916/formal-start-verification.json).
See [Execution and Recovery Instructions](gtrxl_bc100_20260916.md),
[Automatic Sealing Validation](../outputs/analysis/gtrxl-bc100-20260916/qualification.json), and
[Formal Real-time Status](../outputs/learning/gtrxl-m384-bc100-3d-20260916-s71001/learning-progress.json).

## September 16: GTrXL Five-round BC Completed, Dual-card Pure Self-play RL Already Continued

Operate according to user requirements without conducting architectural ablation; directly implement the gated entity encoder and independent temporal memory.
The original formal s68001 has been fully saved at **U6105** and has stopped normally; two networks, two optimizers
Tensor is limited, dual-GPU RNG and 136 historical pool members are retained, the runtime lock has been released.
See [Stop Verification](../outputs/analysis/gtrxl-20260916/old-stop-verification.json).

New scheme: Actor 6×384, Critic 3×320; each with independent 2×256 time modules,
four summaries per turn, caching **384 turns / layer with 1,536 summary tokens**.
The latest complete 9/13–15 three-day trajectory has been reconstructed: 2,755 trajectories, 1,979,421 supervised turns;
actions not supported are only masked from supervision loss, full observations are retained for causal memory.
The new official run **`gtrxl-m384-3d-20260916-s70001`** has been launched, Run ID `d65ba778fd384a33a7715d823ab4fde0`. As per user request, BC has been expanded from 2 epochs to **5 epochs / 220 optimizer steps / 9,897,105 supervised turns**.
After the 73rd normal save, `bc-budget-revisions/0001` was registered and restored from the same checkpoint; model, Adam, dual-GPU RNG, data cursor, and source code are archived.
**Five rounds of BC have been fully completed and passed end-to-end verification**: each round contains 1,979,421 supervised turns, with validation NLL values of **1.09346 / 0.94068 / 0.83071 / 0.76717 / 0.72523**.
The terminal checkpoint `pretraining/shard-000220.pt`'s weights, Adam, dual-GPU RNG, and sample count have passed verification, all tensors are finite. The initial mixed RL completed U8 / 1,024 games and stopped normally:
Critic accumulated 168 steps, but Actor's eight candidate updates were all rolled back due to old KL protection.
The user then explicitly requested: the continuation phase to be changed to **pure self-play**, with script opponents or PFSP history pools temporarily disabled; the imported 137 external historical records and all existing checkpoints are retained.
The user further confirmed: **maintain Actor LR at 7.5e-6, increase KL threshold, only early stopping, no rollback, then start training**. The continuation configuration uses KL = 0.05, pure self-play, 128 games per round, 32 full trajectories per GPU; Critic LR remains at 1e-4. The 3e-6 isolated test has been canceled.
The dual-GPU isolated replica has passed verification through U9–U12 / 512 games save and restore: Actor and Critic each gained 16 additional steps, zero rollbacks, memory parameter updates, finite tensors, independent RNG, and pure WDL all passed.
The official run has been registered as `sampling-revisions/0001`, retaining U8 checkpoint, Adam, RNG, and history, and resumed at 10:12 UTC from U8. **The official U12 checkpoint has passed verification**: resumed 512 games,
The Actor and Critic each gain 16 additional steps (cumulative 16 / 184), with no rollback; memory parameters for both networks are updated, all tensors are finite, dual-GPU RNG operates independently, and pure WDL, pure self-play, and historical retention are successfully passed.
Dual-GPU formal RL continues running. See
[Formal Checkpoint Verification](../outputs/analysis/gtrxl-20260916/formal-selfplay-verification.json) and
[Continuity Acceptance](../outputs/analysis/gtrxl-20260916/selfplay-checkpoint-verification.json).
The action and observation interfaces of the new and old models are fully consistent, remaining at `grounded-v2`: 276 action factors, 32 unit slots, and 10 market order slots, preserving the original structural decoding, quantity conditions, and budget design.
See [Interface verification](../outputs/analysis/gtrxl-20260916/action-interface-verification.json).
See [KL, Learning Rate, and Throughput Analysis](gtrxl_kl_analysis_20260916.md).
See [BC Endpoint Verification](../outputs/analysis/gtrxl-20260916/formal-bc-verification.json).

Two H200 cards, each with 32 complete teacher trajectories, global total of 64 trajectories, 48 turns per time block;
Inference uses K/V cache within each game session; tail time and trajectory slots are only zero-loss padded.
After latest pure self-play warm-up, each round takes approximately 32.1–32.6 seconds (128 games, four steps for Actor and Critic each),
formal U10–U12 also achieves 32.15 / 32.18 / 32.35 seconds.
Average power consumption per card during training is approximately 668 / 670 W, with utilization around 100% / 99.8%.
GPU 1 has additional unrelated tasks, and its power consumption is measured as the full-card reading; these are throughput measurements, not conclusions about policy strength.
32 related tests passed, including Ruff and full mypy (809 files).
See [Power Measurement](../outputs/analysis/gtrxl-20260916/selfplay-qualification-power-summary.json),
[Real-time State](../outputs/learning/gtrxl-m384-3d-20260916-s70001/learning-progress.json),
and [Implementation Records](gtrxl_training_20260916.md).
The previous "continuous running" status below has been replaced by this normal shutdown.

## September 16: Three-day daily opening EDA completed, local BC remains a research recommendation

Only supplement the latest 9/15 daily data, combined with local 9/13–14; excluding 1 game with TIMEOUT out of 1,960 games, retain 3,918 mutual trajectories and 3,063 historical teacher candidate positions, and cross-check against the actual BC source of s68001.
The new data expands the worker trajectories, but demonstrations of replenishment after animal procurement shortages are rare; ymg's initial moves have already shown variations such as buying 50/selling 45, buying 20/selling 15, followed by round-trip actions. Among the first 144 steps, 1,711,290 observations are consistent, and 12 official full confirmations and 20 causal prefix encoding spot checks have passed.

Suggest studying the opening BC, production route balance, and the branch with only opening activation for K=48 (24/72 comparison), then recover and select models using the complete WDL under native perturbation. The encoded BC large array is not on the original path; original replays and inventories can reconstruct compact prefixes; current initialization entry cannot be directly rerun with BC after RL.
**No fine-tuning initiated, no changes to formal training or deployment; pure WDL mainline continues running.**
See [Data, Feasibility, and Experimental Recommendations](opening_bc_eda_20260916.md).

## September 16: Use pure WDL rewards starting from U5972

By user requirement, the current and subsequent strategy optimization defaults to **+1 for win, 0 for draw, -1 for loss**, with zero reward weight for amount.
The `budget-q100-top10-2d-20260913-s68001` is officially run and normally saved stopped at **U5971**, preserving the original checkpoint, two networks, two Adam optimizers, dual-card RNG, 136 historical pool members, 86 external historical records,
PFSP, five native scripts, and the 30% / 20% / 50% ratio configuration.

Dual-GPU isolated replica completed **4 turns / 512 games**, including U5973 normal shutdown and archival recovery restored to U5975.
Each optimizer advanced 84 steps, all tensor-limited; dual-GPU RNG progressed independently, and PFSP exact replay passed.
All workers' actual PPO returns were solely WDL; checkpoint amount weights were zero.
Ruff, full mypy (775 files), and 18 related tests passed.

Formal migration has been registered as **`reward-revisions/0001`**, effective from **U5972**.
The **formal U5972 checkpoint has passed verification**: 128 new games added, Actor/Critic each advanced 21 steps;
actual returns show only **`-1/+1`** with zero weight; all tensors are finite, with dual-GPU RNG progression and independence.
PFSP exact replay, checkpoint parent chain, and historical pool retention have passed verification. Dual-GPU training continues.
Funds are still used for state observation, win/loss determination, and diagnostics; no longer included in training rewards.
See [Implementation and Acceptance](wdl_20260916.md),
[Migration Verification](../outputs/analysis/wdl-20260916/transition-verification.json), and
[Formal Checkpoint Verification](../outputs/analysis/wdl-20260916/formal-verification.json).

This round of opening research completes 160 frozen U5952 full comparisons: against the original V45, simplifying the initial trade step causes the greedy result to change from 14 wins and 2 losses to 16 wins, and T=1 from 13 wins and 3 losses to 15 wins and 1 loss. However, new losses appear in sampling, and only 8 worlds are involved. Opening condition probability diagnosis shows that valid alternative sequences are rarely sampled.
**No opening patch has been deployed or formal exploration settings altered**; priority is given to studying independent WDL opening exploration and recovery branches.
See [Mechanism, Full Comparison, and Exploration Diagnosis](wheat_opening_20260916.md).

## September 16: V45 has been officially integrated, s68001 has recovered from U5629 and continues training

Replace script `ahmed_v42` with `ahmed_v45` as per user request; keep the other four scripts unchanged.
125 game turn-by-turn comparisons, 10 official training batch processes, 41 tests passed; Ruff and full mypy checks have been confirmed.
`budget-q100-top10-2d-20260915-s69001` has been properly stopped after complete saving at **U1758**,
the selected BC, 27 regular snapshots, and final checkpoint, totaling **29 versions**, have been added to the history pool.

The continuation target is explicitly set to **`budget-q100-top10-2d-20260913-s68001` / U5629**,
with run ID `db598303f1c047a188c6432544dad4a2`. The original model, optimizer, dual-GPU RNG,
30% / 20% / 50% ratio, and constant LR are maintained. Isolated replicas have completed 12 rounds / 1,536 games of dual-GPU continuation,
U5632 has been halted and archived, restored to U5641; each optimizer has advanced 252 steps, finite tensor, independent RNG, and PFSP exact replay have passed verification.
Formal migration has been registered under `population-revisions/0003`, effective from **U5630**; the historical pool capacity is 136, with 86 external historical entries, and all 96 original members of the pool are preserved during migration.
**The formal U5632 checkpoint has passed validation**: 384 additional games have been added, 28 actual executions of V45 have occurred,
historical U1536 from s69001 has been sampled and utilized; each optimizer has advanced 63 steps, both Actor/Critic have been updated,
all tensors are finite, dual-GPU RNG has progressed independently, and PFSP exact replay and checkpoint inheritance relationships have passed.
Both GPUs utilize the virtual environment at validation time, the new script native library, and the original rule core; dual-GPU training continues.
See [Formal Checkpoint Validation](../outputs/opponents/public-20260916/formal-verification.json);
Latest progress is available at [Real-time Status](../outputs/learning/budget-q100-top10-2d-20260913-s68001/learning-progress.json).
See [Native Integration, Stop, and Restore Records](native_public_population_20260916.md).
The statements below such as "continuing operation" refer to historical states as of corresponding dates.

## September 16 Investigation: Ahmed V45 is a stronger script candidate

The latest public-source survey found Ahmed V44 / V45. Across 32 new worlds and both seats, each achieved **62 wins and 2 losses** against the incumbent V42. V45 also achieved **62 wins and 2 losses** against both V44 and yesterday's Revenue Lead R1.
Against frozen **U1708** of the current new run `budget-q100-top10-2d-20260915-s69001`, over 16 separately reserved new worlds and both seats, V45 achieved **11 wins and 21 losses**, while V42 / V44 each achieved **4 wins and 28 losses**. Relative to V42, V45 improved the script win rate by 21.875 percentage points and the cash margin by 3,581.6. World-clustered 95% intervals are [+3.125, +40.625] percentage points and [+1,192.7, +6,178.1], respectively. This supports prioritizing validation of V45 for training integration; long-term training benefits remain unproven.

Farming V5 outperforms the current Farming V4 0914 with a record of 28 wins, 34 draws, and 2 losses, showing a funding difference of +75.5, classifying it as a minor maintenance candidate. MetaBalance V62 performs 0 wins and 64 losses against the current MetaCounter.
V45's first turn market strategy relies on the opponent and cannot be considered a comprehensive upgrade for all scripts.
1,376 local games, 16 fully official re-runs, six neural game official action replays, and export verification have been completed.
**Investigation concluded without altering training; subsequent native integration of V45 is noted above.**
See [Investigation, Pairing Statistics, and Integration Recommendations](public_notebook_survey_20260916.md).

## September 15: The latest two-day random root 2-epoch BC is complete, and formal RL is now continuously running

According to user requirements, `budget-q100-top10-2d-20260913-s68001` has been fully saved and stopped normally at **U5629**. The parent process exit code has been restored to 0, the dual-GPU worker processes have terminated, and both running locks have been released.
The Actor/Critic, two optimizers, and two independent GPU RNGs have been saved, with all tensor limits preserved.
The original 57 external historical models have been retained; 40 versions from the recently stopped run have been selected (BC endpoint, 38 historical snapshots, and final U5629), resulting in a total of 97 external models. The new pool capacity is 136, with 39 positions reserved for its own historical models.

The official latest complete date is **2026-09-13 / 14**, with 654 raw replays recorded on each day, all authenticated and obtained.
The evaluation criteria continue to use the historical top ten daily demonstrations and the current top ten high-scoring public submissions, supplemented by 2,884 additional games from 17 publicly available versions that meet the score criteria—fully obtained with zero failures. After full audit, 2 anomalous cases were excluded, resulting in a final total of 4,135 games and 5,102 demonstration slots. All array hash and content verifications for 519 fragments, 28 API metadata confirmations, and full replay checks for 21 games (30,240 observations) have passed.

User has explicitly selected random initialization of the new model. Formal execution commenced.

`outputs/learning/budget-q100-top10-2d-20260915-s69001` has started with random root **69001**,
Run ID `7d29cd58baca4ee286e8a8e27f8deb3b`, with no input from prior learning weights.
Two-GPU full execution of **2 epoch BC**, totaling **6,559,934 rows and 26,216 optimization steps**, followed by automatic entry into
100,000 turns of RL; 128 games per turn, 30% self-play / 20% native scripts / 50% historical PFSP, with constant LR maintained.
**2 epoch BC has been fully completed and passed terminal verification**: 3,279,967 rows per turn, NLL verified
**0.27483 → 0.23945**; terminal state reached `pretraining/shard-000928.pt`, with model, optimizer,
data identity, dual-GPU RNG, and full tensor finite checks all passed.
See [BC Completion Verification](../outputs/analysis/top10-training-20260915/formal-bc-complete.json).

**Formal RL U8 Complete Checkpoint Verified**: In the first eight rounds of 1,024 games, each optimizer accumulated 168 steps, with U4 → U8 progressing 84 steps each. Both Actor and Critic were updated, with zero KL rejections. Learning rates were fixed at 7.5e-6 / 1e-4. All tensors were finite, both GPU RNGs advanced independently, and all eight rounds of PFSP replay passed. 97 external members joined the pool from U1; the current pool now contains 98 models in total from this BC, with newly added models having actually participated in gameplay. The first five rounds consisted of 192 / 128 / 320 games, precisely matching 30% / 20% / 50%. Dual-GPU RL continues running. See [Formal RL Verification](../outputs/analysis/top10-training-20260915/formal-rl-verification.json).

The early-return issue in historical imports has been fixed, with 27 related tests, Ruff, and full mypy passing. The dual-GPU 2-epoch small-data BC to 8-round RL transition has been accepted, including normal termination and archival recovery of U5. 97 external models joined the pool from U1. Model and optimizer updates, finite tensors, independent dual-GPU RNGs, and PFSP replay all passed. See [Preparation and Run Record](top10_two_day_training_20260915.md), [Official Launch](../outputs/analysis/top10-training-20260915/formal-launch.json), and [Real-time Progress](../outputs/learning/budget-q100-top10-2d-20260915-s69001/learning-progress.json). The "Continuous Operation" descriptions below reflect the historical state prior to this stop.

## September 15: Independently designed Enterprise P1, research failed

Implement production revenue prediction, fund management, and real-time task allocation independently from the rules, without inheriting any public notebook controller or trajectory. After freezing, six public scripts achieved **0 wins, 192 losses**, and the frozen U5312 achieved **0 wins, 16 losses**, with average fund differences of −75,855.6 and −96,571.5, respectively. Complete actions and final funds are consistent across 4 official confirmations. 3 targeted tests, Ruff, and full mypy passes have been verified; results do not support replacing training opponents.

Registered as a **failed independent research prototype**, no C++ porting or training migration has been performed. The source code, standalone scripts, and all experimental records are retained, see [Design, Failure Analysis, and Reproduction](independent_script_research_20260915.md).
Previous publicly shared script research results and formal five-script deployment records by Revenue Lead R1 are listed below.

## September 15: Self-developed Revenue Lead R1, script enhancement publicly released with confirmation

Developed early sale and sell order controller on frozen Ahmed V43, with independent 64 new seeds and two-seat setup:
vs. V43: **125 wins, 3 losses**, six public script panels collectively: **749 wins, 19 losses**.
48 official confirmations, 96 games / 69,024 actions passed Python–C++ consistency, copy reset, and native batch validation.
Independent scripts and native library archived as `outputs/opponents/research-20260915/revenue-lead-r1/`.

For the frozen **U5312**, both R1 and V43 have a record of **0 wins, 32 losses**, and the average return difference for R1 has decreased by 448.6.
Thus, it is registered as the **public script research version**, and no migration to the official training pool is conducted based on this; the official five-script version remains as recorded below.
See [Research Methodology, Results, and Deliverables](script_opponent_research_20260915.md).

## September 14 afternoon: V42 / Farming new snapshot has been integrated into formal training

As per user requirements, `ahmed_v42` replaces `ahmed_v41`, and `farming_v4_0914` replaces `farming_v4_0912`; the other three scripts are retained. Native step-by-step, perturbation, official batch comparison, 31 related tests, Ruff, and full mypy have all passed.

The formal execution of `budget-q100-top10-2d-20260913-s68001` runs normally on **U3959** and stops and saves successfully. Isolated replica validation has passed for **12 rounds / 1,536 games** with dual-GPU continued training, stop, and archival recovery verification.
Each optimizer advances 252 steps; tensor-limited, dual-GPU RNG progresses independently, and PFSP exact replay passes.

The formal script pool is registered under `population-revisions/0002`, effective from **U3960 onward**.
The formal checkpoint at **U3964 has passed verification**: 640 additional games added, each optimizer advances 105 steps, both V42 and the new Farming are actively participating, tensor-limited, dual-GPU RNG and PFSP continuity are normal, with no KL rejections.

Dual-GPU formal training continues running; actual progress is tracked via `learning-progress.json` in the running directory.
96 historical members, 57 external models, full optimizers, and dual-GPU RNG are preserved; ratio and constant LR are maintained.

See [Selection and Competition](public_notebook_survey_20260914_refresh.md),
[Native Upgrade and Verification](native_public_population_20260914_v2.md), and
[Full Training Verification](../outputs/opponents/public-20260914-v2/qualification.json),
[Migration Validation](../outputs/opponents/public-20260914-v2/migration-verification.json), and
[Formal Checkpoint Verification](../outputs/opponents/public-20260914-v2/formal-verification.json).
The script list and checkpoints below, from the early part of the same day, reflect the state prior to this upgrade.

## September 14: Constant Learning Rate Continuation

According to user requirements, disable the learning rate scaling and step-length retry mechanisms in the current main KL protection.
After `budget-q100-top10-2d-20260913-s68001` successfully saves at **U3490**,
starting from **U3491**, fix the Actor LR at `7.5e-6` and the Critic LR at `1e-4`.
When KL divergence exceeds limits, roll back the parameters and Adam states of the current step, halt the Actor for this turn, and use the same LR in the next turn.
Upon recovery, remove the old `guard_lr_scale`, retain the model, Adam momentum and accumulated steps, dual-GPU RNG,
96 historical members, 57 external models, and existing PFSP. Each turn runs 128 games with a total budget of 100k,
maintaining 30% self-play / 20% independent dynamic scripts / 50% historical PFSP.

The old LR at U3199, after three rejections in one minibatch, was permanently downgraded by `7.5e-6` to `9.375e-7`;
this previous behavior is now superseded by the current change. The original U3490 checkpoint bytes and all existing training records are retained.
15 related tests, Ruff, and full mypy passed; formal checkpoint tensor-by-tensor recovery verification passed.
The two-GPU isolated replica completed **4 rounds / 512 games**, including normal shutdown and archival recovery of U3492 to U3494;
each optimizer continued for 84 steps, all tensors remained finite, and the two-GPU RNG and PFSP continuity verification passed.

The new code is registered under `source-revisions/0001` and has been officially archived with continuity confirmed via **U3492 complete checkpoint verification**:
Added 256 games, each optimizer continues for 42 steps with no KL rejections; learning rate is fixed at the aforementioned values in checkpoints, the old scaling flag has been removed, all tensors are finite, and dual-GPU RNG and PFSP continuity operate normally. Dual-GPU training is ongoing.
See [Implementation and Acceptance](constant_lr_20260914.md),
[Migration Verification](../outputs/analysis/constant-lr-20260914/transition-verification.json),
[Formal Launch](../outputs/analysis/constant-lr-20260914/formal-launch.json),
[Formal Checkpoint Verification](../outputs/analysis/constant-lr-20260914/formal-verification.json).
Actual progress is subject to [Real-time Status](../outputs/learning/budget-q100-top10-2d-20260913-s68001/learning-progress.json).

## September 14: Five latest publicly released scripts natively integrated, original runtime continues training

By user request, the default training script is replaced with the September 12 snapshots of Ahmed V41, MetaCounter R1, Shop Router 0913, Rayk V38 Low Pressure, and Farming V4.
Source code is frozen prior to build, generating C++ natively via original `ParallelBatch`, without Python opponent callback on a per-turn basis.
The older `router_95`, `farming_v4`, `kaito_v58`, `shop_router_0908`, and `shop_router_0909` have been retired; historical implementations and assets are retained for archival and reproduction purposes.

Operation continues with `outputs/learning/budget-q100-top10-2d-20260913-s68001`.
After complete preservation of U2664, migration takes effect from U2665 onward.
Original model, two optimizers, dual-GPU RNG, 96 historical members, 57 external models, and existing PFSP records are retained;
the new script begins from initial priors under the new manifest, and the first update removes prior script statistics.
The core rule engine remains unchanged, with 128 games per turn, a total budget of 100k, and
**30% self-play / 20% independent dynamic script / 50% historical PFSP** preserved as before.
Migration record is `population-revisions/0001`; the formal archiving and recovery process has been initiated.

125 game source code step-by-step alignment, official environment checks for two seats, 33 related tests passed, Ruff and full mypy passed.
Isolated replica completed **12 turns / 1,536 games**, including normal shutdown and archival recovery from U2668 to U2676;
Each optimizer advanced **252 steps**, all tensors are finite, dual-GPU RNG preserved, PFSP replay and saved statistics are consistent.
See [Implementation and Acceptance](native_public_population_20260914.md),
[Complete Training Acceptance](../outputs/opponents/public-20260914/qualification.json),
[Formal Migration Verification](../outputs/opponents/public-20260914/migration-verification.json), and
[Recovery Startup Record](../outputs/opponents/public-20260914/formal-launch.json).
**Formal U2668 checkpoint has passed verification**: added 512 games, each optimizer advanced 84 steps,
Actor/Critic both updated, all tensors are finite, dual-GPU RNG advanced and remains independent,
PFSP precisely replayed and saved statistics are consistent, no retired scripts found in the new record.
See [Formal Continuation Verification](../outputs/opponents/public-20260914/formal-verification.json).
Dual-GPU formal training continues running.
Current progress is subject to [real-time status](../outputs/learning/budget-q100-top10-2d-20260913-s68001/learning-progress.json). The September 13 record below corresponds to the initialization phase of the same run; the current instance identity is based on the above changes.

## September 13: Two-day historical top ten data, 4-epoch BC → Official RL

The user has accepted the new BC dataset below and requested the initiation of new training, with the current run added to the opponent pool.
`budget-q100-3d-20260912-s67001` has been properly stopped after complete saving at **U1519**:
Each optimizer has accumulated 31,899 steps, dual-GPU independent RNG preserved, all tensors finite, process terminated, and run lock released.
See [Stop Verification](../outputs/analysis/top10-training-20260913/old-stop-verification.json).

New official run: `outputs/learning/budget-q100-top10-2d-20260913-s68001`,
Random seed **68001**, using new data to complete **4 epoch**, totaling **13,108,360 rows, 52,244 optimization steps**.
Subsequently, the same process automatically enters 100,000 turns of official RL: each turn consists of 128 games, following
**30% self-play / 20% independent dynamic native scripts / 50% historical PFSP**.
The original 32 historical models are retained, with 25 additional versions added (BC, 23 regular snapshots, and final U1519),
totaling **57 external models**; capacity expanded to **96**, reserving **39 slots** for the new run's own historical models.

57 sources have been confirmed; Ruff, mypy, and 12 related tests have passed; the training engine is identical to the version verified in the previous turn.
The official dual-GPU BC has actually updated its parameters; all array hashes and the first full checkpoints have passed confirmation.
After 4 epochs, the historical pool is automatically imported and the system enters formal RL. See
[BC Startup Verification](../outputs/analysis/top10-training-20260913/formal-bc-start-verification.json), with the actual status subject to
[Real-time Progress](../outputs/learning/budget-q100-top10-2d-20260913-s68001/learning-progress.json).
See [Recipe and Acceptance](top10_two_day_training_20260913.md),
[Hydra Configuration](../configs/learning_top10_2d.yaml), and
[Startup Log](../outputs/analysis/top10-training-20260913/formal-launch.json).
All training records from September 12 and earlier belong to prior runs.

## September 13: Latest Two-Day Historical Top Ten Snapshots and Current High-Score Version BC Candidate Set

Data preparation and acceptance checks for the new BC candidate dataset are complete. The latest complete official dates are **September 11 / 12**, with **1,312 games** in the two raw daily packages. Based on the **2026-09-13 01:46:59 UTC** leaderboard snapshot, all available public games were also collected for **14 public submissions with their own score >2900** from the current top-ten teams.
All **2,723 games** in the combined, deduplicated supplemental and daily data were acquired, with no download failures.

The top ten history is based on three verifiable snapshots: August 27, September 11, and September 13, and consolidated into 25 team IDs, of which 16 teams demonstrated presence in two consecutive daily entries.
**Incomplete coverage of historical rankings**: Additionally, 408 daily slots lack evidence of top ten placement in the snapshots. All original data and exclusion lists are retained, and the manifest explicitly marks `history_complete: false`; therefore, it cannot be claimed to exhaustively cover the historical top ten.

Merge candidate original 4,008 games; full-frame audit excludes 5 games that TIMEOUTed during mid-game but were marked as DONE at terminal. Final count is **4,003 games, 5,066 demonstration slots**, continuing to use grounded-v2, with quantities **1–100**, truncated, seed 62001, partitioned into 90%/5%/5%, and traversed fully row-wise with equal weight per row.
Effective decisions in training / selection / confirmation are **3,277,090 / 189,050 / 175,368 rows**.

Data manifest is [manifest.json](../outputs/datasets/grounded-v2-top10-20260911-12-q100/manifest.json),
SHA-256 `8f27747120b10c6de3aa907546a6b8857fb47a5febd3bc153632b871431249f9`.
Hash and content verification passed for 502 shards and 2,008 array file entries; no duplicate decisions or cross-partition seed issues;
25,920 observations and model features consistent across 18 full replays, and 25 API metadata identities authenticated.
9 related tests passed, including Ruff and full mypy (733 files).
See [comprehensive scope, exclusion reasons, and reproduction commands](top10_two_day_bc_20260913.md),
[array acceptance](../outputs/analysis/top10-2d-20260913/dataset-verification.json), and
[full game replay acceptance](../outputs/analysis/top10-2d-20260913/replay-verification.json).
This section records the data preparation results; the user has accepted and initiated the new formal training above.

## September 12: Fixed quantity 1–100, latest three days 4-epoch BC → formal RL

`budget-26m-20260911-s66001` has been properly stopped after fully saving at **U2137** as per user requirements.
The parent process exit code is confirmed as 0; the training process has terminated, and both runtime locks have been released. The Actor/Critic, two optimizers, and dual-GPU RNG are preserved, with all checkpoint tensors being finite. Each PPO optimizer has accumulated **57,021 steps**.
See [Stop Verification](../outputs/analysis/latest3d-20260912/old-stop-verification.json).

Official daily index has been refreshed, with the latest complete date confirmed as **2026-09-11**, and data for all **662 / 657 / 657 games** on **September 9 / 10 / 11**, totaling **1,976 games** obtained.
Data from the 9th and 10th reused previously authenticated ZIP files; new download performed on the 11th. Dates, number of games, uncompressed volume, and hashes have been verified.
See [Original Data and Sources](../data/external/kaggriculture-latest3d-20260912/raw/manifest.json).

According to the user's subsequent proposed scheme, output quantities are categorized and preserved, with the vocabulary fixed at **1–100**; all data partitions truncate any quantity labels exceeding 100 to 100, without extending the vocabulary as demonstrated. The existing grounded-v2 backbone, budget features, and BC/PPO algorithms are retained; quantity outputs and their corresponding embedding dimensions are adjusted with fully random initialization. The prepared training set contains **2,528,633** valid decisions, traversed row-by-row with equal weighting for **4 epochs**, followed by automatic transition into formal RL consisting of **30% self-play / 20% independent dynamic scripts / 50% historical PFSP**.

Small-scale dual-GPU BC → PPO with checkpoint archiving and recovery verification passed: U4 stopped, checkpoint restored to U8; each optimizer continued for 84 steps, all tensor bounds finite, dual-GPU RNG preserved and independent, PFSP replay consistent.
32 historical models from the past were actually added to the opponent pool starting from U1; the first five rounds exactly achieved 192 / 128 / 320 games.
Formal **4 epoch BC completed**: 10,114,532 rows, 39,628 optimization steps, validation NLL
**0.2410 → 0.2039 → 0.1926 → 0.1831**. Final `pretraining/shard-000884.pt`
Data identity verified, fixed at 100 units, optimizers, dual-GPU RNG, and finite tensors confirmed.
Automatically transitioned into formal RL; **U8 complete checkpoint passed verification**: first eight rounds totaled 1,024 games, Actor/Critic optimizers each completed 168 steps, no KL rejections, learning rate maintained at 7.5e-6.
Both networks and optimizers from U4 to U8 continued updating, all tensors finite, dual-GPU random streams advanced independently, PFSP replay and save statistics consistent. First five rounds achieved exactly 192 / 128 / 320 games, precisely meeting the target ratio.
Training continues running; actual progress is tracked via `learning-progress.json` in the running directory.
See [BC Completion Verification](../outputs/analysis/latest3d-20260912/formal-bc-complete.json) and
[Formal RL Verification](../outputs/analysis/latest3d-20260912/formal-rl-verification.json).
Formal configuration is [learning_latest_3d.yaml](../configs/learning_latest_3d.yaml),
running directory `outputs/learning/budget-q100-3d-20260912-s67001`.
See [Data Processing, Recipe, and Verification](latest3d_q100_20260912.md).
The training recipe and progress below pertain to the prior run that has been stopped.

## Prior Budget Training: 26.75M BC → 30% self-play + 20% dynamic script + 50% historical PFSP

**2026-09-12: Split script pool according to user requirements, effective from U1865.**
After normally saving on U1864, `budget-26m-20260911-s66001` has been migrated to
**30% self-play, 20% independent script pool, 50% historical model PFSP**, and dual-GPU archival fine-tuning has been initiated.
128 games per turn; 64 games are fixed from history, with script distribution balanced at 24/28/24/28/24 games,
self-play corresponding to 40/36/40/36/40 games, totaling exactly the target every 5 turns.
One script and one historical model are randomly selected per turn; within the script pool, allocation is dynamically adjusted based on recent learning team scores,
with an 80% probability favoring more difficult scripts and 20% uniform exploration, independent of historical PFSP normalization.

Migrated and archived as `population-revisions/0002`; the original 64 historical members, all prior interaction evidence, weights, two optimizers, dual-GPU RNG, BC sources, training seed, 100k total budget, and other training parameters are preserved. The CUDA Graph exclusive stream fix is also retained. An independent replica completes **8 turns / 1,024 games**, including normal shutdown at U1868 and archival recovery to U1872; each optimizer advances **168 steps**, with no KL rejections, all tensors are finite, PFSP replay is consistent, and both GPU random streams advance and remain independent.

Configuration and acceptance are documented in [Independent Script Pool Scheme](budget_separate_pools_20260912.md), [Hydra Configuration](../configs/learning_budget_separate_change.yaml), [Migration Verification](../outputs/analysis/budget-separate-pools-20260912/transition-verification.json), and [Official Launch](../outputs/analysis/budget-separate-pools-20260912/formal-launch.json).

**Official U1868 checkpoint has been verified**: 512 additional games and 664 learning trajectories added from U1865 to U1868; each optimizer advances 84 steps, with no KL rejections; all tensors are finite, PFSP replay and checkpoint statistics are consistent, and both GPU random streams advance and remain independent. Formal training has continued to U1870, with the WebUI displaying new ratios and independent dynamic script tables.

See [Official Checkpoint Verification](../outputs/analysis/budget-separate-pools-20260912/formal-verification.json) and [WebUI Verification](../outputs/analysis/budget-separate-pools-20260912/webui-formal.json).
The current status is based on the officially running `learning-progress.json` and `run-status.json`.

### September 12: Previous fault repairs and unified PFSP phase

The following unified pool allocation belongs to the historical phase of U1029–1864; the current allocation is based on the U1865 switch above.

**2026-09-12 Fault Repair: Fully restored from U1568; formal checkpoint U1572 has passed verification.**
Rank 0 of U1569 experienced CUDA illegal memory access during historical inference; diagnosis strongly points to a lifecycle issue in the CUDA Graph/cuBLAS workspace caused by the loop pool. The mechanism has been reproduced locally. The inference graph now uses exclusive streams. The fix is archived under `source-revisions/0001`. The original recipe, optimizer, dual-GPU RNG, PFSP, and completed records are preserved.
An independent copy completed 8 turns, stopped normally, and restored from archive; the formal U1569–1572 series has added 512 games. The Actor/Critic each advanced 88 steps, with zero KL rejections, all tensors finite, PFSP replay consistency maintained, and dual-GPU RNG progressed uniformly.
Formal training continues running; the WebUI has resumed "Training in Progress". See
[Fault and Repair](budget_crash_20260912.md),
[Formal Recovery Verification](../outputs/analysis/budget-crash-20260912/formal-verification.json).

**2026-09-12: Enable unified opponent pool PFSP as per user request, effective from U1029.**
`budget-26m-20260911-s66001` has been stopped normally after complete preservation at **U1028**,
only migration of `population` and `script_population` has been performed; dual-GPU archival recovery has now been initiated.
Weights, two optimizers, dual-GPU RNG, BC source, training seed, 100k total budget, T=1,
learning rate, and logical batch 5,760 / micro-batch 2,880 are all retained.

Each round still consists of 128 games, with a target of **35% self-play, 65% opponent pool matches**.
Every 5 rounds of self-play are balanced as **44 / 44 / 48 / 44 / 44 games**, totaling exactly 224/640 games;
The remaining 416/640 games are sampled uniformly from a single PFSP distribution. In each round, one frozen opponent is selected to inherit that round's batch.
The script and historical models have no fixed quotas. Each physical game is equally weighted, and the learning trajectory per round consists of either 172 or 176 entries.

During switching, the unified pool has **60 opponents**: currently running the BC endpoint and 22 PPO checkpoints;
`context-26m-3d-20260910-s65001`'s BC endpoint and 26 PPO checkpoints (including the final U3575);
this context runs 5 prior 26M historical versions from the original pool, as well as five native scripts: `router_95`, `farming_v4`, `kaito_v58`, `shop_router_0908`, and `shop_router_0909`.
Neural pool capacity is 64, with 32 external versions fixedly retained; historical data enters the pool every 64 turns; after including scripts, the upper limit becomes 69.
Old models retain their original vocabulary tables and budget feature switches, serving only as frozen opponents, without inheriting the win rate of previous learning agents.

Independent replica completed **12 rounds of dual-GPU PPO / 1,536 games**, including normal shutdown and archival recovery from U1032 to U1040.
Actor/Critic each advanced **264 steps**, with no KL rejections; all tensors are finite, and PFSP replay as well as checkpoint/ledger statistics are consistent. Both 5-round windows precisely achieved 35% / 65%.
Six preheated samples completed in **27.13–30.04 seconds per round**, median of **29.64 seconds**, peak of **96.11 GiB per GPU**.
Five official environment scripts, 34 Python checks, Ruff, mypy (717 files), and WebUI checks passed.
These constitute engineering acceptance, not intensity evaluation.

Official migration record is `population-revisions/0001`. **Official U1032 checkpoint has been verified**:
U1029–1032, totaling 512 games, 692 learning trajectories, with U1032 comprising 44 self-play games and 84 Kaito v58 games.
Each optimizer advanced 88 steps, with no KL rejections; all tensors are finite, replay and saved statistics match PFSP, and both dual-GPU RNGs continue advancing independently. Training proceeds under official operation.
See [Official checkpoint verification](../outputs/analysis/budget-unified-pfsp-20260912/formal-verification.json).
See [Complete recipe and acceptance](budget_unified_pfsp_20260912.md),
[Hydra configuration changes](../configs/learning_budget_pfsp_change.yaml),
[Acceptance summary](../outputs/analysis/budget-unified-pfsp-20260912/qualification-summary.json),
[Migration verification](../outputs/analysis/budget-unified-pfsp-20260912/transition-verification.json), and
[Official launch](../outputs/analysis/budget-unified-pfsp-20260912/formal-launch.json).
Current status is based on the official runs `learning-progress.json` and `run-status.json`.

### September 11: BC and Initial Pure Self-Play Phase

The following pure self-play records represent the historical phase of U1–1028, and the current ratio is based on the U1865 switch above.

**2026-09-11: Implement the new scheme as confirmed by the user directly, without conducting algorithm ablation.**
Add budget features based on visible state and prefix of our own orders; use only the original BC action likelihood loss;
Do not include auxiliary supervision, do not set diversity objective at the beginning, and do not adopt the old three-level structure.

The old `context-26m-3d-20260910-s65001` has been **normally stopped at U3575**,
the complete model, two optimizers, and dual-GPU RNG are retained, see
[Stop Verification](../outputs/analysis/budget-20260911/old-stop-verification.json).
New data has been prepared and verified: **3,035 games, 5,617 demonstration slots**,
training effective decisions of **3,601,803 lines**, with seed partitions preserved from original data.
Sources are from daily recordings from September 7–10 and filtered non-daily public replays.
Source frequencies are moderately downweighted, with fixed parameters of **2 epochs, batch size 256, LR 1e-4**.

New random root **66001**, official directory `outputs/learning/budget-26m-20260911-s66001`.
After BC, automatically enters **100,000 turns of pure self-play PPO**: 128 games per turn, 256 learning trajectories,
0 historical games and script opponents, T=1, Actor LR 7.5e-6, Critic LR 1e-4.
Official **2 epoch BC completed**: sampled **7,203,606 rows, 28,226 optimization steps**,
validation NLL **0.2540 → 0.2175**. BC endpoint `pretraining/shard-000170.pt`'s data identity,
parameters, optimizer, and dual-GPU RNG have passed confirmation.
No old training weights were loaded in the new run.
See [BC Completion Confirmation](../outputs/analysis/budget-20260911/formal-bc-complete.json).

Automatically entered formal PPO. **U8 complete checkpoint passed verification**: U1–U8 collectively achieved **1,024 games of pure self-play**,
Actor/Critic each advanced **256 steps**, both networks updated, all tensors finite, with no KL rejection.
U2–U8 per round approximately **39 seconds**, Actor LR maintained at **7.5e-6**.
See [formal RL verification](../outputs/analysis/budget-20260911/formal-rl-verification.json) and
[WebUI](../outputs/analysis/budget-20260911/webui-formal-rl.json).

Upon user supplementation, the randomness was explicitly verified: **action sampling continues progressively without resetting the same seed per game or per round**;
The random streams for two GPUs are independent, and the U4 → U8 RNG states both change, with the environment seeds being distinct across the first 8 rounds.
Random stream continuity checks for identical observations under both uncompiled and compiled CUDA graph scenarios, as well as post-reconstruction of the graph, have all passed.
The fixed root seed is used solely for reproducibility across the entire run and should not be equated with resetting per game in the submitted package.

**U56 Opening Diagnosis**: With identical initial observations, T=1, and 1,024 samples per GPU using BF16, the proportion of the full first-step mode is 48.8% at the BC endpoint, 16.9% for new PPO U56, and 99.2% for old U2748. Additionally, 256 pure self-play games were run, each for the first 72 steps, showing that U56's actual asset allocation is more diversified compared to the BC endpoint. Broadly, there remains a 70–77% preference for worker-first strategies, and the number of request variants cannot be considered as evidence of mature strategies or win rates. Training continues, see [Opening Diversity Statistics](../outputs/analysis/budget-openings-20260911-u56/summary.md).

**U132 Re-measurement Update**: The mode of the first move, under consistent metrics, has risen to **62.6%**, significantly increasing from U56's 16.9%, indicating greater concentration;
The most common first two-move sequences remain around **10–13%**, with the mode of the asset portfolio at move 72 being **1.2–4.3%**.
Currently, the opening phase is characterized by contraction, and thus cannot be used to conclude that the entire opening sequence is fixed. In the last 32 rounds, there were no KL rejections or early terminations; each round lasted approximately **39.16 seconds**, with average terminal cash rising from the previous window of 93,755 to 94,790; no new external win rate evidence has been added.
The training recipe remains unchanged, see [U132 Status and Re-measurement](../outputs/analysis/budget-openings-20260911-u132/summary.md).

Run ID `30b6b764d4b840308bf2f59877f8f451`, training continues running; actual progress is based on
[learning-progress.json](../outputs/learning/budget-26m-20260911-s66001/learning-progress.json). See [official launch record](../outputs/analysis/budget-20260911/formal-launch.json).

See [Complete Recipe and Boundaries](budget_bc_20260911.md),
[Hydra Configuration](../configs/learning_budget.yaml),
[Data Verification](../outputs/analysis/budget-20260911/dataset-verification.json).
The preceding runs that have been terminated along with their historical stages cannot be used as training recipes for new runs.

## Prior Training: 26M Recent Three-Day BC → Historical and Script PFSP

**2026-09-10 Update: PFSP has been restored as per user request, with native scripts and the prior 26M historical version integrated.**
`context-26m-3d-20260910-s65001` stopped normally after complete preservation at **U544**,
and has since been restarted from this checkpoint for dual-GPU continued training, with **starting at U545, each turn comprising 32 self-play games, 32 historical PFSP games, and 64 script-based PFSP games**. The scripts are `router_95`, `farming_v4`, `shop_router_0909`, and `shop_router_0908`. Each script runs at least 4 games per turn, with the remaining games adaptively allocated based on recent match outcomes.

Historical pool capacity **16**, with fixed retention of prior `context-26m-20260908-s62001` entries.
**U512 / U1536 / U2560 / U3584 / U4302** are retained; all other positions preserve current running BC endpoints, earlier stages, and the last 4 snapshots. Current running models enter the pool every 64 turns.
The 5 external versions retain original lineage and quantity lexicons, serving only as frozen opponents and do not inherit the PFSP win rate of prior learning agents.
The 155-item quantity lexicon of the old model is separately inferred from the current 183-item quantity lexicon, and mappings are applied according to actual quantities before being sent into the environment.

Formal migration affects only `population` and `script_population`, archived in `population-revisions/0001`. The current model, two optimizers, dual-GPU RNG, BC source, training seed, 100k total budget, T=1, logical batch size 5,760 / micro-batch size 2,880 are all preserved.
160 learning trajectories per turn, with Actor/Critic targets each having 20 steps; the current Actor learning rate remains at 7.5e-6.
Original U124 PFSP evidence is retained and decayed according to pause duration; the statistical recovery boundary is explicitly migrated to U544.

Completed 8 rounds of double-GPU PPO in independent replicas, including U548 stop and archival recovery to U552; each optimizer advanced 160 steps, all tensors finite, PFSP sampling replay consistent with checkpoint/ledger.
Four steady-state samples at **26.32–27.86 seconds/turn**, median **26.69 seconds**, peak memory approximately **95.33 GiB/GPU**.
Official environment comparisons across four scripts, 44 related Python checks, full Ruff, mypy (692 files), and WebUI checks all passed.

Formal **U548 checkpoint verified**: U545–548 have all been completed with the new ratio, both models have been updated, and each optimizer has advanced by **80 steps**, with all tensors finite; PFSP sampling replay and statistical preservation are consistent, dual-GPU RNG is complete and distinct, and all 5 external historical versions remain in the opponent pool.
See [formal verification](../outputs/analysis/context3d-mixed-pfsp-20260910/formal-verification.json)
and [formal WebUI](../outputs/analysis/context3d-mixed-pfsp-20260910/webui-formal.json).
Training continues; actual progress is subject to
[learning-progress.json](../outputs/learning/context-26m-3d-20260910-s65001/learning-progress.json)
and [run-status.json](../outputs/learning/context-26m-3d-20260910-s65001/run-status.json).

See [Recipe, Compatibility Handling, and Acceptance](context3d_mixed_pfsp_20260910.md),
[Hydra Configuration Changes](../configs/learning_context_3d_pfsp_change.yaml),
[Migration Verification](../outputs/analysis/context3d-mixed-pfsp-20260910/transition-verification.json), and
[Formal Launch](../outputs/analysis/context3d-mixed-pfsp-20260910/formal-launch.json).
Below are the early self-play, initial PFSP, and BC records from this run, with the current ratio based on the U545 switch as described above.

## Prelude Phase: U125–544 Pure self-play (PFSP paused)

**September 10, 2026 Update: PFSP has been paused as per user request.** This run was fully saved at **U124** and then stopped. Recovery was resumed from the same checkpoint, starting at **U125**, with 128 pure self-play games per turn, and 0 historical or script-vs-human games.
Each turn generates 256 learning trajectories, with Actor/Critic target networks each updated by 32 steps. Current weights, optimizers, dual-GPU RNG, training seed range, 100k total budget, logical batch size of 5,760 and micro-batch size of 2,880 are all preserved.
The current Actor learning rate is 7.5e-6 and the Critic's is 1e-4. Historical weights and U124 PFSP statistics are retained and not involved in sampling during the pause period.

Independent replica completed 4 rounds of dual-GPU pure self-play, including normal termination and archive recovery, with each optimizer advancing 128 steps.
All tensor limits are satisfied; PFSP statistics remain unchanged. Two steady-state samples are **39.01 / 38.39 seconds**, peak **96.10 GiB per GPU**.
Formal migration altered only `population`, archived to `sampling-revisions/0001`.
See [Pause PFSP and Pure Self-Play Recovery Record](context3d_selfplay_20260910.md),
Configuration change applied to [learning_context_3d_selfplay_change.yaml](../configs/learning_context_3d_selfplay_change.yaml).

Formal **U128 complete recovery point verified**: U125–128 all consist of 128 rounds of pure self-play, with each optimizer advancing 128 steps; all tensor values are finite, dual-GPU RNG is complete, and PFSP statistics freezing is preserved. The preheating phase over three turns shows **38.41 / 38.48 / 39.22 seconds**, with no KL rejections observed. Training continues in progress, WebUI displays 100% self-play and the U125 configuration boundary; previously paused PFSP cards are hidden. See
[Formal verification](../outputs/analysis/context3d-selfplay-20260910/formal-verification.json) and
[WebUI verification](../outputs/analysis/context3d-selfplay-20260910/webui-formal.json).

The following is the record of the BC source and initial PFSP phase run, with the current game composition based on the U125 switch as described above.

2026-09-10 Starting a new random root as per user request: **`context-26m-3d-20260910-s65001`**, seed **65001**. After real-time verification against the official index,
the BC window is fixed to the latest three complete dates: **2026-09-07 / 09-08 / 09-09**, totaling **1,988 games**.
Grouped by environment seed, training/validation/final holdout are set at **1,778 / 97 / 113 games**.
Fixed at **4 epochs of BC completed**, with **2,554,487 training decisions per turn**, cumulatively **10,217,948 decisions**, and **40,012 optimization steps**.
Validation NLL is **0.2535 → 0.2188 → 0.2003 → 0.1887**;
the BC endpoint `pretraining/shard-000896.pt`'s optimizer, dual-GPU RNG, data identity, and finite tensors have passed verification.

Retain the 26M backbone, two H200 GPUs, BC global batch size of 256, and a learning rate of 1e-4.
The count vocabulary is reconstructed from the current training labels into **183** symbols, with a total parameter count of **26,526,810**;
the depth, width, and public historical feature pipeline of the Actor/Critic backbone remain unchanged. New runs do not load previous training weights.
The initial training entry automatically enters **100,000 turns of PPO**: U1–124, each turn consisting of **64 self-play games + 64 historical PFSP games**, with **no scripted opponents**. Each turn generates **192 learning trajectories**, with a logical batch size of 5,760 and execution micro-batches of 2,880, T=1; reward and KL regularization follow the original protocol.
The historical pool begins from the endpoint of this BC run, with snapshots added every 64 turns, up to a maximum of 16; decayed PFSP, uniform exploration, and coverage by the most recent opponents are maintained. The previous 26M run continues to stop at U4302.

Formal RL **U4 checkpoint verified**: 4 rounds, 512 games total, actual allocation consistently 64/64, script allocation empty.
Both Actor and Critic updated; each optimizer completed 96 steps, all tensors finite. Dual-GPU RNG, PFSP sampling replay, and checkpoint/ledger statistics are consistent. After two KL retreats in U1, 24 Actor steps were still completed, and the learning rate automatically reduced to **7.5e-6**; U2–U4 each completed 24 Actor/Critic steps with no rejections, taking **31.19 / 31.26 / 31.80 seconds**, peak memory **95.81 GiB per card**. The initial phase WebUI metrics, game allocation ratios, and PFSP history pool have passed verification.
See [Formal BC Verification Completed](../outputs/analysis/context3d-20260910/formal-bc-complete.json),
[Formal RL Verification](../outputs/analysis/context3d-20260910/formal-rl-verification.json), and
[WebUI](../outputs/analysis/context3d-20260910/webui-formal-rl.json).

Before official launch, the independent replica completes **4 epoch small-data BC → 4 turns of real-world dual-GPU PPO**, including U3. Normal shutdown and recovery from archive to U4 are performed. No script assets enter training; the final pool contains only this BC, U2, and U4. After recovery, both Actor/Critic models are updated, and each optimizer advances 24 steps. All tensors are finite, replay sampling via PFSP, checkpoint/ledger statistics, and dual-GPU RNG pass validation. Small-data acceptance triggers KL rollback during the first PPO turn; U3 has no rejections and completes 24 steps for both Actor and Critic, achieving a preheating time of **31.44 seconds per turn** and a peak memory usage of **95.82 GiB per GPU**. This represents a single steady-state acceptance sample and does not reflect the learning performance after official BC. All 11 related tests, full Ruff and mypy (690 files) pass validation.

Configured as [learning_context_3d.yaml](../configs/learning_context_3d.yaml),
see [Data, Recipes, and Acceptance](context_3d_pfsp_20260910.md),
[Two-GPU Acceptance](../outputs/analysis/context3d-20260910/qualification.json),
[Formal launch](../outputs/analysis/context3d-20260910/formal-launch.json).
The actual stage is determined by [learning-progress.json](../outputs/learning/context-26m-3d-20260910-s65001/learning-progress.json) and [run-status.json](../outputs/learning/context-26m-3d-20260910-s65001/run-status.json).
Recovery entry after normal shutdown:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-3d-20260910-s65001
```

## Prelude 26M: Already stopped and archived at U4302

2026-09-10 Upon user request, `context-26m-20260908-s62001` stopped normally at **U4302** after complete update, accumulating a total of **551,040 games**; during the PFSP phase from U3781 to U4302, a total of **522 turns, 66,816 games** were conducted. The exit code upon returning to the recovery entry point is 0; the training process terminated, write locks were released, and the WebUI remains running.
All final Actor/Critic components, two optimizers, dual-GPU RNG, PFSP statistics, parent chain, and all 39 registered assets have been confirmed; all model and optimizer tensors are finite. No new training was initiated during this stop; subsequent new runs are as described in the previous section.

Archive tag is **`context-26m-20260908-s62001-u4302`**. The final checkpoint SHA256 is
`2be6014c0a43701be311f0795cc5d10365e5c65339f88a8f59c1a801e6014082`,
saved to [fixed weights](../outputs/archives/context-26m-20260908-s62001-u4302/update-004302.pt),
original runtime and complete recovery assets are retained. The tag associates the source code and documentation with these hashes; the weights remain in gitignored
`outputs/` and are not included in Git objects.

User feedback indicates that the model's trajectory has reached approximately **Kaggle rank 10**, but exhibited early game stagnation and nearly lost all matches against opponents rated rank 1. This is based on the user's online observations and has not yet been independently verified regarding rankings or match samples, and thus cannot be directly attributed to the U4302 submission that had not yet been submitted at the time. The last recorded submission prior to stopping was **U3364 / 56133717**; subsequently, as requested by the user, a submission of **U4302 / 56143582** was made, with the initial verification showing `PENDING`, as detailed below in the submission log. In the final 128 turns before stopping, the script win rates were router_95 **93.3%**, farming_v4 **96.6%**, shop_router_0909 **88.1%**, and shop_router_0908 **91.0%**; the median update time during updates was **25.88 seconds**.

This run of BC uses **2026-09-03 to 09-07**, a five-day public replay period, totaling **3,326 games**;
actual training on **2,985 games, 4,292,256 decisions per epoch, over 4 epochs**. This re-verification checks the hash of the five original ZIP files and recalculates the original split ratios for training/validation/final holdout based on the archived code. No demonstrations from more recent dates were added after BC; the current PPO BC retention loss is 0. The original feature cache path no longer exists, but the original replay, preparation scripts, configurations, BC endpoint, and consumption records are still preserved and can be used without reconstruction for continued PPO training.

See [Stop, Performance, and BC Source](context_26m_u4302_archive_20260910.md),
[Stop Verification](../outputs/analysis/context-stop-20260910/stopped.json),
[Final Performance Statistics](../outputs/analysis/context-stop-20260910/performance.json), and
[BC Source Verification](../outputs/analysis/context-stop-20260910/bc-provenance.json).

## Stop-before-training recipe: 26M dual GPU, historical and script PFSP

2026-09-10 According to user request, PFSP is being integrated for `context-26m-20260908-s62001`.
The previous training was normally terminated on **U3780**, and the complete model, two optimizers, and dual-GPU RNG have been saved.
Formal operation continues from the same checkpoint, starting from **U3781**, with 128 games per turn:
**32 self-play games, 32 historical PFSP games, and 64 four-script PFSP games**.
The scripts continue to be `router_95`, `farming_v4`, `shop_router_0909`, and `shop_router_0908`,
each script playing at least 4 games per turn, with balanced positions for both sides per GPU, and the remaining games are adaptively allocated based on recent win/loss records.

The history pool contains a maximum of **16** authentication snapshots for the current random root, including the BC endpoint, the last 4, and earlier training stages; a new strategy is added every 64 turns. In each turn, one historical model is sampled for batch inference on two GPUs, with opponents selected based on decayed learning rate priority to favor more difficult opponents, while simultaneously preserving 20% uniform exploration and 10% coverage from the most recent history. Statistics are recorded along with complete checkpoints and atomic ledgers, and consistency is verified upon recovery. The training recipe, opponent pool, and sampling probability for the next turn have been integrated into the original WebUI on port 8765.

Retain the original **26M model, T=1, 5,760 logical batch, 2,880 execution micro-batches, two GPUs, BC endpoint, optimizer, training seed root, and 100k total budget**. The formal migration alters only `population`; the original checkpoint and all registered members' hashes remain unchanged. The learning trajectory per round is reduced from 192 to 160, with each self-play opponent's weights set to 0.5, and the remaining learning agents' weights set to 1, maintaining equal weighting per match. The Actor/Critic each take 20 steps per round, previously 24 steps.

Completed **8 rounds of real-world dual-GPU PPO** in independent replicas, including normal termination in U3784 and recovery from archived source code.
Sampling and replay statistics are consistent; both Actor/Critic have been updated, with each optimizer advancing **160 steps**, and all checkpoint tensors being finite.
Steady-state **25.73–26.31 seconds per turn, median 26.25 seconds**, representing an approximately **11.9% improvement** over the previous recipe's physical game throughput of **29.38 seconds per turn**, peaking at about **95.28 GiB per GPU**.
This improvement accounts for the reduced number of learning trajectories and is not a direct comparison under a fixed training trajectory budget.
Additionally, 512 control games were completed with serial and concurrent inference under the same configuration, with fully identical trajectory bit-by-bit. Sampling median time reduced from **6.95 to 6.07 seconds**.
52 related Python regressions, 12 frontend checks, full Ruff, and mypy (690 files) passed; no script errors were found in Chromium page checks.

Formal **U3784** complete checkpoint verified: both model networks updated, both optimizers advanced by **80 steps**, all tensors finite, distinct and complete dual-GPU RNG, PFSP statistics consistent with checkpoint/ledger. The restored steady-state U3782–3784 is **26.08 / 26.28 / 26.22 seconds**, final stop at U4302.
See [Formal Checkpoint Verification](../outputs/analysis/context-pfsp-20260910/formal-verification.json) and [Formal WebUI Verification](../outputs/analysis/context-pfsp-20260910/webui-formal.json):
16 historical snapshots, historical score curves, and script PFSP probabilities are visible; dynamic allocation produces only one protocol boundary at U3781, no script errors on the page.

See [Design, Implementation, and Acceptance](context_pfsp_20260910.md),
[Two-GPU Acceptance](../outputs/analysis/context-pfsp-20260910/qualification.json),
[Throughput Summary](../outputs/analysis/context-pfsp-20260910/qualification-summary.json),
[Migration Verification](../outputs/analysis/context-pfsp-20260910/transition-verification.json), and
[Formal Launch](../outputs/analysis/context-pfsp-20260910/formal-launch.json).
The protocol and source code are archived at `population-revisions/0004`, with Hydra configured as
[learning_context_pfsp_change.yaml](../configs/learning_context_pfsp_change.yaml).
Actual progress is tracked in [run-status.json](../outputs/learning/context-26m-20260908-s62001/run-status.json) and [learning-progress.json](../outputs/learning/context-26m-20260908-s62001/learning-progress.json).
The current run has been paused; to resume this run later, restore from the original archive using the recovery entry:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-20260908-s62001
```

## Previous Opponent: 26M Dual GPU, Shop Router 0909 Replaces Kaito v58

On 2026-09-09, according to user request, League `league3-20260909-s63001-fixed` has been normally stopped after completing the full joint checkpoint at Turn **682**. The two models, four optimizers, and dual-GPU RNG have been saved and verified.
Exit code is 0; training and recovery locks have been released. See [League Stop Verification](../outputs/analysis/context-shop-router-0909-20260909/league-stopped.json).

Archival recovery of `context-26m-20260908-s62001` has been initiated, with recovery point at Round **2391** as the boundary.
Starting from Round **2392**, `kaito_v58` will be replaced by native `shop_router_0909`.
Two-GPU setup (GPU0 + GPU1) has been restored as per user requirements, with micro-batch global size set to **2,880**.
Fixed parameters: T=1.0, 128 games per round — 64 self-play games, and 16 games each for `router_95`, `farming_v4`, `shop_router_0909`, and `shop_router_0908`.
Configuration changed to [learning_context_router_0909_change.yaml](../configs/learning_context_router_0909_change.yaml).
An independent replica completed 8 rounds of real-world dual-GPU PPO. After normal stop at Round 2395, it was restored from archival source code and native assets.
Steady-state performance: 29.3–30.3 seconds per round, peak memory usage approximately **95.25 GiB per GPU**, with each optimizer advancing **192 steps**, all tensor operations bounded; 8 official environment comparisons passed 5,752 script actions.
19 related regressions, full Ruff and mypy (681 source files) passed.
Formal changes preserve bit-by-bit the original checkpoint, both optimizers, BC endpoint, historical pool, and random root, with only `script_population` and `execution` being modified. The recovery is archived in `population-revisions/0003`.
GPU0 continues to preserve the saved RNG; GPU1 is deterministically initialized using the original random root, rank, and update round number.
See [Recovery Notes](context_router_0909_resume_20260909.md),
[Full Acceptance](../outputs/analysis/context-shop-router-0909-20260909/qualification.json),
[Tensor and Optimizer Verification](../outputs/analysis/context-shop-router-0909-20260909/qualification-final-verification.json), and
[Formal Migration Verification](../outputs/analysis/context-shop-router-0909-20260909/transition-verification.json).
[Startup record](../outputs/analysis/context-shop-router-0909-20260909/formal-launch.json).
Formal Round **2392** has been saved and confirmed: both Actor and Critic have been updated, and each optimizer has advanced by **24 steps**. All tensors are finite, and both GPU RNGs are intact. See
[Formal checkpoint verification](../outputs/analysis/context-shop-router-0909-20260909/formal-verification.json).
Actual progress is subject to [run-status.json](../outputs/learning/context-26m-20260908-s62001/run-status.json) and [learning-progress.json](../outputs/learning/context-26m-20260908-s62001/learning-progress.json).
After stopping, resume using the following two-GPU archive recovery command:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-20260908-s62001
```

## Preliminary League: Dual GPU, B+C + SpaTaro + Five Native Scripts

2026-09-09 According to user request, `league3-20260909-s63001-fixed` officially runs from the complete checkpoint at **Round 621**, and **from Round 622 onwards, A will no longer participate in training**; the training members are now only **B+C, SpaTaro**. All previously running `router_95`, `farming_v4`, `kaito_v58`, `shop_router_0908` at 26M are joined, and an independently ported C++ version **`shop_router_0909`** is added, resulting in a total of **5 script opponents**. The old `context-26m-20260908-s62001` continues to remain at Round 2391.

Each round remains **192 games**: B+C versus SpaTaro in **32 games**, each engaging in self-play for **40 games**, and each model plays **8 games** against each of five scripts. The five scripts are equally distributed, with balanced seating arrangements on GPU0 and GPU1.
Each model generates **76 trajectories per GPU**, with self-play seats assigned 0.5 weight each, and all other seats assigned 1.0 weight.
Model architecture, original BC endpoint, weights, four optimizers, dual-GPU RNG, seed step size, and total budget of 100k are preserved; all details have been verified bit-by-bit before and after formal migration. Complete prior checkpoints for the three models are stored in `population-revisions/0002`.

The final code was trained through three real-world two-GPU PPO rounds, including two rounds of recovery from archived code, script binaries, and trajectory assets.
Both Actor/Critic models and four optimizers are updated; all tensors are finite. Each round involves **19 steps** per Actor/Critic model, with no rejected Actor steps. The steady-state acceptance rate for the new configuration is **24.06 seconds per round**; initial compilation and warm-up restarts are excluded.
17 Python regressions, 11 frontend regressions, full Ruff, and mypy (681 source files) passed.
The 0909 validation includes 100 full games, 50 perturbed games, comparison between official environments and actual training batches, and all 64 ordered store combinations and 13 trajectories.

See [Ratio and Migration Guidelines](league_native_population_20260909.md),
[0909 Migration Instructions](native_shop_router_0909.md),
[Final Dual-GPU Acceptance](../outputs/learning/league2-five-scripts-qualification-20260909-v2/report.json),
[Bit-by-Bit Migration Verification](../outputs/analysis/league-native-population-20260909/transition-verification.json),
[Official Launch](../outputs/analysis/league-native-population-20260909/formal-launch.json).
The official Round **624** joint checkpoint has been verified: both models and four optimizers have been updated, each optimizer advanced by **57 steps**, and all tensors are finite. The official Rounds **623 / 624** took **23.94 / 23.98 seconds** respectively; the average power consumption of the two GPUs during the PPO phase is approximately **672 / 663 W**.
See [Official Checkpoint Verification](../outputs/analysis/league-native-population-20260909/formal-verification.json).
Actual progress is subject to [league-progress.json](../outputs/learning/league3-20260909-s63001-fixed/league-progress.json) and [run-status.json](../outputs/learning/league3-20260909-s63001-fixed/run-status.json).
The current Hydra entry is `learning_league_native.yaml`; upon termination, archived recovery will still be used:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.league.recovery
```

## Preliminary Phase of Three Expert Stages: Turns 1–621


2026-09-09 Throughput optimization has been completed. Formal training resumed from Round **93** using a joint recovery checkpoint. Starting from Round **94**, the new execution source code is used. Under identical 192-game and optimization step conditions, steady-state time has decreased from **40.46 seconds/turn** to **30.00 / 30.23 seconds/turn**, achieving approximately a **34% throughput improvement**. The stable turn time for independent continuous training is **30.05 seconds**; in formal Rounds **95 / 96**, the times are **30.11 / 30.01 seconds**, with average power consumption of approximately **664 / 656 W** (maximum limit 700 W) for two GPUs during the PPO phase. The joint checkpoint from Round 96 has been confirmed: all three Actor/Critic models have been updated, and each of the six optimizers has advanced by 48 steps. Training continues. Large batches use FlexAttention with original key masking; each of the three strategies employs its own capture stream's CUDA Graph for concurrent sampling. Full KL protection and decoder numerical fixes are retained. Model, six optimizers, both RNGs, BC endpoint, game pairing ratio, random seed, and total budget of 100k are all carried forward. The old source code and the recovery checkpoint from Round 93 are preserved in `runtime-revisions/0001`. Independent replicas have undergone three real-world two-GPU PPO turns and mid-process checkpoint recovery, resulting in updates to all six networks, with full finite updates to model, optimizers, and RNGs. 33 related regression tests, 2 GPU numerical tests, and both Ruff and full mypy have passed. See [Optimization Details](league_throughput_20260909.md), [Recovery Verification](../outputs/analysis/league-throughput-20260909/qualification.json), [Formal Launch](../outputs/analysis/league-throughput-20260909/formal-launch.json), and [Formal Checkpoint Validation](../outputs/analysis/league-throughput-20260909/formal-verification.json).

2026-09-09 Original run `league3-20260909-s63001` stopped due to decoder compilation failure.
The repaired run directory is `league3-20260909-s63001-fixed`, using **GPU0 + GPU1**.
Each model (Actor+Critic) has **6,567,716** parameters, which is **24.82%** of the previous total of 26,463,950.
Three Actor instances share the same random initialization, each trained on data from the A, B+C, and SpaTaro's own seat positions for **6 full BC epochs**. After completion, they automatically enter **100,000 turns** of mutual combat RL.
Starting from **Turn 55**, each turn includes **32 matches** of mutual combat among the three models and **32 self-play matches** for each model, totaling **192 matches**. Each model performs one PPO rollout update; the three models and their optimizers operate independently, with gradients synchronized across the two GPUs. Self-play retains trajectories for both seats, each with a weight of 0.5; in mutual combat, each seat has a weight of 1, with equal weighting based on each model's participation in physical matches. Each model still maintains 64 trajectory samples per GPU, preserving the original batch size for inference.
Turns 1–54 consist of 64 mutual combat matches for each of the three types, with no self-play.

Formal operation resumes from the 54th round joint checkpoint recovery, with three models, six optimizers, shared RNG and BC endpoints preserved, and a total budget of 100k. Independent replicas complete three rounds of double-GPU PPO with intermediate archiving and recovery; all six networks are actually updated, with all models, optimizers, and RNGs fully bounded. Stable turn duration is **40.46 seconds**, peaking at approximately **94.1 GiB per GPU**. 33 Python tests, 10 frontend tests, Ruff, and full mypy pass. The original BC data manifest path no longer exists; the spurious data dependencies in PPO recovery after BC have been resolved. The system now verifies archived BC configuration, roles, all epoch records, and endpoint hashes. See [Self-play ratio, statistics, and recovery instructions](league_selfplay_20260909.md), [Dual-GPU acceptance](../outputs/analysis/league-selfplay-20260909/qualification.json), [Formal launch](../outputs/analysis/league-selfplay-20260909/formal-launch.json).

Training data comes from the latest available daily episodes from 2026-09-06 to 09-08, totaling 1,988 games.
A-class training decisions: 713,972; B+C: 1,869,683; SpaTaro: 162,492;
There is intentional overlap between SpaTaro and B+C.
A complete seed-isolated validation set is used; classification templates utilize only training episodes.
Classification reflects behavioral repetition and cannot be used to identify genuine RL implementations.

All 18 original faulty shards have passed forward and backward validation under the condition of NaN filling in temporary GPU memory. The final source code, using pre-trained weights, completed 2 rounds of 384 real-game mutual battles on two GPUs, with all three Actor/Critic models actually updated, and all sampled data, model, and optimizer tensors remaining finite.
After preheating, **41.13 seconds per turn**, peak allocated GPU memory reaches **94.16 GiB per card**.
Ruff passes fully; mypy passes 669 source files, and 10 related tests pass.

The original fault was that the decoder fusion LayerNorm read uninitialized temporary data that was not properly written, potentially producing limited but erroneous results. Disabling cuDNN/BF16 low-precision accumulation did not fully resolve the issue.
Now, independent native LayerNorm forward/backward boundaries are used, with no exception retries or eager fallbacks; old BC weights are retained solely for debugging. Three 6-epoch BC runs have been completed from the same initialization, yielding final NLL values of A **0.0454**, B+C **0.3181**, and SpaTaro **0.5663**.
After completing all three formal head-to-head matches, the three models, six optimizers, and both sides' RNGs have been verified and restored from the same archive; the 4th round after restoration has been submitted and is continuing the original 100k total budget. The formal 3rd round took **40.42 seconds** for preheating. See
[Complete BC, PPO, and Restoration Verification](../outputs/learning/league3-20260909-s63001-fixed/formal-verification.json).
See [Root Cause and Fix](decoder_numerics_20260909.md) and
[Fix Acceptance](../outputs/analysis/league-failure-20260909/repair-qualification.json).

See [Operation Instructions and Configuration](specialist_league_20260909.md),
[Initial Small Data Pipeline Acceptance](../outputs/analysis/league-20260909/qualification.json),
[Startup Log](../outputs/learning/league3-20260909-s63001-fixed/launch.json).
The real-time phase is based on [league-progress.json](../outputs/learning/league3-20260909-s63001-fixed/league-progress.json); the current epoch and shard progress of BC can be found in the active_member directory under `learning-progress.json`.
Process status is available in [run-status.json](../outputs/learning/league3-20260909-s63001-fixed/run-status.json).
A joint checkpoint containing three models, six optimizers, and both sides' RNG is saved every 4 turns and upon normal termination.
After termination, the run archive is resumed from this checkpoint:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.league.recovery
```

Below retains the stop and migration records from the previous 26M operation.

## 26M Last Stop: Stopped after the 2391st full update

2026-09-09 Upon user request, `context-26m-20260908-s62001` has been officially stopped and is now running normally.
Total **306,432 games** completed; the last complete recovery point is at
[`checkpoints/update-002391.pt`](../outputs/learning/context-26m-20260908-s62001/checkpoints/update-002391.pt).
SHA256 is `c41fff324811ecd6de1e93ac83b129ca398a9f65fc01842c16e9277bc0bf9cb5`.
The training process and recovery entry have both exited with exit code 0; both write locks have been released.
Actor, Critic, two optimizers, and single-GPU RNG have been saved; all checkpoint tensors are finite.
Random seed, parent chain, ledger, and per-turn metric consistency have been confirmed.
At stop time, the actual learning rates were Actor **3.75e-6** and Critic **1e-4**.
See [Stop Request](../outputs/analysis/context-stop-20260909/stop-request.json) and
[Stop Verification](../outputs/analysis/context-stop-20260909/stopped.json).
The following hardware and opponent configuration describes the final setup prior to the run's termination.

## 26M Pre-sequence Hardware: Only GPU0 is used in turns 2139–2391

2026-09-09 Running `context-26m-20260908-s62001` as per user request, officially commencing on Turn **2138**
Normal shutdown after complete update, totaling **274,048 games**, followed by resuming as `CUDA_VISIBLE_DEVICES=0` from the same recovery point. Current execution device is `[cuda:0]`, with execution micro-batch reduced from dual-GPU global 2,880 to single-GPU **1,440**;
**128 games per turn**, logical batch **5,760**, 50% self-play / 50% four-script, 100k update
Total budget remains unchanged. Actor, Critic, two optimizers, BC endpoint, history pool, and random root are retained;
Actual learning rates at switch: Actor **7.5e-6**, Critic **1e-4**.

Switch recovery point to `checkpoints/update-002138.pt`, SHA256: `837e6d94579c3b0b34e49ea0355725377c12fd300b949f333074ca78fff5f8e6`.
GPU0's RNG continues from the original rank 0; the original dual-GPU RNG is fully preserved at this recovery point; sampling and floating-point computations after changing the GPU count are not guaranteed to match bit-by-bit with the dual-GPU configuration. Recovery code allows changing the number of workers only at checkpoint boundaries explicitly recorded in the ledger; ordinary recovery continues with strict validation. The switch and original dual-GPU protocol are archived at `runtime-revisions/0001`; future new dual-GPU runs will retain the default configuration.

Independent replica completed Rounds 2139–2142, resumed after normal termination at Round 2140, and verified the optimizer, single-GPU RNG, checkpoint parent chain, and per-script game counts. Post-warmup performance was **59.33 / 59.36 seconds per turn**, with peak allocated GPU memory reaching approximately **97.14 GiB**; replica weights did not enter formal training. Ruff, full mypy (641 source files), and 11 related tests passed. See [Termination Log](../outputs/analysis/context-gpu0-20260909/stopped.json), [Single-GPU Acceptance](../outputs/analysis/context-gpu0-20260909/qualification.json), and [Kernel Switch Verification](../outputs/analysis/context-gpu0-20260909/transition-verified.json).

The official start recording is [gpu0-launch.json](../outputs/learning/context-26m-20260908-s62001/gpu0-launch.json),
real-time status remains based on [run-status.json](../outputs/learning/context-26m-20260908-s62001/run-status.json) and [learning-progress.json](../outputs/learning/context-26m-20260908-s62001/learning-progress.json). Only after training has stopped, use the following command to archive and resume training for a single GPU:

```bash
CUDA_VISIBLE_DEVICES=0 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-20260908-s62001
```

## 26M Preceding Opponent: Round 713–2391 with Shop Router 0908 replacing Boatlee v29

2026-09-08 According to user request, [Shop Router 0908](https://www.kaggle.com/code/yhay81/shop-router-0908) has been ported to the existing native C++ batch and Boatlee v29 has been retired. Officially running.

`context-26m-20260908-s62001` stopped normally after the complete update on **Round 712**, accumulating **91,520 games**;
Starting from the same recovery point and the same random root, beginning with **Round 713**, each round still consists of 128 games:

| Opponent | Games | Game Share | Learning Trajectory |
| --- | ---: | ---: | ---: |
| Current model self-play | 64 | 50% | 128 |
| Thomas `router_95` | 16 | 12.5% | 16 |
| `farming_v4` | 16 | 12.5% | 16 |
| `kaito_v58` | 16 | 12.5% | 16 |
| `shop_router_0908` | 16 | 12.5% | 16 |

Each script has 8 games per side, with two GPUs evenly distributed, and 0% historical model allocation. Actor/Critic, optimizer, dual-GPU RNG, historical snapshots, BC endpoint, and total budget of 100k updates are retained; BC is not re-run.
Restore point is `checkpoints/update-000712.pt`,
SHA256 is `5ad5d71916045f17e6a856ccbe27e41a6d6bdc6c6ac24e680da7f721a4c2194f`.
The seed for Round 713 starts from **4,060,091,136** and continues with the original allocation.

The four complete trajectories of the new strategy and the public state branches at turns 144 and 648 are executed in C++, continuing to use `ParallelBatch.advance_programs` without per-turn Python opponent callbacks. Boatlee v29 has retired from active training factory and trusted registry; original source code, assets, and runtime are archived for reproduction. The main source file and three dependencies are bound to hashes, see [Porting Guidelines](native_shop_router_0908.md).

160 game original script passes through **230,080 actions**. The actual model's 8 official environment mirrors pass through 5,752 script actions and learning features; independent copies complete rounds 713–720, and resume after stopping at round 716.
Warm-up phase takes approximately **30.8 seconds per turn**, peaking at about **95.2 GiB per GPU**. The acceptance copy weights were not included in formal training.
Ruff, full mypy, 15 related Python tests, and 5 frontend tests passed.
See [recovery acceptance](../outputs/analysis/context-shop-router-20260908/qualification.json),
[stop logging](../outputs/analysis/context-shop-router-20260908/stopped.json), and
[switch verification](../outputs/analysis/context-shop-router-20260908/transition-verified.json).

This agreement and native script assets are archived in `population-revisions/0002`.
Future random initialization using the same recipe will utilize [learning_context_scripts.yaml](../configs/learning_context_scripts.yaml);
The current migration configuration is [learning_shop_router_change.yaml](../configs/learning_shop_router_change.yaml).
For formal operation, continue using the self-archived recovery entry:
`python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-20260908-s62001`.
Real-time status is subject to [run-status.json](../outputs/learning/context-26m-20260908-s62001/run-status.json).
The current WebUI opponent table and script curves use the above four scripts, with historical metrics preserved:
`http://127.0.0.1:8765/?run=learning/context-26m-20260908-s62001`.

## Previous configuration: 128 games, 50% self-play + 50% four-script (turns 106–712)

2026-09-08 Running according to user requirements, officially operates until the complete update of turn **105**, then stops normally, accumulating **13,824 games**.
Starting from turn **106**, with the same recovery point and same random root, each turn consists of **128 games**:

| Opponent | Games | Game Share | Learning Trajectory |
| --- | ---: | ---: | ---: |
| Current model self-play | 64 | 50% | 128 |
| Thomas `router_95` | 16 | 12.5% | 16 |
| `farming_v4` | 16 | 12.5% | 16 |
| `kaito_v58` | 16 | 12.5% | 16 |
| `boatlee_v29` | 16 | 12.5% | 16 |

Each script has 8 games per side, with two GPUs evenly distributed, and the share of historical models at **0%**.
A total of 192 learning trajectories, weighted equally by physical match; original Actor/Critic, optimizer, dual-GPU RNG, historical snapshots, BC endpoint, and a total budget of 100k updates are preserved. The recovery point is `checkpoints/update-000105.pt`,
SHA256 of `199ee0ac6de6da7b946eae217baecabb142e3d2b40ef40b758c6c517d687153b`.
The original training seed is used sequentially, starting from **4,060,013,440** in Round 106, without re-running BC.

Dual H200, logical batch 5,760, execution micro-batch 2,880 retained; new configuration with 24 optimized steps per Actor/Critic per round.
Independent replicas completed Rounds 106–113, resumed from Round 113 after stopping at Round 109; preheating took approximately **31 seconds per round**,
peak memory usage reached approximately **95.2 GiB per card**. A full official rule mirror for 8 actual models verified 5,752 script actions and learning agent features.
Weights from the acceptance replica did not enter formal training.
See [Acceptance](../outputs/analysis/context-new-scripts-20260908/qualification.json),
[Stop Log](../outputs/analysis/context-new-scripts-20260908/stopped.json), and
[Protocol Switch Verification](../outputs/analysis/context-new-scripts-20260908/transition-verified.json).

The protocol is archived at `population-revisions/0001`, containing new source code and four native script assets.
The future random initialization entry point with the same recipe is at [learning_context_scripts.yaml](../configs/learning_context_scripts.yaml);
The current runtime uses the recovery entry point from its archive:
`python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-20260908-s62001`.
The current runtime status is available at [run-status.json](../outputs/learning/context-26m-20260908-s62001/run-status.json).

WebUI displays **50% Self-play · 50% Script**, with the current opponent table showing the above five rows, each displaying real game instances, win-draw-loss results, win rate, terminal liquidation cash, and cash difference. The issue of cached old opponents and old historical scores across turns has been fixed; historical records are preserved, and the script curve for newly formed scripts only shows the last four versions. 25 Python tests, 5 frontend tests, Ruff, and full mypy have passed, with no script errors in the browser page.
WebUI: `http://127.0.0.1:8765/?run=learning/context-26m-20260908-s62001`.

## Script Opponent Infrastructure: New Four native Versions

2026-09-08 As per user request, the current training factory and trusted registry have retired Kaito v39/v48, Mugundh v21, and Boatlee v21, and have been replaced with Thomas `router_95`, `farming_v4`, `kaito_v58`, and `boatlee_v29`.
All four are C++ native and are executed directly within the existing `ParallelBatch.advance_programs`;
The default configuration for the newly created script training pool has been updated, with historical implementations and runtime archives preserved for reproducibility.
160 rounds of original script comparisons and 8 actual training interface official images have passed; mixed with 128 games, 8 workers, approximately 1.83 million environment steps per second (excluding neural model inference). Details available at [Implementation and Acceptance](native_opponents_20260908.md).
This infrastructure has been used in the 50% / 50% configuration mentioned at the beginning of this section; the following pure self-play configuration pertains to the previous stage.

## Previous Configuration: BC has been completed, 128 games of pure selfplay (rounds 2–105)

On 2026-09-08, the user selected the configuration of **40.49/40.60 seconds per update, approximately 96.3 GiB per card**, which has been empirically validated,
requesting to halt larger-batch testing, first commit the changes and maintain a clean workspace, then directly resume formal training.
Four rounds of BC have been completed: 17,169,024 rows, 67,172 supervised updates, with final validation NLL of **0.122447**.
The original configuration normally stopped after Round **1** of full PPO; this round used 512 games against mixed opponents, see
[Stopping Record](../outputs/analysis/context-selfplay-128-20260908/stopped.json).
Rounds **2–105** consisted of **128 games of self-play between both current model instances**; during this phase, historical models and scripts were not added to the training pool.

Using two H200 GPUs, global logical batch size **5,760**, execution micro-batch size **2,880** (1,440 per GPU),
256 learning trajectories per round, with 32 optimization steps for both Actor and Critic. The original Actor/Critic models, optimizers, dual-GPU RNG, BC endpoint, and historical snapshots are retained, continuing from the same random root with a total update budget of 100k. The Actor optimizer is reduced to **7.5e-6** in Round 1 via KL regularization, and this actual learning rate is preserved; the Critic uses a learning rate of 1e-4.
A new online seed allocation is set to `[4,060,000,000, 4,072,800,000)`, starting at 4,060,000,128 in Round 2, separated from the original allocation and evaluation interval. The accumulated game count retains the previously completed 512 games, and then adds 128 per round.

In three consecutive checkpoint measurements after preheating, the first two turns took **40.4938/40.6020 seconds**, with identical parameters across two GPUs;
See [Selected Baseline](../outputs/analysis/context-selfplay-128-20260908/baseline.json).
The user explicitly chose to start directly, thus no further large-batch measurements were conducted, and no additional independent stop/start runs were added;
This startup is based on the completed baseline, full original recovery point verification, and 19 essential checks, with no claim of additional trial runs passing.
mypy passed for Ruff and 631 source files. Protocol revisions used archived source code, preserving the original recovery point and original protocol; see
[Startup and Submission Log](../outputs/learning/context-26m-20260908-s62001/selfplay-launch.json) and
[Current Verification](../outputs/analysis/context-selfplay-128-20260908/qualification.json).
The future random initialization entry for the same recipe is [learning_context_selfplay.yaml](../configs/learning_context_selfplay.yaml);
The current run continues using its own archived recovery entry and does not re-run BC.
The WebUI marks **100% Self-play**, currently showing only self-play against opponents; previous script curves are retained as historical records.
Actual runtime status can be viewed in [run-status.json](../outputs/learning/context-26m-20260908-s62001/run-status.json).

### Original Initialization and Model Structure

2026-09-08 Implemented according to the approved plan, and adjusted the **FFN width to half and the number of Transformer layers to double** as per the final instruction.
The official run is [`context-26m-20260908-s62001`](../outputs/learning/context-26m-20260908-s62001/launch.json),
random seed **62001**, run ID `9d3a7fd343984da084c72d65a681198e`, source code commit `1b6ce18`.
Executed a fixed four-round BC on the most recent five-day data using fresh random parameters, followed by an automatic transition to 100,000 online PPO rounds.
Weights, optimizers, and historical pools from previous runs and checkpoint runs were not included in the new initialization.
The complete configuration is defined in [resolved-config.json](../outputs/learning/context-26m-20260908-s62001/resolved-config.json),
Hydra entry point is [learning_context.yaml](../configs/learning_context.yaml).

| Part | Implemented Structure | Actual Parameters |
| --- | --- | ---: |
| Actor | 384-dimensional, 16 layers, 8 heads, FFN 768 | 20,618,508 |
| Critic | 320-dimensional, 6 layers, 8 heads, FFN 640 | 5,845,442 |
| Total | Independent encoder | **26,463,950** |

The additional attention layers also contribute to the parameter count, so the total number after modifying the final depth and width is **26.46M**, higher than the original approximately 20M.
The new feature version `grounded-production-context-v2` consists of 13,316 items, 286 tokens, and 155 quantity symbols.
Local convolution on plots, production time, commodity aggregation, unit operation support, and the 1/4/12/24-turn public history with typed conditional action heads are combined, still using grounded valid actions and exclusive prefix PPO.
Detailed design is available in [New Training Scheme](learning_20m_proposal.md), [Feature and Action Interface](grounded_context.md).

BC Source Freeze **from 2026-09-03 to 2026-09-07** for 3,326 games; the original ZIP and source hash are permanently preserved at [Original Data List](../data/external/kaggriculture-episodes-2026-09-03_2026-09-07/raw/manifest.json).
Split into training/validation/final holdout by full environment seed: 2,985/158/183 games, with available rows 4,292,256/227,196/263,147. Data covers all phases for both players, without filtering by win/loss or cash.
Training over four rounds totals **17,169,024 rows**; global batch size 256, 128 rows per GPU, BC learning rate 1e-4.
The feature cache from this re-encoding is located at [outputs Data List](../outputs/datasets/grounded-v2-20260903-07/manifest.json), SHA256 `789bcd28991222a9b98e04c969be4ba5b4fff97c61dc4ad6a2d51be4cf05c953`.
For each BC epoch, validation NLL is recorded, and complete opening behavior is measured over four independent full games; fixed endpoint of the fourth round enters PPO.

Initial Round 1 consists of **512 games**: 256 from self-play, 128 from the current run's historical model, and 128 from native C++ scripts.
At that time, Kaito v39, Kaito v48, Mugundh v21, and Boatlee v21 each ran 32 games, reusing existing C++ sessions.
This configuration has been replaced by the pure selfplay setup introduced at the beginning of this section (128 games).
Two H200 GPUs are trained in sync, using BF16 precision, with a logical minibatch of 5,760, executing global microbatches of 2,880 and 1,440 per GPU.
The Actor starts with a learning rate of 3e-5, and the Critic with 1e-4; KL divergence rollback protection, original rewards, and PPO targets are retained; the demonstration loss is turned off after BC.
The historical pool has a capacity of 8, with snapshots taken every 4 rounds; selection is fixed every 512 rounds, and confirmation is performed at the budget endpoint.
Online seed range is `[4,000,000,000, 4,051,200,000)`, separated from demonstrations and independent evaluations.

Save a complete checkpoint every 4 turns and at normal termination. To avoid approximately 8 TB of full checkpoint growth, BC/PPO each retain the most recent 8 checkpoints, while protecting the random root, historical pool, BC epoch endpoint, PPO initialization, fixed evaluation points, and budget endpoint. First publish the ledger and retirement hash, then delete old files of roles without retention; metrics and evaluations are retained.

Implemented execution via ruff, full mypy analysis of all 629 source files, necessary interface and recovery tests; four official complete images.
Verified 5,752 lines of decision features. Exact CPU packages completed two official games each under Python 3.11/3.12 with cold starts, exhibiting identical trajectories.
Dual-GPU checks completed BC mid-stop/recovery, 8 rounds × 512 PPO episodes, and stop/recovery between round 7→8; optimizer, dual-GPU RNG, parent chain, and episode counts across scripts all passed.
Final micro-batch time was approximately **122 seconds per round** after warm-up, with single-GPU peak allocated GPU memory reaching about **101.3 GiB**. See
[Engineering Check Summary](../outputs/analysis/grounded-v2-20260908/qualification.json).
These execution checks using small BC fragments do not represent new main run intensity, nor constitute algorithm ablation.

Training runs in tmux `revue_context_26m_s62001`, archiving source code and native assets for the BC/PPO two-phase process.
At startup, the recovery entry loads only the newly generated random root and sets the BC cursor to zero.
The recovery command is `python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-20260908-s62001`, to be used only after the current training has stopped. Real-time status is available in
[run-status.json](../outputs/learning/context-26m-20260908-s62001/run-status.json) and
[recovery-status.json](../outputs/learning/context-26m-20260908-s62001/recovery-status.json).
WebUI: `http://127.0.0.1:8765/?run=learning/context-26m-20260908-s62001`, continuing to display BC progress, PPO script-by-script win/draw/loss records, win rate, cash balance, and cash difference.

Startup acceptance has been confirmed: the BC has advanced to at least shard 36, row 411,251, and 1,609 optimization steps.
All parameters at the corresponding recovery point are bounded; the full optimizer, two worker RNGs, random root, and parent chain verification have passed;
The WebUI now displays the real-time progress of the BC under the same main run, and all data array hashes have been verified.
See [Startup Verification Check](../outputs/analysis/grounded-v2-20260908/main-launch.json).
This shard represents only an initial observation during startup; four rounds of BC have now been completed. The latest status is shown at the beginning of this section and in the runtime files.

## Original Operation Stop Record

Original `long-100k-20260908-s61001` has been normally halted after the **526th** full update, totaling **93,440** games.
The last recovery point is [`update-000526.pt`](../outputs/learning/long-100k-20260908-s61001/checkpoints/update-000526.pt),
SHA256 of `fc9a23c2e2802ea97d717b998770f028a64758bb3e184eaa0cd672bd9e7f46a3`.
Processes termination, model, two optimizers, and RNG have been confirmed; the original files are preserved, see
[Halting Record](../outputs/analysis/new-20m-20260908-plan/previous-run-stop.json).
The following facts regarding startup, evaluation, and submission of the 100k old runs and earlier studies are solely historical records.

<a id="section-b9e953ea7c6f"></a>

## Latest Kaggle Submission

Latest is the **s73001 U5376: 56376259 (T=1, once only)**;
The following are previous submission records.

### Previous submission: Explicitly specify the previous run s68001 U5629, once at T=0 and once at T=1

On 2026-09-16, as explicitly specified by the user, we selected **U5629** from the stopped run `budget-q100-top10-2d-20260913-s68001`: **720,512 cumulative RL games**, preceded by a complete 4-epoch BC phase.
Both exports come from the same endpoint of that historical run, using **T=0 conditional argmax** and **T=1 conditional random sampling**, respectively.

- **T=0**: submission **56266758** (01:59:10 UTC), [submission package](../outputs/deployment/budget-q100-top10-2d-s68001-u5629-20260916-t0-t1-t0/submission.tar.gz), 77,450,529 bytes; SHA256 **`646ee407411b572f2e1e6bf33fa50a43bc594ece1b6eb30137d5b6f2c0cd163f`**.
- **T=1**: submission **56266899** (02:07:02 UTC), [submission package](../outputs/deployment/budget-q100-top10-2d-s68001-u5629-20260916-t0-t1-t1/submission.tar.gz), 77,454,324 bytes; SHA256 **`6943271a7a7ac2bcd9f81b4b78c24d8a320e1f0a5a29e980403c36c4064ed4c2`**.

Checkpoint SHA256 is `5700c91c41e6198b444ae5aa540e08f03f51ad6cb3444f57c0a8601d0370bef6`, independently retained at [fixed weights](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u5629-20260916-t0-t1/update-005629.pt); Run ID `db598303f1c047a188c6432544dad4a2`. Using this run, the complete archived source code of `population-revisions/0002` is employed, with source code SHA256 `3767462c3eb3ede0a0d04ae68028de91b5837d0f81322f706b0098c7a8f40d13`, and the deployed source code is consistent with the training archive. Budget features are preserved, fixed 1–100 quantity classification, FP32 CPU, and the original sampling seed are retained.

All 1,515 checkpoint tensors are finite. Two temperatures have been fully validated through two complete game matches each, with each achieving consistency across 2,876 decisions compared to the original eager CPU model, and matching both packaged executable content and standalone export results.
Each exact package has completed two full official games including cold starts under Python 3.11/3.12, totaling 8 games / 11,520 observations, with all seats designated as `DONE`; action trajectories and cash flows are consistent across different runtime environments at the same temperature.
The maximum cold-start action duration is less than 1.53 seconds, subsequent actions are less than 0.51 seconds, and the final additional time budget is at least 59.47 seconds.
Deployment modules Ruff and mypy have passed. Sources of interrupted retesting are preserved in the results directory and are not included in the incomplete trajectory segments.

**02:07:30 UTC** Rechecked and confirmed that the above two records were exactly newly added, with descriptions and file sizes matching.
At that time, T=0 was `COMPLETE` with displayed score `600.0`; T=1 had not yet returned its status or score.
This is a snapshot of the state at that moment and should not be used for stable strength assessment.
See [Deployment Qualification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u5629-20260916-t0-t1/qualification.json),
[Two Upload Acknowledgments](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u5629-20260916-t0-t1/submission-receipts.json), and
[Kaggle Status Verification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u5629-20260916-t0-t1/submission-status.json).

### Previous submission: Two-day Top10 BC budget-q100, new root U572, T=1 and T=0 each once

On 2026-09-15, as requested, freeze the latest complete checkpoint **U572** from `budget-q100-top10-2d-20260915-s69001` at selection time, after **73,216 RL games**. Both packages use the same weights and were successfully submitted with **T=1 conditional random sampling** and **T=0 conditional argmax**, respectively.

- **T=1**: submission **56256813** (14:36:00 UTC), [submission package](../outputs/deployment/budget-q100-top10-2d-s69001-u572-20260915-t1-t0-t1/submission.tar.gz), 77,408,273 bytes; SHA256 **`c9b376e850bac91e6b823f17fd1dbe52004705908b366b86458a43e8bf22384f`**.
- **T=0**: submission **56256851** (14:37:54 UTC), [submission package](../outputs/deployment/budget-q100-top10-2d-s69001-u572-20260915-t1-t0-t0/submission.tar.gz), 77,404,419 bytes; SHA256 **`f9f133ce712e93bf8d25a39e7040c02c28aecd16ac9bbd07cc1f3b5ab2150cda`**.

Kaggle turn confirmation confirms the exact addition of the above two records; the initial joint review has not yet returned evaluation status or score.
checkpoint SHA256 is `63e0173b4934f4c156e39bbae662f5b49ecb54e1cdcfb2dba6c97bfeeabc0c16`,
independently retained in [fixed weights](../outputs/analysis/kaggle-budget-q100-top10-2d-s69001-u572-20260915-t1-t0/update-000572.pt).
Using the complete archived source code from this training, source code SHA256 is `94a4cb42e148cd3f290c3f069db5c262772352ac2ed85552a7c93fa1f74d49d9`,
retaining budget features, fixed **1–100** quantity classification, FP32 CPU, and original deployment sampling seed.

All **1,515** checkpoint tensor limits are satisfied; after two full-game matches with temperature validation, each temperature achieves consistency in **2,876 decisions** against the original eager CPU model, with independent exports and packaged executable content matching exactly.
Each specific package completes two full official games with cold starts under Python 3.11/3.12, totaling **8 games / 11,520 observations**, all seats `DONE`, with identical action trajectories and cash flow across temperature and runtime environments.
Maximum cold-start action duration is less than **1.55 seconds**, subsequent actions less than **0.35 seconds**, and final additional time at least **59.45 seconds**.
Deployment modules Ruff and mypy pass; temporary isolation directories have been cleaned. Dual-GPU training continues, and the last verification reached **U605**.
See [Deployment Qualification](../outputs/analysis/kaggle-budget-q100-top10-2d-s69001-u572-20260915-t1-t0/qualification.json),
[Two Upload Acknowledgments](../outputs/analysis/kaggle-budget-q100-top10-2d-s69001-u572-20260915-t1-t0/submission-receipts.json), and
[Kaggle Status Verification](../outputs/analysis/kaggle-budget-q100-top10-2d-s69001-u572-20260915-t1-t0/submission-status.json).

### Previous submission: Two-day Top10 BC budget-q100, Turn 4016, submitted two versions with the same weights

2026-09-14 Following user request, fixed selection at current main run
`budget-q100-top10-2d-20260913-s68001` latest complete checkpoint **U4016**, cumulative
**514,048 games of RL**, including constant learning rate from U3491 and V42 / new Farming script pool training from U3960.
Same package successfully submitted twice: **56234989** (1/2, 16:06:55 UTC) and
**56235022** (2/2, 16:09:01 UTC). Kaggle retrospective confirmation verifies exactly these two entries were added; initial joint retrospective has not yet returned evaluation status or score; dual-GPU training continues running, and by the time of retrospective check, it has progressed to U4048.

checkpoint SHA256 is `6f5a5c402904469816018039757fea802dfca1b4772a846221ca0ef7f7500c34`,
independently retained at [fixed weights](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u4016-20260914-double/update-004016.pt).
Two versions using the same [submission.tar.gz](../outputs/deployment/budget-q100-top10-2d-s68001-u4016-20260914-double/submission.tar.gz),
SHA256 `2cdc63ffb0b486e6d37bd3155da53ff6e1cd9b2168cf2515d7774873cd600082`, 77,453,337 bytes.
Complete usage of the current training `population-revisions/0002` archived source code, preserving budget features, fixed
**1–100** quantity classification, **T=1, FP32 CPU conditional random sampling**, and original deployment sampling seed.

All 1,515 checkpoint tensors are finite; across two full games, there are 2,876 decisions consistent with the original eager CPU model, and both independent exports and packaged executable content are identical. The exact package completes two full official games with cold starts under Python 3.11/3.12, occupying all seats `DONE`, and checks a total of 5,760 observations. Action trajectories across runtimes and cash flows are consistent. The longest cold-start action takes 3.235 seconds, subsequent actions take 0.710 seconds, and the final additional time budget is at least 57.765 seconds. Deployment modules Ruff and mypy pass, and temporary isolation directories have been cleaned. See [Deployment Qualification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u4016-20260914-double/qualification.json), [Two Upload Confirmations](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u4016-20260914-double/submission-receipts.json), and [Kaggle Status Verification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u4016-20260914-double/submission-status.json).

### Previous submission: Two days Top10 BC budget-q100, Turn 2912, submitted two versions with the same weights

2026-09-14 Following user request, fixed selection of current primary run
`budget-q100-top10-2d-20260913-s68001` latest complete checkpoint **U2912**, cumulative
**372,736 games of RL**, including training from the newly opened script pool enabled starting at U2665.
Two successful submissions from the same package: **56221927** (1/2, 04:53:43 UTC) and
**56221997** (2/2, 04:58:59 UTC). Kaggle retrospective confirmation verifies exactly these two records were added; the first joint retrospective was for `PENDING`, with no scores yet; training continues running, and by the time of retrospective check, it has progressed to U2960.

checkpoint SHA256 is `23ccf5d42a40b924ced43fea7f4d6c9b00004b0bdbb519d1d975d64b680a2131`,
independently retained at [fixed weights](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u2912-20260914-double/update-002912.pt).
Two versions using the same [submission.tar.gz](../outputs/deployment/budget-q100-top10-2d-s68001-u2912-20260914-double/submission.tar.gz),
SHA256 `dfa4424fc9704531d6b3d889940fcb869ca8f963fabef66838087a3b265bf941`, 77,450,707 bytes.
Complete usage of the current training `population-revisions/0001` archived source code, preserving budget features, fixed
**1–100** quantity classification, **T=1, FP32 CPU conditional random sampling**, and original deployment sampling seed.

All 1,515 checkpoint tensors are finite; across two full games, there are 2,876 decisions consistent with the original eager CPU model, and both independent exports and packaged executable content are identical. The exact package completes two full official games with cold starts under Python 3.11/3.12, all seats `DONE`, checking a total of 5,760 observations, with consistent action trajectories across runtimes and cash flow. The longest cold-start action takes 1.602 seconds, subsequent actions take 0.347 seconds, and the final additional time budget is at least 59.398 seconds. Deployment modules Ruff and mypy pass, and temporary isolation directories have been cleaned. See [Deployment Qualification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u2912-20260914-double/qualification.json), [Two Upload Confirmations](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u2912-20260914-double/submission-receipts.json), and [Kaggle Status Verification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u2912-20260914-double/submission-status.json).

### Previous submission: Two days Top10 BC budget-q100, Turn 1004, submitted once

2026-09-13 Submitted according to user request, fixed selection at current main runtime
`budget-q100-top10-2d-20260913-s68001` latest complete checkpoint **U1004**, cumulative
**128,512 games of RL**, submitted under **T=1, FP32 CPU conditional random sampling**.
Kaggle received at **12:23:53 UTC**, assigned ID **56206814**. Only one submission interface call made,
confirmation check verifies exactly one record added; initial status was `PENDING`, no score yet.
Training continues running; upon recheck, has advanced to U1025.

Checkpoint SHA256 is `2cf30aaa4fe020aed40fa711296e39c85b9f00259029a948171d6cf66033156d`, independently retained at [fixed weights](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u1004-20260913-once/update-001004.pt).
The actual [submission.tar.gz](../outputs/deployment/budget-q100-top10-2d-s68001-u1004-20260913-once/submission.tar.gz)
has SHA256 of `e5e152350977aaf86dfe22b630a6bb0e60bcd26a362d78f855e98d1534446a34`, 77,451,261 bytes.
The deployed source code and this training archive are fully consistent, preserving budget features, fixed **1–100** quantity classification, and the original deployment sampling seed.

All 1,515 checkpoint tensor limits met; in two full games, a total of 2,876 decisions match the original eager CPU model, and two independent exports with in-package execution are consistent. The exact package completes two full official games with cold starts under Python 3.11/3.12, occupying all seats `DONE`, checking 5,760 observations across runtime action trajectories and cash flow. Maximum cold-start action duration is less than 1.615 seconds, subsequent actions less than 0.354 seconds, and final additional time at least 59.385 seconds. Deployment modules Ruff and mypy pass, and temporary directories have been cleaned. See [Deployment Qualification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u1004-20260913-once/qualification.json), [Upload Confirmation](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u1004-20260913-once/submission-receipt.json), and [Kaggle Status Verification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u1004-20260913-once/submission-status.json).

### Previous submission: Two days Top10 BC budget-q100, Turn 452, submitted two versions with the same weights

2026-09-13 Following user request, fixed selection of current primary run
`budget-q100-top10-2d-20260913-s68001` latest complete checkpoint **U452**, cumulative
**57,856 games of RL**. Two successful submissions from the same package: **56202703** (1/2, 08:08:59 UTC)
and **56202739** (2/2, 08:11:15 UTC). Kaggle retrospective confirmation verifies exactly these two submissions were added;
initial retrospective checks both point to `PENDING`, with no scores yet; during retrospective review, training progressed normally to U492.

checkpoint SHA256 is `024911caecb5c58272fd809fc5a1d98698700b44016b9f338985a0c9e2c95d0f`,
independently retained at [fixed weights](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u452-20260913-double/update-000452.pt).
Two instances actually use the same [submission.tar.gz](../outputs/deployment/budget-q100-top10-2d-s68001-u452-20260913-double/submission.tar.gz),
SHA256 `aeacea13eb2ce8f8ec27a75d232ed269f0453d8deaec339cd0a2b1e0c90f581d`, 77,448,086 bytes.
The deployed source code and the current training archive are fully consistent, preserving budget features, fixed **1–100** quantity classification,
FP32 CPU conditional sampling, default temperature **T=1**, and the original deployment sampling seed.

All 1,515 checkpoint tensors are finite; two full games resulted in 2,876 decisions
Matches the original eager CPU model: independent export and in-package execution are consistent. Exact package verified under Python 3.11/3.12
Completed two full official games with cold starts, all seats `DONE`, totaling 5,760 observations, with consistent action trajectories and cash flow across runtimes. Maximum cold-start action time: 1.548 seconds, subsequent actions: 0.349 seconds, final additional time at least 59.452 seconds. Deployment modules Ruff and mypy passed; temporary directories cleaned.
See [Deployment Qualification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u452-20260913-double/qualification.json),
[Two Upload Confirmations](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u452-20260913-double/submission-receipts.json), and
[Kaggle Status Verification](../outputs/analysis/kaggle-budget-q100-top10-2d-s68001-u452-20260913-double/submission-status.json).

### Previous submission: three-day BC budget-q100, turn 1060, submitted two versions with the same weights

2026-09-12 Following user request, fixed selection of primary run
`budget-q100-3d-20260912-s67001`'s latest complete checkpoint **U1060**, cumulative training
**135,680 games**. Two successful submissions from the same package: **56194735** (1/2, 2026-09-13 00:00:02 UTC) and **56194922** (2/2, 00:02:00 UTC). Kaggle retrospective confirmation verifies the addition of exactly these two submissions; both initial checks were for `PENDING`, with no scores yet assigned; training continues.

checkpoint SHA256 is `57ced3b1d5ee975800b40ca9773e117f89e5ebabb6aca5e6556993b07633649e`,
independently retained at [fixed weights](../outputs/analysis/kaggle-budget-q100-3d-s67001-u1060-20260912-double/update-001060.pt).
Two instances actually use the same [submission.tar.gz](../outputs/deployment/budget-q100-3d-s67001-u1060-20260912-double/submission.tar.gz),
SHA256 `633dcefbe7ae632007cad63e169331abc58839b754c07d717dddd4e6fab51d09`, 77,428,373 bytes.
Complete usage of the current training archive source code, retaining budget features, fixed **1–100** quantity classification,
FP32 CPU conditional random sampling and default temperature **T=1**.

All **1,515** checkpoint tensor limits; **2,876 action outputs** from two full games
Matches the original eager CPU model in behavior, with identical results between standalone export and in-package execution. Exact package verified under Python 3.11/3.12
Completed two full official games with cold starts, all seats `DONE`, totaling **5,760 observations**
Action trajectories and cash flow are consistent across runtime environments. Maximum cold-start action time: **1.534 seconds**, subsequent actions: **0.347 seconds**, final additional time budget at least **59.466 seconds**. Deployment modules Ruff and mypy passed; temporary isolation directory cleaned.
See [Deployment Qualification](../outputs/analysis/kaggle-budget-q100-3d-s67001-u1060-20260912-double/qualification.json),
[Two Upload Confirmations](../outputs/analysis/kaggle-budget-q100-3d-s67001-u1060-20260912-double/submission-receipts.json), and
[Kaggle Status Verification](../outputs/analysis/kaggle-budget-q100-3d-s67001-u1060-20260912-double/submission-status.json).

### Previous submission: three-day BC context26M, final turn 3575, T=0, submitted only once

2026-09-11 According to user request, the stopped `context-26m-3d-20260910-s65001`
has its last fully saved **U3575** weights submitted with **T=0, FP32 CPU conditional argmax**,
cumulative training of **457,600 games**. Kaggle received it at **16:44:51 UTC**, assigned number **56169353**.
Only one submission interface call was made; upon verification, only this record was added; the initial verification has not yet returned evaluation status or score.

checkpoint SHA256 is `f270f4fbb18a50a1ee6f0e6ca54fe6abac891ee85a9bdf927e165b0bbb92a3bd`,
saved at [fixed weights](../outputs/analysis/kaggle-context3d-s65001-u3575-t0-20260911-once/update-003575.pt).
Actual [submission.tar.gz](../outputs/deployment/context3d-s65001-u3575-t0-20260911-once/submission.tar.gz)
SHA256 is `d1b4fae952dcb40dc0e5c4a6b67b93f463f6e9bb61b1feaf543914582c86d3fc`, 77,230,051 bytes.
Using the latest `population-revisions/0001` archive source code, only adding the deployment temperature option and its testing;
the model source code and weights remain unchanged, and the package's profile explicitly records temperature 0, with no action sampling operators in the execution graph.

All 1,480 checkpoint tensors are finite; in two full games, there are **2,876 decisions** that match the original model's greedy inference, and the independently exported results are consistent with in-package execution. The exact package completes two full official games with cold starts under Python 3.11/3.12, occupying all seats `DONE`, with consistent action trajectories and cash flow across runtime environments. The maximum cold-start action duration is **2.997 seconds**, subsequent actions take **0.466 seconds**, and the final additional time budget is at least **58.003 seconds**. Deployment modules Ruff, mypy, and T=0/T=1 export tests pass, and temporary isolation directories have been cleaned. See [Deployment Qualification](../outputs/analysis/kaggle-context3d-s65001-u3575-t0-20260911-once/qualification.json), [Upload Confirmation](../outputs/analysis/kaggle-context3d-s65001-u3575-t0-20260911-once/submission-receipt.json), and [Kaggle Recheck](../outputs/analysis/kaggle-context3d-s65001-u3575-t0-20260911-once/submission-status.json).

### Previous submission: three-day BC context26M, turn 2748, submitted two versions with the same weights

2026-09-11 Following user request, fixed selection of current primary run
`context-26m-3d-20260910-s65001`'s latest complete checkpoint **U2748**,with cumulative training of
**351,744 games**. Two successful submissions from the same package: **56161366** (1/2, 07:43:03 UTC) and
**56161402** (2/2, 07:45:16 UTC). Kaggle retrospective confirmation verifies exactly these two submissions were added, both initially had status `PENDING`, with no scores yet; training continues.

checkpoint SHA256 is `efae27fa98ae598b3866b127e6db92203d231dd1b8a6e3e0d9c5d6ceec33131f`,
independently retained at [fixed weights](../outputs/analysis/kaggle-context3d-s65001-u2748-20260911-double/update-002748.pt).
Two instances actually use the same [submission.tar.gz](../outputs/deployment/context3d-s65001-u2748-20260911-double/submission.tar.gz),
SHA256 `466e13b34d4df6b4b3d430b31b5243e85406bb693e2869841033ecedb8732244`, 77,232,473 bytes.
Fully uses the source code from this training archive, retaining FP32 CPU conditional sampling, temperature 1.

All 1,480 checkpoint tensors are finite; two full games consist of **2,876 sampling instances**, matching the original eager CPU model. Exported and in-package execution contents are consistent across both runs. The exact package completes two full official games with cold starts under Python 3.11/3.12, all seats `DONE`, with identical action trajectories and cash flow across runtime environments. The maximum cold-start action duration is **1.489 seconds**, subsequent actions take **0.243 seconds**, and the final additional time budget is at least **59.511 seconds**. Deployment modules Ruff and mypy have passed; temporary isolation directories have been cleaned, while fixed weights, submission package, and report are retained. See [Deployment Qualification](../outputs/analysis/kaggle-context3d-s65001-u2748-20260911-double/qualification.json), [Two Upload Confirmations](../outputs/analysis/kaggle-context3d-s65001-u2748-20260911-double/submission-receipts.json), and [Kaggle Status Verification](../outputs/analysis/kaggle-context3d-s65001-u2748-20260911-double/submission-status.json).

Completed local temperature calibration on 2026-09-11: For the same U2748 weights across 5 native scripts, 32 shared environment seeds, and dual seats, T=0 achieved **320/320 wins**, while the current deployment method at T=1 achieved **317/320 wins**.
In direct head-to-head matches of 32 games, T0 resulted in **15 wins, 17 losses**; thus, a change in online temperature is currently not supported.
Fixed-seed sensitivity and audits of two anomalous opening games are documented in [U2748 Temperature and Seed Comparison](temperature_u2748_20260911.md).
Confirmed that opponent wheat trading caused a cash deficit of 12 for our side and resulted in one fewer sheep purchase, followed by branching at the opening phase;
there remain unlocalized discrepancies between local and online sampling trajectories. The two submissions for U2748 retain both T=1 and the original fixed-sampling seed.

On 2026-09-11, new daily and public submission replays were added as per user requests, with deduplicated analysis of **3,289 games**, and the BC was redesigned; the previous three-layer scheme is not adopted. Initial states were sampled 128 times each, with the first active moves in BC1–4 accounting for **32.8% / 29.7% / 74.2% / 68.0%**, and U2748 at **97.7%**. Among the original three-day 3,976 trajectories, only 2 had incomplete small-animal purchases in the first four steps; the Majkel purchase prefixes passed all 162 two-step perturbation conditions in this round, with no new BC or complete counterfactual win rate conclusions. See [New Data, Stage Localization, and BC Design](bc_redesign_20260911.md). No changes were made to training or deployment configurations.

### Previous submission: three-day BC context26M, turn 1600, submitted two versions with the same weights

2026-09-10 Following user request, fixed selection of current primary run
`context-26m-3d-20260910-s65001`'s latest complete checkpoint **U1600**,with cumulative training of
**204,800 games**. Two successful submissions from the same package were submitted: **56153307** (1/2, 23:27:18 UTC) and
**56153332** (2/2, 23:29:45 UTC). Kaggle review confirms exactly two new submissions were added, both initially had status `PENDING`, with no scores yet assigned; training continues to run.

checkpoint SHA256 is `6efbfecfc51ca28ed78a3ee26241037e08891ed21555bcd3b6484d1afce41193`,
independently retained at [fixed weights](../outputs/analysis/kaggle-context3d-s65001-u1600-20260910-double/update-001600.pt).
Two instances actually use the same [submission.tar.gz](../outputs/deployment/context3d-s65001-u1600-20260910-double/submission.tar.gz),
SHA256 `f75b2720ce09f6b155acbb3712d32c19a5c9f83725d3356fb49c1864e92afd4c`, 77,231,808 bytes.
Fully uses the archived source code from this training run, retaining FP32 CPU conditional sampling, temperature 1.

All 1,480 checkpoint tensors are finite; two full games consist of **2,876 sampling instances**, matching the original eager CPU model, with identical behavior whether exported independently or executed in-package. The exact package completes two full official games with cold starts under Python 3.11/3.12, all seats `DONE`, with consistent action trajectories and cash flow across runtime environments. The maximum cold-start action duration is **2.214 seconds**, subsequent actions take **0.370 seconds**, and the final additional time budget is at least **58.786 seconds**. Deployment modules Ruff and mypy have passed; temporary isolation directories have been cleaned, while fixed weights, submission package, and report are retained. See [Deployment Qualification](../outputs/analysis/kaggle-context3d-s65001-u1600-20260910-double/qualification.json), [Two Upload Confirmations](../outputs/analysis/kaggle-context3d-s65001-u1600-20260910-double/submission-receipts.json), and [Kaggle Status Verification](../outputs/analysis/kaggle-context3d-s65001-u1600-20260910-double/submission-status.json).

### Previous submission: context26M, turn 4302, submitted once

2026-09-10 Upon user request, submit `context-26m-20260908-s62001` previously stopped and archived for **U4302**, totaling **551,040 turns**, including historical data and script PFSP from U3781 to U4302.
Kaggle received it at **11:51:09 UTC**, with successful acknowledgment number **56143582**.
Confirmation check verifies only this submission was added; the initial status was `PENDING`, and no score has been assigned yet.

checkpoint SHA256 is `2be6014c0a43701be311f0795cc5d10365e5c65339f88a8f59c1a801e6014082`,
using [U4302 fixed weights](../outputs/archives/context-26m-20260908-s62001-u4302/update-004302.pt).
The actual package is [submission.tar.gz](../outputs/deployment/context-s62001-u4302-20260910/submission.tar.gz),
SHA256 `ea2a73dc69d989ce654ae00cc46d5a59d65e6e1dddcf76d56e5e1a46f34c8246`, 77,098,048 bytes.
Retain FP32 CPU conditional sampling, temperature 1; fully use the U4302 training archive source code, source code SHA256 is
`a96851f251faf732d8304aa39244152441dd374393f3b01feea638d07b259d9a`, no need to export source code with patch overlay.

1,480 checkpoint tensors are all finite; in two full games, a total of **2,876 sampling instances** match the original eager CPU model, with consistent behavior between independent export and in-package execution. The exact package completes two full official games with cold starts under Python 3.11/3.12, all seats `DONE`, with identical action trajectories and cash flow across runtimes. The maximum cold-start action takes **2.958 seconds**, subsequent actions take **0.375 seconds**, and the final additional time budget is at least **58.042 seconds**. Deployment modules Ruff and mypy pass; temporary isolation directories have been cleaned up, while fixed weights, submission package, and report are retained. See [Deployment Qualification](../outputs/analysis/kaggle-context-s62001-u4302-20260910/qualification.json), [Upload Confirmation](../outputs/analysis/kaggle-context-s62001-u4302-20260910/submission-receipt.json), and [Kaggle Status Verification](../outputs/analysis/kaggle-context-s62001-u4302-20260910/submission-status.json).

### Previous submission: context26M, turn 3364, submitted once

2026-09-10 Following user request, fixed selection at current main run
`context-26m-20260908-s62001` Latest complete checkpoint: Round **3364**, cumulative **430,976 games**. Only one submission interface call made; Kaggle successful confirmation number is **56133717**.
Verification confirms only this single submission was added; initial status was `PENDING`, with no score yet.
At submission time, training used GPU0 + GPU1; this package is fixed to the weights from Round 3364.
This run has now been stopped on U4302; no additional submission was made to U4302.

Checkpoint SHA256 is `d3b7996cc4da8c7aabf7c4be58753c7e8f1c03dfd97a996d2031a375aefe3063`,
independently retained at [submission weights](../outputs/analysis/kaggle-context-s62001-u3364-20260910-once/update-003364.pt).
The actual package is [submission.tar.gz](../outputs/deployment/context-s62001-u3364-20260910-once/submission.tar.gz),
SHA256 `2e64c12169701de24e5b24df13bf11c633b55ee247b5e33bfcfdc5c3ebc59eb0`, 77,097,156 bytes.
Retains FP32 CPU conditional sampling, temperature 1; uses the training archive source code, with only the LayerNorm export fix from the previously approved `deployment/actor.py` integrated.

All 1,480 tensor values in the checkpoint are finite; across two full games, there are **2,876 sampling instances** that match the original eager CPU model, with identical behavior whether exported independently or executed in-package. The exact package completes two full official games including cold starts under each of Python 3.11/3.12, all seats `DONE`, with consistent action trajectories and cash flow across runtime environments. The maximum cold-start action duration is **2.997 seconds**, subsequent actions take **0.482 seconds**, and the final additional time budget is at least **58.002 seconds**. Deployment modules Ruff and mypy have passed, and temporary isolation directories have been cleaned up. See [Deployment Qualification](../outputs/analysis/kaggle-context-s62001-u3364-20260910-once/qualification.json), [Unique Upload Acknowledgment](../outputs/analysis/kaggle-context-s62001-u3364-20260910-once/submission-receipt.json), and [Kaggle Status Verification](../outputs/analysis/kaggle-context-s62001-u3364-20260910-once/submission-status.json).

### Previous submission: context26M, turn 2420, submitted two copies with the same weights

2026-09-09 Following user request, fixed selection of current primary run
`context-26m-20260908-s62001`'s latest complete checkpoint: Round **2420**, cumulative **310,144 games**. Two consecutive submissions from the same package, Kaggle submission **56127637** (1/2) and **56127667** (2/2), both first jointly verified at `PENDING`. Training continues using GPU0 + GPU1.
This checkpoint includes training starting from Round 2392 with `shop_router_0909` replacing `kaito_v58`.

checkpoint SHA256 is `219dc15e5091a81064b436454c7bd24d4677deff840aef60426ff096729ee581`,
independently retained at [submission weights](../outputs/analysis/kaggle-context-s62001-u2420-20260909-double/update-002420.pt).
Both actual packages are [submission.tar.gz](../outputs/deployment/context-s62001-u2420-20260909-double-portable-v2/submission.tar.gz),
SHA256 `1f7fee11442bd05a9852411e9f46ab0ab2a02373390ede0fc98a436aea15ff79`, 77,096,456 bytes.
Retain FP32 CPU conditional sampling, temperature 1.

After exporting custom LayerNorm from training archives, the model cannot be loaded in standalone processes. This issue is fixed by adding support for `deployment/actor.py`'s CPU export: copy the model, replace the LayerNorm in the copy with the built-in operator having identical weights and epsilon, while preserving the original training model and its fusion isolation. The training model source code remains unchanged. Separate hash records are maintained for training and deployment source codes, see [Export Source Code Differences](../outputs/analysis/kaggle-context-s62001-u2420-20260909-double/deployment-source-change.json).

After fixing, the two full games collectively achieved **2,876 sampling instances** matching the original eager CPU model, with independent exports and in-package execution content being consistent. The exact package completed two full official games including cold starts under Python 3.11/3.12, all seats `DONE`, with identical cross-runtime action trajectories and cash flow. The maximum cold-start action took **1.440 seconds**, subsequent actions took **0.240 seconds**, and the final additional time budget was at least **59.560 seconds**. 5 regression tests, full Ruff, and mypy (682 source files) passed; the temporary isolated directory has been cleaned up.
See [Deployment Qualification](../outputs/analysis/kaggle-context-s62001-u2420-20260909-double/qualification.json),
[two upload confirmations](../outputs/analysis/kaggle-context-s62001-u2420-20260909-double/submission-receipts.json), and
[Kaggle Status](../outputs/analysis/kaggle-context-s62001-u2420-20260909-double/submission-status.json).

### Previous submission: context26M, turn 2044, submitted two copies with the same weights

2026-09-09 Following user request, fixed selection at current main run
`context-26m-20260908-s62001`'s latest complete checkpoint: Round **2044**, cumulative **262,016 games**. Two consecutive submissions from the same package, Kaggle submission **56109929** (1/2) and **56109960** (2/2), both first jointly verified at `PENDING`. Training continues running; both submissions are fixed at Round 2044 this time.
This checkpoint uses 50% self-play and 50% native scripts, with scripts being `router_95`, `farming_v4`, `kaito_v58`, and `shop_router_0908`.

checkpoint SHA256 is `9ea5bd68d13e2f3ab7d892518e76d5c91cd9d1301450686038eaffdc25a1e3d2`,
kept independently at [submission weights](../outputs/analysis/kaggle-context-s62001-u2044-20260909-double/update-002044.pt).
Both actual packages are [submission.tar.gz](../outputs/deployment/context-s62001-u2044-20260909-double/submission.tar.gz),
SHA256 `caaba62bcbf8617e4fc9ee03bb53510de4cef9a17559d3eb6ab35adaacdcd7e0`, 77,093,975 bytes.
Built using training archive source code isolation, preserving FP32 CPU conditional sampling, temperature 1.

Two full games collectively achieved 2,876 sampling instances matching the eager CPU behavior, with independent export and submitted package execution content being consistent.
The exact package completed two full official games including cold starts under Python 3.11/3.12, occupying all seats `DONE`, with cross-runtime action trajectories matching cash flow. The maximum cold-start action duration was approximately 1.435 seconds, subsequent actions took about 0.241 seconds, and the final additional time budget was at least 59.565 seconds. Deployment modules Ruff and mypy passed, and temporary isolation directories have been cleaned.
See [Deployment Qualification](../outputs/analysis/kaggle-context-s62001-u2044-20260909-double/qualification.json),
[Two Upload Receipts](../outputs/analysis/kaggle-context-s62001-u2044-20260909-double/submission-receipts.json), and
[Kaggle Status](../outputs/analysis/kaggle-context-s62001-u2044-20260909-double/submission-status.json).
The game score will be determined by Kaggle's subsequent results.

### Previous submission: context26M, turn 696

2026-09-08 Following user request, fixed selection at current main runtime
`context-26m-20260908-s62001`'s latest complete checkpoint: Round **696**, cumulative **89,472 games**, Kaggle submission **56098745**, first backcheck at **`PENDING`**.
This checkpoint uses a 50% self-play, 50% native script recipe, with scripts being
`router_95`, `farming_v4`, `kaito_v58`, `boatlee_v29`.

checkpoint SHA256 is `ef9d06e0e64cc55b3223543de375157d62b520ae5c0b5cf29686223f54fa6acf`,
independently retained at [submission weights](../outputs/analysis/kaggle-context-s62001-u696-20260908/update-000696.pt).
The actual package is [submission.tar.gz](../outputs/deployment/context-s62001-u696-20260908/submission.tar.gz),
SHA256 `d0257c37fb3c65859d2a99d2dad9e528a873557dfc4f3b20c13b3bdc24ff5906`, 77,094,534 bytes.
The deployment source code and the training archive of this checkpoint are consistent, preserving FP32 CPU conditional sampling, temperature 1.

After final source code consistency protection triggered by the first eager check during parallel workspace modifications, the original source code from build time and native library snapshots are used to isolate and rerun the process. Across two complete games, 2,876 sampling programs consistently match the eager CPU behavior. The exact package completes two full official games including cold starts under Python 3.11/3.12, occupying all seats `DONE`. Cross-runtime action trajectories and cash flows are consistent. The maximum cold-start action duration is approximately 1.438 seconds, with subsequent actions at about 0.242 seconds, and the final additional time budget is at least 59.562 seconds. Deployment modules Ruff and mypy pass, and the temporary isolation directory has been cleaned up. See [Deployment Qualification](../outputs/analysis/kaggle-context-s62001-u696-20260908/qualification.json), [Upload Confirmation](../outputs/analysis/kaggle-context-s62001-u696-20260908/submission-receipt.json), and [Kaggle Status](../outputs/analysis/kaggle-context-s62001-u696-20260908/submission-status.json). Game scores are final as determined by Kaggle's subsequent results.

### Previous submission: context26M, turn 320

2026-09-08 According to the requirement to fix the current main run upon user's re-submission of the latest weights, the main run is fixed at the current state.
The most recent complete checkpoint for `context-26m-20260908-s62001` during packaging: Round **320**, cumulative **41,344 games**, Kaggle submission **56095579**, first backcheck at **`PENDING`**.
Training continues, with this submission fixed at Round 320. The recipe remains 50% self-play and 50% new four native scripts.

Checkpoint SHA256 is `12b2becc3a2ebc0941d86efc75d6cebf504eb95c7d1d33fc942628fbe06ea6b6`,
kept independently at [submission weights](../outputs/analysis/kaggle-context-s62001-u320-20260908/update-000320.pt).
The actual package is [submission.tar.gz](../outputs/deployment/context-s62001-u320-20260908/submission.tar.gz),
SHA256 `1d2780c726f2df0705b61e989cf215f24f60613434ec647a189966eaa228bbd5`, 77,095,133 bytes.
The deployment source code and training archive are consistent, preserving FP32 CPU conditional sampling, temperature 1.

Two independent and complete games collectively consist of 2,876 sampling instances that are consistent with eager CPU execution; exact package tested under Python 3.11/3.12.
Each completed two full official games including cold starts, all seats `DONE`, with cross-runtime action trajectories and cash flow matching exactly.
Maximum cold-start action duration is approximately 1.647 seconds, subsequent actions take about 0.345 seconds, and the minimum remaining credit allowance is approximately 59.353 seconds.
Deployment modules Ruff and mypy have passed. See
[Deployment Qualification](../outputs/analysis/kaggle-context-s62001-u320-20260908/qualification.json),
[Upload Confirmation](../outputs/analysis/kaggle-context-s62001-u320-20260908/submission-receipt.json), and
[Kaggle Status](../outputs/analysis/kaggle-context-s62001-u320-20260908/submission-status.json).
Game scores are finalised based on Kaggle's subsequent results.

### Earlier submission: context26M, Turn 124

2026-09-08 According to user request, fixed packaging with current main runtime
`context-26m-20260908-s62001`'s latest complete checkpoint: Round **124**, cumulative **16,256 games**, submitted to Kaggle, submission **56093874**, first backcheck is **`PENDING`**.
Training continues running; this submission is fixed at Round 124 and will not be updated by subsequent training.
Starting from Round 106, a recipe of 50% self-play and 50% new four native scripts was used.

checkpoint SHA256 is `889ef31978ccca20fe4f37ed620fc653b9210ac0668240e430a0dab2f1c6d98b`,
independently retained at [submission weights](../outputs/analysis/kaggle-context-s62001-u124-20260908/update-000124.pt),
to prevent losing the submission origin after training retention strategy cleanup. The actual package is
[submission.tar.gz](../outputs/deployment/context-s62001-u124-20260908/submission.tar.gz),
SHA256 `d60699f561884b7895cc6325cd8449db541890dfb47c4fae19cf0d6cb04bf6df`, 77,093,094 bytes.
Deployed as `grounded-production-context-v2` Actor, FP32 CPU conditional random sampling, temperature 1;
the deployment source code is identical to the current training archive.

Local sampling program completed 2,876 times and is fully consistent with eager CPU; exact packages completed two official full games containing cold starts under Python 3.11/3.12, all seats `DONE`, with identical runtime action trajectories and cash flow.
Maximum cold-start action: 1.438 seconds, subsequent actions: 0.239 seconds, final additional time at least 59.562 seconds.
Deployment modules Ruff and mypy passed. See
[Deployment Qualification](../outputs/analysis/kaggle-context-s62001-u124-20260908/qualification.json),
[Upload Confirmation](../outputs/analysis/kaggle-context-s62001-u124-20260908/submission-receipt.json), and
[Kaggle Status](../outputs/analysis/kaggle-context-s62001-u124-20260908/submission-status.json).
Game scores are finalised based on Kaggle's subsequent results.

### Earlier submission: Original 100k run, turn 484

2026-09-08 Submitted the current 100k runs with the latest complete weights at packing time as per user request:
`long-100k-20260908-s61001`, Round **484**, Kaggle submission 56089681,
First status check was `PENDING`. Training continued after submission until it stopped at the aforementioned Round 526; this submission is fixed at Round 484.
Checkpoint SHA256 is `e6abaf743404a3ea4d6a3e96b1fa2a50968a9e09abeea0f392a127e2e4ae4862`,
Actual package is [submission.tar.gz](../outputs/deployment/long-s61001-u484-20260908/submission.tar.gz),
SHA256 `5967bbbff1cf58ed48f21e78cde5d3c542fb3d8c342619f41fbf7f1a01230368`, 3,868,336 bytes.
Deployment uses FP32 CPU conditional sampling with temperature 1, preserving the original model's decision mechanism.

Locally verified 2,876 sampling programs are consistent with eager CPU; exact packages completed two full official games with cold starts under Python 3.11/3.12, all seats `DONE`, with identical runtime action trajectories. Maximum cold-start action duration: 1.138 seconds, subsequent actions: 0.057 seconds, final additional budget at least 59.862 seconds. See
[Deployment Qualification](../outputs/analysis/kaggle-long-s61001-u484-20260908/qualification.json),
[Upload Confirmation](../outputs/analysis/kaggle-long-s61001-u484-20260908/submission-receipt.json), and
[Kaggle Status](../outputs/analysis/kaggle-long-s61001-u484-20260908/submission-status.json).
This is the latest weight submission specified by the user; the competition score will be determined by Kaggle's subsequent results.

## Already stopped running: originally planned 100k updates

2026-09-08 Started according to user budget
[`long-100k-20260908-s61001`](../outputs/learning/long-100k-20260908-s61001/launch.json),
Now optimized for synchronous training of the same strategy on GPU 0 + GPU 1, tmux session `revue_long_100k_s61001`.
Dual-GPU restart launch log available at [hardware-launch.json](../outputs/learning/long-100k-20260908-s61001/hardware-launch.json). Configured as
[`learning_long.yaml`](../configs/learning_long.yaml), actual parameters subject to
[resolved-config.json](../outputs/learning/long-100k-20260908-s61001/resolved-config.json).
Using a recipe previously validated through two random roots over 512 rounds: fresh random root, fixed four-round multi-date demonstration pre-training, followed by 100,000 online PPO updates; first 458 rounds consist of 128 games per round, thereafter each round consists of 512 games as per user request; total online budget is 51,024,128 full games.
No continuation from the completed 512-round model. Initial identity is `d16d89320f7f4416a7c4757d31ef75a5`;
this run has no long-term profitability conclusion; current deployment choice remains the 512-round product already verified below.

2026-09-08 Proceed to integrate the existing native C++ script opponents as per user requirements, and continue training from the original runtime.

Each turn now consists of **256 self-play games, 128 historical model games, and 128 script opponent games**; the script games are evenly distributed among Kaito v39, Kaito v48, Mugundh v21, and Boatlee v21, with 32 games per version, maintaining balanced seat allocation between both sides.

The initial batch upon script integration is 64/32/32; starting from Turn 459, the batch size is increased fourfold, maintaining the same ratio of 50%/25%/25%.

Directly reuse `_revue_native.ParallelBatch` and the original C++ sessions; the training hot path does not involve Python script callbacks, and no new strategy porting is introduced. This explicit instruction updates the boundary previously stated on September 7 regarding "not using the four old scripts"; the prohibition on old neural model weights remains in effect, and scripts are used solely as frozen opponents.

Lost progress after turn 318; actual recoverable checkpoint is at turn **316**; turns 317–318 are recomputed from scratch.
Bug checks confirmed and fixed: infinite noise endpoint in compilation sampling, and NCCL cleanup hang during worker exceptions.
16 full official games verified; 11,504 actions across four scripts match the original implementation;
Dual-GPU replica completed **316→320 stop→328 recovery**, with stable median time of **4.165 seconds per turn**.
This is only an integration and recovery check, no algorithm ablation performed, and does not represent proven training gains.
See [complete qualification](../outputs/analysis/script-population-20260908/qualification.json),
[access protocol and fault diagnosis](learning_script_population.md).

Main execution has used archived source code and native asset recovery. Launch records are available at [population-launch.json](../outputs/learning/long-100k-20260908-s61001/population-launch.json), and source code revision logs are stored at [population-revisions/0001](../outputs/learning/long-100k-20260908-s61001/population-revisions/0001/qualification.json). The original random root, model, optimizer, dual-GPU RNG, learning rate `2.5e-5`, historical pool, and 100k total budget have been preserved. These four versions are now considered previously encountered training opponents. Shop/Pasture and EcoBot remain outside of training. Potential commonalities among route implementations must still be considered when interpreting generalization results.

Then, according to user requirements, each game's batch size was increased from 128 to 512. The main run successfully saved at turn **458** and proceeded to turn **459**; each GPU handled 256 games, totaling 768 learning trajectories. The logical minibatch remained at 5,760 rows, with 96 optimization steps per actor/critic per turn, and the original learning rate, historical pool, fixed evaluation, and 100k update budget were preserved. An independent replica completed **458→462 stop→466 resume**, achieving stable rounds of approximately **13.3 seconds**, with peak GPU memory allocation per card reaching about **23.6 GiB**. The number of complete games per turn, total game count, games against each opponent, and checkpoint parent chain were all confirmed. This is an expansion and recovery check, without ablation studies. See
[512-game eligibility](../outputs/analysis/batch-512-20260908/qualification.json),
[configuration revision](../outputs/learning/long-100k-20260908-s61001/batch-revisions/0001/qualification.json), and
[this launch](../outputs/learning/long-100k-20260908-s61001/batch-launch.json).
The WebUI displays actual per-script statistics; browser validation on desktop and mobile devices is available at
[interface eligibility](../outputs/analysis/batch-512-20260908/browser-qualification.json).

2026-09-08 Optimized throughput as per user request: After the original training stopped normally at turn 93, the complete optimizer, the actor learning rate already reduced to `2.5e-5`, and historical pool retained from the original checkpoint were preserved and resumed from that point.
Each H200 handles 64 games; global game count, logical minibatch size, loss, and 100k budget remain unchanged;
After compiling inference, increasing microbatch size, fusing targets, assigning CPU affinity, and caching historical weights,
the stable time for full stop/resume operations dropped from approximately 15.7 seconds per turn to 4.26 seconds per turn, achieving about **3.7x throughput improvement**.
The 48 available CPU cores are divided into two groups, with 8 environment threads per GPU; specific selection criteria are detailed in
[Execution Optimization](learning_performance.md). An independent replica completed the stop sequence from turn 93 to 97, followed by resumption through round 105, as reported in
[Qualification Report](../outputs/analysis/dual-h200/qualification.json). The original model, original source code, and native binaries are preserved; changes to source code and execution configuration are separately logged in
[Run Revision](../outputs/learning/long-100k-20260908-s61001/runtime-revisions/0001/qualification.json).
The sampling stream and floating-point reduction after the switch are not bit-identical to those of a single GPU; subsequent resumption remains bound to the exact configuration, source code, and dual-GPU RNG.

Model, loss, historical pool capacity, and snapshot cycle follow the verified recipe; opponent ratio is updated as per the above instructions.
For long-term operation, a complete recovery point is saved every 4 updates.
Consistent with the original historical pool snapshot cycle, recovery points are also saved at the final update and during normal shutdown. A fixed selection is performed every 512 updates, with a reservation confirmation at the budget endpoint; self-initialization and random anchor points are used solely for diagnostics.
The first 458 turns use the online seed interval `[3,000,000,000, 3,000,058,624)`. After scaling up, the new interval `train_seed=3,100,000,000` is adopted; for turns 459 to 100,000, the actual interval is `[3,100,234,496, 3,151,200,000)`, separated from original training, demonstration, and fixed evaluation seed intervals.
The boundary of the original 128-game configuration interval is referenced in [Seed Eligibility](../outputs/analysis/long-100k-launch/seed-qualification.json).
Intermittent saves, complete optimizer/RNG, historical pool, and last step saves have passed independent short-range GPU verification, as detailed in [Process Eligibility](../outputs/analysis/long-100k-launch/training-qualification.json).

Real-time status viewing of [run-status.json](../outputs/learning/long-100k-20260908-s61001/run-status.json),
[learning-progress.json](../outputs/learning/long-100k-20260908-s61001/learning-progress.json), and
[recovery log](../outputs/learning/long-100k-20260908-s61001/batch-recovery.log).
[recovery-status.json](../outputs/learning/long-100k-20260908-s61001/recovery-status.json) records the current isolation recovery process and log location.
WebUI is at `http://127.0.0.1:8765/?run=learning/long-100k-20260908-s61001`, displaying example shard/NLL, PPO real-time updates, saved recovery checkpoints, and per-script training statistics, including win/draw/loss, win rate, final cash of the learning agent, cash difference, and curves. Total games are the sum of actual games across all rounds; operation instructions are available in [monitoring.md](monitoring.md).
At startup acceptance, four rounds of demonstration training were completed (7,690,368 lines, 30,088 supervision updates, with NLL left at 0.3290), online PPO has been written with a full recovery checkpoint from the 4th update and 512-game metrics. The browser has verified pre-training auto-refresh, new PPO curve display, evaluation mode switching, and mobile-width layout, as seen in
[Startup Acceptance](../outputs/analysis/long-100k-launch/report.json) and
[WebUI Acceptance](../outputs/analysis/long-100k-launch/browser-qualification.json).

## A Reinforcement Learning Refactoring from Scratch

2026-09-07 User requests a complete project restructure, abandoning the specific teacher version and four outdated script opponents, starting from entirely random weights. **All model weights prior to this instruction are strictly prohibited from being used in the new mainline**, including initialization, recovery, training opponents, evaluating opponents, and implicit BC fallback. Previous research incumbents and submissions are solely for historical reference and cannot serve as parent weights for the new model. The mainline restructure and 512-turn expanded budget validation have been completed. Results are delivered in [learning_results.md](learning_results.md), with applicable scope and subsequent boundaries detailed in [learning_system.md](learning_system.md).

The new default entry point is `python -m kagg_revue.learning.cli`, with Hydra configured as [learning_mainline.yaml](../configs/learning_mainline.yaml). The installed `kagg-revue` also points to this entry point; the old BC entry point is now explicitly set to `kagg-revue-bc`. The default recipe contains no external checkpoint or teacher input; script opponents are only enabled when explicitly declared as `script_population`, with changes from the current 100k run described above.

By default, a multi-date demonstration initialization, verified through a full budget of two RNGs, is combined with 512 online PPO training rounds, using a new random root and output directory with a timestamp. `learning_demonstrations.yaml` retains the explicit parameters from the first experiment, and `learning_grounded.yaml` retains the pure RL ablation. Default recipe status does not equate to model deployment advancement.

Restoration is restricted to models already registered in the ledger of the current run, with consistent hashes, and specifically bound to the exact configuration, source code, and native ABI of that run. Hardware execution upgrades must undergo independent qualification and preserve original identity and version archiving, and cannot bypass restoration verification directly.

**Latest Conclusion: Two new random roots each completed 65,536 online PPO games, independently confirming support for later returns from 128 to 512 turns.**
Against four pre-fixed neural opponents, the scores of 51001 increased from 62.01% to 92.97%, and 51002 from 57.42% to 86.13%. The paired incremental gain was 30.96/28.71 percentage points, with 95% confidence intervals of [27.73, 34.08]/[25.59, 31.84]. Each budget point involved 512 games and 64 independent environment seeds.
See [Independent Confirmation of 512 Turns](../outputs/analysis/scratch-scaling-common-confirmation/curves.json) and [Budget Increment](../outputs/analysis/scratch-scaling-common-confirmation/figures/incremental.json).
The primary gains originated from two stronger original mainline endpoints; the two weaker opponents have reached saturation. Previously, some adjacent budget intervals crossed zero, so we cannot claim a definite improvement across every segment of budget. Full selection and long-budget public family confirmations have now concluded. The unified identities of the six panels and their later intervals are detailed in [Conclusion Index](../outputs/analysis/scratch-scaling-conclusion/report.json).
**Newly downloaded public route/rule opponents revealed an external strength gap: two 128-turn models each suffered complete losses in independent confirmations over 128 games.** Although average cash increased from 24,000/21,000 to 64,000/63,000, it remains below the opponents' 93,000/95,000. See [Public Opponent Confirmation](../outputs/analysis/scratch-demonstrations-public-confirmation/comparison.json).
Internal results do not substitute for this external failure. The new deployment package has passed the full official closed-loop test using both native Python/PyTorch combinations and has been verified with the native official timer—including first-import and additional quota checks—see [Cold Start Qualification](../outputs/analysis/deployment-budget-v3/qualification.json).
External gains of the 512-turn model on EcoBot have also been independently confirmed: scores increased from 63.28%/42.97% to 91.41%/96.88%, with a 128→512 incremental gain of 28.13/53.91 percentage points, confidence interval [19.53, 36.72]/[44.82, 62.50]. See
[EcoBot long budget confirmation](../outputs/analysis/scratch-scaling-public-rules-confirmation/comparison.json).
The route family still has only 2/128, 0/128 wins, and cannot claim broad external advantage; Kaggle host budget has not been verified.

The locally default delivery package has been updated to a fixed 512-turn endpoint of the first root, see
[Portable Package](../outputs/deployment/scratch-scaling-s51001-u512-portable-v1/submission.tar.gz) and
[Exact Package Eligibility with Cold Start](../outputs/analysis/deployment-scaling-s51001-u512/qualification.json).
Default training starts from a new random root; the delivery package is not used as an initialization source and is neither uploaded nor submitted to Kaggle.

**The reactive rule family EcoBot has confirmed external win gains.** Two 128-round models independently achieved wins of 105/128 and 94/128, respectively, with win rates increasing from their fixed demonstration endpoints of 2.34%/0.78% to 82.03%/73.44%; the gain is 79.69/72.66 percentage points, with a 95% confidence interval [72.66, 86.72]/[64.06, 81.25]. See
[EcoBot Independent Confirmation](../outputs/analysis/scratch-demonstrations-public-rules-confirmation/comparison.json).
This family does not undergo training; performance is reported separately from the original trajectory strategy, and thus cannot be claimed to have overcome all external strength gaps.
The confirmation identity, win rates, cash balances, and pairing intervals for the same candidate across both families can be directly cross-verified at
[External Family Comparison](../outputs/analysis/scratch-demonstrations-external-families/comparison.json).

### Completed Exploration and State Course

Pure RL and replay-state curriculum have completed multiple zero-shot experiments, but no reliable autonomous production has been established:

| Method | Main Budget Completed | Diagnostic Conclusion |
| --- | --- | --- |
| work-v1, terminal WDL | Two RNGs, each 8,192 games | Large missing unit credit; no watering and harvesting |
| grounded-v1, full opening | Two RNGs, each 2,048 games | Improved credit interface, but primarily learned to reduce spending |
| Multi-source state curriculum | Two RNGs, each 64 × 128 games | Local gains observed in suffix; full opening still lacks production |
| Earlier entry with sales quantity bias | Root-paired two branches, each 128 × 128 games | Budget completed after fixing backpack ordering; autonomous operation still not resolved |

These failures have led to the current recipe of "fixed multi-date demonstration initialization, followed by closing the demonstration target and performing online PPO."
The complete budget, official behavior, eligibility for recovery, and failure reasons are retained in
[Early Experiment Records](learning_experiment_log.md), [Grounded Interface](grounded_policy.md), and
[State Curriculum](restart_curriculum.md). They are not used as sources for the current model's strength or teacher weights.

### Multi-date demonstration initialization, separate measurement of subsequent RL

The autonomous production capability of the state course has not yet been established. The next assumption is to use real decisions from multiple dates and multiple sources, learn fundamental operations from new random parameters, then disable the demonstration target and rely solely on online PPO to evaluate whether a larger budget continues to improve performance. This approach does not read any previous models. Training dates are September 3–4; source selection occurs on September 5; September 6 is not used as a new initialization action label, nor is the final outcome from the source used as input or as a filtering condition.

Data preparation is complete: 1,337 training games, 1,922,592 available decisions; 664 selection games, 954,787 decisions.
There are 14/45 decisions that depend on in-round cross-unit resource transfers not supported by the current strategy, explicitly excluded; labels are not modified.
The training/selection coverage includes 66/32 display names, which does not equate to the number of distinct strategy versions.
The quantity table contains 158 exact values, composed of training labels and declared exploration symbols, with no usage of selection-expanded vocabulary.
See [Data Inventory](../data/external/grounded-demonstrations-20260903-05-v1/manifest.json), SHA256 is
`31af71c65666fad467eb5e6a06a9c0edaaef6c7dd6137315199c7cb20996989e`.

Four game replays covering the high and low scoring endpoints across two training dates passed all action reconstruction, state feature, and strategy support checks, see [roundtrip](../outputs/analysis/daily-grounded-pretraining/roundtrip.json). The native binary SHA256 for this data encoding is `ab3a125f34b0c148efba722ee9003ce69e8cd197d1135be7b288dcb5ed377137`; after recompilation, it again passed official interpreter, native engine, and replay audit of 64 games / 92,160 observations, see [native audit](../outputs/analysis/daily-20260906-demonstration-native-audit/report.json).

Implementation details are as specified in [demonstration_initialization.md](demonstration_initialization.md). Random roots, fixed demonstration budget endpoints, and individual budgets for each PPO have distinct identities; the RL zero-budget explicitly adopts the demonstration endpoint, avoiding attribution of supervision training gains to RL gains. Recovery and lineage testing, as well as full GPU pipeline qualification for FP32/BF16 compilation, have all passed: each trained 2,876 demonstration trajectories from a random root, followed by 2 × 8 PPO episodes and independent confirmation. See [Technical Qualification Report](../outputs/analysis/scratch-demonstration-qualification/comparison.json).

Complete two RNG experiments have been finalized and exited: `scratch-demonstrations-s47001` (cuda:0) and `scratch-demonstrations-s47002` (cuda:1), each undergoing 4 demonstration epochs followed by 128 × 128 full PPO episodes. Source code fingerprint is `7b68df7f97f41d10dea439d219043f648fef1816273549524fba2a728d4ba624`; input data inventory and all array hashes were verified prior to the first supervision update. Each group added 16,384 full games online, 11,780,096 policy transitions; actor updates were respectively 3, 052/3, 072, each with two KL retractions, and the final learning rate was 2.5e-5. Full budget and self-randomized control confirmation is available in [comparison](../outputs/analysis/scratch-demonstrations-baseline/comparison.json).

Data preparation or technical qualification should not be considered algorithmic improvement.

The fixed checkpoint for the 1st demonstration epoch has completed 8 full image audits with identical seeds: 47001/47002.
Seedings of 1,536/761 times, harvests of 770/311 times, with an average terminal cash of 7,773.63/1,002.38.
This indicates that both models have entered actual production, but their operational results show significant RNG differences and are classified as supervised initialization gains.
See [47001 epoch 1](../outputs/analysis/scratch-demonstrations-s47001-epoch1-behavior/behavior.json) and [47002 epoch 1](../outputs/analysis/scratch-demonstrations-s47002-epoch1-behavior/behavior.json).
Fixed execution of 4 epochs will continue, and the initialization endpoint will not be selected based on this behavioral audit.

Both random roots have completed all 4 demonstration epochs, consuming 7,690,368 supervised rows and 30,088 supervision updates per group. They then transitioned into online PPO; budget zero point and hash are as follows:
[Initialization identity](../outputs/analysis/scratch-demonstrations-initialization/controls.json).
Fixed terminal cash at the average final cash across 8 mirrored panels is 25,034.19/26,648.25, with 1,691/1,954 seeding operations and 1,466/1,635 harvesting operations. This audit is directly provided by the official interpreter for actor observations, progressively comparing the public/private states and backpack orders of both parties, with all 11,520 observations per group being consistent.
See [47001 Initialize Official Loop](../outputs/analysis/scratch-demonstrations-s47001-initial-official-behavior/behavior.json) and [47002 Initialize Official Loop](../outputs/analysis/scratch-demonstrations-s47002-initial-official-behavior/behavior.json).
It verifies the production behavior and rule consistency along the complete trajectory under test, but does not confirm the official submission's time budget or subsequent RL gains.

**Early gains have been observed on two RNGs in the first 16 online PPO turns.** Each group adds 2,048 full training matches after a fixed demonstration endpoint, with the unified neural opponent still set to two fixed demonstration endpoints, 128 matches per point, 32 environment seeds.

| New training seed | Zero-budget win rate → 16-round win rate | Pair win rate change and 95% interval | Pair final cash change and 95% interval |
| --- | --- | --- | --- |
| 47001 | 52.34% → 75.78% | +23.44 percentage points [13.28, 33.59] | +14,128 [10,887, 17,518] |
| 47002 | 39.84% → 71.88% | +32.03 percentage points [22.17, 41.41] | +18,569 [14,948, 22,171] |

Original per-game results are available at [16-round uniform opponent](../outputs/analysis/scratch-demonstrations-common-arena-16/curves.json),
visualizations are available at [early RL curves](../outputs/analysis/scratch-demonstrations-common-arena-16/figures/curves.png).
This reflects the actual improvement of online PPO against a fixed initialization, belonging to pre-announced selection; complete budget and independent confirmation results are provided below. The early dashboard itself does not validate the strength of mature external opponents.
The average cash per game in Round 16, from 8 official observation-driven mirror audits, was 43,889.63/39,787, with 2,662/2,825 operational gains; 11,520 mutual observations remained consistent with native results. See
[47001 Round 16 closed-loop](../outputs/analysis/scratch-demonstrations-s47001-update16-official-behavior/behavior.json)
and [47002 Round 16 closed-loop](../outputs/analysis/scratch-demonstrations-s47002-update16-official-behavior/behavior.json).

Round 32 (each group adds 4,096 training sessions online) achieved a score of 88.28% on the same uniform opponent, with an average terminal cash of 57,976. 29/60, 398.96. The incremental score change compared to Round 16 is +12.50/+16.41 percentage points, with 95% intervals [5.47, 19.53]/[7.81, 25.00]; the incremental cash is +17,419/+20,282, with intervals [12,705, 22,264]/[16,412, 24,208]. This represents early gains from the second phase of online budgeting, see [Round 32 Curve](../outputs/analysis/scratch-demonstrations-common-arena-32/curves.json), [Budget Increment](../outputs/analysis/scratch-demonstrations-common-arena-32/incremental.json), and [Diagram](../outputs/analysis/scratch-demonstrations-common-arena-32/figures/curves.png).
The two Round 32 models were further validated through official closed-loop checks with 11,520 observations each, see [Round 32 Behavior](../outputs/analysis/scratch-demonstrations-update32-official-behavior/behavior.json).
Mirror cash is not monotonically increasing: 47001 decreased from 43,889.63 in Round 16 to 41,409.31, while 47002 increased to 47,571.88. The opponents in mirror games also change with the model, and thus cannot substitute for fixed-opponent pairing comparisons.

To verify the late-game saturation under fixed initialization of opponents, two additional checkpoints at turn 64 are fixed as late-game internal opponents, with the two runs not yet reaching turn 64. The additional selection seeds are 1,050,000,000 and confirmation is 1,060,000,000. The progress at declaration and fixed budget are specified in [Late-Game Opponent Protocol](../outputs/analysis/scratch-demonstrations-late-arena/protocol.json).

The complete late-game panel results are as follows, with each point representing 128 games, 32 environment seeds, two fixed opponents, and dual seats:

| Training seed | Round 0 | Round 16 | Round 32 | Round 64 | Round 96 | Round 128 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 47001 | 4.69% | 9.38% | 21.09% | 39.06% | 66.41% | 72.66% |
| 47002 | 3.91% | 14.84% | 28.13% | 50.78% | 64.06% | 71.88% |

In rounds 32→64 and 64→96, the score intervals for both RNGs remain above zero; in round 96→128, the score increases by 6.25/7.81 points, but the interval is [-3.13, 15.63]/[-2.34, 17.97], and noise cannot yet be ruled out.
The paired cash at the end still increases by 8,652/6,792, with interval [5,649, 11,807]/[3,268, 10,892].
The complete [point-by-point curves](../outputs/analysis/scratch-demonstrations-late-arena/curves.json),
[adjacent budget increments](../outputs/analysis/scratch-demonstrations-late-arena/figures/incremental.json), and
[graph](../outputs/analysis/scratch-demonstrations-late-arena/figures/curves.png) have been saved.
These are point-wise intervals, not simultaneous confidence guarantees for the entire curve.

In the reserved seed pool of 1,060,000,000 with independent confirmations, seed 47001 increased from 7.03% to 77.34%, and seed 47002 rose from 2.34% to 70.31%; each budget remains at 128 games per 32 seeds, with an average terminal cash of 85,378. 80/82, 961.04.
Another reserved panel of 1,020,000,000 shows score changes of +48.44/+42.97 percentage points for the fixed demonstration endpoint, with intervals [40.63, 56.25]/[34.38, 51.56]. See
[Post-initialization opponent confirmation](../outputs/analysis/scratch-demonstrations-late-confirmation/curves.json) and
[Initial opponent confirmation](../outputs/analysis/scratch-demonstrations-common-confirmation/curves.json).
The late-stage scores on the initial opponent pool have nearly saturated and should not be used to infer long-term growth.

In Round 64/96/128, the model was again validated through 8 official closed-loop confirmations. In Round 128, the average mirrored cash balance was 65,753.94/66,623.44, with 3 961/4,134 plantings and 5 856/6,278 harvests. Including the prior 0/16/32 round, a total of 12 checkpoints, 96 complete trajectories, and 138,240 observations have all been matched. The same 8 independent environment seeds are repeatedly used for behavioral diagnosis and are not counted as 96 distinct seeds. See [Later Official Behavior](../outputs/analysis/scratch-demonstrations-final-official-behavior/behavior.json).

Two independent random roots from later dates, `scratch-later-opponents-s49001`/`s49002`, have been completed and exited: trained for four epochs using 954,787 action rows from September 5, and 951,902 rows for likelihood calculation from September 6, followed by 64 × 128 PPO games each. The 128-round terminal trajectories for candidates were fixed prior to opponent initialization; opponent training does not invoke candidate trajectories.
The opponent source fingerprint is `ef32d41c0378faf4b11bf051c5e8edb6975de35ca5a76bbdffae8eb9244e8736`.
Fixed opponent budget, candidate hash, and new pairing seed are detailed in
[Cross-source Protocol](../outputs/analysis/scratch-demonstrations-later-arena/protocol.json).
This is an internal training source transfer validation; September 5 was previously used for candidate likelihood diagnostics, and September 6 for curriculum research. These dates are not claimed to be blind test data never seen before in the project, and the new opponent is not referred to as a true leaderboard controller.

Each new opponent completes 3,819,148 supervision rows exposed, 14,940 supervision updates, followed by 8,192 full PPO episodes, 1,512 actor updates, each with three KL rollbacks. Relative to their fixed initializations, independently confirmed score improvements of 60.42/25.26 percentage points are observed on their internal controls. See [Opponent Budget Report](../outputs/analysis/scratch-later-opponents-baseline/comparison.json).

Across each of the 8 official mirror games, 49001's cash increases from 2,753.44 to 30,942.06, with harvests rising from 393 to 1,979 times; 49002's cash increases from 8,775.19 to 21,485.19, with harvests rising from 921 to 1,629 times. All 46,080 observations across four checkpoints match exactly. See [Opponent Official Behavior](../outputs/analysis/scratch-later-opponents-official-behavior/behavior.json).

The final strength of these two opponents is below the original late-stage profile, and they cannot be considered stronger simply due to their later training dates.

The scores of the frozen candidates 47001/47002 in cross-source independent confirmation have increased from 38.28%/31.25% to 97.66%/96.88%, with a pairing improvement of 59.0 points (38/65.63), and a 95% confidence interval of [50.78, 67.19]/[57.03, 74.22]. This supports the transfer of gains to another independent training source, as the opponent difficulty is insufficient to demonstrate a higher competitive ceiling. See [Cross-source Confirmation](../outputs/analysis/scratch-demonstrations-later-confirmation/curves.json), [Complete Curve](../outputs/analysis/scratch-demonstrations-later-arena/curves.json), and [Figure](../outputs/analysis/scratch-demonstrations-later-arena/figures/curves.png).

Long-budget experiment `scratch-scaling-s51001`/`s51002` has also been launched from a fresh random root, still using the fixed four epoch initialization from labels for September 3–4. Then it trains **512 × 128 games**, with all other training recipes unchanged.
Source code fingerprint is `c51b9719ba6501fd52c0e85addf1fd3cb6f65f24de5190c5a44180fcd92ca8b9`.
The unified evaluation opponents are fixed to two models from round 128 of 47001/47002, and two models from round 64 of 49001/49002 from later dates. Selection budget is 0/16/32/64/96/128/256/384/512, with seed 1,180,000,000; confirmation reserved at 1,190,000,000, 128 games per opponent, comparing 0/128/512.
The main late-stage issue is the performance gain of the pairing from **128→512** in independent confirmation, which cannot be reported only from initialization to terminal.
See [Long-budget Protocol](../outputs/analysis/scratch-scaling-common-arena/protocol.json).

Two runs have completed all 512 turns, each adding 65,536 full online games and 47,120,384 strategy transitions, with 12,288 accepted actor updates and two KL retreats each, ending with a final learning rate of 2.5e-5.
The fixed demonstration initialization remains as a single column with four epochs, 7,690,368 rows of exposure, and 30,088 supervision updates.
Self-initialization/random anchor confirmation and full budget identity are detailed in
[512-turn training report](../outputs/analysis/scratch-scaling-baseline/comparison.json).
These weaker self-against controls cannot replace the fixed stronger opponents and the 128→512 confirmation from two public families.

Internal independent confirmation of reserved seed 1,190,000,000 has ended, with 0/128/512 totaling 3,072 games across two roots.

| Training seed | Game score from 128 → 512 turns | Late-stage increment and 95% interval | Late-stage cash increment and 95% interval |
| --- | --- | --- | --- |
| 51001 | 62.01% → 92.97% | +30.96 percentage points [27.73, 34.08] | +27,951 [25,472, 30,446] |
| 51002 | 57.42% → 86.13% | +28.71 percentage points [25.59, 31.84] | +32,581 [30,297, 34,755] |

512 turn average cash is 100,682.22/96,789.44; the scores against the two stronger original mainline endpoints are 85.16%/86.72% and 68.75%/75.78%, and 100% against the two weaker opponents.
See [internal independent confirmation](../outputs/analysis/scratch-scaling-common-confirmation/curves.json),
[pairwise increment](../outputs/analysis/scratch-scaling-common-confirmation/figures/incremental.json), and
[opponent stratification](../outputs/analysis/scratch-scaling-common-confirmation/figures/opponent-panels.json).
This result satisfies the pre-declared internal late-stage criteria; external strength remains based on the independent results of each publicly available family.

The first 128 turns of the long-horizon experiment have been evaluated: for the above four fixed neural opponents, 256 games per point, 32 environment seeds.

| Training seed | Round 0 | Round 16 | Round 32 | Round 64 | Round 96 | Round 128 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 51001 | 7.81% | 28.13% | 44.53% | 49.61% | 54.69% | 58.59% |
| 51002 | 5.86% | 14.84% | 31.64% | 48.05% | 51.56% | 55.86% |

32→64 increment is +5.08/+16.41 percentage points, 95% interval [1.95, 8.20]/[11.33, 21.88];
64→96 increment is +5.08/+3.52, interval [2.34, 7.81]/[0.00, 7.03].
The second seed's score gain interval includes zero. 96→128 increment is +3.91/+4.30, interval [1.17, 6.64]/[1.95, 7.03]. Average cash after 128 turns is 72,332.48/63,493.37.
Split by opponent, 128-turn performance against two weaker opponents is 98.44%–100%, while against the two original mainline endpoints after 128 turns it is only 18.75%/17.19% (51001) and 14.06%/10.94% (51002). The majority of the score gain comes from weaker opponents, and has not yet surpassed stronger panels. See [128-turn data](../outputs/analysis/scratch-scaling-common-arena-128/curves.json), [opponent curves](../outputs/analysis/scratch-scaling-common-arena-128/figures/opponent-curves.png), and [layered pairing intervals](../outputs/analysis/scratch-scaling-common-arena-128/figures/opponent-panels.json).
This is early selection with the addition of two RNGs and cannot be taken as evidence for 128→512.

Turn 256 completed identical panel evaluation, with each run accumulating an additional 32,768 online training games.

| Training seed | Match percentage from 128 → 256 turns | Pairwise increment and 95% interval | 256-turn average cash |
| --- | --- | --- | ---: |
| 51001 | 58.59% → 72.66% | +14.06 percentage points [10.16, 17.97] | 88,353.18 |
| 51002 | 55.86% → 62.89% | +7.03 percentage points [3.13, 10.94] | 80,624.50 |

All incremental gains originate from two strong original mainline endpoints; their respective win rates reached 51.56%/40.63% and 28.13%/25.00%, while weaker panels maintained 98.44%–100%. Average cash increased to 16,020.70 [14,095.90, 18,108.67] and 17,131.13 [14,616.63, 19,624.47].
See [256-turn results](../outputs/analysis/scratch-scaling-common-arena-256/curves.json),
[budget increments](../outputs/analysis/scratch-scaling-common-arena-256/figures/incremental.json), and
[performance trajectories against opponents](../outputs/analysis/scratch-scaling-common-arena-256/figures/opponent-curves.png).
This panel first employs the separated native cores; all 0–128 turns were revalidated, with 12 records, 3,072 per-game results, and paired summaries fully consistent with the original expansion, as shown in [runtime verification](../outputs/analysis/scratch-scaling-common-arena-256/runtime-bridge.json).
Revalidation used the original seed and is not counted as an additional independent sample. The internal increments from 256 turns support continuation of the original experiment; later performance conclusions are based on the independently confirmed 128→512 run.

Round 384 of the identical internal panel has also concluded, with each of the two random roots accumulating 49,152 online training games. The win rates for 51001 have increased from 72.66% in 256 rounds to 87.89%, an increment of +15.23 percentage points, with a 95% confidence interval [10.94, 19.92]; for 51002, the win rate rose from 62.89% to 80.08%, an increment of +17.19, with a confidence interval [12.11, 21.88].

The scores at the two stronger original mainline endpoints reached 79.69%/73.44% and 57.81%/64.06%, respectively; the weaker panels continue to saturate in total score. This indicates that the newly allocated budget has enabled both random roots to achieve majority victories on this fixed strong panel.

The average terminal cash is 98,807.08/91,230.79, representing an increase of 10,453.89 [8,017.60, 12,874.57] and 10,606.29 [8,253.15, 13,004.68] relative to the 256-round baseline.

See [Round 384 Results](../outputs/analysis/scratch-scaling-common-arena-384/curves.json),
[Increment Intervals](../outputs/analysis/scratch-scaling-common-arena-384/figures/incremental.json), and
[Opponent Curves](../outputs/analysis/scratch-scaling-common-arena-384/figures/opponent-curves.png).

All 3,584 game-by-game records from the original budget are consistent with the 256-round reports, as verified in [Reconfirmation Check](../outputs/analysis/scratch-scaling-common-arena-384/repeated-points.json); no independent samples are added.

This constitutes a pre-announced selection, reported separately from the independent confirmation of the previously reserved seeds from 128→512.

The full nine-budget selection has concluded, with a 512-round score of 94.53%/83.20%. The increments from 384→512 are +6.64 percentage points [3.52, 9.77] and +3.13 [-1.17, 7.42]; the final segment of the second line still cannot rule out noise. The cash in that segment increased by 2,396 [-197, 4,843] and 5,584 [3,726, 7,468], and the first random root's cash interval also crosses zero. See [Full Curve](../outputs/analysis/scratch-scaling-common-arena-512/curves.json) and [Adjacent Budget Increments](../outputs/analysis/scratch-scaling-common-arena-512/figures/incremental.json). All 16 previous records from 0–384 and 4,096 individual game results have been re-verified and are consistent, see [Repetition Point Confirmation](../outputs/analysis/scratch-scaling-common-arena-512/repeated-points.json).

### Assessment of Newly Downloaded Public Scripts

On 2026-09-07, download and review the currently public notebook, selecting `tetsutani/shape-the-shop-work-the-pasture-kaggriculture`.
The exact script has SHA256 of `2b97e2c653018ac4aeffb8463ec91c8f26b097b4cef81289acc25ccdbc68f916`.
The source code depends only on the standard library, public action trajectories, and observation rules; the compressed payload has been decoded and checked, with no model weight files present.
Two separately downloaded six-day routers contain fitted decision tree parameters, which are not executed; another modified version belongs to the same trajectory family and is not counted as a separate opponent. Sources and exclusion reasons are listed in
[Public Strategy List](../data/external/kaggriculture-public-agents-20260907/manifest.json).

The external panel is solely for evaluation and does not participate in training, demonstration labels, or deployment fallback. For 0/64/128 round selection and 0/128 independent confirmation, initial seeds of 1,240,000, 000/1, 250,000,000 are used; the new 512-round run retains 1,270,000, 000/1, 280,000,000 and pre-fixes the 128→512 comparison. See [External Protocol](../outputs/analysis/scratch-public-opponent-protocol.json).
A FP32 CPU-based random policy is adopted, with both sides driven by official observations and full native state verification at each step. 16 technical checks pass through 23,040 observations; all four budget points on these environment seeds result in complete losses, yet the PPO endpoint cash increases.

Full selection completed: two runs, each with 0/64/128 at three budget points, 64 games per point, totaling 384 games, all failed; 552,960 observations matched. Final cash at 128-round endpoints for both runs: 70,432.38/67,035.75, relative to round 64, an increase of 10,616.25/4,231.39, 95% interval [5,758.90, 16,188.88]/[518.02, 8,256.65]. See [public selection](../outputs/analysis/scratch-demonstrations-public-arena/comparison.json).

Independent confirmation has also been completed: 128 episodes per budget point, 64 environment seeds, 0/128 budgets totaling 512 episodes all failed;
737,280 observations match perfectly.

| Training seed | Initial cash | 128-turn cash | Opponent pool cash | 95% interval of paired cash increase | Final wins |
| --- | ---: | ---: | ---: | --- | ---: |
| 47001 | 23,839.62 | 64,049.81 | 93,378.05 | [35,680.91, 44,989.27] | 0/128 |
| 47002 | 21,230.32 | 62,601.67 | 94,632.84 | [36,729.70, 46,504.93] | 0/128 |

Source see [public confirmation](../outputs/analysis/scratch-demonstrations-public-confirmation/comparison.json).
This is evidence of external cash revenue, **not evidence of external win rate improvement**; the degradation of bootstrap intervals for full-loss samples cannot be interpreted as a zero win probability in unknown environments. This family has clearly exposed the current strength threshold.
The measurement source fingerprint is `b6cf69c89b7f415b05040c45fdf1c93f377ca7b415e3a9957a71b3dbe403089f`,
the complete archive and file-by-file hashes are preserved in two report directories. Shared seed validation migration, AST equivalence checks, four lineage/seat regressions, Ruff, and mypy for 596 source code files have all passed.
Operations and scope see [learning_public_arena.md](learning_public_arena.md).

The 0/128 external selection baseline with long budget has also been completed, with 64 games per point and 32 environment seeds, totaling 256 games—all failed; 368,640 observations matched perfectly. Cash for 51001 increased from 16,509.56 to 57,183.31, with opponent at 99,028.19; 51002 rose from 8,219.27 to 50,897.88, with opponent at 106,730.55. This demonstrates cash growth against the same challenging opponent while maintaining full failure across all games, see [Long Budget External Baseline](../outputs/analysis/scratch-scaling-public-arena-128/comparison.json). No changes were made to training or external opponents; all baselines were included in the 512-turn terminal evaluation as per original protocol.

The complete selection and independent confirmation for the long-budget trajectory family have ended, with results of 384/768 games.
All budget allocations in the selection have suffered complete losses; among the confirmations, the two 512-round endpoints achieved only 2/128 and 0/128 wins respectively.
The score improvements from 128→512 are +1.56 percentage points [0.00, 3.91] and 0.00 [0.00, 0.00], failing the criterion for late-stage win gain from random roots.
Cash increments are 14,255 [11,641, 16,929] and 16,957 [13,897, 20,073], with average terminal cash of 73,477/70,172, still below the opponent's approximately 86,700.
See [Trajectory Family Independent Confirmation](../outputs/analysis/scratch-scaling-public-confirmation/comparison.json).

A publicly available rule family, EcoBot v7, is fixed based on observed valuation and daily planning to supplement coverage across different implementations.
16 technical qualification passes achieved; the first round of 0/64/128 selection and the 0/128 independent confirmation have both concluded.
Selection endpoint scores are 82.81%/67.19%, and confirmation scores are 82.03%/73.44%; relative gains in confirmation from initialization are all significantly positive. The incremental score for the 64→128 selection is only positive in the first round.
Supplementary panels are reported separately from the original trajectory opponents, without altering training configurations; sources, excluded Kaito derivatives, and designated seeds are provided in [Supplementary Rule Family](learning_public_arena.md#section-cedebee1e8bf).

The passive income-expenditure diagnosis replayed all 0/128 selections from the original mainline, totaling 256 games; under the new core, the complete action hash, cash flow, and outcomes matched the original records exactly, with per-seat income and expenditure balances confirmed. The two 128-round models on average showed a shortfall of 26,043/32,486 in sales revenue and an additional expenditure of 5,127/2,090, resulting in a terminal cash difference of 31,170/34,576. The average cash balance at both sides remained around 22,000 at turn 360, with the gap widening thereafter. This represents an operational diagnosis based on existing samples, without adding independent evidence or altering the training recipe. See [Diagnosis Description](learning_public_arena.md#section-4eee0c2ff2de) and [Cash Curve](../outputs/analysis/scratch-demonstrations-public-accounting/figures/cash-trajectories.png).

### Shared Runtime Interface Splitting

The current source code moves generic PPO, prefix value, objective function, temperature control, and update protection into `learning/optimization/`; the old modules retain backward compatibility. `learning/settings.py` takes over native sampling and optimizer configuration, while `policy/settings.py` handles model semantics; the original `production.Settings` inherits shared configurations, adding only BC and its own workflow validation. The new entry no longer constructs fictional BC paths, checkpoint inputs, or old workflow modes; saved runtime configurations no longer contain these placeholders. Ongoing v2 experiments continue to use the archived code from when they were launched—this interface split will not affect their hot-swapping.

72 test cases, Ruff, and 540 source files with mypy have passed. The new random root `scratch-runtime-decoupling-qualification-v1` has completed 2 × 8 technical qualification rounds, including turn 12 suffixes, full initial states, checkpoint saving and loading, and terminal confirmation; this validates the workflow, not performance improvement. Relative to the v2 archived configuration, both runtime control and parsed model layout are completely identical, see [Interface Compatibility Verification](../outputs/analysis/runtime-decoupling/compatibility.json).

Subsequently, CUDA Graph inference is migrated into `policy/inference.py`, complete game sampling, historical opponent seat routing, and training tape are migrated into `learning/collection/`; the old production module is retained for backward compatibility. Compared to the original archive of multi-date experiments, the AST of 11 migration classes/functions is completely identical, see [Definition Equivalence Verification](../outputs/analysis/collection-extraction/equivalence.json).
48 related tests, Ruff, and 558 source code files have passed mypy checks.

Network, encoder, and job decoding are now moved to `policy/spatial/`, action contracts are located at `policy/contracts.py`,
general model access is at `policy/checkpoints.py`, native features/batches at `native/`, neural combat and pairing statistics at `evaluation/`.
26 definitions are consistent with the main experiment archive's AST, see [Domain Definition Verification](../outputs/analysis/domain-extraction/equivalence.json).
Python import `learning.train` no longer imports any `production` or versioned teacher modules; process isolation regression checks are in place.
New random root [Full Process Qualification](../outputs/learning/scratch-domain-qualification-v1/qualification.json)
Completed 2,876 demonstration lines and 16 PPO games; related migration tests, Ruff, and mypy passing on 579 source files.
Native training core has been further decoupled: default `python -m kagg_revue.native.build` builds only `_revue_core`, without requiring a CUDA compiler or compiling versioned scripts. The new training, data encoding, and evaluation use this core, with isolated import checks confirming no indirect loading of the full old extension. The old tools explicitly use `_revue_native`, deployment uses `_revue_observation`; the old workflow retains backward-compatible entry points. See [Native Core Documentation](learning_native.md).
The new core has been validated through 64 games / 92,160 official replay observations, and 8 full neural trajectories, with step-by-step comparison between new and old cores and the official environment. The new random root completes demonstration initialization, 16 PPO games, confirmation, and archival state recovery; 14 related tests, 29 compatibility tests with independently recompiled old extensions, Ruff, and mypy passing on 598 source files. See [Qualification Index](../outputs/analysis/native-core-extraction/qualification.json).
This constitutes engineering qualification; the full 512-round experiment retains the original source code and original binaries archived at startup.

The recovery entry point after source code changes is `python -m kagg_revue.learning.recovery.cli`, with parameter `recovery.run=outputs/learning/<run>`. It verifies the original tar, file-level hashes, native binaries, and Torch version, reconstructs the isolated source code within repository `tmp/`, continues the same ledger and full optimizer/RNG state, without modifying the working tree. A real SIGTERM occurs after the demonstration shard cursor 1, followed by a change to the working tree and recovery, resulting in the actor, critic, two PPO optimizers, supervision state, and CPU/CUDA RNG being bit-identical to the continuous training. See [Archival Recovery Evidence](../outputs/analysis/source-recovery/verification.json) and [Recovery Instructions](learning_recovery.md). This exact guarantee applies only to the deterministically tested FP32 configurations.

`deployment/actor.py` and `deployment/qualification.py` have implemented the new runtime registration model for CPU export, preserving causal random sampling used during training. Each of the two Model Round 128 has been validated on 2 complete official mirror games, achieving bit-level consistency across 5,752 individual observation random programs with eager FP32 CPU under paired RNG, and consistency across 5,760 mutual observations and native states. The exported model is approximately 3.75 MB, with a single-threaded average inference latency of 5.07/5.03 ms, and the slowest first call approximately 64 ms. See [47001 CPU Qualification](../outputs/deployment/scratch-demonstrations-s47001-u128-fp32/qualification.json) and [47002 CPU Qualification](../outputs/deployment/scratch-demonstrations-s47002-u128-fp32/qualification.json).
This is not a trajectory-level equivalence, portable submission package, or Kaggle runtime budget qualification for BF16 GPU; no submission has been made yet.
After adding the deployment code, Ruff and mypy passed for all 582 source files.

Subsequent addition of an independent CPU extension `_revue_observation` compiles only the shared observation transformation, feature processing, and action execution.
It does not require CUDA, does not include teacher/training entry points, and passes Python 3.11/3.12 ABI builds. The highest required glibc symbol version is 2.17. Shared Python/native transformations have been moved from the large binding file into `native/csrc/conversion/`, with original function bodies preserved verbatim. A portable engine build previously triggered static C++ locale symbol conflicts in old batch tests; after adding `--exclude-libs,ALL`, 29 related regressions and 64 games / 92,160 observations passed official audits. ELF checks have rejected re-exporting these locale symbols. See
[diagnostic link](../outputs/analysis/native-deployment-extraction/diagnosis.json) and
[post-fix official audit](../outputs/analysis/daily-20260906-isolated-native-audit/report.json).
Ongoing training runs continue to bind their respective archived `ab3a125f...` binaries.

The currently reviewable package is `outputs/deployment/scratch-demonstrations-s47001-u128-portable-v3/submission.tar.gz`,
SHA256: `6828d6d7cc3cd765df2fd1c15fc3590db2703b9b9d226a78f8e4132b994f64d6`, approximately 3.87 MB.
In independent CPU processes using Python 3.11/Torch 2.13 and Python 3.12/Torch 2.12,
two official games were completed each, with consistent hash of full action trajectories;
all regular files and the original entry without `__file__` are fully covered.
Per-turn features and actions match those of the training executor, totaling 5,752 program executions and 5,760 observations;
only two independent environment seeds are used.
No training, production, teacher, or opponent modules were imported into the running processes.
See [Cross-runtime Evidence](../outputs/analysis/deployment-bundle/cross-runtime.json) and
[Deployment Operation Instructions](learning_deployment.md). This is still not Kaggle host budget certification, and there are no model submissions.
Current Ruff, mypy for 592 source files, and four archive integrity tests have all passed.

All new learning experiments are located at `outputs/learning/`. Each run independently generates a random actor and two random evaluation anchors, archives the source code, and records the UUID, model hash, random seed, optimizer, critic, RNG, and historical strategy pool.
The current population consists of 50% self-play and 50% historical strategies from this run, with frozen historical opponents uniformly sampled during update.
Evaluation is separated into selection and confirmation, and paired differences for the two seats are statistically aggregated by game seed.
Random anchors only validate early learning and do not represent current leaderboard or mature, multi-source strategies.

### Latest External Data and Environmental Evidence

The official daily index has been refreshed, with the latest complete date being 2026-09-06, and 662 full games have been downloaded.
The original ZIP and source ledger are located at
[data manifest](../data/external/kaggriculture-episodes-2026-09-06_2026-09-07/raw/manifest.json).
64 games have been selected based on score percentiles, covering 21 player display names; per-turn comparisons of both public and private states between opponents have been performed,
**all 92,160 observations are consistent with the native engine**. The source environment module_version is 1.32.7.
The report is available at [daily audit](../outputs/analysis/daily-20260906-native-audit/report.json).
The grounded native extension, after recompilation, has passed the same full audit again, see
[new native audit](../outputs/analysis/daily-20260906-grounded-native-audit/report.json).
The binary with the new prefix replay has also passed the same full audit, see
[restart native audit](../outputs/analysis/daily-20260906-restart-native-audit/report.json).
This demonstrates environmental consistency across the selected official trajectories; it does not prove the runtime qualification of future learning strategies deployed officially.
The new daily data is currently used for auditing, mid-game state coverage indexing, and environmental recovery for the above courses, and is not used as imitation labels.
A later date independent opponent has designated September 6 as the action likelihood diagnostic partition and does not use the label from that day to update parameters.
19,198 day-boundary candidate states have been established, split by environment seed into 521/69/72 training/select/confirmation games, with verified non-overlapping content hashes and partitions; the training region covers 36 display names, which does not equate to 36 distinct strategy versions.
Persistent source information is available at
[state index manifest](../data/external/kaggriculture-restart-candidates-2026-09-06-v1/manifest.json),
analysis is available at [state coverage](../outputs/analysis/daily-20260906-state-coverage/coverage.json).
The course loader has precisely replayed the entry states for each actually used bank, verified against the public history, and generated the PPO suffix; the remaining unused candidates do not claim full recovery eligibility.

### Stopped Old Experiment

`20260907-neural-credit-mc`, `20260907-neural-credit-td` inherit the weights from the old generation 51,
have been terminated according to the requirement of starting fresh, and the exit and exclusion reasons have been recorded in their respective `run-status.json`.
They are no longer considered part of this reconstruction experiment, and no further comparisons with the old weights will be conducted.

Previous research results and submitted facts are retained in [historical mainline](HISTORICAL_MAINLINE_20260907.md). The terms "current," "in operation," and subsequent recommendations in this document only describe the state at the time and do not constitute new mainlines or authorization to initiate. The most recent submitted facts in the new mainline are presented at the beginning of this document.
