# Redesign of BC Based on Newly Public Game Data

Subsequent implementation has been adjusted according to user supplements: adopting [Budget Feature BC → pure self-play](budget_bc_20260911.md), without incorporating auxiliary supervision, without enforcing opening diversity, and without conducting algorithm ablation. This page retains the data analysis and proposal history.

This round, following user requirements, has re-downloaded and analyzed daily and non-daily games; the previous three-tier scheme is not adopted.
Data collection, existing model phase diagnosis, and two-turn procurement stress testing have been completed; no new BC formulation has been trained yet.

Suggest first validating the **state coverage and execution quality sampling of BC, and explicitly learning procurement budget and post-disturbance adjustments**.
The complete strategy conditions are treated as a separate ablation study. Current evidence simultaneously points to late-stage concentration in BC, further concentration in PPO, and insufficient demonstration of procurement misalignment states; increasing the number of dates or pursuing a greater variety of original actions is insufficient to resolve these issues.

## New Data and Audit Scope

Reacquire official indices with the latest complete date of 2026-09-10, downloading 657 games on that day.
Obtain the leaderboard, public submissions from each team, game matches between submissions, and full replays via the official Kaggle SDK.
Freeze the top 20 teams and the teams at positions 30/40/60/80/100; for the top six, take the two most recent public versions, and for the rest, take the most recent version.
Explicitly include U2748's 56161402 and ymg_aq's 56161578. Final target of 31 submission versions.
For each version, select up to 12 games per seat based on a fixed hash priority; sampling does not consider win/loss outcomes; if insufficient, retain the actual number.
After deduplication, download 693 games, with 0 failures. All limited lists of games returned by the API are fully preserved.

Comparison with original BC's September 7–9 and the newly added September 10 daily:

| Source | Independent Games |
| --- | ---: |
| Original three-day BC source, including original training and held-out data | 1,988 |
| New additions from September 10 daily | 657 |
| Public sampling without overlap with the above four-day daily games | 644 |
| Total | **3,289** |

In 693 publicly downloaded games, 49 games overlap with the above daily entries. Among the additional 644 games, 194 occurred from September 7–10 and did not enter their respective daily records; 443 came from September 11, a date without any daily entries yet; the remaining 7 were from September 6, for which full daily confirmation was not performed this time, so they cannot be considered as having never entered a daily record.

A total of **6,578 bidirectional trajectories**, all 720 frames, both sides marked DONE, with no data exclusions.
The first four action transitions in each game were re-calculated using the native engine; all farm, private, market, and town states for both sides were matched against the official replay.
Only the first four steps were verified, and thus cannot be used to claim full state consistency throughout the game. Original actions and states are aligned with `obs[t] → action[t+1]`, preserving the order and quantity of orders in action fingerprints. The complete action sequence, unit trajectories, market transactions, and quantity structures are separately counted and analyzed.

Publicly supplemented samples are drawn by version and seat, still subject to API list scope, version launch timing, and automatic matching.
Early opponents in new versions may be relatively weak; sample win rates do not constitute a fair assessment of true strength. Team rankings cannot be directly taken as an indicator of the quality of all their submissions. For example, in this SpaTaro instance, the two versions have publicScores of 1905.0/3086.2.

Original source permanently preserved at:

- [New daily source and hash](../data/external/kaggriculture-bc-redesign-20260911/raw/index/manifest.json)
- [Public sampling selection, version identity, and all replay hashes](../data/external/kaggriculture-bc-redesign-20260911/raw/public/manifest.json)
- [Exact data list of the original BC](../outputs/datasets/grounded-v2-20260907-09/manifest.json)
- [Comprehensive analysis report](../outputs/analysis/bc-redesign-20260911/report.json)
- [Trajectory-by-trajectory diagnosis](../outputs/analysis/bc-redesign-20260911/trajectories.jsonl)

## What happened to BC and PPO respectively

Read the four BC epoch endpoints from the same training root and the already-submitted U2748. Fix the initial state of anomaly replay.
Each seat uses the same set of **128 independent sampling seeds**, with CPU FP32, batch one, T=1.
The results for the two seats in the table are identical, and thus they cannot be combined to count as 256 independent initial states.

