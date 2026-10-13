# Comparison of New and Old BC Datasets: September 21, 2026

The changes in the new data are primarily concentrated in **teacher composition, opening moves, and market requests**, with magnitude sufficient to affect the behaviors learned by BC.
The data interface remains identical, and the overall frequency of fundamental operations is nearly the same; one cannot simply conclude that teachers are stronger based solely on more or more recent games.

Baseline verified by current s73001's `resolved-config.json` is
`agronomy-v4-sequences-3d-20260917-q100`, manifest SHA256
`d2b8d381b4cb33cde404e438f17ad922baa5e1367ff8df6cfbe1876c2179f812`.
New set is `agronomy-v4-selected8-5d-20260921-q100`, manifest SHA256
`8def06dbcad7881bcb4b3c2fbc2049c702cb050a1a8aaeb8121dac66088c34eb`.

Conducted a comprehensive descriptive analysis on the union of two sets after deduplication—4,028 official original replays and 6,212 selected seat trajectories—without sampling. The original daily package hashes, data manifests, and current training baseline bindings have all been verified.

| Metric | Previous Version | New Version | Change |
| --- | ---: | ---: | ---: |
| UTC Date | 9/14–16 | 9/16–20 | Updated backward and extended by two days |
| Original Daily Package Games | 1,945 | 3,223 | +65.7% |
| Selected Games | 1,767 | 2,777 | +57.2% |
| Teacher Trajectory | 2,706 | 4,189 | +54.8% |
| Supervised Turns | 1,944,470 | 3,011,489 | +54.9% |
| Training Trajectory | 2,456 | 3,815 | +55.3% |
| Training Supervised Turns | 1,764,824 | 2,742,636 | +55.4% |
| Actual Teacher Display Name | 19 | 8 | More focused |
| Proportion of Turns Unable to Express or Masked Supervision | 0.0588% | 0.0133% | Decreased |
| Proportion of Turns with q100 Quantity Truncation | 0.0407% | 0.0245% | Decreased |

Both versions retain 719 decision turns, 22,003 v4 observation features, and the identical q100 action interface,
`layout` is exactly the same. The quantity truncation, supervision mask, and encoding of the original market requests are consistent.

Two versions overlap in 516 games and 683 teacher trajectories, all from 9/16; the new dataset contains 3,506 new trajectories (83.7%), while the old dataset has 2,023 trajectories not present in the new dataset. The hash values of the original replay recordings for the 516 games are all identical; in 337 of these games, the seat selection is also identical, with matching hash values for observation, action, and mask arrays. Using the same environment seed splitting rules, there is no cross-partition seed leakage after merging.

Teacher weights exhibit significant variation. The table counts trajectories fully; each trajectory has the same length, and the supervision mask ratio is very low, thus approximately reflecting the variation in training exposure. The distribution of teacher weights in the training partition alone is essentially consistent with the full results.

| Teacher | Old Trajectory | New Trajectory | Old Share | New Share |
| --- | ---: | ---: | ---: | ---: |
| Majkel1337 | 428 | 817 | 15.82% | 19.50% |
| DSM | 0 | 793 | 0% | 18.93% |
| SpaTaro | 352 | 638 | 13.01% | 15.23% |
| ymg_aq | 353 | 593 | 13.05% | 14.16% |
| Unknown Mother-Goose | 202 | 563 | 7.46% | 13.44% |
| THIRD FARM CLUB | 168 | 485 | 6.21% | 11.58% |
| M & M & P & Q | 215 | 251 | 7.95% | 5.99% |
| Artem The Farmer 🍅 | 216 | 49 | 7.98% | 1.17% |
| Other Old Teachers | 772 | 0 | 28.53% | 0% |

The main teachers removed include Orbital Terraformer (314 entries), Mengfei Li (148 entries), feel the agi (94 entries), and HowardLeeTW (83 entries). The total variation distance of teacher distribution is **37.30%**, meaning that at least about 37.3% of the trajectory weights need to be reallocated to transform the old teacher distribution into the new one. The effective number of teachers calculated by entropy decreased from **11.60 to 6.94**; the sample count increased, while teacher sources became more concentrated. Notably, Artem's training trajectory dropped from **196 to 40**, with its training share decreasing from **7.98% to 1.05%**.

Behavioral changes are concentrated in the market and opening phases:

| Distribution Comparison | Total Variation Distance |
| --- | ---: |
| Unit request categories: mobile, watering, harvesting, etc. | 1.04% |
| Market request categories: buy, sell, hire, etc. | 17.31% |
| Complete market order set in the first turn, including quantity and sequence | 38.52% |
| Opponent display name distribution | 31.19% |

Distance on category frequency does not imply that the corresponding trajectory proportions are invalid or that the corresponding decision proportions are superior.
Unit requests adopt existing normalization logic to remove trailing PASS padding; different unit quantities and request patterns still affect the statistics.
Among the **3,506 new trajectories**, **48.2% of the first 24-turn unit request sequences** have no exact matching samples in the old dataset,
with market request sequence correspondence at **61.1%**. The precision of sequence novelty is influenced by quantity, path details, and sample size,
and cannot be directly interpreted as the proportion of new strategies.

The true deployment status in turn 72 also changes:

