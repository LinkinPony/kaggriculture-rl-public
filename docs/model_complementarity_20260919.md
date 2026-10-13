The Complementarity of Two Training Sessions and Recommendations for the Next Training Session (September 19, 2026)

We recommend adopting a new experiment consisting of "freezing two teachers, selecting supervision based on game situations, supplementing teaching along student trajectories, pure WDL reinforcement learning, and group-based anti-degradation verification." Starting from the validated v4 weights as the initial student model, we prioritize supplementing learning objectives and evaluation coverage. Current materials support divergent behaviors between the two, indicating specific weaknesses; however, it has not yet been proven that the new model and the old model exhibit stable complementary win rates under the same opponent distribution, nor can it be guaranteed that a single model achieves better performance on a per-game basis compared to either of the two.

This round only involved data reading, public data download, and writing of analysis outputs; no modifications were made to the training code or runtime configuration. Existing working tree changes were not altered. During analysis, s73001 was running, and the training statistics read were up to U3268; online new submissions remain fixed at U2724.

**Four Submissions and Evidence Boundary**

At 04:29 UTC on September 19, freeze the entire API-visible episode lists of four submitted entries via the authenticated Kaggle SDK. Filter out completed public competitions, excluding each of the self-validation matches; do not sample by result. The denominators in all opponent tables are the number of matches, not the number of losses.

| Model and Temperature | Submission | All-visible Public Game | vs. ymg_aq | vs. Majkel1337 |
|---|---:|---:|---:|---:|
| s68001 U5629, T=0 | 56266758 | 248/343, 72.3% | 3/11, 27.3% | 56/86, 65.1% |
| s68001 U5629, T=1 | 56266899 | 237/313, 75.7% | 4/7, 57.1% | 26/43, 60.5% |
| s73001 U2724, T=0 | 56331731 | 118/136, 86.8% | 3/5, 60.0% | 0/1 |
| s73001 U2724, T=1 | 56331777 | 118/140, 84.3% | 3/7, 42.9% | 0/4 |

No draws. Overall win rate cannot be directly ranked: the two submissions occurred on different dates with significantly different match distributions. The old T=0 had 86 games against Majkel, while the new T=0 had only one.

Split according to the exact opponent version, mixed factors become more apparent:

- Old T=0: Majkel 56156662 becomes 26/33, and 56216119 becomes 30/53; old T=1 versions are respectively 16/22 and 10/21.
- In the five games against Majkel for the new model, four games were played against 56332038, with no historical matchup records for this version in the old submissions; the only shared version, 56216119, has one loss in the new T=1 setting.
- The old model's primary opponents against ymg were 56265944/56265958; the new model faces 56305493/56305515. Together, the two temperature levels of the old model against these shared new versions total only four games, with a record of 3/4, making it unsuitable for estimating stable performance.
- The new model's performance against Majkel at two temperatures totals 0/5, which constitutes a warning requiring attention; even the upper bound of the Wilson 95% confidence interval based on the independent binomial approximation remains approximately 43%. Temperature, seat, version, and world differences imply a significantly larger actual uncertainty, and this cannot be interpreted as a zero overall win rate.
- Other warnings include new T=0 matchups against DSM 0/4, SpaTaro 0/3, and Sida Zuo 0/3; new T=1 against THIRD FARM CLUB 3/8. All samples are very small, and their role is to define future test coverage; they should not be used to establish hard-coded routing for these teams.

Original response and request time, SHA256 in [data directory](../data/external/kaggriculture-model-comparison-20260919/raw/submissions/). [Complete statistics](../outputs/analysis/model-comparison-20260919/submission-results.json) include per-team, per-version, per-turn, Wilson intervals, and cash difference; cash difference is for diagnostic purposes only. This snapshot is the API-visible set and does not claim to be permanently complete.

**Actual Differences in Training Recipes**

| Project | Submitted U5629 for s68001 | Submitted U2724 for s73001 |
|---|---|---|
| Input and Structure | grounded-v2, budget features, no additional time memory | agronomy v4, budget features, 384 turn time memory |
| Main Backbone | 16 × 384 | 16 × 384, plus 2 × 256 time memory |
| BC Source | 9/11–12 daily and supplemented public versions matching the historical top ten evidence | 9/14–16 daily, continuing with historical top ten evidence filtering |
| BC Training Set | 4,559 seat trajectories, 3,277,090 valid decision lines | 2,456 complete trajectories, 1,764,824 supervised turns |
| Actual BC | 4 epoch, 13,108,360 lines | 13 epoch + 196 batches, 24,069,461 supervised turns |
| RL Game Count Submitted | 720,512 | 348,672 |
| Reward at Submission | Final outcome + own final cash item | Pure final WDL |
| Average Actor Steps per Turn in 256 Updates Before Submission | 20.86 | 3.00 |

