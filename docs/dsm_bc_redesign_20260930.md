# DSM BC Rewrite (September 30)

## Conclusion

Move RL to GPU0 (s101102), and use GPU1 for re-doing DSM behavior cloning. **No Kaggle submissions.**

Like MMPQ, the primary issue with DSM clones is that **data mixes different playing styles, and newer data is preferred**:

- **Old play data cannot be used to clone the current DSM.** Using only the previous play set B (the ten strongest versions, with data 2.5 times that of C), the average performance at T=0 against four RL reference opponents is only 40.0%, 9.2 percentage points lower than using the current play C alone (95% confidence interval: −17.3 to −1.2).
- **The latest and strongest DSM version, 56693917, performs best.** After verifying freshness via user alerts and reconstructing the data:
  The standalone clone of 56693917 over 108 games, starting from s100901 U756 and ending at s101303, achieves a **66.2%** average across four reference opponents and a total score of 60.5%, 11.2 percentage points higher than the v3 play C clone (+3.7 to +18.9), and 5.9 percentage points higher than the previous top performer s100801 (−3.0 to +14.7, not statistically significant). The clone using all four C versions yields 57.4%.
- **The starting point has little impact.** The same data shows no significant difference across three starting points: U0, s99001 U1061, and s100901 U756, and the advantage of U756 is not reproduced in v4 data.
- Under teacher enforcement, the latest version clone achieves the highest accuracy for unit targets and market actions on 56693917 (94.1% / 92.5%), while its starting point U756 only reaches 90.6% / 81.5%, indicating that performance stems from learning DSM behaviors rather than preserving RL weights.

- Reproducing the seed and starting from U0 both achieved replicated returns (total score 58.0% / 55.9%, both significantly higher than the v3 method C clone);
  From the four-version clone continuation training to the latest version, there was no specialization, nor any gain in returns.

The recommended DSM clone is the **v4 latest version (s101303, epoch 9, `pretraining/shard-000117.pt`, T=0)**.
The second seed, s101304, may serve as an alternative. All DSM clones still fall short against MMPQ v4 P clones (losing by 27%–42%).
According to user selection, s101303 has been assigned to GPU1's single-card RL, see [s101401](s101401_dsm_clone_rl_20260930.md).

## Diagnosis: DSM's Play Family

Cluster the 25 DSM versions starting from 9/24 based on publicly replayed macro-behavioral fingerprints (number of hiring instances per game, timing of land purchases, quantities of each crop purchased and first purchase date, number of market orders per turn).
New tool `python -m kagg_revue.datasets.watching.fingerprint` (`configs/replay_fingerprint.yaml`)
Compute the average of all publicly available games already downloaded for each version, and store the result in `outputs/analysis/dsm-bc-redesign-20260930/fingerprints/fingerprints.json`.

| Strategy | Version | Daily Hire Cost | Market Orders per Turn | Most Common Land Purchase (Day) | Other Notes |
| --- | --- | --- | --- | --- | --- |
| A | 56518845, 56527482, 56541087, 56575949 | 10.7～10.9 | 2.5～3.1 | 6, 9, 10 | Tomato starts buying around day 8 at about 24; Gourd 29～45 |
| B | 56537901, 56541009, 56553722～56664798 (remaining 14) | 9.4～9.6 | 1.3～1.7 (56643615 is 5.1) | 6, 4～5 blocks on day 8 | Tomato does not buy or starts buying from day 14～17 (0～13) |
| C | 56605436 (9/27, single), 56675988, 56681605, 56692773 | 10.2 | 2.6～3.5 | 6, 8, (9), 10 | Tomato starts buying around day 8.6～8.9 at about 23; Carrot 64～68 |
| C′ | 56693917 (9/30 at 01:50) | 10.2 | 5.2 | 6, 8, 8, 10 | Wheat 167, Carrot 80, Gourd 19 |

The different playing styles overlap in time (A still submits up to 9/26, and C appears once at 9/27), so data is selected based on behavior rather than date.

Old clone data: v1 and v2 only have strategy B; the "last two days" data for s100801 mixes B with the first C version.

