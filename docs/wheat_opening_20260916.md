# 2026-09-16: Ahmed V45 / ymg_aq Wheat Opening Analysis

Both indeed utilize the same category of market round-trip trading. It leverages identical order positions within the same turn and unit price changes, enabling opponents constrained by tight budgets to purchase fewer production assets, while simultaneously protecting itself from the impact of similar trades. The "few sheep" issue in the original model has causal prefix evidence; the current frozen model has preserved the animals, yet still exhibits budget clearly insufficient at step 20 while continuing to procure. Subsequent 160 full-game comparisons confirm that modifying the initial step can reverse part of the loss, but the sampling strategy still introduces new losses, warranting further research into opening exploration and post-disturbance adjustments. The WDL reward transfer has been completed separately, see [Implementation and Formal Continuation Validation](wdl_20260916.md).

This analysis did not deploy any opening patches, and the official opponent distribution was not altered as a result of this analysis.

## Actual Settlement Mechanism

Under standard rules, V45's first turn is `BUY_PRODUCT WHEAT 70`, `SELL WHEAT 70`.
V44 originally bought 5, bought 10, and sold up to 60; in practice, it could only sell wheat it had actually purchased.
The V45 source code comment explains that this change originated from the impact of 78-unit round-trip trades by other opponents on its original opening position, causing it to miss purchasing one watermelon seed. It simultaneously serves to protect its own opening and disrupt opponents' openings.
Source differences are saved in
[V45–V44 Source Code Differences](../data/external/kaggriculture-notebook-survey-20260916/ahmed_v45-vs-ahmed_v44.diff).

The actual rule is: the k-th order from each side is aligned; for each unit, both parties simultaneously submit bids, then settle simultaneously, and then proceed to the next unit. For product purchases, the bid is based on the dynamic price after inventory is reduced by one unit; for sales, the bid is based on the current inventory level. Therefore, in a static market, the net gain from buying and selling is zero, and when both sides trade 70 units, the net gain remains zero.
When the opponent places a buy order in the second transaction, the counterparty places a sell order in the second transaction, thereby altering the settlement amounts between both sides.
The warehouse capacity and funding limits are enforced based on actual settlement outcomes; requesting 100 units does not guarantee that 100 units will be executed.

In this native settlement example, both parties start with 3,000 yuan and have no inventory:

| V45 opponent first turn | V45 cash after settlement | opponent cash after settlement | opponent remaining wheat |
| --- | ---: | ---: | ---: |
| No trade | 3,000 | 3,000 | 0 |
| Buy 70, sell 70 | 3,000 | 3,000 | 0 |
| V44 split buy/sell | 3,061 | 2,939 | 0 |
| U5629/U5952 buy 13, buy 5, sell 13 | 3,038 | 2,829 | 5 |