| Model Stage | Initial Action Types | Most Common Action Share | Original Validation NLL |
| --- | ---: | ---: | ---: |
| BC epoch 1 | 46 | 32.81% | 0.2535 |
| BC epoch 2 | 38 | 29.69% | 0.2188 |
| BC epoch 3 | 23 | 74.22% | 0.2003 |
| BC epoch 4 | 23 | 67.97% | 0.1887 |
| PPO U2748 | 3 | 97.66% | — |

This is a distribution of first-step actions, not of complete openings or win rates. BC's four dominant actions all buy 13 wheat first; the dominant U2748 action adds a trade that buys 36 and sells 36 wheat. Thus, both **concentration and the dominant action changed**.
Among the 3,556 trajectories in the original training split, the complete first-step action of buying 13 wheat accounts for **30.15%**.
Late BC is substantially more concentrated than this empirical frequency, and PPO further reinforces its own dominant action.
Declining NLL does not guarantee calibration of the initial action distribution or opening robustness, nor does this establish epoch 2 as the strongest over complete games.

The current first-step complete action has 51 exact matches in the four-day daily, but there are no exact matches for the first two-step combination.
This does not imply that the combination is necessarily harmful, nor does it support interpreting the current two-step sequence as a simple copy of a demonstrated example.

The same probe also preserves the action distribution from steps 1 and 4 under abnormal states. These are diagnostic records of fixed state trajectories, not states actually visited by each BC strategy during execution.

See [stage probe and checkpoint hash](../outputs/analysis/bc-redesign-20260911/stage-probe.json).

## How do new data change judgments?

The update date does not automatically bring new reliable strategies. Among the full trajectories of both sides in the original three-day sample, the most common first 24-step unit trajectories account for 25.80%; on September 10, this rises to 39.42%; with additional publicly available samples, it reaches 44.95%. These are frequencies within their respective samples; different sampling frameworks cannot directly infer changes across the entire leaderboard. At least, they indicate that full-scale augmentation will still introduce a large amount of repetition.

A fixed initial step can be paired with a conservative budget branch. Majkel1337's 56148003/56156662 each recorded 24 trajectories, all with identical first steps. At step 24, all 48 trajectories retained 2 Cows, 3 Sheep, and 6 Melons, with wheat fields ranging from 7 to 10. This demonstration of "stable primary production assets, with variable quantities of cheaper crops adjusting according to state" is worth studying. Observing correlations alone does not prove the adjustment mechanism; however, it can verify whether the procurement prefix resists known perturbations.

Fix Majkel's first two recorded moves and U2748's first two recorded moves, using the same initial world and ymg's remaining opening actions, only varying ymg's first wheat purchase quantity from 0 to 80 (0 means deleting both buy and sell orders), and test both sides:

| Pre-fix for two-turn procurement | 0–80, total for two seats | Animal procurement not fully completed | When opponent buys 30 |
| --- | ---: | ---: | --- |
| U2748 | 162 condition | 104; both seats have quantity 29–80 | 2 cows, 1 sheep; remaining balance 488 |
| Majkel 56156662 | 162 condition | 0 | 2 cows, 3 sheep; remaining balance 565 |

Majkel first arranges animal procurement, while the timing for planting procurement differs from ours. This indicates that the downloaded data indeed contains alternative prefixes capable of passing this specific early budget stress test. **No full counterfactual games were conducted, and Majkel's callable strategy was not executed; therefore, we cannot claim it is immune to all perturbations or prove an improved win rate.**
See [324 two-turn procurement tests](../outputs/analysis/bc-redesign-20260911/procurement-stress.json).

**Restoration states are extremely rare.** Among the first four steps of the original 3,976 trajectories, the number of animal purchases within the range of 1–10 that were not fully completed was only **2**, both of which occurred in the actual training partition; the new daily addition contributed only 1, and the additional public samples added 3 more.
This represents only a clear indicator of scarcity in the restoration state, not a comprehensive statistical account of all resource shortages or restoration behaviors.
Partial fulfillment might also be intentional requests to "buy as much as possible," and cannot be universally deemed a wrong action.

**Action changes must undergo execution effect verification.** In SpaTaro's 56114097, across 26 trajectories with version identity,
the first 24 unit routes are all distinct; under the same version, same seat, and identical visible history, different actions are observed.
However, among the first four steps involving 406 procurement requests, 221 were rejected by the engine, including requests for unbuyable products.
The volume of these order changes cannot be considered as valid new strategies. Unit route diversity still exists, and thus the entire strategy cannot be invalidated based on this.
Comparing against historical data while excluding remainingOverageTime fails to identify genuine RL implementation.

