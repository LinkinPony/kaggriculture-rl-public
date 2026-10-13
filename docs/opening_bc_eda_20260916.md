# 2026-09-16: Three-day daily startup EDA and local BC fine-tuning feasibility

**Reusable existing BC raw replays, with independent fine-tuning for the opening phase.** This dataset supports supplementing different production routes,
but is insufficient on its own to rely on BC learning for recovery from market disturbances. It is recommended to use the **first 48 moves** as the initial experimental window,
with 24 and 72 moves as controls; freeze the current main model and study only the trainable branches activated during the opening phase.
If the goal also includes actual exploration of multiple opening strategies, a consistent random policy selection across the entire sequence is required; a pure greedy deployment will not automatically transition to a multi-opening strategy as demonstration data increases. These are experimental recommendations, and there is currently no evidence of improved win rate after fine-tuning.

Data download, EDA, code reuse validation, and charting have been completed. **Fine-tuning or changes to formal training have not been initiated**.
The formal s68001 continues with pure terminal WDL (win +1, draw 0, loss -1); no additional monetary rewards have been added.
BC uses action likelihood supervision; subsequent RL and model selection will still be based on complete game WDL.

## Data and Audit Basis

According to the [official daily index](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index),
the latest complete date obtained this time is **2026-09-15**. Only the ZIP file for this day (652 games) and the index were newly downloaded; local ZIP files from September 13 and 14 were reused; no new submissions were retrieved, and no individual game replays were pulled back.
The original packages are permanently stored in `data/external/`, with details on date, count, expanded byte size, SHA256, and source of reuse available in the [collection list](../data/external/kaggriculture-opening-eda-20260916/raw/daily/manifest.json).

| Date | Original Games | Audit Retained Games |Trajectories from both players | Historical Teacher Candidate Seats |
|---|---:|---:|---:|---:|
| September 13 | 654 | 653 | 1,306 | 1,165 |
| September 14 | 654 | 654 | 1,308 | 920 |
| September 15 | 652 | 652 | 1,304 | 978 |
| Total | 1,960 | 1,959 | 3,918 | 3,063 |

Exclude `108447638`: Although the final summary is DONE, TIMEOUT seats appear from step 697.
Exclude the entire game according to the complete valid game criteria consistent with existing BC, without explaining that the opening must necessarily be invalid.

The baseline is the actual BC source list used by currently running s68001: 4,003 games, 5,066 selected slots, with 4,559 trajectory entries for train. It is not the later-stopped s69001 dataset. The encoded large arrays for both are not located in their original paths; this confirmation verifies the completeness of the original replays and filtering list, enabling reconstruction of the compact opening array based on this. There is 61-game overlap between the three-day daily data and the baseline; after deduplication by episode, 5,902 games are analyzed, with 5,901 retained.

"The candidate history teacher" only indicates that the team name is present in the existing ranking evidence/alias table, and does not mean that the team is currently in the top ten or that this daily submission ID has been authenticated. The daily itself is biased toward games with high average scores, and is not a random sample from the leaderboard. All game outcomes are retained, and teachers are not filtered by final cash or win/loss results; weights are not assigned based on such criteria.

For each game, the first 144 steps are replayed using the native rule engine, with both sides' complete key observations compared step by step, yielding a total of **1,711,290 observation matches**. Additionally, daily samples of 4 games are selected according to a pre-defined hash, with 12 games replayed in full by an independent official 1.32.7 engine, resulting in **17,280 observation matches**. Furthermore, 8 older BC sources are selected, and 20 game openings comprising 5,760 sequential causal encodings are matched one-by-one against the full replay encodings.
See [Audit Statistics](../outputs/analysis/opening-eda-20260916/report.json),
[Sampling Encoding and Official Confirmation](../outputs/analysis/opening-eda-20260916/validation.json).

## Opening already exhibits diversity, but distribution exposure is clearly skewed

"The Worker Sequence" preserves the order, quantity, and trajectory of actions; "Production Combination" records the crops planted at step 24, the animals deployed/stocked/in carried, and the number of hired workers already contracted, ignoring harvested products in cash, geometric, or warehouse forms. These two metrics are kept separate to avoid treating a single discrepancy in quantity or positioning as a completely new economic trajectory.