Bradley–Terry strength (9/25 and all observed teams' public games): C′ 56693917 is 4.56, the three versions of C are 4.35 / 4.00 / 3.56, and the strongest version of B is 4.65 / 4.62 / 4.51.

DSM version strengths show little variation (MMPQ's strongest version is 7.49); the real DSM achieved 11 wins and 0 losses against our Kaggle submissions.

## Data Freshness

09:44 UTC Direct query on Kaggle: DSM's currently public versions are still 56692773 and 56693917, with no updated versions.
v3 data freeze corresponds to the replay list at 08:36, with these versions containing 88 / 79 games (104 / 102 games collected by 09:01).
Thus, after the data collection cycle at 10:01 UTC (completed at 10:09 UTC), v4 data is reconstructed:

| Data | Version | Games (Training/Validation) | Manifest SHA256 |
| --- | --- | --- | --- |
| v4 Strategy C | Same as v3 Strategy C, four versions | 490 (461/29) | `d760db0b…868382` |
| v4 Latest Version | Only 56693917 (C′) | 108 (103/5) | `e68718be…a99de31` |

C′ differs in behavior from the other C version strategies and is kept as a separate data set to avoid reiterating the MMPQ strategy mixing issue.

## v3 Data and BC

| Data | Version | Games (Training/Validation) | Run | Optimal | Validation Action NLL |
| --- | --- | --- | --- | --- | --- |
| Strategy C | 56675988, 56681605, 56692773, 56693917 | 438 (413/25) | s101201 | epoch 10, `shard-000520` | 0.1453 |
| Strategy B | 56571979～56664798 with intensity ≥3.9, ten in total | 1,084 (1, 017/67) | s101202 | epoch 8, `shard-001024` | 0.1305 |

Recipe same as MMPQ v4 P: U0 (s99001 `initial.pt`), cosine learning rate 2e-5, one epoch warmup,
final 5% based on validation NLL early stopping (C: 14 epochs, patience 5; B: 10 epochs, patience 4).
The validation sets for the two datasets are different, so NLL values are not comparable.

## Panel (all T=0)

Same panel: four RL references (s100901 U480 i.e. Kaggle 56689315, s100901 U756, s100201 U200, s99001 U200) and MMPQ v4 P clone, 128 games per opponent, same seed.

| Candidate | MMPQ v4 P | s100201 U200 | s100901 U480 | s100901 U756 | s99001 U200 | Four-reference average | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| s100801 (U1061 start, B+C mixed) | 34.4% | 54.7% | 55.5% | 49.2% | 78.9% | **59.6%** | 54.5% |
| v3 strategy C (s101201) | 38.3% | 56.2% | 37.5% | 47.7% | 66.4% | 52.0% | 49.2% |
| v2 (strategy B) | 37.5% | 46.1% | 41.4% | 41.4% | 53.1% | 45.5% | 43.9% |
| v1 (strategy B) | 37.5% | 40.6% | 41.4% | 36.7% | 59.4% | 44.5% | 43.1% |
| v3 strategy B (s101202) | 39.8% | 43.0% | 37.5% | 39.8% | 39.8% | 40.0% | 40.0% |
| v3 strategy C, U756 start (s101204) | 27.3% | 64.8% | 47.7% | 53.9% | 69.5% | 59.0% | 52.7% |
| v3 strategy C, U1061 start (s101203) | 33.6% | 50.8% | 53.1% | 50.0% | 54.7% | 52.1% | 48.4% |

At the same time, pairwise with a 95% radius of about 10 percentage points. Pairing by seed (difference in total score):

| Comparison | Difference | 95% Interval |
| --- | --- | --- |
| v3 Strategy B − v3 Strategy C | -9.2 | -17.3 to -1.2 |
| v3 Strategy B − s100801 | -14.5 | -20.6 to -8.3 |
| v3 Strategy B − v2 | -3.9 | -11.2 to +3.3 |
| U1061 Start − U0 Start (both v3 Strategy C) | -0.8 | -7.3 to +5.8 |
| U756 Start − U0 Start (both v3 Strategy C) | +3.4 | -2.7 to +9.5 |
| U756 Start − s100801 | -1.9 | -9.7 to +5.8 |

All DSM clones are outperformed by MMPQ v4 P clones (the latter achieving 62.7% on the same four references).

Three starting points on the C validation set of v3 strategy with optimal action NLL: U0 0.1453 (epoch 10), U1061 0.1450 (epoch 10), U756 0.1437 (epoch 8). U756 is the RL weight trained after s100801, and has already learned DSM behavior.

## v4 Data on BC

| Run | Data | Start | Recipe | Optimal | Validation Action NLL |
| --- | --- | --- | --- | --- | --- |
| s101301 | v4 Playstyle C | U0 | Same as v3 Playstyle C, warmup 58 shard | epoch 11, `shard-000638` | 0.1457 |
| s101302 | v4 Playstyle C | s100901 U756 | Same as above | epoch 7, `shard-000406` (early stop at epoch 12) | 0.1438 |
| s101303 | v4 Latest Version | s100901 U756 | 13 shard per epoch, warmup 13, up to 30 epochs, patience 6 | epoch 9, `shard-000117` (early stop at epoch 14) | 0.1912 (5-game validation set) |

## v4 Panel (all T=0, same opponents and seeds as v3 panel)

| Candidate | MMPQ v4 P | s100201 U200 | s100901 U480 | s100901 U756 | s99001 U200 | Four-reference average | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **v4 latest version, starting at U756 (s101303)** | 37.5% | 71.9% | 52.3% | 62.5% | 78.1% | **66.2%** | **60.5%** |
| v4 strategy C, starting at U0 (s101301) | 42.2% | 64.1% | 44.5% | 51.6% | 69.5% | 57.4% | 54.4% |
| v4 strategy C, starting at U756 (s101302) | 33.6% | 58.6% | 41.4% | 49.2% | 64.8% | 53.5% | 49.5% |

With three candidates' total scores, the pairwise 95% radius is approximately 8.4 percentage points. By seed pairing (difference in total scores):

| Comparison | Difference | 95% Interval |
| --- | --- | --- |
| v4 latest version − v3 strategy C (U0) | +11.2 | +3.7 to +18.9 |
| v4 latest version − v3 strategy C (U756) | +7.8 | +0.5 to +15.0 |
| v4 latest version − s100801 | +5.9 | -3.0 to +14.7 |
| v4 strategy C (U0) − v3 strategy C (U0) | +5.2 | -0.9 to +11.3 |
| v4 strategy C (U0) − s100801 | -0.2 | -8.3 to +8.1 |
| v4 strategy C (U756) − v3 strategy C (U756) | -3.1 | -9.8 to +3.3 |

## Teacher-enforced Fidelity

`kagg_revue.evaluation.diagnosis.errors` takes argmax over each field using the frozen T=0 actor on two held-out validation sets, and compares the resulting actions with the actual actions from DSM. The data is split into training/validation by game, with consistent splits across games: the 5 validation games in the v4 latest version are also validation games or do not exist in the v4/v3 play style C; the 29 validation games in v4 play style C are not present in the training sets of v3 play style C or s100801. Thus, both validation sets constitute held-out data for all candidates.

| actor | 56693917 holdout (5 games): unit target | market | quantity | strategy C holdout (29 games): unit target | market | quantity |
| --- | --- | --- | --- | --- | --- | --- |
| s100901 U756 (start) | 90.62% | 81.46% | 75.84% | 93.39% | 89.77% | 89.69% |
| s100801 | 90.53% | 81.63% | 75.82% | 93.39% | 89.89% | 89.75% |
| v3 strategy C (U0) | 93.87% | 90.87% | 81.34% | 94.77% | 92.89% | 91.84% |
| v3 strategy C (U756) | 93.86% | 91.32% | 82.24% | 94.79% | 92.97% | 91.90% |
| v4 strategy C (U0) | 93.99% | 91.72% | 82.50% | 94.82% | 93.14% | 91.98% |
| v4 strategy C (U756) | 93.96% | 91.96% | 82.49% | 94.82% | 93.14% | 91.84% |
| **v4 Latest Version (U756)** | **94.05%** | **92.50%** | **82.58%** | 92.31% | 84.52% | 80.26% |

The latest version clone of 56693917 shows only a slight improvement over the four-version clone, but performs significantly worse on other C versions, indicating that it has specifically learned C'. The gap in closed-loop performance is much larger than the gap in incremental fitting, consistent with MMPQ's experience: mixed-version clones show nearly identical incremental predictions, but in closed-loop scenarios, they inconsistently switch between two decision strategies at critical points (e.g., buying land on day 8/9). s100801 and U756 have nearly identical incremental predictions (RL with KL 0.3 alters only a few argmax values), and both clearly deviate from C'.

## Latest Version Data: Repeated Seeds and Starting Points

Same v4 latest version data and recipe, train three variants additionally:

| Run | Start | Optimal | Validation Action NLL |
| --- | --- | --- | --- |
| s101304 | s100901 U756 (Second seed) | epoch 9, `shard-000117` (early stop at epoch 15) | 0.1905 |
| s101305 | v4 strategy C cloned from s101301 epoch 11 | epoch 2, `shard-000026` (early stop at epoch 7) | 0.2005 |
| s101306 | U0 | epoch 9, `shard-000117` (early stop at epoch 15) | 0.1955 |

The starting point of s101305 has already been trained on the same 103-game trajectory, and overfitting occurs after two additional epochs. Same panel (T=0):

| Candidate | Against MMPQ v4 P | s100201 U200 | s100901 U480 | s100901 U756 | s99001 U200 | Four-reference average | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| U756 start, seed 1 (s101303) | 37.5% | 71.9% | 52.3% | 62.5% | 78.1% | **66.2%** | **60.5%** |
| U756 start, seed 2 (s101304) | 35.2% | 61.7% | 66.4% | 60.2% | 66.4% | 63.7% | 58.0% |
| U0 start (s101306) | 32.0% | 56.2% | 59.4% | 62.5% | 69.5% | 61.9% | 55.9% |
| From v4 strategy C cloned continuation (s101305) | 32.8% | 55.5% | 62.5% | 53.9% | 66.4% | 59.6% | 54.2% |

| Comparison (difference in total scores, seed-paired) | Difference | 95% Interval |
| --- | --- | --- |
| Seed 2 − Seed 1 | -2.5 | -9.4 to +4.4 |
| Seed 2 − v3 playstyle C (U0) | +8.8 | +2.2 to +15.2 |
| Seed 2 − s100801 | +3.4 | -5.3 to +11.7 |
| U0 start − Seed 1 | -4.5 | -11.1 to +2.0 |
| U0 start − v3 playstyle C (U0) | +6.7 | +0.9 to +12.7 |
| Continued training − Seed 1 | -6.2 | -12.7 to -0.0 |
| Continued training − v4 playstyle C (U0) | -0.2 | -7.3 to +6.7 |

The returns using only the latest version data are reproducible: both seeds and U0 starting points significantly outperform the v3 method's C clone; U756 starting points show a slight advantage over U0 (not statistically significant). Continuing training from the four-version clones remains the four-version clones (for the C strategy, the unit target accuracy is maintained at 94.67% for the market at 92.49%, nearly identical to the starting point), showing no specialization, and the closed-loop performance is not better than the initial state.
Three variants achieve unit target accuracy of 94.12% / 94.22% / 94.13% and market accuracy of 92.59% / 91.67% / 92.05% for 56693917.

## Products

- Data: `outputs/datasets/team-clone-v3-dsm-plan-{c,b}-20260930-train-val-q100` (`41f5d922…` / `c0bc88ee…`),
  `outputs/datasets/team-clone-v4-dsm-{plan-c,latest}-20260930-train-val-q100` (`d760db0b…` / `e68718be…`).
- Operation: `outputs/learning/dsm-clone-v3-plan-{c,b}-bc-20260930-s10120{1,2}`,
  `dsm-clone-v3-plan-c-from-{u1061,u756}-bc-20260930-s10120{3,4}`,
  `dsm-clone-v4-plan-c-bc-20260930-s101301`, `dsm-clone-v4-plan-c-from-u756-bc-20260930-s101302`,
  `dsm-clone-v4-latest-from-u756-bc-20260930-s101303`, `dsm-clone-v4-latest-from-u756-r2-bc-20260930-s101304`,
  `dsm-clone-v4-latest-from-plan-c-bc-20260930-s101305`, `dsm-clone-v4-latest-bc-20260930-s101306`;
  the optimal member is the `latest` of each `state.json`.
- Panel, fidelity, and fingerprint: `outputs/analysis/dsm-bc-redesign-20260930/` (`panel-t0`, `panel-t0-plan-b`,
  `panel-t0-rl-init`, `panel-t0-v4`, `panel-t0-v4-latest`, `errors/`, `fingerprints/`).
- Configuration: `configs/sequences_team_clone_dsm_{v3_plan_c,v3_plan_b,v4_plan_c,v4_latest}_20260930.yaml`,
  `configs/learning_dsm_clone_*_20260930.yaml`, `configs/evaluation_dsm_clone_*_20260930.yaml`,
  `configs/replay_fingerprint.yaml`.

Reproduction (recommended cloning):

```bash
PYTHONPATH=src python -m kagg_revue.datasets.sequences.versions --config-name sequences_team_clone_dsm_v4_latest_20260930
PYTHONPATH=src python -m kagg_revue.datasets.sequences.prepare --config-name sequences_team_clone_dsm_v4_latest_20260930
PYTHONPATH=src python -m kagg_revue.learning.cli --config-name learning_dsm_clone_v4_latest_u756_bc_20260930 \
  experiment.output_dir=outputs/learning/dsm-clone-v4-latest-from-u756-bc-20260930-s101303 experiment.seed=101303 \
  experiment.device=cuda:1 "experiment.execution.devices=[cuda:1]"
PYTHONPATH=src python -m kagg_revue.evaluation.checkpoints.panel --config-name evaluation_dsm_clone_v4_20260930
```

Data selection depends on the replay list at runtime; reconstruction will include subsequently collected games. If DSM has a new version, a new fingerprint judgment of playing style must be performed.

<a id="section-0f87b6ee9071"></a>

## v5 Data and Cloning (14:00 UTC Reconstruction)

s101102 Stop after GPU0 is passed to DSM. At 14:00 UTC, read-only query of DSM's public version: still 56693917 (01:50) and 56692773 (01:00), no new versions, no need to re-fingerprint. After the collection cycle at 13:36 UTC, 56693917 has downloaded **132 games** (108 games at v4 freeze), of which DSM has won 104 games.

| Data | Version | Games (Training/Validation) | Training Rows | Manifest SHA256 |
| --- | --- | --- | --- | --- |
| v5 Latest Version | Only 56693917 (C') | 132 (127/5) | 91,313 | `69ceb207…290585e7` |

The training/validation split is fixed: v5's 5 validation games match v4 (both have 3,595 lines), so the validation NLL can be directly compared with s101303.
Configurations:
`configs/sequences_team_clone_dsm_v5_latest_20260930.yaml` (inherits the latest version of v4, only with a different output directory),
`configs/learning_dsm_clone_v5_latest_u756_bc_20260930.yaml` (same recipe as s101303, 16 shards per epoch, warmup 16). Both seeds start from s100901 U756, parallel training on cuda:0 at 14:01 / 14:04 UTC, both terminate early at epoch 14 due to patience.

| Run | Seed | Optimal | Validation Action NLL (Same 5 Games) |
| --- | --- | --- | --- |
| s101501 | 101501 | epoch 8, `shard-000128` (`d0388995…`) | **0.1857** |
| s101502 | 101502 | epoch 8, `shard-000128` (`bca83107…`) | 0.1864 |
| v4 s101303 / s101304 (Control) | 101303 / 101304 | epoch 9, `shard-000117` | 0.1912 / 0.1905 |

Same T=0 panel (`configs/evaluation_dsm_clone_v5_latest_20260930.yaml`, `outputs/analysis/dsm-bc-redesign-20260930/panel-t0-v5-latest`, same opponent and 64 seeds as v3/v4 panels):

| Candidate | MMPQ v4 P | s100201 U200 | s100901 U480 | s100901 U756 | s99001 U200 | Four-reference average | Total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **v5 seed 1 (s101501)** | **52.3%** | 82.0% | 61.7% | 68.0% | 68.0% | **69.9%** | **66.4%** |
| v5 seed 2 (s101502) | 35.2% | 64.8% | 50.8% | 60.9% | 69.5% | 61.5% | 56.2% |
| v4 seed 1 (s101303) | 37.5% | 71.9% | 52.3% | 62.5% | 78.1% | 66.2% | 60.5% |
| v4 seed 2 (s101304) | 35.2% | 61.7% | 66.4% | 60.2% | 66.4% | 63.7% | 58.0% |

| Comparison (difference in total scores, seed-paired) | Difference | 95% Interval |
| --- | --- | --- |
| s101501 − s101303 | +5.9 | −1.4 to +13.3 |
| s101501 − s101304 | +8.4 | +1.9 to +14.8 |
| s101502 − s101303 | −4.2 | −10.9 to +2.3 |
| s101502 − s101304 | −1.7 | −8.3 to +5.0 |
| v5 mean of two seeds − v4 mean of two seeds | +2.1 | −2.7 to +7.0 |

Adding 24 game data points causes both seed variants' out-of-sample NLL to decrease by approximately 0.005, but the closed-loop strength is dominated by the seed: the same data leads to a 10.2-point difference between the two seeds, with an average gain of +2.1 for v5 over v4 that is not statistically significant. s101501 is currently the strongest DSM clone on the panel and the first DSM clone to win more than half of its games against MMPQ v4 P clones, yet its advantage over s101303 is not statistically significant.

Real Kaggle games (DSM data collection archive of public games where both players are present) indicate that local cloning is still significantly weaker than real DSM:
DSM's current two versions have a record of **8 wins, 0 losses** against our 56689315 (56692773 in 5 games, 56693917 in 3 games), and 4 wins, 1 loss against 56671443; games submitted by our side from September 26 onward, across 11 versions, have a combined record of 3 wins and 59 losses.