## Specific Design of the Next BC Round

### 1. Data is measured by version, status, and actual execution

Establish a unified episode/seed index, merge daily and public replays, ensuring both sides remain in the same partition. When the API has clear identity, retain team/submission; versions in daily that cannot be verified are marked as unknown to avoid treating display names as stable strategy versions. Maintain continuous repetition and state coverage metrics, without introducing A/B/C or any other fixed three categories.

The priority for continuous data collection is **the currently missing visible states and successful branch adjustments**: funds crossing procurement thresholds, reduced animal purchases, partial order fulfillment, changes in workforce numbers, inventory shortages, and production-consumption shifts caused by store operations. Maintain the complete context before and after around these events, prioritizing the supplementation of normal versus perturbed comparisons within the same submission and same seat. Retain strong-version defeat and recovery segments; a full victory does not imply that every action should be assigned high weight.

Requests, actual trades, and subsequent states are separately stored. Actual trades serve as the supervision target and sampling basis; invalid requests are not counted toward "effective strategy coverage." The original encoding maps unexpressible requests to action interfaces. The new deduplication and sampling must be based on truly executable actions and state effects, not merely on hashing the original JSON.

### 2. First perform sampling modification with interpretability, keep the current main trunk

Organize data into a 12–24-step fragment with causal context, batching simultaneously from multiple episodes/versions/phases; preserve complete coverage of the base game. The current implementation already includes random shuffling of shard order across epochs and shuffling within shards, but batches are still generated within individual eight-game shards; it must not be claimed that the existing data has no shuffling at all.

Experiment with continuous weights `w = q × clip((n + 1)^(-α)) × e`:

- `n` is the repetition count of "near-visible states + near-execution snippets" within the training zone, with the first comparison set at α = 0 and α = 0.5.
  The number of animals, funding/cost ratio, inventory, workforce, market, and time must participate in the distance calculation; funding values of 988 and 1,054
  Even with identical routes, states cannot be merged into the same supervision state. Precise funding differences near thresholds must be preserved.
- `q` is the quality weight of version/snippet under confidence constraints. In the first round, it can be fixed at 1 to isolate the effect of density sampling;
  in subsequent rounds, quality weights must take into account the actual opponents and sample size of the version, and cannot directly use team leaderboard scores or sample win rates.
- `e` moderately weights execution mismatches and subsequent verified adjustments, with an overall weight cap; it must not repeat failed actions hundreds of times.
  When successful recovery of demonstrations does not occur, such states are retained for stress assessment and future interactive training.

Maintain the basic coverage of opening, daily production, store branch, and closing phases; separately record NLL, effective action rate, and complete game performance for each stage. The first move accounts for only about 1/719 of the entire game, and overall NLL cannot serve as a substitute metric for evaluating the quality of the first move.

### 3. Let the model learn procurement priority and adjustments after execution

Add to the market self-regression decoding features such as a funding/inventory ledger, core procurement cost, remaining budget, and others calculated from current observations and generated orders by our side. Sales of goods are affected by simultaneous actions, so revenue estimates must account for uncertainty; one cannot disguise a price estimate as exact available cash. The priority of sequential learning states depends on the order of purchasing seeds, animals, and labor.

Add small-scale auxiliary supervision: requested quantities versus actual transaction quantities, and the next-state quantities of animals/seeds/workers.
In the next turn, make decisions based on real observations, learning to adjust layout, work assignments, or delay purchases when missing one sheep, rather than continuing to rely on expected assets.

The actual opponent actions within the same turn, precise funds after execution, future store items, and future random outcomes cannot serve as input features.
They may be used for offline verification or subsequent state supervision. All new features and action constraints must be shared between training and deployment.
Simply truncating the number of sheep purchased can only prevent excessive requests and cannot resolve the plan misalignment that arises after a single sheep is missing.

### 4. Treat the complete strategy conditions as independent ablation

If new sampling still mixes multiple long-range play strategies, a strategy condition `z`, training can be added. `π(a_t | current visible state and history, z)`. The initial version can use strategy identity conditions on clearly defined and validated data;
A version may allow internal state branching, and source versions do not have to be treated as distinct strategies. During inference, one expert strategy is selected at the opening phase instead of re-drawing an expert at each step. The condition constrains strategy preferences without overriding actual state feedback.

