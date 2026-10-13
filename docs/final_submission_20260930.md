# Final Submission Preparation (September 30 17:00–23:00 UTC)

<a id="section-570f7bf73353"></a>

## Submitted: s101701 U200 with terminal liquidation (56720178)

The user explicitly requested submission of their preferred option after final selection. Kaggle received **56720178** on **2026-09-30 22:25:55.547 UTC**: s101701 U200, FP32, T=0, with terminal liquidation patch.
The package is `outputs/deployment/s101701-u0200-20260930-t0-liquidation/submission.tar.gz`,
SHA256 `c1e2ff723ed680c10fe3100947558f0220d906d9bb801232539d72235dd7db7b`,
93,714,448 bytes. Confirm the complete package hash, package file hashes, checkpoint, inference configuration, and official qualification report prior to submission.

Use [Independent Submission Configuration](../configs/kaggle_submission_s101701_u0200_liquidation_20260930.yaml)
Call `kagg_revue.deployment.submission`, invoking the submission interface only once; the list has increased from 86 to 87 entries.
The new record's ID, description, and size all match. Confirmation received at 22:26 UTC; no processing completion status or score has been returned yet.
See [Submission Acknowledgment](../outputs/analysis/s101701-u0200-20260930-t0-liquidation/submission-receipt.json).
Alternative s101701 U250 was not submitted; the "not submitted" below refers to the preparation phase prior to submission.

## Objectives and Constraints

User instructed at 16:56 UTC (UTC+8 00:56): concentrate remaining resources on the MMPQ line; prepare 1–2 final submission packages before 07:00 UTC+8 (23:00 UTC); **do not submit, decision to be made by user**; final selection does not have to come from the MMPQ BC line.
At 17:00 UTC, the two submissions in the scoring were 56709373 (s101102 U200, FP32, T=0) and 56689315 (s100901 U480, FP32, T=0).

## Event

- Around 16:42 and 17:25 UTC, the container restarted twice. 6 replay collectors, the Drive export service, and all training processes were terminated.
  DSM's two lines had already been normally stopped prior to the restarts: s101401 stopped at U219, in state `stopped`; both workflows were in state `cancelled`. After each restart, the collectors and export services were restarted according to their respective documentation.
- The second restart interrupted the first opponent-guided phase of two new RL workflows, which had not yet begun training. Therefore, the guided phases were rerun in sequence:
  When both guides export inference outputs in parallel, they compete for CPU resources, reducing the speed from approximately 140 per minute to 15–30 per minute.

## Kaggle Real-World Performance (17:00 UTC Read-Only)

- 56709373: 47 games, 46 wins, 1 loss, only lost to DSM. Score 2750.1, still rising; opponents are mostly teams outside the top of the leaderboard.
- 56689315: 166 games, 117 wins, 49 losses, score 2886.8.
  - Against teams with 2900+ points: 7 wins, 28 losses — DSM 0–9, DECEM 1–7, Tufa 6–9, MMPQ 0–3.
  - Against teams with 2700–2900 points: 43 wins, 17 losses.

## Two MMPQ Lines RL

| run | starting point | actor learning rate | device |
|---|---|---|---|
| s101701 | s101102 U200 (actor, critic, KL anchor) | warmup 50 then constant 4e-6 | cuda:0 |
| s101702 | v4 P clone of s101001 epoch 9; critic taken from s100901 U756 | warmup 200 then constant 5e-6 (U200 prior identical to s101102) | cuda:1 |

**Formula.** The rest is the same as s101102:
- Pure terminal WDL, KL 0.3, 64 games/update;
- 50/50 self-play and unified PFSP;
- mastery 64/0.95/0.05, inheritance discount 0.5.

Design Rationale: s101102 achieves its optimal performance at U200 when the learning rate rises to 5e-6 during warmup; upon increasing to 7.5e-6, U300 and U400 fail to defeat U200 in direct matches. s101701 continues searching with a lower constant learning rate near U200; s101702 is a second seed from the same starting point and recipe, with the learning rate stabilizing at the level observed when U200 was reached.

