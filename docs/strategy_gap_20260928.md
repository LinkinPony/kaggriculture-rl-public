# Further Diagnosis of the Current Model's Gap Against Strong Players, September 28, 2026

The most clear-cut finding is: **PPO is indeed stronger than BC at the starting point, but simultaneously significantly reduces the tendency to purchase geese under strong hand conditions; BC's teacher trajectory count is nearly balanced, yet its market loss weight is heavily skewed toward Boey's high-frequency orders.** The newly added official replays still show insufficient mid-term animal capacity. Together, these three pieces of evidence support prioritizing an investigation into the actual weights of training objectives and opponent distributions, rather than directly increasing model size or training duration.

Must distinguish between objects: official replays come from three previously submitted versions of **s95001** from the previous round; local model experiments fix today's **s97001 U472** and its exact BC starting point. There is no official performance of **s97001** against top players, and the results of the two generations of models cannot be treated as a randomized controlled experiment.

![Teacher loss weight, BC/PPO purchase animal probability, and official match income difference](../outputs/analysis/strategy-gap-20260928/overview.png)

**1. Add 38 official matchups: the gap in mid-term investment and output remains persistent.**

Frozen five existing collectors at UTC 06:34:34, selecting submissions from s95001: 56608595 / U556, 56614434 / U964, and 56623562 / U1664, including all downloaded games, without filtering by result. The window is from 9/27 17:17 to 9/28 05:38 UTC, totaling 38 games, with no missing downloads of previously discovered games. All games were verified frame-by-frame using the native engine, **54,720 mutual observations from both sides**, and the transaction ledger matches the final cash settlement.

Our side has **1 win and 37 losses**, an average cash of **104,183 vs. 108,190**, a difference of **−4,007**, with a 95% resampling interval of **[−4,831, −3,175]**. Split by version: 1/20, 0/14, 0/4; variations in opponents and seeds do not form a training progress curve, and the latest version has only four games.

| Source of Cash Difference in Same Game | My Side − Opponent |
| --- | ---: |
| Net revenue from wheat, after deducting cost of purchased products | -2,328 |
| Goose egg | -2,098 |
| Milk | -1,520 |
| Strawberry | -984 |
| Tomato | +1,846 |
| Savings on land, labor, seeds, and animals | +1,883 |

The table lists only the main items; all items are strictly summed in the machine report. The sales volume items with income differences for duck eggs are **−2,117** and the average price item is **+19**; for milk, they are **−1,698** and **+178**, respectively. The primary issue is capacity versus output; adjusting only the selling points is insufficient to cover the gap.

On game days 6–8, the average number of geese purchased is **3.71 to 4.34**; on days 9–11, it is **1.92 to 2.55**. The goose occupancy is **120.6 to 148.9 plot-days**; the cow volume is **174.6 to 185.2**. On day 12, cash leads by **1,564**, but by day 17 it lags by **816**. Cash includes investment outlays and cannot independently reflect operational value; insufficient investment, combined with subsequent low output, supports the diagnosis of underinvestment.

Our side consists entirely of three-location units, while the opponent has six four-location games. Only the 32 games involving both sides' three-location units are retained, resulting in a record of 1 win and 31 losses, with an average of −3,697; the "ge egg" and "milk" values are each reduced by 2,343 and 1,719, respectively. Our side still has zero illegal unit actions, and warehouse overflow is 7.21 versus 7.95 units per game—insufficient to explain the primary gap.

Source: [Selection and Original List Snapshot](../outputs/analysis/strategy-gap-20260928/replays/selection.json), [Frame-by-Frame Verification](../outputs/analysis/strategy-gap-20260928/replays/audit.json), [Version, Opponent, and Revenue Report](../outputs/analysis/strategy-gap-20260928/replays/report.json).

**2. The strength change from BC to PPO has been directly compared: PPO clearly outperforms the BC starting point.**

Fixed s97001 `initial.pt` (consistent with the final 2047th batch Actor of s96001) and U472, T=1, complete 384-turn memory. 64 independent environment seeds exchange positions, totaling **128 games**; model weights unchanged confirmed, native binary SHA256 matches the mainline.

- U472: **111 wins, 17 losses, 86.72%**; 95% confidence interval based on environmental seed clustering **[80.47%, 92.19%]**.
- U472's average cash lead during the same game: **8,212**; interval **[6,428, 10,094]**.

This clearly indicates that PPO has gained direct strength against this BC starting point; it does not yet prove improvements in external generalization, nor does it prove superiority over any arbitrary opponent.

The training ledger for U1–U472 consists of **60,416 games**, with 30,208 self-play games, 29,888 against its own historical policies, and 320 from native scripts; the first two categories account for **99.47%**. The Actor and Critic each update **1,888 steps**, with KL early stopping occurring **0 times**, and the Actor being skipped due to constant returns **0 times**; the recorded maximum prefix KL is **0.00461**, with a threshold of 0.05. BC preservation loss remains zero throughout.