| Metric | Old BC train | 9/13 candidate | 9/14 candidate | 9/15 candidate |
|---|---:|---:|---:|---:|
| Trajectory count | 4,559 | 1,165 | 920 | 978 |
| Percentage of most common first 24-step worker sequences | 34.1% | 13.6% | 18.0% | 13.6% |
| Effective number of worker sequence types exp(H) | 22.6 | 33.6 | 39.5 | 41.2 |
| Percentage of most common 24th-step production combinations | 47.1% | 39.5% | 30.1% | 37.3% |
| Effective number of production combination types exp(H) | 10.7 | 11.9 | 12.8 | 9.6 |
| Percentage of worker sequences not seen in old train: trajectory share | — | 17.6% | 45.1% | 45.8% |
| Percentage of production combinations not seen in old train: trajectory share | — | 12.0% | 23.4% | 13.7% |

exp(H) is a descriptor of frequency entropy, not the number of independent strategies or intensity. The effective number of distinct worker sequences for the merged candidates over three days is 54.4, and the production combinations are 13.7. **The movement patterns on the latest day are richer, but the production combinations have not continued to expand**, therefore it is not recommended to simply add BC with higher weight for "newer" data.

The combination of 2 Cattle, 2 Sheep, 12 Melons, 7 Wheat, and 5 Laborers from the old train accounts for **2,148/4,559 = 47.1%**, while the three-day candidates still include **1,102/3,063 = 36.0%**. This combination is used jointly by multiple teachers and may still lead to repeated reinforcement of the same economic trajectory even when distributed evenly by team name. Other candidates include 2 Cattle/3 Sheep/6 Melons, mixed Cattle/Sheep/Goose combinations, multi-Cattle routes, and YMG's new combination of 2 Cattle/3 Sheep/2 Melons/12 Wheat.

![Opening coverage and procurement transaction chart](../outputs/analysis/opening-eda-20260916/opening-coverage.png)

In the figure, each date uses the historical teacher candidate pool; the old baseline uses train. This comparison is only about distribution and cannot be regarded as a causal effect of date after controlling for teacher identity. Novelty refers only to the relative change in coverage compared to the old train and cannot be taken as evidence that the new strategy outperforms the old one.

## Direct Relationship with Wheat Interference

The initial "buy 13, buy 5, sell 13" step frozen for U5952 appears exactly 0 times in the old BC train, and 149 times among the three-day candidates. Therefore, it cannot be said that this fragile sequence was exactly taught by BC. Concentration of economic trajectories and specific transaction sequences after RL need to be handled separately.

In the prior full comparison, the "buy only 5 wheat" strategy proved helpful, with the old train showing only **5/4,559 = 0.11%**, and three-day candidates showing **84/3,063 = 2.74%**. New data has increased exposure to such choices, but standard equal-weighted BC is still easily outperformed by more common opening moves. It should not be treated as a universally mandated rule; the prior T=1 comparison still shows additional losses, see [previous round mechanism and full comparison](wheat_opening_20260916.md).

ymg's trading is also changing; the table below describes replay team names, without inferring submitted versions:

| Source | Number of Trajectories | Initial Wheat Transactions |
|---|---:|---|
| Old BC train | 318 | Buy 30 all, sell 1000 request |
| 9/13 daily | 126 | 62 times buy 30/sell 1000; 64 times buy 50/sell 45 |
| 9/14 daily | 166 | Buy 50 all/sell 45 |
| 9/15 daily | 68 | 36 times buy 50/sell 45; 32 times buy 20/sell 15 then buy 12/sell 12 |

The last case still has a "buy 1 bull" at the end of the first move. Therefore, fixing only the point response to "buy 30" or V45 "buy 70" will miss new market sequences and net positions. These can guide the construction of native valid perturbation families; recording actions cannot pretend to correctly respond to a complete ymg opponent after altering our opening move.

## Recovery demonstration is the primary gap

Filter the first 24 turns of small purchase requests: animal count ≤10, seeds ≤20, and HIRE; require actual fulfillment.
Check whether the actual purchases of the same item in the subsequent 12 turns make up for the shortfall. Additional purchases within the same turn do not count as subsequent.
Exclusions: large buy-max/sell-max are not included in this filter. This rule detects fulfillment gaps, **does not evaluate whether the request was erroneous**, and **does not consider subsequent make-up purchases as valid recovery strategies**.