**Opponent Pool.** A total of 509 external opponents:
- 485 external opponents from s101102;
- s101102's own 10 snapshots (initial, U50…U433, including U200, to allow learners to continuously face the current submission);
- 12 DSM clones from September 30;
- s101401 U100/U200.

Evidence from unengaged opponents is inherited from the s101102 ledger (discount 0.5). Profiles:
[`learning_mmpq_rl_u200_cont_1gpu_20260930`](../configs/learning_mmpq_rl_u200_cont_1gpu_20260930.yaml),
[`learning_mmpq_clone_kl_ppo50_1gpu_r2_20260930`](../configs/learning_mmpq_clone_kl_ppo50_1gpu_r2_20260930.yaml).

**Fix implementation.** The RL checkpoint of s101102 and s101401 explicitly includes `joint_units: False` in the layout field, while the current `layout_record` omits this field, causing the critic migration's strict dictionary comparison to reject U200. `learning/pretraining/critic.py` is now changed to perform semantic comparison based on `layout_from_payload`, aligning with the actor migration and opponent import practices.

**Operating Mode.** A direct start (non-workflow) run records the fingerprint of the entire `src/` and `configs/` at startup. Any subsequent configuration changes will result in a resume being rejected. Therefore, both run continuations start from frozen copies of `tmp/final-20260930/impl-a` and `tmp/final-20260930/impl-b`, whose fingerprints have been individually confirmed and found to match their respective current states.

**Speed.** During evaluation when training is performed on the same GPU, the update time increases from 43 seconds to 90–130 seconds,
thus, no panel is run during training, and evaluation is performed only in the final window.

## Final Evaluation Design

- Seeds: New 9950000000 / 99500001, 256 shared seeds, both slots played, 512 games per opponent; T=0, bf16.
- Baseline: s101102 U200 vs s100901 U480, v4 P clone, DSM v5 clone s101501
  ([Configuration](../configs/evaluation_final_baseline_20260930.yaml)).
- Candidates: Same opponents and same seeds as baseline, paired seed-by-seed; additionally, 512 direct games against U200
  ([Configuration](../configs/evaluation_final_candidates_20260930.yaml), pairing statistics and summaries see
  `outputs/analysis/final-candidates-20260930/paired.py`, `summary.txt`).
- Baseline results (completed at 18:55, 1536 games): overall 61.6% (946-590), average cash difference +$753;
  65.2% against DSM v5 clone, 59.2% against v4 P clone, 60.4% against U480.