Therefore, there is currently no indication of "KL protection causing the Actor not to update." A small sequential KL does not imply cumulative policy invariance, and one cannot simply conclude that the learning rate should be increased merely because it is below a threshold.

Source: [Fixed-weight identity](../outputs/analysis/strategy-gap-20260928/imitation/snapshot.json), [128-game matchups](../outputs/analysis/strategy-gap-20260928/duel/report.json), [turn-by-turn records](../outputs/analysis/strategy-gap-20260928/duel/games.jsonl), [training audit up to U472](../outputs/analysis/strategy-gap-20260928/training/report.json).

**3. PPO has clear directional changes: reduced goose purchases, more active tomato procurement.**

For two fixed-weight re-runs of the current BC, verifying all 94 validation trajectories / 83 games / 67,578 effective turns, confirm the array hashes used. Each trajectory retains complete 719-turn observations and causal memory. Both models use identical teacher action prefixes and loss masks.

| Teacher's chosen action | Average probability from BC | Average probability from U472 |
| --- | ---: | ---: |
| Buy goose | **71.64%** | **50.87%** |
| Buy cow | 75.36% | 76.90% |
| Buy sheep | 71.13% | 61.21% |
| Buy land | 87.46% | 72.07% |

The buying probability of geese changed by **−20.77 percentage points**, with a 95% interval based on environmental seed clustering of **[−23.86, −17.65]**. The buying probability of geese in the DSM subset decreased from **83.98% to 54.83%**. The change in buying probability for cows crosses zero, so the procurement of all animals cannot be described as equally degraded.

To eliminate confusion caused by order sequence and teacher action prefixes, all 94 trajectories were fully decoded with autonomous action parsing: no teacher actions were provided, and a greedy selection approach was used, checking at each turn whether any identical purchase appears at any position in the market list, ignoring quantity and position.

| Comprehensive Action Diagnosis on Fixed Teacher Observations | BC | U472 |
| --- | ---: | ---: |
| In 800 turns where the teacher chose to buy geese, the model also selected buying geese | **637 / 800 = 79.63%** | **458 / 800 = 57.25%** |
| Total turns in which the model chose to buy geese | 784 | 567 |
| Matching rate of DSM teacher's turns buying geese | 89.25% | 56.54% |
| Total turns in which the model chose to buy tomato seeds | **110** | **386** |
| Total turns in which the teacher chose to buy tomato seeds | 171 | 171 |

This indicates that the differences are not limited to merely changing the order position within the same operation. It aligns with the direction of insufficient goose capacity and excessive tomato input in public games, but still cannot be deemed a causal mechanism for external failure: the public game is s95001, the local intervention is s97001; the autonomous action probe still maintains a fixed teacher state, without allowing choices to alter the subsequent environment. The turn number here is not the actual purchase quantity.

The trajectory was previously used for BC optimization and belongs to the out-of-distribution validation set rather than a new independent confirmation set. Field accuracy, teacher action probabilities, and turn-T=0 match rate are not the T=1 game win rate.

Source: [By Teacher and Operation](../outputs/analysis/strategy-gap-20260928/imitation/report.json), [Pairing Change Interval](../outputs/analysis/strategy-gap-20260928/imitation/paired.json), [BC Autonomous Actions](../outputs/analysis/strategy-gap-20260928/actions/bc-report.json), [PPO Autonomous Actions](../outputs/analysis/strategy-gap-20260928/actions/ppo-report.json).

**4. The actual loss allocation of BC is vastly different from "each teacher being roughly equally important".**

Current training set contains 1,828 trajectories, with the Boey strong version accounting for **375 trajectories, or 20.51%**. Due to its frequent orders, each Boey trajectory contains on average **6,616 valid market operation fields**, while the other four are approximately 1,600–2,000 fields. These fields include STOP orders, and not all can be interpreted as actual trades.

Reconstruct the true domain-normalized denominator for each batch, following the original training configuration with seed 96001, eight complete trajectories per batch, and the same group order:

| Boey's Share | Value |
| --- | ---: |
| Training Trajectory | 20.51% |
| Average Loss Coefficient in Market Operation Domain | **44.58%** |
| Average Loss Coefficient in Market Quantity Domain | **57.29%** |

There are five types of actions with equal weights, ensuring balance only among the five domains—target, operation, quantity, etc.—but not among teachers or specific operations. This is the normalized loss coefficient, not the actual gradient norm or learning contribution.

The total coefficient of all teachers' goose-buying labels within the market operation domain amounts to only **0.3165%**, multiplied by the proportion of this domain in total loss (1/5), yielding approximately **0.0633%**. The combined share of the four categories—buying wheat, buying fertilizer, selling wheat, and selling fertilizer—accounts for about **30.46%** of the market operation domain. This explains why overall NLL improvement may primarily stem from frequent trading activities, while supervision over critical expansion decisions remains relatively sparse.