| Request Category in Three-Day Candidate | Involved Trajectory | Gap Event | Event to Fill Within 12 Steps |
|---|---:|---:|---:|
| Animal | 6 | 6 | 0 |
| Seed | 927 | 1,686 | 109 |
| Laborer | 2 | 23 | 23 |

Events can be repeated within the same trajectory and should not be considered independent samples. In the first 4 steps, there are only 11 such gap events in total, and none of the subsequent 12 steps close these gaps. Only 5 animal cases are in the train set, with an additional 1 in confirmation.
Failure to purchase may indicate an active change of plan; what can be definitively stated is that **there are very few labels available for direct imitation of purchases**.

A real-world example consistent with previous questions is `108349933 / seat 0` (9/13, train):
Unknown Mother-Goose vs. ymg, turn 1 requests to buy 2 sheep, pre-order balance is 988, only 1 sheep is actually executed,
and in the subsequent 12 steps, no action is taken to buy back the missing sheep. This is merely an observed event; cash is an observation explaining execution, not a reward.
Another batch of repeated seed failures may involve deliberate trial purchases, and thus not all failed entries should be mechanically copied with high weight.

Start from BC candidate trajectories, and run different buy-sell sequences, quantities, and positions within the native engine to let the model enter the true state after disturbance, then learn recovery using the complete final WDL outcome. Do not manually reduce cash and reuse the original teacher action labels, nor should "completing the sheep/seeds" itself be made a reward target.

## The Implementation Boundaries of Training Only the Opening

The existing `datasets/demonstrations/loading.py` supports `row_selection`, allowing the selection of an opening trajectory based on real `origins[:, 0] < K`, while maintaining the same world seed and player positions within the same partition. However, the current `learning/pretraining/train.py::initialize` explicitly prohibits reinitializing the BC after RL begins. Therefore, a new independent fine-tuning entry point derived from a frozen checkpoint and an independent BC optimizer must be added, without modifying the main state file or resetting the old pretraining cursor to circumvent the protection.

Preserve the complete 720-frame configuration and 719 decision turns' encoding semantics, then truncate the opening.
The currently verified feasible paths are full-game encoded sequences, consisting only of the prefix required for board placement; a fast encoding interface that computes only the first K steps has not been implemented. Changing episodeSteps to K+1 would alter the feature/contract semantics and cannot serve as a replacement for truncation.

The first 24 steps of 20 sampled games cover 960/960 rows within the worker support range; the first 48 steps are 1,919/1,920.
This is not the full data availability rate. Two opening rows have counts greater than 100, exceeding the current q100 vocabulary; existing truncation records must be retained, and it must be verified whether truncation alters trade outcomes. Such cases cannot be reported as precisely covering all original requests.

The candidate and old BC, after deduplication by episode/seat, have 8,024 trajectories, of which 7,220 belong to train.
This is the **upper bound before full-action support filtering and before route balancing**, and it is not the prepared training set:

| Window | Train candidate rows | Observed/Label/Source/Coverage array estimate | Global 719 pedestrian proportion |
|---|---:|---:|---:|
| 24 steps | 173,280 | 4.39 GiB | 3.34% |
| 48 steps | 346,560 | 8.78 GiB | 6.68% |
| 72 steps | 519,840 | 13.16 GiB | 10.01% |

Each row contains 13,316 float16 features, 276 int16 labels, two int16 source values, and a coverage boolean, totaling 27,189 bytes; excluding optional sample weights, NPY header, and optimizer. The window significantly reduces the number of landing and optimization rows, but this does not imply a proportional decrease in current full replay encoding CPU time.

**The opening sample limits loss inputs but does not automatically constrain the range of parameter impacts.** Currently, the encoder, worker head, market head, and budget module share across time periods; updating only the market head might alter post-trade transactions.

| Trajectory | Implementation and Assurance | Recommended Action |
|---|---|---|
| Update opening data across the network | Existing losses are easily reusable; requires backend reference to KL strategy and full game regression, cannot guarantee unchanged posterior behavior | Conduct minimal control, avoid direct integration with mainline |
| Freeze main model, enable opening branches/adapter by step count | After K, follow original actor; output remains identical under identical full observations; requires new training/export support | Prioritize experimentation |

Even if the K posterior parameters/output paths remain, new openings will produce different inventories, positions, and histories, requiring the original strategy to adapt to these new states. **Posterior equivalence to input does not imply a complete game without rollback**; WDL must be verified after the handoff. Modifying only the market while keeping workers on their old routes might result in purchasing new combinations without proper deployment.