| Metric | Old | New |
| --- | ---: | ---: |
| Proportion of trajectories with strawberry plots | 35.88% | 63.62% |
| Average number of strawberry plots per trajectory | 0.70 | 1.32 |
| Average number of cucumber plots per trajectory | 9.41 | 10.81 |
| Average number of wheat plots per trajectory | 8.34 | 7.49 |
| Average number of cows per trajectory | 2.53 | 2.29 |
| Average number of sheep per trajectory | 2.41 | 2.63 |

These numbers only count crops and animals stationed on the plots, excluding those in warehouses or carried by units.
The new data shows a greater emphasis on earlier entry into strawberry and melon production; the average value for strawberry plots at turn 360 in the mid-phase is nearly identical (28.19 → 28.22), indicating that many changes stem from the initial phase and transition timing, rather than representing fundamentally different production systems at the end.

Teams with the same name also show changes. To avoid inflated similarity due to repeated samples of 9/16, a separate comparison is made between the old 9/14–15 and the new 9/17–20:

| Teacher | Old/New Trajectory | Proportion of Unit Request Sequences in First 24 Turns Not Appearing in Old Named Sample | Observation |
| --- | ---: | ---: | --- |
| ymg_aq | 234 / 474 | 100% | Turn 72: Watermelon Field 3.36 → 10.61, Strawberry Field 0.27 → 1.75 |
| SpaTaro | 253 / 539 | 100% | Unit sequence changed at the beginning; Turn 72: Wheat Field 7.30 → 9.91 |
| M & M & P & Q | 27 / 63 | 98.4% | Significant increase in strawberry and watermelon; old window had only 27 entries, explanation must retain sample limitation |
| Unknown Mother-Goose | 157 / 518 | 40.0% | Turn 72: Strawberry Field 0 → 1.24 |
| Majkel1337 | 287 / 676 | 37.4% | Unit combinations updated at the beginning; overall unit category frequencies are similar |
| THIRD FARM CLUB | 77 / 394 | 0% | Order in first turn and average production combination at turn 72 are identical |
| Artem The Farmer 🍅 | 216 / 49 | 0% | Stable at the beginning; main change is reduction in sample weights |

Same naming only indicates the display name and cannot be used to prove the submitted version, implementation, or reason for update.

There is also an additional burden of imitation in market actions. The average market request per trajectory increases from **863.5 to 1,286.4**, with SELL requests rising from **332.2 to 678.7**. The new DSM set has an average of **2,102.3 SELL requests per trajectory**, meaning that the increase in order volume cannot be considered equivalent to actual trade growth.

DSM has **486 trajectories** that begin with "buy one cow, buy five wheat, then SELL 3 units each of seven empty inventory items," accounting for **11.60%** of the new set. Independent native replay confirmation of the first turn of the original replay `109468286` shows that all seven SELL orders have 0 volume; see [replay example](../outputs/analysis/bc-dataset-comparison-20260921/dsm-opening-witness.json).
The existing BC encoding preserves market requests, thus retaining these zero-volume SELL labels.
Additionally, original `INVALID` shows increased requests, primarily from THIRD FARM CLUB; these are treated as invalid requests during encoder parsing and cannot be conflated with the effective rate of supervised action units.

The median terminal cash for two episodes is almost identical: **103,867.5 → 103,926.0 (+0.06%)**,
the mean **105,067.8 → 105,817.8 (+0.71%)**. The average pairing score per game is approximately **3,039.5 → 3,089.2**.
The opponent pool, dates, and teacher composition differ across samples; these descriptive statistics do not provide insight into post-training win rate improvements.

Actual training implications: The new dataset provides a large number of new openings and world states, but significantly reduces coverage of previous teachers, especially Artem.
Under the current setting of 8 full trajectories per batch, the old dataset covers **307 steps per epoch**, while the new dataset covers **477 steps per epoch**;
Over 100 epochs, the step count increases from **30,700 to 47,700 steps (+55.4%)**.
When comparing training gains, optimization budget should be controlled: approximately 100 epochs of the old dataset are equivalent to **64.36 epochs** of the new dataset.
To achieve comparable training impact across eight teams, separate sampling weights need to be explicitly defined; currently, the data maintains the actual daily package frequency.

![Teacher weights, production status, and new sequence comparison](../outputs/analysis/bc-dataset-comparison-20260921/comparison.png)

Complete results: [Machine-readable report](../outputs/analysis/bc-dataset-comparison-20260921/report.json),
[Duplicate and partition verification](../outputs/analysis/bc-dataset-comparison-20260921/overlap-verification.json),
[Trajectory-wise extraction](../outputs/analysis/bc-dataset-comparison-20260921/trajectories.json).

Replay command:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv/bin/python -m kagg_revue.datasets.comparison.cli \
  --config-name comparison_selected8_20260921
MPLCONFIGDIR=tmp/matplotlib-bc-comparison \
  .venv/bin/python -m kagg_revue.datasets.comparison.plots \
  --config-name comparison_selected8_20260921
```

Configuration located at [comparison_selected8_20260921.yaml](../configs/comparison_selected8_20260921.yaml).
Extracted cache record source and implementation hash, verified with Ruff and mypy.