The `bc100` in the new run name is the original budget; actually, it was transferred from BC cursor 4187 to RL, without completing 100 epochs. The old model switched to pure WDL at U5972, so the `cash_weight=0` in the current old run configuration cannot be traced back to the training reward at U5629.

The number of actor steps, BC epochs, and training rounds are not fairly comparable in terms of computational load or data utilization efficiency: all factors including batch size, sequence organization, input structure, and optimizer steps differ. These variables change together, and thus cannot be directly attributed to changes in opponent win rate caused by memory, v4 features, WDL, or BC date. The new experiment still follows the pure terminal win +1, draw 0, loss -1 rule, without copying the old cash target.

Source: [Old BC](top10_two_day_bc_20260913.md), [New BC](agronomy_v4_bc_20260917.md), [Reward Migration](wdl_20260916.md), two active runs `state.json` and `resolved-config.json`, new run `bc-completion/0001/transition.json`. When comparing, use the current main document's commit identity and archival records; do not infer progress based on directory names.

Why doesn't current training guarantee the absorption of advantages from the old model?

The historical pool of 177 members currently has 51 models from the old s68001. In the 256 turns of new submissions prior to U2469–2724, there were 6,848 games against these older models, accounting for 20.9% of the total 32,768 games; the win rate of current models against these mixed older versions is 61.6%. This is neither a fixed evaluation against U5629 nor a test on Majkel.

Therefore, the absence of the old model is not a primary issue. In this context, the old model serves as an opponent, and its actions do not become the target of student supervision. Defeating the old model only indicates that the system has learned the winning strategy within that specific interaction, not that it has acquired the strengths required to handle the old model when facing third-party opponents.

Current PFSP has been adjusted according to `(1 - win rate)^2` to prioritize difficult opponents and includes uniform and recent snapshot quotas; it is not limited to selecting opponents with a 50% win rate. The issue is more about pool strategy coverage and target evaluation, rather than a lack of PFSP algorithm. Both running `bc_retention_loss` inspection windows are zero, with no explicit retention of the behaviors of two teachers within RL.

A more direct blind spot is evaluation saturation:

- Over the 256 rounds preceding U2724, the win rate against five native scripts ranges from approximately 95.2% to 97.7%.
- With fixed selection consisting only of the RL-initial BC model and two random models (each running 64 games), U2048, U2560, and U3072 all achieve 192/192.
- In the newly released script investigation for 9/19, Thomas 2945 and Ahmed V49 each have only 1/32 wins against the current U3044. Switching to the new scripts warrants a regression coverage, but there is currently no evidence that they provide sufficient strong opponent pressure.

Records available at [Training Statistics Snapshot](../outputs/analysis/model-comparison-20260919/training-snapshot.json), [Current PFSP Implementation](../src/kagg_revue/learning/matchmaking/statistics.py), and [New Script Investigation](public_notebook_survey_20260919.md). Training statistics originate from evolving strategies and adaptive sampling, and cannot be proven to indicate regression based on win rate changes between windows.

**Replay notes which capabilities should be retained and which cannot be directly copied**

Add download and complete verification for 29 games: new two submissions against ymg/Majkel's full 17 games; old two submissions against the common ymg new version's full 4 games; old two submissions, each by seat, against Majkel 56216119 with win-loss ignored draws of 4 games each, totaling 8 games. The old Majkel sampling uses a fixed hash seed 73119, and the results of these eight samples cannot replace the full statistical analysis of the entire dataset.

All 29 games achieved 720 frames, with both sides active for the first 719 frames and terminal state marked as DONE. After native engine replay, **41,760 observation trajectories are exactly consistent**, and both sides' full cash ledgers and final API rewards match. In 17 new model replays, there were no illegal unit action changes. In this game, the current analysis focuses on decision-making behavior, rather than timeout issues.

1. The production rhythm of the new model has changed. For the new ymg version with t=144, there are approximately 10 strawberry plants on average, compared to 3.8 plants reported by the existing old-version ymg at t=0. The new model has a unit PASS ratio of about 4.3% for ymg, compared to 13.7% in the old report. This constitutes evidence of behavioral differences; since opponent versions and map conditions differ, the difference cannot be attributed to independent gains, and less PASS should not be rewarded.

