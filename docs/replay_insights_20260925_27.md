Deep Replay Analysis of Five Players since September 25 (2026-09-27)

The most actionable insight is: **Recent strong teams are adopting a three-location, low-tomato operating strategy; the main gap in our latest three-location strategy has now become wheat and goose eggs; the existing six-party BC has mixed in submission versions with significantly different characteristics.** Boey has performed exceptionally well under high wool demand, warranting study of his conditional operating strategy, but high trading volume cannot be directly equated to profit.

The production and revenue variances in this report represent the actual differences between the two teams in the same game. They can identify gaps, but cannot prove that copying a specific procurement quantity will yield similar returns.

**Scope and Verification.** At Beijing Time 2026-09-25 00:00, i.e., UTC 9/24 16:00, freeze the activities and retain the historical log of the five collectors: DSM, M & M & P & Q, DECEM, Boey, and Vadim, deduplicated by episode ID, without win/loss filtering. Among the recorded entries, 3,775 games have their earliest download times falling within the window; 12 of these are catch-up recordings from previous games. The download time for each game is taken as the earliest record across the five logs, not the file modification time.

Latest download record at UTC **9/27 08:19:39**; the last game began at **08:05:21**. Analysis is based on a frozen snapshot; subsequent collector growth will not alter this report. Adhering to the original collection scope, exclude submission 56414341.

All final states in the replay are marked as DONE, but **113215371**'s Fourth Quadrant timed out starting from frame 354, thus is explicitly excluded from the operational analysis. The remaining **3,774 games / 5,434,560 mutual observations** are consistently verified frame-by-frame against the native engine, with actual transaction ledgers and final cash balances fully confirmed and balanced. The environment version is 1.32.7. The environment seeds for these valid games are all distinct.

The following main statistics are based on **3,762 valid games** played within the window, of which **754 games** involve direct matchups between five players and our side. Our participation in these collected matchups does not represent all of our public games. If the date is changed to UTC 9/25 00:00, Boey's victory against DSM is recorded as 39/79, and our victory against DSM is recorded as 3/41; the primary conclusions remain unchanged.

![Match matrix, DSM business plan changes, our latest version cash differential and Boey store condition stratification](../outputs/analysis/replay-insights-20260925-27/overview.png)

**1. Understand players based on the submitted version: the latest mainstream is no longer "buying four plots fully and growing tomatoes."**

DSM has frequently switched between two sets of operational strategies in the past two days, and not all updates have progressed in the same direction:

| DSM Submission | Valid Recent Replay | Buy Fourth Plot | Average Tomato Sales |
| --- | ---: | ---: | ---: |
| 56527482 | 113 | 113/113 | 152 |
| 56541087 | 110 | 110/110 | 149 |
| 56553722 | 112 | 0/112 | 29 |
| 56557996 | 117 | 0/117 | 0 |
| 56575949 | 88 | 88/88 | 149 |
| 56582621 | 124 | 0/124 | 0 |
| 56582776 | 122 | 0/122 | 12 |

Simultaneously, MMPQ's 56544748, 56553720, 56570008, and 56594027 conducted a total of **646 games covering all three locations**; DECEM's four versions starting from 56573934 totaled **369 games covering all three locations**; Vadim's five versions starting from 56574353 totaled **406 games covering all three locations**. In Boey's strong version 56521745, out of 267 games, 264 were conducted across all three locations and 3 were conducted across four locations.

This is not causal evidence that three locations are inherently superior to four locations: the version also alters routes, animal configurations, procurement and sales, as well as encountered opponents and seed conditions. Yet it is sufficient to refute the diagnosis that "the latest strategy should unconditionally supplement SE and tomatoes."