## From "Capable of Imitating Various Openings" to "Genuine Exploration"

The initial observable states of the old train and the three-day candidates each have only two groups (one per seat), with multiple action labels within each group. The conditional action entropy of the initial state is 2.445 / 2.556 nats. Therefore, there is insufficient information in the exact initial observation to tell the model which teacher label is the uniquely correct answer. The future state of the teacher cannot be input into the model.

For the same initial input, a deterministic argmax will still select only one opening; independently warming up each worker and trading slot blindly may lead to mixed strategies without demonstration support. It is recommended to first extract a small number of complete opening families from train that have sufficient samples, valid actions, and coherent execution, impose cross-family teacher constraints to prevent repeated exposure, and assign upper bounds on weights for rare families. Family definitions and weights are fitted only on train data and should not be tuned using confirmation statistics.

To ensure multi-game execution, at the start select a branching condition that can persist until K, under which both workers and the market operate jointly. The selector uses current information or randomness, without relying on the true teacher's future label.

The branching condition is plan preference, yet it must still allow modifications to actions based on actual budget/market conditions—never becoming a rigid script.

This is an extension requiring development and validation; the current model lacks a ready-made full-game opening selector. Subsequent PPO must correctly record selection probabilities and corresponding credit assignment; it cannot simply alter sampling behavior while still computing log-probabilities from the old distribution.

Suggested experiment sequence is:

1. Derive a research branch from the frozen current checkpoint; maintain mainline WDL training, reconstruct and confirm the compact data for K=48.
   Compare against unfine-tuned, equally-weighted opening BC, balanced opening BC following production pathways; further compare against K=24/72.

2. Validate sampling frequencies across opening families, execution rates of complete actions, trade gaps, asset and worker deployments after opening, rather than relying solely on overall BC NLL. Retain existing effective trajectories to avoid full equal-weight training overwhelming rare choices.

3. Evaluate full game trajectories using native V45, remaining active scripts, and historical neural strategies; additionally, use a family of legal wheat-first-move perturbations to cover non-roundtrips, varying quantities, sequences, net positions, and player seat assignments, leaving untrained perturbation combinations uncovered.

4. Compare full WDL across new worlds and player seat pairings, separately reporting greedy versus actual sampling patterns, worst opponent groups, world clustering uncertainty intervals, and newly observed losses. A reduction in BC loss, increased cash, or replication of teacher trajectories is not a qualification for acceptance. When recovery requirements are not met, continue pure WDL learning using real perturbation states, rather than repeating rare failure labels.

The existing seed division maintains train/selection/confirmation = 90/5/5, and no row-wise random splitting is performed.
The three-day EDA conducted this time has been used for method research; future confirmation of the final strength of "the unseen world" should use a separately predetermined new seed.
It is not permissible to package the entire daily data from the research phase into a new blind test set.

## Products and Reproduction

- [Complete statistics](../outputs/analysis/opening-eda-20260916/report.json),
  [Trade/source/space estimation](../outputs/analysis/opening-eda-20260916/comparisons.json),
  [PNG image](../outputs/analysis/opening-eda-20260916/opening-coverage.png) / [SVG image](../outputs/analysis/opening-eda-20260916/opening-coverage.svg).
- [Source list](../outputs/analysis/opening-eda-20260916/sources.json),
  [Extraction protocol](../outputs/analysis/opening-eda-20260916/protocol.json),
  [Game-by-game caching and source code hash](../outputs/analysis/opening-eda-20260916/extraction.json).
- Configuration: [opening_analysis.yaml](../configs/opening_analysis.yaml); Implementation:
  [datasets/openings](../src/kagg_revue/datasets/openings/cli.py).
  All new code is located in src, with no modifications to third_party, model implementation, or training entry points.

```bash
.venv/bin/python -m kagg_revue.datasets.openings.cli
.venv/bin/python -m kagg_revue.datasets.openings.validation
.venv/bin/python -m kagg_revue.datasets.openings.plots
```

On encountering original empty orders in the first round, perform repair and full re-execution; failed attempts and protocol preservation are retained in the results directory under `attempts/0001-null-order-failure`. Verify coverage of newly added code for Ruff, mypy, and two targeted tests; include checks for empty orders, purchases within the same turn, out-of-window purchases, and asset counting involving animals.