2. The new model still exhibits a stable procurement gap: in 17 games, all requests for two melon seeds at t=11 resulted in zero transactions; in 12 games related to ymg, all requests for one wheat seed at t=19 or t=20 resulted in zero transactions. The actual wheat seed holdings at ymg's first day were 8 units, while for Majkel they were 10 units. Existing audit confirmations verify transaction facts, but no initial intervention has yet been applied to the new version; therefore, causal conclusions from the old model's initial pricing cannot be directly applied.

3. In five games involving Majkel under the new model, three of the final-day starting positions were cash-leading, yet all ended with a deficit. For example, 110659520 went from +4,754 to -892; 110535791 went from +2,180 to -1,247. Cash leadership does not imply total asset leadership; thus, the endgame capacity, maturation timing, transportation, sales, and remaining inventory must be evaluated together. It cannot be directly diagnosed as "forgetting to sell inventory."

4. In the new T=1 version for ymg, there are only games with losses of 5 yuan or 66 yuan. This indicates that final execution and boundary decisions warrant special review; it does not imply that a single selling patch will necessarily reverse the outcome.

5. The existing replay data from the old T=0 version shows an advantage in melon income, but also reveals persistent issues such as delayed capacity establishment, insufficient transition production, and failure in early-stage re-purchases. The old model can provide candidate strategies, but its full-game actions cannot be unconditionally labeled as correct.

New evidence: [Select Protocol](../data/external/kaggriculture-model-comparison-20260919/raw/replay-selection.json), [Download List](../data/external/kaggriculture-model-comparison-20260919/raw/manifest.json), [Game-by-Game Highlights](../outputs/analysis/model-comparison-20260919/behavior-findings.json), [Playback Verification](../outputs/analysis/model-comparison-20260919/replay-accounting/verification.json), [Grouping and Detailed Ledger](../outputs/analysis/model-comparison-20260919/replay-accounting/). Previous evidence see [56266758 Replay Report](submission_56266758_matchups_20260918.md).

**Recommended training plan**

First, establish a fixed "capability × opponent" matrix. It must cover at least the following scenarios: initial budget perturbation, early sustained production capacity, changing store demand, market saturation leading to production shift, feed procurement, and harvest and monetization in the final days. Include both submission weight baselines at T=0 and T=1; additionally, incorporate recoverable v4 candidates without assuming the latest version is necessarily the best. For strong opponents, record exact versions, and test under identical world seeds, player seats, and sampling seeds; identical initial seeds do not guarantee identical store random trajectories after interaction.

Without private opponent programs, public replays are used for diagnosis and demonstration data. A fixed replay suffix cannot be treated as a real opponent that responds to new states; opponents trained from replays must also undergo separate closed-loop credibility testing and retain genuine online evaluation. A reproducible panel can first be established using existing native scripts, two-generation models, and validated specialized opponents, but it cannot be claimed to represent the Majkel entity itself.

Then freeze two teachers, using the ability panel to select the recoverable v4 as the student's starting point:

- Teacher A is the validated strategy of the new model; Teacher B is the submitted strategy of the old U5629. Both U6105 and the nearby U5632 must be registered as distinct teachers and cannot silently replace U5629.

- The independently trained checkpoint at the two exact submission points has been stored and cleaned; the submission package and source code remain preserved. A complete closed-loop action trajectory can be generated from the exact package to enable action label distillation. If soft probability KL is required, it is necessary to first verify whether an equivalent teacher distribution can be reconstructed; the package interface that only exports sampled actions cannot be considered as providing logits.

- The applicable scope of each teacher is determined based on repeated terminal WDL performance in shared training scenarios, while simultaneously preserving win/loss trajectories to avoid collecting only lucky victories. It is not permissible to select actions step-by-step based on the future final winner in the same game, nor to choose a teacher based on the short-term cash maximum.

- In the first version, prioritize complete trajectories and long segments to avoid arbitrarily stitching together A's procurement, B's farming, and A's sales into inconsistent plans. When both teachers are reliable, different complete trajectories can be mixed; when disagreements lack sufficient evidence, reduce supervision weight to let WDL learn the decision itself.

- Periodically collect states reached by the student, with both teachers providing advice based on the same observable history, and then validate through closed-loop continuation against an executable opponent. v4 must replay the complete available prefix or restore the correct memory state; memory cannot be cleared midway. Early training must not rely solely on the teacher's own trajectory distribution.