Especially update [9/25's old DSM diagnosis](dsm_duels_20260925.md): at that time, the latest ten games of tomatoes were indeed insufficient; now, within the window, our side has **51 games** against DSM, with average tomato income being **2,705 more**, egg income **2,592 less**, and milk income **2,012 less**. The same gap description must not be carried over across versions.

**2. The main deficiency of the latest three-region strategy is the complete production combination of "feed crops – geese – goose eggs".**

To avoid contamination from old strategies, examine separately the U560, U1064, and U2137 versions of our s91001, i.e., submit **56574712, 56580983, 56593706**. These three versions have **55 games** in the collection library, all from three locations; 54 games against opponents from three locations, and 1 game from four locations.

Our side has **10 wins and 45 losses**, with an average terminal cash difference of **−2,877**; the 95% resampling interval per game is **[−3,745, −1,942]**. U2137 itself has only 5 games, with 1 win, so it cannot be individually characterized based on this data, nor can the non-paired win rates across the three versions be treated as a training progress curve.

The following table shows the averages from 55 individual game pairings. Wheat and fertilizer income have been adjusted by deducting BUY_PRODUCT expenses to avoid exaggerating results due to Boey's large-scale buying and selling. Expenses for seeds, animals, land, and labor are listed separately.

| Source of Cash Difference: Me − Opponent in Same Game | Average per Game |
| --- | ---: |
| Tomatoes | **+5,228** |
| Wheat Net Income | **−3,112** |
| Eggplant | **−2,730** |
| Fertilizer Net Income | −883 |
| Strawberry | −710 |
| Carrot | −479 |
| Wool | −468 |
| Milk | −442 |
| Cucumber | +201 |
| Savings from Expenses on Seeds, Animals, Land, and Labor | +518 |
| Final Cash Difference | **−2,877** |

After rounding, the sum of individual items may differ by 1. The original precise ledger is strictly balanced.

We convert the total field occupancy duration into "plots·days". Compared to our opponents, tomatoes are 112 to 17, wheat is 449 to 521, and geese are 125 to 161; the total sustained quantities of strawberries, cattle, and sheep are nearly equal. The configuration substitutions on limited land are highly evident.

The actual sales of Ge Dan are **205.6 vs. 266.7**, a shortfall of **61.1** per game. Using the symmetric accounting identity, the quantity term in the revenue difference is **−2,729**, and the average price term is only **−1**. Thus, the primary issue is a production shortfall, which cannot be resolved by adjusting the selling point.

Procurement gaps are concentrated in the earlier stages: on Game days 6–8, we average buying 3.55 geese, compared to 4.38 from our opponents; on days 9–11, it is 2.33 versus 2.96. Opponents also average buying 0.15 geese earlier, while we buy 0. Neither side continues to buy geese after day 12. These numbers use the in-game day count starting from 0.

Cash differential is also realized mid-term: on day 12 we averaged a lead of **278**, on day 15 it became **−1,032**, on day 18 it was **−2,194**, and on day 21 it reached **−2,479**. The cash curve combines inflows and outflows and is not itself an asset value; only when combined with the goose's remaining quantity and trading volume does the source of the gap become clear.

A specific example is [113819629: Our U1064 vs. DSM 56582776](https://www.kaggle.com/competitions/kaggriculture/leaderboard?submissionId=56580983&episodeId=113819629). We purchased 1 goose at move steps 223, 225, and 226, and then stopped further purchases; DSM bought 6 geese between moves 204–231. The final goose eggs were **96 to 201**, with revenue **5,021 to 10,510**; globally, we lost **6,887**. This represents a fully traceable end-to-end procurement–production–revenue chain, rather than illegal actions or unsold inventory at the endgame.

My inference is: the current strategy allocates some land and workload to tomatoes, but the accompanying wheat and goose production capacity is insufficient, resulting in no overall advantage in returns. This inference needs to be validated within a closed-loop experiment with identical seeds and opponents, and cannot be directly deduced into "in all games, reduce tomato planting and increase by two geese."

**3. Boey's worth learning might be operational plans tailored to specific requirements.**

First look at head-to-head encounters, rather than the overall win rate across different opponent pools:

| Opponent | DSM Win-Loss | DSM Average Cash Difference |
| --- | ---: | ---: |
| MMPQ | 51–12 | +2,414 |
| DECEM | 67–3 | +5,350 |
| Vadim | 62–8 | +4,535 |
| Our Side, Mixed Version | 48–3 | +5,792 |
| Boey 56521745 | **40–41** | **+567** |

Boey's win rate against DSM is 50.6%, and it cannot be claimed to be overall stronger than DSM; its resampled average cash spread of −567 also crosses 0. However, when grouped by final store composition, the differences are significant:

| Final Gross Store Count in This Game | Boey vs. DSM Win-Loss | Boey Average Cash Difference | Boey Wool Income Difference |
| --- | ---: | ---: | ---: |
| 0 | 7–19 | −2,413 | −653 |
| 1 | 16–18 | −1,336 | +223 |
| ≥2 | **18–3** | **+2,962** | **+2,865** |

At least two wool stores' 21 games: Boey sold 279 pairs of 257; wool inventory stands at 258 pairs of 240 plots·days. Focusing only on the DSM three-location games, this group still shows Boey as **11/13 win**; in the DSM four-location games, it is **7/8 win**, not simply explained by whether the opponent purchases the fourth plot.

This suggests a strategy condition worthy of independent validation: when the revealed demand for wool is sufficiently strong, enhancing capabilities for sheep management, care, harvesting, and delivery may be more valuable than a unified operating approach. The final number of wool shops is merely a post-hoc analysis label and cannot serve as an input that an online strategy can anticipate. Extensive exploratory comparisons across multiple shop configurations have been conducted, but with only 21 games, a 85.7% win rate cannot be considered a standalone test result.

Another key aspect is the **temporal alignment**. In the three-location samples of strong teams facing off, Boey has on average already purchased 2 geese by the first three days; DSM typically does not buy geese in the first three days, but instead concentrates its purchases between days 6–8, buying about 4.69 geese. Boey buys fewer geese later on, while DSM's initial non-purchase of geese represent two distinct, complete strategies. If the model learns the latter half of the former strategy and the former half of the latter strategy, it may suffer from capacity gaps. Currently, this is only a data-supported training risk hypothesis and has not been proven to be the cause of our shortage of geese.

**4. The current BC data indeed contains a weak old version mixed in, and team names are not quality tags.**

| Boey submitted | Recent valid games | Win–loss | Median final cash | Land situation |
| --- | ---: | ---: | ---: | --- |
| 56484772 | 255 | **0–255** | 61,794 | 210 two-location games, 45 three-location games |
| 56521745 | 267 | **179–88** | 107,670 | 264 three-location games, 3 four-location games |

Their opponents differ, so the table above is not a strict version-up experiment; yet the older version cannot be considered an equivalent teacher to the strong version merely because both belong to Boey.

Verify the current frozen dataset used by U2137 for Sixfang BC: out of 3,853 teacher trajectories, **419 come from Boey's old version and 283 from the strong version**. The old version accounts for **10.9%** of the entire dataset and **59.7%** of Boey's trajectories. This refers to trajectory proportions and cannot be directly equated to the gradient proportion for each action category.

We cannot conclude that all 419 trajectories from the old version are draws: across the full dataset, it is **102 wins and 317 losses**; within the current time window, it's 0–255. This further illustrates that time and match phase affect the judgment of "this teacher performs well."

I will change the basic unit for the next round of BC comparison to "submitted version + business plan," examining complete trajectories such as three regions, four regions, early goose farming, and post-complement goose farming, while preserving all original data. Prioritize control experiments involving downweighting or exclusion of Boey's old version, rather than directly filtering out all losing cases; replaying failures of strong strategies remains valuable.

Verification also requires simultaneous examination of recent external win/loss records and key decisions: the quantity and timing of goose purchases on days 6–11, wheat/tomato allocation under three scenarios, and sheep/cattle replenishment after the store's appearance. The overall reduction in NLL from random teacher splitting alone cannot substantiate that these capabilities have improved.

**5. Large buy-sell transaction flows and zero illegal actions are not the metrics we should prioritize the most.**

Boey's 81 games against DSM, with an average revenue of **118,436** per game from selling wheat, leaving **10,654** after deducting purchase costs; DSM's corresponding figures are **16,594 → 11,898**. Boey buys approximately **3,081 units of wheat and 679 units of fertilizer per game**, showing significant buying and subsequent selling behavior.

Fertilizer is similar: Boey's sales revenue is **36,546**, after deducting procurement costs it becomes **12,829**; DSM is **12,025**, with no fertilizer procurement. High cash flow does not necessarily imply additional production or successful arbitrage. Actual buy-sell activities can influence opponents' quotes and feasible procurement options, and one cannot simply conclude that these orders are useless based on net income being close; no post-order-cancellation counterfactual analysis was conducted in this case.

In our 51 games against DSM, our actual illegal unit actions average **0**, while DSM averages approximately **38.7 times per game**, yet we only achieve 3 wins. Rule legality is no longer sufficient to distinguish strength. Even legally making mistakes—such as planting the wrong crops, underbuying animals, or allocating manpower to low-value tasks—still results in losses.

The latest 55 games across three locations show an average warehouse overflow of **5.0 units** per game, with opponents exhibiting **6.1 units** per game; milk sales are **164.3 vs. 164.7**, no longer showing the significant gap seen in the previous mixed version. These findings do not support continuing to attribute the current issue primarily to overflow, illegal moves, or simply insufficient milk supply.

**6. Outside of production combinations, strawberry monetization represents a smaller, independent opportunity.**

In the latest 55 games across three locations, strawberries were sold at **224.9 vs. 224.7**, with nearly identical quantities, yet revenue was approximately **710 less**. Upon breaking down each game, the quantity difference was **−7**, and the difference in average price realization was **−702**.

The average price component includes production time, delivery, order sequence, and price changes caused by bilateral sales, and cannot be entirely labeled as "timing loss." However, it provides a diagnostic objective decoupled from goose capacity: when strawberries enter the maturity and concentrated sales window, examine the delays from harvest to warehouse receipt, from warehouse receipt to sale, and the observable unsold supply visible to competitors. Directly planting more strawberries is not the first step supported by this set of evidence.

**My recommended three experiments, prioritized.**

1. **Teacher version versus operation plan comparison.** Retain the current frozen data, separately apply Boey's old version discounting/exclusion, and conduct BC comparisons for the recent three-location complete plans; fix the training budget, reserve validation based on submission time, and ultimately compare win/loss/draw outcomes using the same opponents and seeds. First verify consistency of data objectives, without prematurely expanding the model or adding more historical trajectories.

2. **Goose procurement and land allocation from day 6 to day 11.** Isolate and diagnose the quantity and timing of BUY_ANIMAL:GOOSE, as well as land usage and labor support for wheat and tomatoes. Evaluation should focus on final WDL (win/draw/loss), net cash, number of goose eggs, and net wheat income; do not rely solely on tomato revenue or individual action accuracy.

3. **Conditional animal plan and strawberry monetization.** Compare Boey-style comprehensive animal management plans when wool demand is high; in games where production is fundamentally balanced, separately optimize strawberry distribution and sale. Online decisions must use only revealed store information and visible production capacity.

The complete v5b includes features such as future supply and demand, income and expenditure of new assets, service pressure, and delivery deadlines, as defined in [Field Definitions](../src/kagg_revue/native/derived_fields.py). These replay scenarios initially highlight issues regarding information utilization and maintaining consistency in operational planning; they have not yet demonstrated the need for additional network structures or a larger feature set.

**Evidence and Reproducibility.**

- [Freeze selection and original source](../outputs/analysis/replay-insights-20260925-27/selection.json), [Acquirer's original snapshot](../outputs/analysis/replay-insights-20260925-27/sources/).
- [Frame-by-frame and cash verification](../outputs/analysis/replay-insights-20260925-27/audit.json), [Detailed game ledger](../outputs/analysis/replay-insights-20260925-27/episodes/), [Seat-level feature analysis](../outputs/analysis/replay-insights-20260925-27/features.jsonl).
- [Player, version, and co-occurrence breakdown](../outputs/analysis/replay-insights-20260925-27/insights.json), [Our latest three-region breakdown](../outputs/analysis/replay-insights-20260925-27/latest-paired.json), [Boey's yarn store layering](../outputs/analysis/replay-insights-20260925-27/boey-yarn-strata.json).
- [Timezone sensitivity and BC data identity](../outputs/analysis/replay-insights-20260925-27/scope-checks.json), [PNG image](../outputs/analysis/replay-insights-20260925-27/overview.png), [SVG image](../outputs/analysis/replay-insights-20260925-27/overview.svg).
- [Analysis configuration](../configs/replay_study.yaml); added Ruff and mypy passes for the new analysis module. Verified using actual replays and revenue identity equations, without simulated strategy test replacement data verification.

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  python -m kagg_revue.evaluation.matchups.study
PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  python -m kagg_revue.evaluation.matchups.insights
PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  python -m kagg_revue.evaluation.matchups.visuals
```

Turns are calculated per independent match, without correction for match selection, submission version correlation, or multi-exploration. The aggregated win rate across different versions is not a randomized controlled experiment; store stratification is descriptive discovery. Original replays and historical training results are preserved; this update only adds analysis code, configuration, reports, and analysis outputs.
