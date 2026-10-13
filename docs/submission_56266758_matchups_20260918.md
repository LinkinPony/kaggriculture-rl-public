# 56266758 Real Game Analysis against ymg_aq, M & M & P & Q

**Conclusion: Insufficient disturbance resistance during initial procurement is a definite defect of ymg_aq; the larger revenue gap shared by both groups stems from delayed capacity establishment, suboptimal strawberry launch timing, and insufficient transition production in the mid-to-late stages.** Our cucumber revenue is superior, but it is insufficient to offset the revenue shortfall from strawberries, milk, and other products. No losses were found to be caused by over-time or illegal unit actions.
The following presents the game replay facts and ledger breakdown; except for explicitly noted initial transaction experiments, these are not to be interpreted as independent causal gains.

## Samples, Submissions, and Verification

2026-09-18, by the authenticated Kaggle SDK, freeze all **289 games** visible in this submission,
consisting of **288 public competitions and 1 internal validation match between the same submission**.
Of the two designated teams, **17 games were fully downloaded and fully analyzed, with no sampling based on win/loss outcomes**.
These games occurred in 9/16–17; the most recent game in the 289-game list was created at 9/18 01:08 UTC.
This is the available API sample, and it does not claim to be a complete or permanent record, nor does it represent an exact estimate of true win rate.

| Opponent | Win / Draw / Loss | Sample Win Rate | Our Average Final Cash | Opponent Average Final Cash | Our Average Cash Difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| ymg_aq | 2 / 0 / 8 | 20.0% | 110,522.6 | 115,194.1 | -4,671.5 |
| M & M & P & Q | 0 / 0 / 7 | 0.0% | 95,277.3 | 106,190.9 | -10,913.6 |

Excluding self-verification against oneself, the overall public match record is **217 wins / 71 losses, 75.3%**, indicating that weaknesses are concentrated against specific strong opponents.
ymg has two seats each with 5 games: our first seat achieved 2 wins, the second seat 0 wins; in the M group, each seat played 3 and 4 games respectively, with no wins in either.
The sample size is insufficient to isolate seat effects, but procurement gaps are identical across both seats in ymg, and M's losses also cover both seats.

Split according to the opponent's exact version, avoiding equating team names with strategies:

| Opponent Version | Team | Our Wins / Losses | Our Average Cash Difference |
| --- | --- | ---: | ---: |
| 56265958 | ymg_aq | 1 / 6 | −5,384.4 |
| 56265944 | ymg_aq | 1 / 2 | −3,008.0 |
| 56254996 | M & M & P & Q | 0 / 2 | −3,741.5 |
| 56281630 | M & M & P & Q | 0 / 5 | −13,782.4 |