- Adaptation is based solely on observed budget, production capacity, inventory, prices, store states, and observable opponent behavior. Teacher selection or conditional variables must not leak opponent names, private states, future store information, or game outcomes to the deployed model. If the same observable history indeed supports two incompatible routes, a persistent strategy selection variable may be added; however, route switching should not be performed randomly per turn.

This falls under the application of multi-teacher strategy distillation and teacher-assisted RL, with methodological basis for cross-architecture transfer; however, the effectiveness still requires validation through controlled experiments in this project: [Policy Distillation](https://arxiv.org/abs/1511.06295), [Kickstarting Deep Reinforcement Learning](https://arxiv.org/abs/1803.03835).

Finally, distillation and pure WDL are jointly trained. The objective consists of the original PPO loss, plus a teacher behavior loss within applicable scenarios and a preservation loss in advantageous scenarios. The preservation loss constrains the action distribution or enforces supervised training with verified labels on fixed advantageous scenarios, and is not based on intermediate reward values. The supervision strength gradually decreases, allowing the student to deviate from the teacher when reliable improvements are achieved in terminal WDL. The original teacher, trained with cash, is unsuitable as a target for the new WDL Critic.

Train opponents to continue using native C++ with existing batch entry points. Retain regression coverage on the current script, which is nearly undefeated, and allocate new budgets preferentially to strategies that genuinely expose weaknesses: those targeting current student training challengers, historical models exhibiting significant behavioral differences on external capability panels, and opponent agents validated through closed-loop testing. Historical models should be selected based on behavioral characteristics and cross-win rate contributions, not merely by increasing the number of adjacent checkpoints within the same lineage. Difficult sampling should preserve uniform coverage and minimum quotas for each strategy family, preventing the forgetting of previously mastered trajectories.

The key lies in simultaneously achieving "learning the teacher's actions" and "retaining the ability to respond to different strategies." Simply adding the old model to the historical pool, directly averaging the two sets of weights, averaging logits separately for each action head, or concatenating the two BC datasets with equal weights, does not guarantee this. The identical input structures and independent random roots also make direct parameter averaging unsuitable as a primary approach.

**Start with a small-scale comparison, then decide on the formal long-term run**

| Experiment | Content | Purpose |
|---|---|---|
| A | Same recoverable v4 starting point, original pure WDL PPO | Measure the changes from continued training alone |
| B | Same starting point and same opponent pool, adding dual teacher selective distillation and advantage retention | Verify whether complementary capabilities are actually transferred |
| C | B plus challenging opponents pre-screened and strategy family coverage | Verify whether training distribution coverage remains a bottleneck |

In the first stage, screen each approach with 256 updates / 32,768 games, then extend promising approaches to 512 updates. This is a proposed experimental budget, not a promise of improvement. Report actual optimization steps, teacher inference, and total computation as well as game counts. For rigorous attribution, confirm shortlisted approaches using multiple independent training seeds.

Evaluation first uses 64 world × two seats screening against each executable opponent to identify candidates, then expands the confirmation set. At T=1, additional action random seeds are repeated for key groups. Compute intervals by world seed clustering, separating selection and confirmation seeds. Do not treat the two seats of the same world as two independent worlds, and do not claim exclusion of several percentage points of regression based on a small sample of 128 games.

The release criteria should be based on the WDL panel of ability groups: an average performance improvement, with both the previous strong groups and the new strong groups meeting pre-defined non-inferiority tolerances, and prioritizing the reduction of weaknesses in the weakest groups. For example, a tolerance of 3–5 percentage points is merely a business objective; whether the target is met must be confirmed with sufficient sample data; when sample size is insufficient, it should be marked as uncertain, and it must not be assumed to have passed merely because the mean exceeds the threshold. The model selection must not be based on the average win rate of training PFSP, victory over a random model, or the highest average amount.

The current mainline `Experiment` explicitly supports only random initialization or continuation from prior runs, with no teacher/replay fields; memory PPO has also not been integrated with the aforementioned auxiliary supervision. Therefore, B/C are experiments requiring new creation, archiving, and acceptance—mere modification of a Hydra configuration cannot be considered sufficient. Implementation should involve establishing independent new runs, binding teacher identity, data source, opponent version, pure WDL rewards, and evaluation panels, and must verify consistency across versions in observation encoding, action condition prefixes, and memory.