Also need to correct the previous vague statement about "market operations having only learned seventy percent": At the BC starting point, the market operation accuracy and quantity accuracy on the DSM validation trajectory are **92.12%, 92.10%**; for Vadim, they are **93.41%, 93.05%**. Boey achieves only **54.70%, 52.38%**, and has a high proportion in the market fields, significantly dragging down the overall metrics. Boey's own buy-goose matching and wheat seed procurement have not stabilized either, and thus it cannot be understood that occupying a large share of loss weight indicates that "Boey's operational strategy has been mastered."

This does not mean that the strong version of Boey should be excluded, or that its frequent buy-sell actions are useless; instead, priority should be given to verifying the teacher normalization, layering of key operations, and the independent learning effects of different business strategies. The old Boey 56484772 has been excluded, yet the issue still appears in the current compliant strong version data.

Source: [Complete Label and Loss Coefficient Audit](../outputs/analysis/strategy-gap-20260928/imitation/census.json), [Actual Normalization Implementation](../src/kagg_revue/learning/pretraining/objectives.py). The count of label census matches individually with the field masking counts from the two models' actual fields.

**5. Current Assessment and Most Discriminating Next Step.**

I have updated the priority of the cause to:

1. **The operating environment generated by training opponents differs from that of external strong hands.** This is a direct distributional fact; "it leads to reduced goose purchases and external losses" still requires causal validation. The current model outperforms its BC baseline starting point while deviating from key procurement decisions of several strong hands—these two facts can coexist.

2. **The BC loss coefficient is significantly influenced by high-frequency orders and specific teachers.** It has been precisely quantified, but whether adjusting weights can improve WDL remains to be validated through comparison.

3. **Learning and retention of a few key investment decisions are insufficient.** There is already repeated evidence regarding goose purchases; these should be prioritized over average illegal action rates or overall field accuracy.

4. **Cross-teacher plan mixing, long-term memory learning, and model capacity** remain possible causes; current evidence is insufficient to attribute them individually. The 48-turn gradient block indeed cuts off gradient writes for cross-block memory, but early actions still receive full terminal rewards; it cannot be stated that "actions before turn 48 receive no rewards."

Next, prioritize three experiments with clear evaluation criteria:

- Fix the dataset, BC starting point, and optimization budget, and compare the current five-domain equal-weight and teacher normalization approaches, while separately evaluating key operations such as purchasing geese. Monitor both teacher performance and the independent operation outcomes—including procurement, production capacity, and final WDL. Do not draw conclusions solely based on NLL.

- Fix the BC starting point and PPO budget, and compare the opponent pool that can reproduce the independent operation strategy against the current opponent pool. When no executable top-tier source code is available, imitation of opponents must be individually verified and cannot treat fixed replays as opponents that would respond to our actions.

- Conduct localized procurement interventions under the current strategy to first validate whether increasing or restoring goose investments at appropriate times can improve the final win rate under constraints of supplementary feed and labor. This is an exploratory experiment for root-cause analysis, not a proven deployment rule; unconditional goose purchases are not permitted.

It is not recommended to revert based on this result alone. BC: The current PPO performs significantly better in direct matchups. There is no evidence supporting the immediate expansion of the network, further increasing BC epochs, or restoring already saturated script auto-evaluation as a metric for progress.

**Reproduction and engineering verification.** All newly added code is located at `src/kagg_revue/evaluation/diagnosis/`; configured as `configs/diagnosis_{replays,imitation,actions,duel}.yaml`. Original data and training runs are retained, and diagnostic outputs are located at `outputs/analysis/strategy-gap-20260928/`.

```bash
PYTHONPATH=src .venv/bin/python -m kagg_revue.evaluation.diagnosis.replays
PYTHONPATH=src .venv/bin/python -m kagg_revue.evaluation.diagnosis.imitation
PYTHONPATH=src .venv/bin/python -m kagg_revue.evaluation.diagnosis.census
PYTHONPATH=src .venv/bin/python -m kagg_revue.evaluation.diagnosis.duel
PYTHONPATH=src .venv/bin/python -m kagg_revue.evaluation.diagnosis.actions
PYTHONPATH=src .venv/bin/python -m kagg_revue.evaluation.diagnosis.actions analysis.model=ppo analysis.device=cuda:1
PYTHONPATH=src .venv/bin/python -m kagg_revue.evaluation.diagnosis.training
PYTHONPATH=src .venv/bin/python -m kagg_revue.evaluation.diagnosis.reporting
```

Ruff, mypy, and two tests targeting statistical semantics pass. Actual data verification includes 38 official game draws, 94 trajectory condition inferences from two models and autonomous action inferences, 128 complete games, and weight-invariance verification. Interval correction for exploratory multi-metric comparisons, public match selection, and strategy version correlation is not performed.