56266758 is **s68001 / U5629 / T=0**, a prior submission trained for 720,512 games after 4 epochs BC, and is not the currently training agronomy-v4 model. Identity is defined by the [CURRENT_MAINLINE commit record](CURRENT_MAINLINE.md#section-b9e953ea7c6f) and its exact package.

All 17 games were run in the official environment **1.32.7** at 720 frames; for each seat, the first 719 frames were all `ACTIVE`, and terminal liquidation was all `DONE`. The native engine replayed the actual bilateral actions from the original seed, with **24,480 observations matching frame-by-frame**, including the insertion order of private inventories. All 34 cash ledgers satisfied the condition: "initial cash + total cash change from trades = final cash = API reward". All of our game requests matched the actual legal actions; warehouse overflow occurred only sporadically. This supports focusing the analysis on economic decisions, and does not allow us to claim that all potential model implementation issues have been ruled out.

## 1. ymg's first trade indeed disrupted our budget

In 10 ymg games, the initial moves are consistently: buy 60 wheat, sell up to 1,000 (actually sell 60), hire labor, and buy animals.
Our side consistently buys 13, then buys 5, sells 13, leaving 5 wheat.

In [109725351](https://www.kaggle.com/competitions/kaggriculture/episodes/109725351)
Fix the recorded actions of both parties subsequently, and only remove the two wheat transactions from the opponent's first turn, to get:

| Condition | Cash after our first move | Cash before buying seeds at t=20 | Actual quantity filled when requesting 2 wheat seeds |
| --- | ---: | ---: | ---: |
| Original ymg trade | 2,829 | 7 | 0 |
| Remove opponent's first move round trip | 2,867 | 45 | 2 |

**The first move caused a loss of 38 RMB for our side, followed by crossing the seed procurement threshold.** All real 10 games occurred at t=20.
Still requesting to buy 2 grains, with 0 completed; on the first day there were only **5 units of wheat**, while in 7 games against M, each had **7 units**.
Both oxen and sheep were fully purchased; the previous U2748 conclusion of "buying one less sheep" cannot be applied.

This experiment only proves the causality between settlement and procurement under a fixed request prefix, without allowing the opponent's response to alter the state; therefore, it is not a proof that winning the entire game can be achieved by simply deleting a transaction. Among the 10 games, there are still 2 instances where victory was achieved under the same low wheat condition; in 7 of the M's opening procurement scenarios, the full procurement process was still met with losses, indicating this is not the sole cause of defeat.

See [fixed prefix experiment](../outputs/analysis/submission-56266758-matchups-20260918/opening-fixed-prefix-counterfactual.json).

## 2. Two groups' shared primary gap: Delayed formation of sustained production capacity

Average actual on-balance assets after 10 days (t=240, beginning of day 11):

| Opponent Group | Strawberry: Self / Opponent | Cow: Self / Opponent | Watermelon: Self / Opponent |
| --- | ---: | ---: | ---: |
| ymg_aq | 15.3 / 26.3 | 5.2 / 7.6 | 12.4 / 13.0 |
| M & M & P & Q | 17.4 / 26.7 | 6.7 / 8.9 | 12.7 / 8.6 |

This gap is not something that only emerges at terminal liquidation: at t=144, strawberry counts were already at **3.8 / 9.1** and **4.0 / 7.6**. On day one, our side heavily positioned 12 melons, while ymg held 3 oxen, 3 sheep, 18 wheat, and 1 melon—clearly different rhythms in establishing sustained income. It wasn't until t=360 that both sides' strawberry counts came close; early production cycles lost cannot be automatically recovered simply by later adding the same number of plants.

Our side indeed has gained an advantage in the fruit sales: additional fruit sales revenue of **4,632.9 / 4,850.4 RMB** from ymg / M.
However, the revenue gap for the following ongoing products is significantly larger:

| Average revenue difference per game (our side minus opponent) | Against ymg_aq | Against M & M & P & Q |
| --- | ---: | ---: |
| Strawberry | −6,564.6 | −8,187.4 |
| Milk | −4,891.8 | −3,463.3 |
| Wool | −846.4 | −4,882.4 |
| Carrot | −1,471.7 | −3,721.1 |
| Melon | +4,632.9 | +4,850.4 |
| Egg | −342.4 | +5,091.0 |
| Tomato | +2,094.4 | +1,094.6 |

The table above is not a complete profit and loss statement, nor does it represent a causal amount that can be recovered by simply switching a route.

In the full ledger, our total revenue from ymg is understated by **11,423.9**, but our expenses are also understated by **6,752.4**, resulting in a net difference of **−4,671.5**; for M, total revenue is understated by **10,988.3**, while expenses are understated by only **74.7**, resulting in a net difference of **−10,913.6**. The issue with M is particularly close to "spending the same amount, but with significantly lower output and monetization efficiency."

## 3. Strawberries produce less and sell at lower prices; milk cannot be generally attributed to rush sales

The average transaction price is calculated by dividing the total sales revenue by the total transaction volume:

| Opponent Group and Product | Our Sales per Game | Opponent Sales per Game | Our Average Transaction Price | Opponent Average Transaction Price |
| --- | ---: | ---: | ---: | ---: |
| ymg: strawberry | 217.0 | 236.2 | 144.3 | 160.3 |
| ymg: milk | 176.4 | 233.3 | 129.1 | 118.5 |
| M: strawberry | 223.7 | 252.4 | 130.5 | 148.1 |
| M: milk | 184.3 | 215.6 | 99.4 | 101.0 |
| M: wool | 100.3 | 116.1 | 115.9 | 142.1 |

The strawberry gap exists simultaneously in quantity and price. Building capacity earlier allows earlier entry into the high-price sales window, so the average price difference cannot be entirely attributed to the market order module; the current replay also does not prove that the opponent is deliberately targeting us for rush sales. YMG's milk average price is actually lower than ours, primarily achieving higher revenue by selling approximately 57 units more.

Extreme example 109725351: Our side has 257 units / 28,475 yuan of strawberry, and ymg has 273 units / 42,243 yuan. The quantity difference is only 16, with a revenue difference of 13,768; the average price is approximately 111 / 155.
In this game at t=600, the strawberry market price had dropped to 28. We still hold 21 strawberry plants and 4 carrot plants, while the opponent holds 7 strawberry plants and 14 carrot plants. This indicates direct evidence of the opponent exiting surplus products early, but the entire revenue gap cannot be attributed solely to the asset composition at this moment.

## 4. For the strong version of M, the gap between production transfer and labor allocation becomes more apparent

[109802918](https://www.kaggle.com/competitions/kaggriculture/episodes/109802918)
There are **3 wool shops**. At t=480, our side / opponent has 4 / 6 sheep; at t=600, it is **4 / 10 sheep**.
At that time, wool prices have recovered to **233**, while milk and strawberries are only **3 / 5**.
The opponent expanded wool production capacity in response to increased wool demand; our sheep herd has not kept up.

Final wool: Our side has **95 units / 16,416 yuan**, opponent has **151 units / 31,165 yuan**,
a difference of **14,749**; strawberries are short by **11,918**. Our side earns **12,620** from eggs, while the opponent has no egg income.
These advantages are still insufficient to close the gap, resulting in a final score of **82,003 : 98,971**.

Labor utilization also warrants study: the proportion of PASS actions during our units' turns in the ymg/M group was **13.7% / 12.3%**, while that of opponents was **3.4% / 4.3%**. Our average labor expenditure per M was **4,743.6**, compared to opponents' **3,834.1**. This is consistent with the observation that "hiring more workers results in slower production establishment." However, PASS can reasonably represent waiting, and walking does not equate to productive work. Not all idle time should be treated as recoverable profit, and the training reward for PASS should not be penalized.

## 5. Mid-game cash lead is prone to misjudgment; there is still a substantial gap on the final day

For ymg, at t=360 our average lead is **12,305**, and at t=480 we have an average lag of **7,110**.
The former includes our early sales of watermelons; opponents still had watermelons to harvest and other productive assets at that time.
The cash balance at that time cannot determine the final outcome, nor can the entire cash trajectory be treated as "losing existing profits."

[109848550](https://www.kaggle.com/competitions/kaggriculture/episodes/109848550)
On the final day, our side started at **122,531 : 115,395**, leading by **7,136**; at the end, the score became **128,961 : 132,043**, falling behind by **3,082**. Our side had a net increase of **6,430**, while the opponent had a net increase of **16,648**.
At the beginning of the day, the opponent had 21 tomato units, while we had only 2; the opponent's warehouse also contained 26 tomatoes, 12 melons, and 5 milk units.
The opponent unloaded and sold large quantities of products in the last two steps; our inventory was already sold out, and we passed on all remaining steps.
The key fact here is that the opponent had more assets available for liquidation; it is incorrect to misdiagnose this as our side forgetting to sell warehouse inventory.

![Turn-by-turn cash differential and product revenue breakdown](../outputs/analysis/submission-56266758-matchups-20260918/matchups.png)

## Suggestions for Future Work

1. **Prioritize resolving procurement shortfalls with confirmed reproducibility**: Initial transaction budgeting, rescheduling plans after seed transactions, and recovery of replenishment orders.
   Validate using a complete closed-loop game simulation—do not limit validation to simply observing two additional wheat plots on the first day.

2. **Direct primary research efforts toward capacity timing and transition production**: Establish sustained strawberry/animal production earlier, integrating store capacity, opponent capacity, and market inventory to determine whether to continue production or switch categories. Focus on post-mortem analysis of the period t=144–600.

3. **Evaluate the interplay between labor allocation and market timing**: Verify whether fertilization, harvesting, transportation, and sales were timely prior to high-price windows. Do not pursue reduced PASS actions or increased output in isolation.

4. **Conduct targeted assessments using precise versions of two teams under similar economic contexts**, reporting by version, store scenario, and both team positions.
   Public replays can serve as behavioral evidence, but fixed suffixes cannot be used to falsely represent responses to a real-time evolving opponent.
   Training and selection continue to be based solely on complete terminal outcomes (WDL), without adding cash rewards or intermediate action incentives.

Same-weight T=1 56266899 current visible samples, show ymg as **2/4 win**, and against M as **0/1 win**.
This is not a same-world pairing test at T=0, and the sample size is too small to claim that the temperature increase has resolved the issue.
This analysis is conducted only; no changes to training, rewards, submission package, or online strategy have been made.

## Data and Reproduction

- [Original API List](../data/external/kaggle-submission-56266758/raw/submission-episodes-20260918.json)
  and the corresponding directory `.source.json` stores query time, requests, and hashes.
- [17-game download list](../data/external/kaggle-submission-56266758/raw/manifest.json), each game's original
  gzip file and `.source.json` are permanently saved in `data/external/`, including official URLs and content hashes.
- [Per-game summary](../outputs/analysis/submission-56266758-matchups-20260918/summary.json),
  [Group ledger](../outputs/analysis/submission-56266758-matchups-20260918/aggregates.json),
  [Frame-by-frame state verification](../outputs/analysis/submission-56266758-matchups-20260918/frame-statuses.json).
  The directory `episode-*.json` contains each actual trade, complete cash sequence, daily assets, procurement gaps, and unit action diagnostics.
- [Analysis implementation](../src/kagg_revue/evaluation/matchups/extraction.py),
  [Hydra configuration](../configs/matchup_analysis.yaml). Running
  `.venv/bin/python -m kagg_revue.evaluation.matchups.cli` re-calculates and generates charts.
  New modules are verified using Ruff and mypy; all unit tests are based on the above actual replays, with no simulated implementation tests added.

| Episode | Opponent Version | My Cash | Opponent Cash | My Result |
| --- | ---: | ---: | ---: | --- |
| 110026691 | 56265958 | 118395 | 121784 | Loss |
| 109978530 | 56265944 | 153930 | 158234 | Loss |
| 109893101 | 56265958 | 78469 | 76504 | Win |
| 109872743 | 56265958 | 95164 | 100762 | Loss |
| 109872761 | 56265958 | 103422 | 104762 | Loss |
| 109839941 | 56265958 | 128016 | 134856 | Loss |
| 109835616 | 56265944 | 98100 | 97363 | Win |
| 109798401 | 56265944 | 111354 | 116811 | Loss |
| 109725351 | 56265958 | 93919 | 111265 | Loss |
| 109676271 | 56265958 | 124457 | 129600 | Loss |
| 109848550 | 56254996 | 128961 | 132043 | Loss |
| 109835621 | 56281630 | 84776 | 92947 | Loss |
| 109802918 | 56281630 | 82003 | 98971 | Loss |
| 109789754 | 56281630 | 70412 | 87941 | Loss |
| 109783336 | 56281630 | 90404 | 98746 | Loss |
| 109780145 | 56281630 | 96484 | 114386 | Loss |
| 109682633 | 56254996 | 113901 | 118302 | Loss |
