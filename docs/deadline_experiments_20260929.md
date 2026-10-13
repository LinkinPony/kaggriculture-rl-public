# Pre-Deadline Experiment: Strong Team Agent Evaluation and Targeted Retraining for Strong Teams (2026-09-29)

**Background.** Kaggle official evaluation page: final submission deadline **2026-09-30 23:59 UTC**; up to 5 submissions per day;
only track the **latest 2 submissions**, and perform Bradley–Terry ranking based on games played approximately two weeks after the deadline;
scoring considers only win/draw/loss, not cash difference. This round involves only local experimentation, and **no Kaggle submissions are made without user authorization**.

**Motivation.** The retention weight comparisons and training logs for s99001 show that U200 has reached an internal panel plateau before and after; after U307, each weight performs worse than the average of earlier weights; U308–U1016 achieve a real-time learner performance of 49.6% against BC, and approximately 44% against U192/U256. Meanwhile, Kaggle's performance records against five continuously strong teams dropped from 19–9 for s80001 U816 to a combined 4–64 for three submissions at s95001, while the internal panel has continued to rise. All 12 neural opponents in the internal panel originate from the same lineage and are present within the training pool; 7 scripts are already saturated and thus cannot represent the strength of the leaderboard.

## 1. s99001 stop

Sent SIGTERM to the identity-verified recovery parent process at **23:06:27 UTC**, completed the current update according to the stop protocol, wrote an atomic checkpoint, and normally terminated at **U1061** (`checkpoints/update-001061.pt`). Recovery entry exit code is 0.

## 2. Negative Outcome: Loop-back video replay cannot serve as a proxy for strong teams

Method: Retrieve the latest two versions of official games for each team from five data collectors, reconstruct them in the native engine using the recorded `info.seed`; replay the move sequences frame by frame from the strong team side, while replacing the other side's moves with our exact submitted package (independent interpreter, CPU FP32). Code: `src/kagg_revue/evaluation/tapes/`, Configuration: `configs/evaluation_tapes.yaml`.

Rapid validation (4 packages × 40 game recordings, plus package s68001 failed to run all 40 games due to incompatibility):
U588, s95001 U964, s91001 U2137, s80001 U816 achieved a win rate of **90%–95%** in the recordings, with an average cash lead of approximately **42,000**; however, U964 performed 1–23 against the same strong teams on Kaggle. Revenue from recorded games is about **20,000 less** than the median of original games; the proportion of farm consistency with original games reached 59% on Day 5, dropping to only 20% on Day 10.

Reason: The daily random number stream (`csrc/engine.cpp::EndOfDay`), which is reset daily and follows the sequence "seat 0 empty space, seat 1 empty space, then draw a new store," shares the same stream. Different empty space counts on our side result in different stores being drawn afterward. The recorded actions pertain to the original store sequence and the original opponent's market behavior; after the loop is broken, the plan becomes misaligned and cannot adjust according to price changes. Such market interactions cannot be corrected by patching and are therefore abandoned.
The result is saved in `outputs/analysis/strong-tapes-20260929-quick/`.

## 3. Closed-loop Agent: Strong Team BC Clone Panel

Evidence: The win rate of pure BC starting point U0 against the old lineage is close to that of actual strong teams against these old submissions
(83.9% against the s91001 family, 84% for strong teams against s91001's three submissions).

- Version selection: `configs/sequences_team_clones_20260929.yaml`, all versions of the six teams from 9/27 since 12:00 UTC,
  (Tufa Labs has only one version, see also `configs/sequences_team_clone_tufa_20260929.yaml`),
  excluding two anomalous new versions 56652700 and 56654377.
- Cloning: Clone from U0 (s99001 `initial.pt`), normalize BC recipe by strength, single-team fine-tuning, up to 12 epochs,
  early stopping validation (`configs/learning_team_clone_bc_20260929.yaml`), seeds s100011–s100016.
- Panel: `src/kagg_revue/evaluation/checkpoints/panel.py`, each of the six clones forms one family with equal weight,
  each pair plays 128 matches with seat swapping, environment seed `9400000000+` (not overlapping with training or prior evaluations).
  Validation candidates are Kaggle-verified strong team records: s95001 U960, s91001 U2137, s82001 U3243.

## 3.1 Clone Panel and Round-Robin Tournament Results

Cloned panel (11 candidates × 6 clones × 128 games = 8,448 games): U200 72.8%, U256 68.4%, U192 67.8%, U512 65.0%, U588 63.0%, U0 60.9%, U1061 59.8%, 9/29 new BC 55.5%; old submissions s95001 U960 46.6%, s91001 U2137 35.2%, s82001 U3243 25.4%. Boey's cloned instances failed (all candidates approximately 100%), after removal U200 reaches 67.5%, U588 reaches 55.8%. U200 − U588 = +9.8 percentage points, exceeding the simultaneous 95% radius of 7.7 percentage points.

Complete round-robin tournament (`configs/evaluation_round_robin_clones.yaml`, 8 players × 64 matches = 1,792 matches):

| Rank | Participant | Average Score |
| ---: | --- | ---: |
| 1 | s99001 U200 (RL) | 65.6% |
| 2 | DSM Clone (U0 Top Lane Team Pure BC, 9 epoch) | 64.2% |
| 3 | s99001 U588 | 57.0% |
| 4 | s99001 U0 (DSM+MMPQ Mixed BC) | 52.0% |
| 5–8 | Tufa / Vadim / DECEM / MMPQ Clone | 49.6% / 43.8% / 40.8% / 27.0% |

DSM clone achieves 45.3% win rate against U200 (not statistically significant in 64 games), 61.7% against U588, and 60.9% against U0. Conclusion: On current weights, pure BC learning from a single mimicked strong team (DSM) has already reached near-optimal RL checkpoint performance; mixed BC (U0, 9/29 new BC) involving multiple teams is significantly weaker; although MMPQ ranks first, it performs the weakest in cloning.

## 4. Continued Training

New BC Starting Point: U0 continues BC on the Strength Selection Version of 9/29 (MMPQ 56640167, 56624842, DSM 56643615, 56619023, 56646963; `configs/sequences_strength_canonical_20260929.yaml`), s100001.

RL s100101: Restart of the Actor from s99001 U200 (new Critic, new 300 update warmup), pure terminal WDL,
PFSP unified pool = external strategy inherited from s99001 + checkpoint retained by s99001 + six strong team clones,
high win rate frequency reduction: 64/0.95/0.05, inheritance of prior evidence with s99001 as the archive. A checkpoint is retained every 50 updates for panel evaluation.
Plan to stop at U300 (where learning rate is fully increased and s99001 begins to degrade) according to the stop protocol, with evaluation conducted using U100/U200/U300.

RL s100201 (`configs/learning_dsm_clone_ppo50_20260929.yaml`): Use the same recipe and opponent pool, switch the starting point to the verified optimal checkpoint of DSM clone, verify whether "single team BC + short-range RL" can exceed U200; after s100101 is stopped, take over the two cards.