The final entry is: when the opponent does not engage in round-trip transactions, my side still has 5 wheat but cash of 2,867; thus, V45 causes my side to lose 38 yuan and gains 38 yuan in this first turn. These are single-turn settlement results, not the final game outcome (WDL). Rule implementation is available in [local native settlement](../src/kagg_revue/native/csrc/market.cpp) and [official interpreter](https://raw.githubusercontent.com/Kaggle/kaggle-environments/master/kaggle_environments/envs/kaggriculture/kaggriculture.py).

## ymg_aq: Confirmed historical trigger points

The saved submission `56161578` covers three public games against our U2748/`56161402`, with `107806761`, `107807755`, and `107810794`—all of which we lost, all in second seat.
This supports the existence of obvious weaknesses in the prior submission, and thus cannot be used to infer the overall win rate of all historical or current submissions against ymg_aq.

Opponent's first turn buys 30 wheat and sells up to 1,000; actually sells 30.
Fix my side's first two requests, and only remove opponent's two transactions:

| Condition | Our cash before buying sheep | Sheep actually purchased when requesting two |
| --- | ---: | ---: |
| Original ymg_aq trades | 988 | 1 sheep |
| Remove these two trades | 1,054 | 2 sheep |

This has been re-verified using the official 1.32.7 interpreter. Here, we only demonstrate that transactions cause procurement mismatch and initial fork, without proving that deleting transactions can reverse the overall game outcome.
In the old quantity scan, request volumes from 29 to 80 all trigger the "few sheep" phenomenon, and switching T=0 does not resolve the funding threshold issue.
See [original two-turn analysis](temperature_u2748_20260911.md).

The subsequent unit control and public scripts of ymg_aq are not equivalent; one cannot substitute V45's win rate for an evaluation of the real ymg_aq version, nor can a fixed replay suffix be treated as an opponent that can observe new states.

## Newly Added: The current model still has procurement branching

Freeze submission model **s68001/U5629** (T=0 and T=1) and switch WDL prior to **U5952** (T=0).
A fixed world with two seats, comprising **88 24-step prefixes**: two greedy models respectively cover
request volume 0/13/30/70/78/100; submission at T=1 covers 8 paired sampling seeds and request volume 0/30/70/100.
Only replace the wheat round-trip volume in the first turn of V45; subsequent decisions are made by the native V45 and neural model based on actual observations.

The first-day results are identical for two greedy models with dual seats; at T=1, the corresponding conditions also yield the same asset allocation:

| Opponent round-trip request volume | Cash before Step 20 buying wheat seeds | Volume of requests for 2 grains | Initial assets |
| --- | ---: | ---: | --- |
| 0 | 43 | 2 | 2 cows, 2 sheep, 12 melons, 7 wheat |
| 13 | 25 | 2 | 2 cows, 2 sheep, 12 melons, 7 wheat |
| 30 | 15 | 1 | 2 cows, 2 sheep, 12 melons, 6 wheat |
| 70 | 5 | 0 | 2 cows, 2 sheep, 12 melons, 5 wheat |
| 78 / 100 | 0 | 0 | 2 cows, 2 sheep, 12 melons, 5 wheat |

Previously, the model allocated a large amount of melon seeds before animals, which easily led to a shortage of sheep; in this model, we first ensure two oxen and two sheep, but the remaining funds deficit persists into the first period's later stages. At step 17, two melon seeds are purchased; at step 19, one wheat seed is bought; at step 20, two more wheat seeds are requested, followed by under-sowing two plots of land.

Special inspection of the budget module input at step 20: real cash **5**, restored budget cash **5.00083**, wheat seed quote **10.00214**, and clearly defined affordable quantity **0**.
Thus, this step is not due to floating-point errors or unobserved opponent orders from the current turn.
The current model has access to budget information but fails to reliably adjust its actions based on it.
On the other hand, the initial budget estimation still does not fully incorporate the price impact of its own large order or the opponent's trading activity, leaving room for improvement.

These probes all have short prefixes, and one cannot claim that a shortage of two wheat units caused all the current losses based on this.
Records are available at [Complete Actions and Trades](../outputs/analysis/wheat-opening-20260916/report.json),
[Budget Inputs](../outputs/analysis/wheat-opening-20260916/budget-boundary.json).
Of the 16 prefixes plus two historical prefixes, 776 dual-seat observations have been confirmed consistent by the official interpreter, see
[Official Replay](../outputs/analysis/wheat-opening-20260916/official-replay.json).

## A modification worth prioritizing for complete game validation

In the original first move `buy 13, buy 5, sell 13` of U5952, the final purpose inventory is 5 wheat.
Modify it to a single transaction `buy 5`, and thereafter let the original neural model respond to actual observations.

For the V45 70-unit round trip, our initial wheat holding remained at 5, but cash increased from 2,829 to 2,864;
the opponent's first round trip profit decreased from 38 to 3. For the request of 13/30/70/78/100 units, single purchase at 5 units, the initial cash is 2,864; for non-trading opponents, it is 2,867, unchanged from the original opening.

Further execute **70/100 two-request volume × dual seats, totaling four 24-step prefixes**:
Fully retain **2 Cattle, 2 Sheep, 12 Melons, 7 Wheat**, remaining balance 20; no seed, animal, or labor procurement shortages occurred;
192 dual-seat observations align with the official interpreter.
See [Single-turn comparison](../outputs/analysis/wheat-opening-20260916/opening-candidates.json) and
[Neural model closed-loop prefix](../outputs/analysis/wheat-opening-20260916/single-feed-reactive.json).

This group of short prefixes supports treating "simplified first-step round-trip trading" as a priority candidate. The complete WDL screening carried out subsequently is presented in the following section;
No modifications to the official strategy or submission package were made.

## Complete WDL Matchup: Valid, but cannot be used to fix another opening

Before observing the results, fix **8 new worlds 1960916200–1960916207, both sides' seats**, and freeze U5952.
For each world, compare four combinations: original V45 / remove V45's first-step round-trip, and original opening for me / conditional replacement.
For single buy 5. Replacement only takes effect when the original request is exactly buy 13, buy 5, or sell 13; thereafter, both sides respond based on the actual state.
First run greedy, then on the same worlds supplement T=1, with root sampling at `2 * world + seat`, resetting and pairing each game.
A total of 128 games of Ahmed comparison, plus another 32 games of greedy regression from four other active scripts, each running on 2 worlds with two seats and two strategies.

| Opponent / My First Move | T=0 Win / Draw / Loss | T=1 Win / Draw / Loss |
| --- | ---: | ---: |
| Original V45 / Original Opening | 14 / 0 / 2 | 13 / 0 / 3 |
| Original V45 / Buy 5 Single | 16 / 0 / 0 | 15 / 0 / 1 |
| Remove V45 Round Trip / Original Opening | 16 / 0 / 0 | 15 / 0 / 1 |
| Remove V45 Round Trip / Buy 5 Single | 16 / 0 / 0 | 15 / 0 / 1 |

The other four scripts have two schemes each of 4 / 0 / 0; this is a small greedy regression panel, not fully covered.
Other scripts have T=1. All results pertain to the U5952 before the switch to WDL and cannot be interpreted as gains from continued WDL training.
See [complete greedy results](../outputs/analysis/wheat-opening-20260916/full-wdl/report.json),
[complete T=1 results](../outputs/analysis/wheat-opening-20260916/full-wdl-t1/report.json),
[reproducible configuration](../configs/evaluation_trades.yaml).

The two reversals in greedy were both from World 1960916206: originally, our side had **94,754** and the opponent had **94,915**. After buying 5 units alone, our side ended up with **94,748** and the opponent with **89,545**. Our balance slightly decreased, yet the outcome shifted from loss to win.
The initial move altered the subsequent production and trading trajectories of both sides. One cannot judge the result solely by our balance or the initial asset amount on day one.

In T=1, single purchase of 5 **fixes three games while adding one failure**, resulting in a net gain of two wins. The newly added failure is
1960916202 / seat 0; removing the opponent's first-move transaction also fails, indicating that the current subsequent sampling strategy still has weaknesses.
Therefore, new games cannot be considered as having already undergone optimization and can be treated as fixed patches.
The paired score improvement by world clustering shows a 95% bootstrap interval: greedy is **[0, 37.5]** points, and T=1 is **[−12.5, 43.75]** points; the sample size is insufficient to prove generalization improvement, let alone approaching 100%.

**24 full-turn replays, 34,512 dual-seat observations** verified through the official 1.32.7 interpreter, including original losses, repaired, and newly added counterfactual losses. After removing opponent back-and-forth actions, all subsequent actions, saved observations, and terminal liquidation cash for both our strategies are identical across all **32 pairs** of greedy / T=1 controls.
See [Basic Replay](../outputs/analysis/wheat-opening-20260916/full-wdl/official-replay.json),
[Greedy Loss Replay](../outputs/analysis/wheat-opening-20260916/full-wdl/official-loss-counterfactuals.json),
[Sampling Inversion Replay](../outputs/analysis/wheat-opening-20260916/full-wdl-t1/official-replay.json),
[Negative Control](../outputs/analysis/wheat-opening-20260916/negative-controls.json).

## Initial exploration is indeed insufficient

Compute the actual greedy prefix conditional probabilities for U5952, world 1960916200 / seat 0:

- When the initial unit action is fixed as greedy, the probability of completing three original market requests is **99.19365%**.
- The conditional probability of changing the first wheat quantity to 5 is **0.17484%**, but the complete "buy 5 then stop" sequence is only **0.00027253%**. The difficulty of altering a single quantity is significantly higher than finding a continuous alternative trading sequence.
- When cash remains at 5 by the 20th step, the probability of placing a market sequence to buy two wheat seeds is **99.65096%**.

These are probabilities under specified states and fixed-unit actions, not statistical values from the entire training distribution.
They are consistent with the identical initial asset portfolio generated by multiple T=1 sampling seeds, indicating that effective opening alternatives are difficult to naturally sample. See [Probability and Entropy Diagnosis](../outputs/analysis/wheat-opening-20260916/opening-probabilities.json).

Fixation occurs within the learned action distribution. The current `grounded-v2` does not have a fixed timetable of actions; market actions are fully supported. For `time_prior=false`, RL applies to `bc_weight=0`. The configured `market_stop_probability=0.98` is used solely for random initialization and cannot be modified to alter already-trained models.

The current entropy_weight is set at **1e−4**, PPO clip at **0.1**, target_kl at **0.01**, and actor LR at **7.5e−6**. These values are current and have not yet been validated through ablation studies to determine whether any single parameter causes insufficient exploration.

Existing results support treating "lack of consistent early-game exploration" as a key unresolved issue; its impact on the final model's performance ceiling still requires validation through training branches and independent WDL analysis.

## Follow-up Processing Order

1. **Prioritize independent exploration training branches for initial setup.** Start from the same current WDL checkpoint and retain the baseline. Increase exploration intensity during the first day of a small number of games, then restore normal sampling. First, separately compare temperature or opening entropy settings, without simultaneously modifying learning rate, opponent pool composition, or other controls. Exploration should cover procurement combinations, action sequences, and coherent subsequent actions. Rewards remain limited to terminal WDL only, without adding monetary amounts, asset quantities, or novelty rewards. If temperature is changed over stages or per game, behavior temperature and corresponding log probabilities must be preserved row by row, and the PPO ratio must use a consistent distribution. Currently, the temperature field in a single rollout is scalar and cannot be modified only at the sampling stage.

2. **Cover the trading family within the existing native script training budget.** Modify legal request volumes, order positions, splitting strategies, buy/sell timing, and combinations with procurement. Continue using native controllers that read actual state; retain unseen combinations as out-of-sample evaluation. V45 has already been heavily sampled by PFSP; repeating a fixed 70-unit opening does not constitute coverage of the trading family.

3. **Train recovery after procurement failure.** Continue WDL training from legitimate perturbations that naturally lead to states such as cash shortage, insufficient seed purchases, or changed workforce size. Learn how to replenish, adjust seeding, and reassign work. Only prohibit over-purchasing that cannot recover previously missing assets. When no reliable recovery teacher is available, do not use original replay actions as labels for modified state transitions.

4. **Improve budget representation based on actual shortages.** Incorporate the impact of unit prices on own budget and funding ranges under different opponent trading assumptions, while preserving key procurement margins. Do not feed into the model unknown opponent actions or future states within the same game. However, there is already evidence of "correct budget, non-responsive decisions," so feature engineering cannot replace perturbed state training.

5. **Select exploration branches based on complete WDL.** Use new worlds, distinct player seats, and independent sampling roots to cover current scripts, trading perturbations, and historical neural opponents. Simultaneously evaluate the weakest opponent group and average performance. Early entropy levels, opening combination coverage, and procurement recovery rates are diagnostic tools and cannot replace WDL. The above 8 worlds have already been used in research; future formal confirmations should use previously unused worlds.

In previous complete game matchups of s69001/U1708 with independent pairing, our side won against V42/V44 with 28/32, and against V45 with 21/32. The version difference of V45 is sufficient to alter the outcome. However, our average cash also increased, with V45 showing a greater rise—thus its advantage cannot be fully attributed to reduced gains for our side.

Additionally, V45 retains the mid-to-late game trajectory of V44, including early exit of control. After stable opening phases, we must still monitor the timing of sales and market competition; we cannot attribute all remaining losses solely to the initial wheat move.

See [Previous Complete Game Study](public_notebook_survey_20260916.md).