The unknown version daily cannot forge precise source labels; it can be used for shared representations/unconditional controls or for waiting on reliable training trajectory encoding. If latent variables extracted from future trajectories are used as training labels, the deployment end must have a separate selection mechanism relying solely on current information and cannot access future demonstrations. This architecture has not yet been implemented or validated; therefore, comparisons should be made separately from sampling modifications.

Use it only when retaining a few strategies improves the performance on both normal and perturbed complete games, without aiming for higher action entropy.
Do not use full-action uniform label smoothing to create differences.

### 5. Reliable Interaction Complements and PPO Acceptance

Public replays can only provide actual occurred branches and cannot automatically assign correct expert labels to arbitrarily modified states.
In particular, it is not permissible to modify cash values while retaining the original actions, or to treat a frozen replay suffix as an observation state for experts.
Only native experts capable of calling and verifying recovery capabilities can be used for interactive annotation; perturbed states without reliable labels are used for PPO/search evaluation.
Reuse existing native opponents to generate legitimate initial perturbations, while preserving coverage of normal games.

The U2748 has been observed to be more concentrated than BC4, therefore BC candidates must undergo the same PPO budget and pass confirmation.
The number of historical versions and scripts cannot substitute for actual behavior coverage; simultaneously, comprehensive game evaluations must be conducted to assess whether "different strategy conditions can maintain" and "whether a strategy can recover from perturbation" under the same strategy.

## Suggested Minimum Control Order

| Branch | Data and Method | Questions Addressed |
| --- | --- | --- |
| Baseline | Original three-day, current equal-row weight BC | Original process reference |
| New Data Comparison | New source, current equal-row weight BC | Can simply changing data improve performance? |
| Main Candidate | Same new source, state coverage sampling + budget/execution auxiliary objectives | Does changing the learning objective and sampling improve recovery? |
| Conditional Strategy Ablation | Main candidate with added continuous strategy conditions | Do multiple long-term strategies need explicit distinction? |

During implementation, first compare equal-weighted and density-sampled data from the same new source, then gradually add auxiliary objectives and strategy conditions, avoiding simultaneous changes to multiple factors that would make attribution impossible. Fix the number of effective training decisions, optimization steps, backbone scale, and paired initialization seeds; epochs across different datasets are not equivalent. Save the 1/2/4 epoch-wise progress, but determine the termination point based on complete behavioral validation.

First conduct at least two random root BC mini-control games; expand the number of roots after confirmation. Fully cover game scenarios involving ordinary opponents, independent opponents, procurement threshold perturbations, different stores, and positions on both sides. Report paired differences and intervals for identical environment seeds, without double-counting shared seeds treated as independent samples. Compare the best candidate against the equally weighted baseline using the same PPO game budget.

All previously viewed data are considered part of the method development materials. Final testing of the new method should separately freeze new game/version/perturbation combinations; first partition by episode/seed, and all deduplicated templates, weights, and strategy conditions are fitted using only the training partition. In addition to standard seed holdout, include time/version or strategy holdout to check for clone trajectory leakage.

The primary acceptance criteria are the complete game win rate and the degradation of returns under perturbation; auxiliary metrics include procurement completeness, recovery time, effective production assets, invalid action rate, and concentration of first-step/24-step strategies. The win rate from frozen replay with suffix cannot be used to substitute the win rate against opponents in responsive states.

## Code and Reproduction

Added data collection, analysis, and stress testing at `src/kagg_revue/datasets/coverage/`; stage probes are at `src/kagg_revue/evaluation/temperature/stages.py`. Data collection uses the existing installed Kaggle SDK on `python`, analysis uses project `.venv/bin/python`. Original replay does not execute the participants' code.

```bash
PYTHONPATH=src python -m kagg_revue.datasets.coverage.acquisition
.venv/bin/python -m kagg_revue.datasets.coverage.analysis
.venv/bin/python -m kagg_revue.evaluation.temperature.stages
.venv/bin/python -m kagg_revue.datasets.coverage.stress
```

The collection reuses frozen responses and previously saved replay; to obtain a later snapshot, specify a new `acquisition.raw`.
All new raw data is located in the gitignored `data/external/`, while analysis is stored in `outputs/analysis/bc-redesign-20260911/`.
The current training process, training data configuration, and deployment package remain unchanged. Static analysis results and source code hashes are saved separately in the analysis directory.