- U100 early screening (19:16, 512 direct games each against U200): s101701 50.3% (44.7–55.8), s101702 51.6% (46.1–57.0),
  both tied with U200. s101702 matched U200 on U100, faster than the original s101102's trajectory
  (s101102's own U100 performance was clearly weaker than its U200).
- U200 full panel (20:48, each candidate plays 512 direct games against U200 plus 1536 games paired against baseline seed-by-seed):

  | Candidate | vs U200 | Pair Difference (95% CI) | DSM v5 | v4 P | U480 |
  |----------|--------|-------------------------|--------|------|------|
  | s101701 U200 | 55.1% (49.4–60.7) | +4.7pp (+0.7 to +8.9) | +7.0 | +3.5 | +3.5 |
  | s101702 U200 | 56.4% (51.0–61.9) | +1.0pp (−3.5 to +5.5) | +7.8 | −5.1 | +0.2 |

  s101701 performs better than U200 across all opponents; s101702 has a significant advantage when directly facing U200, but performs worse against v4 P clones.
- Kaggle validation (read-only at 19:00): U200 has a record of 68-9, with recent losses primarily coming from MMPQ (2 games, deficits of $3.8k/$4.5k) and Tufa Labs (2 games, deficits of $3.3k/$3.1k). The local v4 P clone is notably weaker than the online MMPQ; local panel performance overestimates our win rate against top-tier teams.
- Real match records by opponent tier (read-only at 19:25): Against the top 5 opponents, U200: 0-9, U480: 15-37 (CDE 8-5, Tufa 6-10); our total submissions against DSM: 1-38, against MMPQ: 0-23. Against opponents ranked 6–20, U200: 20-4, U480: 33-9; against opponents ranked below 20, U200: 54-0, U480: 70-7. U200 is most stable in mid-to-low tiers, consistent with the local observation that "U200 is stronger than U480".
- Submission deadline: 23:59 UTC on 2026-09-30. Up to 5 submissions per day. Team score equals the highest score among active submissions (19:00 score is 2878.8, corresponding to U480; earlier 56644629 shows 2888.0 but is not counted).

<a id="section-50f02ac40138"></a>

## Final Conclusion (22:15 UTC, not submitted)

21:41 UTC Stop two training jobs as per user request; both GPUs are now fully allocated to evaluation. s101701 stops at U292 (U295 is saved upon shutdown), s101702 stops at U292 (U293 is saved); the training outputs are retained and can be resumed from frozen checkpoints. Candidates run the full panel on the baseline seed; additionally, on a non-overlapping new seed (9960000000), 512 games are played against U200. As requested by the user, s99001 U588 is added (online 56644629 running at T=1); due to its older network architecture, it cannot share panel workers with other candidates and thus runs on its own dedicated panel.

"Four-opponent average" is the average of the direct match score against U200 plus the baseline score plus pairing difference from three panel opponents:

| Candidate (T=0) | vs. U200 (1024 games) | Pairing difference vs. baseline (1536 games) | Four-opponent average |
|---|---|---|---|
| **s101701 U200** | 53.6% (49.7–57.4) | **+4.7pp (+0.7 to +8.8)** | **63.1%** |
| s101701 U250 | 56.2% (52.2–60.1) | +2.3pp (−2.1 to +6.8) | 62.0% |
| s101702 U200 | 55.0% (51.1–59.1) | +1.0pp (−3.6 to +5.5) | 60.7% |
| s101701 U292 | 55.1% (51.2–59.2) | −0.1pp (−4.2 to +4.2) | 59.9% |
| s101702 U292 | 49.6% (45.7–53.4) | −1.0pp (−5.5 to +3.5) | 57.9% |
| s99001 U588 | 20.9% (17.6–24.4) | −37.0pp (−41.4 to −32.5) | 23.7% |
| s99001 U588, T=1 | 18.4% (14.8–22.3, 512 games) | — | — |
| s101102 U200 (reference) | 50% | 0 | 58.7% |

- The performance against U200 fluctuates significantly depending on the seed set: s101701 U292 scores 48.0% and 62.1% on the two seed groups, while U250 scores 59.8% and 52.7%. Therefore, only the merged 1024 games should be used.
- s99001 U588 is significantly weaker than U200 regardless of T=0 or T=1. Its 2888 score on the line is from a previously disabled and frozen record and does not reflect its current strength.
- No further improvement is observed in the late training phase: both U292 lines perform worse than their respective U200/U250 counterparts, consistent with s101102's plateau observed after playing against U200.

**Recommendations (all FP32, T=0, with terminal liquidation, officially budget-certified, not submitted):**

1. **Preferred: s101701 U200.** `outputs/deployment/s101701-u0200-20260930-t0-liquidation/submission.tar.gz`,
   sha256 `c1e2ff723ed680c10fe3100947558f0220d906d9bb801232539d72235dd7db7b`, checkpoint `cbb7b9e3…`, 93.7 MB.
   It is the only candidate that improves across all three panel opponents with a significantly positive pairing difference, achieving +3.5pp against MMPQ agent v4 P clone;
   it has the highest average performance across four opponents and does not lose when directly matched against U200. Recommendation description:
   `MMPQ line U200-continuation RL v5b s101701 U200; FP32 T=0; final-turn liquidation; ckpt cbb7b9e3; pkg c1e2ff72`.

2. **Alternate: s101701 U250.** `outputs/deployment/s101701-u0250-20260930-t0-liquidation/submission.tar.gz`,
   sha256 `c278b324677210baca9dbc79ebe193426c1c13eae16894228f20aee1e65ea165`, checkpoint `f0b34daa…`.
   It performs strongest when directly matched against U200, but loses by −1.8pp against v4 P clone.

**Submission Method.** It is recommended to submit only the preferred option. If "the last two submissions scoring" applies, it will replace the earlier U480; the active combination becomes s101701 U200 paired with s101102 U200 featuring online performance records. To replace both, submit the alternative option as well, which will simultaneously replace the U200. New submissions start from the initial score, with only about 1 hour of gameplay remaining before the deadline; whether gameplay continues after the deadline is subject to the competition rules.
The local panel is not representative of top teams such as MMPQ and DSM (online, our combined record against these two teams is 1-61).
Additionally, constructed but not recommended packages: s101701 U292 (`dafe6268…`), s101102 U200 with terminal liquidation (`f6e997db…`).

<a id="section-3d01b11d39c4"></a>

## Expanded Evaluation After Submission (22:29–22:58 UTC)

User submitted the preferred package at 22:25:55 UTC, receiving 56720178 (`c1e2ff72…`). Then, evaluations were expanded as requested and s100901 was added.

The new seed is 9970000000, which does not overlap with the previous two groups; each candidate plays 256 games against each of the 7 opponents, with dual seats, T=0.

The 7 opponents are: two online anchor points s101102 U200 and s100901 U480, v4 P MMPQ clone, v5 DSM clone, and clones of the Tufa Labs, DECEM, and Vadim teams.
([Configuration](../configs/evaluation_final_expanded_20260930.yaml); s100901 has different network configuration,
[separate panel](../configs/evaluation_final_expanded_s100901_20260930.yaml), with the same seed and opponents, enabling one-to-one pairing).
Summary is available in `outputs/analysis/final-candidates-20260930/expanded-summary.txt` (script `expanded.py`).

| Candidate | U200 | U480 | MMPQ | DSM | Tufa | DECEM | Vadim | 5 Clone Average | Difference with U200 |
|----------|------|------|------|-----|------|-------|-------|------------------|------------------------|
| s101102 U200 | — | 60.2 | 55.5 | 66.0 | 78.1 | 77.7 | **77.7** | 71.0 | 0 |
| s101701 U200 (submitted) | 48.4 | **64.5** | 54.7 | 69.9 | 69.9 | 73.0 | 75.4 | 68.6 | −1.3 (−5.1 to +2.6) |
| s101701 U250 | **55.1** | 63.7 | **60.2** | **78.5** | 70.3 | 74.6 | 73.0 | **71.3** | +0.8 (−2.9 to +4.4) |
| s101702 U200 | 53.1 | 55.5 | 58.6 | 64.8 | 67.2 | 71.5 | 71.5 | 66.7 | −4.4 (−8.3 to −0.3) |
| s100901 U480 | 39.8 | — | 46.9 | 41.4 | 77.0 | 82.0 | 71.1 | 63.7 | −7.3 (−12.5 to −2.2) |
| s100901 U756 | 32.8 | 59.0 | 42.6 | 39.5 | **80.9** | **83.6** | 76.6 | 64.6 | −5.5 (−10.8 to −0.2) |

Compare the merged three seed groups with s101102 U200:

| Candidate | Direct Match (1280 games) | Pair Difference (3072 games) |
|----------|--------------------------|-----------------------------|
| s101701 U200 | 52.6% (49.1–56.1) | +2.7pp (−0.3 to +5.7) |
| s101701 U250 | 56.0% (52.3–59.5) | +1.8pp (−1.3 to +5.2) |
| s101702 U200 | 54.6% (50.9–58.2) | −0.8pp (−4.0 to +2.3) |

- The new seed s101701 U200 ties with s101102 U200, and the pairing difference after merging is no longer significant. Its improvement is concentrated on U480 and DSM clones;
  however, against the three team clones, it is actually 2–8 percentage points weaker.
- s101701 U250 is the strongest overall locally, being the only candidate that directly outperforms U200 in head-to-head matches, though the pairing difference remains insignificant.
- Both s100901 versions are clearly weaker on U200, MMPQ, and DSM clones, but it is strongest against Tufa and DECEM clones.
  This aligns with its U480's online performance: it has a 15-37 record against the top 5, while U200 has 0-9. U756 ties with U480 (−0.4pp).

**Online status (read-only at 23:00 UTC).** After submitting 56720178, the team score on the leaderboard immediately changed from U480's score to s101102 U200's score.
U480 remained at 2846.1 without further change, confirming "only the highest score from the last two submissions is taken for the team score."
56720178 started at 600 and rose to 951.9 within 35 minutes; s101102 U200 scored 2822.3 and ranked 13th.

**Corrected Recommendation (23:11 UTC): Resubmit the original package for U480, replace s101102 U200.**
User notes that the final leaderboard will continue to run for another 15 days after the deadline,
so current scores have no value and each submission will converge to the true performance level; team scores take the higher of the two, thus both submissions should be strong and distinct.
- The two current submissions being scored are nearly identical: s101701 U200 is simply s101102 U200 retrained for 100 additional steps, and they are equal on the local panel.
- Online evidence supports U480: during the 8.5-hour overlap, U480's score was consistently higher (2846.6 vs. 2831.1 at 22:17), with a 15-37 record against the top 5 teams, while U200 achieved 0-9.
  The local panel reaches the opposite conclusion, but local clones fail to predict outcomes against top teams: U480 performs weakest against MMPQ and DSM in local clones, yet performs best against the top 5 teams online.
- U480 originates from the DSM line, and has a different style from s101701 U200 from the MMPQ line, offering better complementarity.
- s101701 U250 is the strongest locally, but it comes from the same training run as s101701 U200, differing by only 50 update steps, thus offering poor complementarity.
- s100901 U756 with terminal liquidation (`8bf76b3b…`), performing equally with U480 locally, but lacks online records and is only considered as a backup.

After submitting `outputs/deployment/s100901-u0480-20260929-t0-once/submission.tar.gz` (sha256 `809acef5…`, byte-for-byte identical to 56689315, checkpoint `49bee543`), the scoring submission becomes U480 and 56720178.
Additional, unsubmitted: s101702 U200 with terminal liquidation (`72e18748…`), s100901 U756 with terminal liquidation (`8bf76b3b…`).

<a id="section-17562d275f76"></a>

## User's final submission (23:15–23:29 UTC)

The user decides to submit two packages sequentially, with each package uploaded once by the [commit module](../src/kagg_revue/deployment/submission.py) of this repository.
The submission records and acknowledgments are both located under the corresponding `outputs/analysis/<tag>/`:

| Order | ID | Upload Completed (UTC) | Package | sha256 | Kaggle Validation |
|---|---|---|---|---|---|
| 1 | 56721201 | 23:17:39 | s100901 U756 Add Clearance ([$Configuration](../configs/kaggle_submission_s100901_u0756_liquidation_20260930.yaml)) | `8bf76b3b…` | 23:25:40 COMPLETE, 600 starting point |
| 2 | 56721459 | 23:28:25 | s101701 U250 Add Clearance ([$Configuration](../configs/kaggle_submission_s101701_u0250_liquidation_20260930.yaml)) | `c278b324…` | 23:33:50 COMPLETE, 600 starting point |

With "only counting the most recent two submissions," scoring submissions are now 56721459 and 56721201: MMPQ line's U250 and DSM line's U756, both FP32, T=0, with terminal liquidation. 56720178 (s101701 U200) and 56709373 (s101102 U200) are no longer scored. After cutoff, the final leaderboard will continue for 15 more days.

## Terminal Liquidation Patch (18:10–19:00 UTC)

Can selling all sellable items before the game ends increase the win rate?

**Rule basis.** At terminal settlement, only cash is compared. The last processed turn is step 718 (`episodeSteps - 2`);
Within the same step, unit actions are executed first, followed by market matching, so within the same turn, goods placed in the shed by `DROP` can still be sold.
`SELL` only sells goods from the shed, matching by piece, and orders automatically stop when all goods are sold, with a minimum price of $1; thus, selling any additional item will not reduce cash.

**Implementation.** [`liquidation.py`](../src/kagg_revue/deployment/liquidation.py) takes effect only in the final turn:
Units standing in the entrance grid of the shed, carrying products, are changed to `DROP`; all market orders are replaced with `SELL ×1000` per product, sorted by "quantity × current price" in descending order, and executed before the opponent lowers the same price. In all other turns, the original state is restored.
During packaging, `deployment.liquidation=true` writes an entry with exception rollback, places it into the module, and declares `final_turn_liquidation` in `agent_profile.json`; during authentication of `budget` and `check`, the same rewrite is applied to native actions before step-by-step comparison.
Default is disabled; existing packages and processes are unaffected.

**Real Kaggle game logs.** Downloaded exclusively the full 233 games (`data/external/kaggriculture-own-replays-20260930/`, excluding self-vs-self games), and calculated the realization value of remaining inventory at the terminal market price per game:

| Submission | Game count (wins-losses) | Remaining inventory | Average/max leftover | With carried inventory | Revivable losses |
|-----------|-------------------------|---------------------|----------------------|------------------------|------------------|
| 56709373 (U200) | 64 (61-3) | 55 | $268 / $1271 | $298 | 0 / 3 (differences: 337, 1597, 2434) |
| 56689315 (U480) | 167 (117-50) | 89 | $78 / $1686 | $132 | 1 / 50 (difference: $11) |

By the way, I checked the other expenses on the last day: about 10 `HIRE` per game, totaling no more than $88 for the day according to the Fibonacci pricing. The hired laborers were working the entire day, so it's not a waste.

**Paired games in the official environment.** The original and patched U200 packages each played against the certified U480 package, using 8 seeds and both seats (scripts, per-game logs, and reports are in `outputs/analysis/liquidation-duel-20260930/`). Across all 16 pairs, action hashes were identical before the final step. The patch increased the cash margin by a mean of +$208 and median of +$155, with a range of 0–691; no game became worse. The win-loss record remained 8-8, with 0 outcome flips. All sheds were empty at the end of the patched games, and all statuses were DONE.

**Formal package certification.** Using `package.py ... liquidation` to rebuild `outputs/deployment/s101102-u0200-20260930-t0-liquidation/submission.tar.gz` from U200 checkpoint
(sha256 `f6e997dbbe44bd320567e4e300d86d2c3d79fb8d22668f6ffd5b9d2695cff6aa`, not submitted), official budget certification passed.
Compared to the officially certified U200 package, `actor.pt` differs only in TorchScript's random serialization ID and debug information; weights and code are byte-for-byte identical.
In self-play games using the same certification seed, each side's cash increased from 108999 to 109021 (an additional $22 in the final move).

**Conclusion.** The patch is strictly non-loss, but it provides only a small improvement in win rate, estimated at 0–0.6 percentage points: the final step of the strategy would naturally sell most of the inventory, and the remaining inventory value is much smaller than the typical gap in negative outcomes. It incurs no cost, and is recommended to be included in the final package; whether to adopt it is left to the user's discretion.
