# 2026-09-15 Public notebook update survey

**Found a successor version with measurable improvements: Ahmed V43, recommended as a minor upgrade candidate for V42.**
It primarily recovers revenue losses caused by warehouse overflow at the end of the day, offering an advantage over the current V42; it provides only minor win increments over other current scripts. This investigation and competition have been completed, but native integration or formal training modifications have not yet been implemented.

## Benchmark, Sources, and Scope

The baseline is [current mainline](CURRENT_MAINLINE.md) and officially running.
`budget-q100-top10-2d-20260913-s68001/resolved-config.json`'s five scripts:
`ahmed_v42`, `metacounter_r1`, `shop_router_0913`,
`rayk_v38_low_pressure`, `farming_v4_0914`.
All five sources have been re-downloaded, and the extracted `main.py` matches the training frozen hash exactly.
The page runtime for V42 and Farming has changed, but the source code remains unchanged.

Starting from 03:50 UTC, query via Kaggle CLI for `dateRun` and `scoreDescending`, two pages each with 100 entries, resulting in **324 distinct notebook references**; additionally, query eight upstream authors, downloading **16 notebook/script references**, including five active sources.
These lists are not exhaustive enumerations and do not return specific competition scores. The ordering cannot be interpreted as current leaderboard strength.

The original is stored in [Source and Hash List](../data/external/kaggriculture-notebook-survey-20260915/source-inventory.json),
the competition uses [frozen manifest](../data/external/kaggriculture-notebook-survey-20260915/manifest.json).
No notebook cells were executed; instead, the source code was extracted statically via literals, the body of `writefile`, and embedded compressed packages,
and then the original agent was executed within the existing standalone CPU competition process.

## Ahmed V43: Changes are clear, improvements are limited

The API of [Kaggriculture V43: Recovering Lost Harvests](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v43-recovering-lost-harvests) last ran at **September 14 21:41 UTC**; this time does not equal the first release time.
The exact source code SHA-256 obtained this time is
`919fc1d61050cd96f799979e49177ae3ac7bce98ec9835724238bea73f4a08ed`.

Compared to the current V42, the original code prefix is retained, with the addition of end-of-day inventory recovery: when automatic warehouse return would discard goods, additional sales of inventory that can be replenished by these goods are appended, and it requires that the complete inventory vector after warehouse return be consistent with the original plan. It retains the original field actions and market order prefixes. Additionally, it introduces optimized deep copying for ordinary containers and optimized distance calculation in terminal planning. Although the source code includes fixes for seed pre-purchase/buying requests, `_R148_SEEDS=False`, **these two features are not enabled**, and thus cannot be counted as actual strategy improvements.

The author reports a record of 39 wins, 3 losses, and 22 draws against V42 in direct independent play, with an average cash difference of +116.86;
the author also explicitly states that performance improvements against other opponents are minimal. The following conclusions are based on local new-seed matches, and do not count the author's results or historical fixed-replay opponents as evidence for this analysis.

### Direct Match Against Current V42: 64 Games

Pre-set seed `1860915001`–`1860915032`, and swap seats for each seed.
V43 has **37 wins, 26 draws, 1 loss**; strict win rate **57.81%**, and with draws counting as half-points, the score is **78.13%**. Average cash difference is **+91.41**, and the 95% bootstrap interval by seed clustering is **[54.38, 133.19]**. The value 78.13% cannot be interpreted as the strict win rate.

Adding the cash differences of two seats with the same seed yields **19 seeds leading, 13 seeds tied, and 0 seeds lagging**.
The two games involving seat changes are not counted as independent seeds. The results support a minor improvement in revenue, with a leading amount approximately 0.086% of the average terminal cash.
See [Per-game and aggregate](../outputs/analysis/notebook-survey-20260915/v43-v42/benchmark-report.json),
[Clustering statistics](../outputs/analysis/notebook-survey-20260915/v43-v42-statistics.json).

### Same batch of four-script panel: V42 / V43, each 256 turns

After observing the direct match results and before the extended match begins, fix `1860915201`–`1860915232`, swapping seats for each opponent and each seed.
All entries in the table are candidates for one's own **win/draw/loss**.

| Opponent | V42 | V43 | Average Cash Difference Increment (V43 vs V42) |
| --- | ---: | ---: | ---: |
| MetaCounter R1 | 64/0/0 | 64/0/0 | +67.44 |
| Shop Router 0913 | 64/0/0 | 64/0/0 | +156.28 |
| Rayk V38 Low Pressure | 61/0/3 | 61/0/3 | +207.39 |
| Farming V4 0914 | 47/12/5 | 51/8/5 | +188.36 |
| Total | **236/12/8** | **240/8/8** | **+154.87** |

Draws count as half a point, scoring improved from **94.53% → 95.31%**, an increase of **0.78 percentage points**;
The 95% interval by seed clustering is **[0.00, 1.95] percentage points**.
The cash difference increment interval is **[100.39, 223.34]**. Resampling retains all opponents and dual seats within the same seed, not treating 256 games as 256 independent environments. Win improvements are concentrated in matchups approximately mirroring Farming.

See the [V42 Panel](../outputs/analysis/notebook-survey-20260915/ahmed_v42-common-panel/benchmark-report.json),
[V43 Panel](../outputs/analysis/notebook-survey-20260915/ahmed_v43-common-panel/benchmark-report.json),
[Pair Increment](../outputs/analysis/notebook-survey-20260915/common-panel-statistics.json), and
[Extended Protocol](../outputs/analysis/notebook-survey-20260915/expanded-protocol.json).

## Other New Candidates and Deduplication

The following two new titles do not offer new strategies:

- [Nathan Pipe 2](https://www.kaggle.com/code/nathanjacob/kaggriculture-pipe-2-agent):
  The extracted source code is identical to the current **Ahmed V42**, with hash `728fdfb4…`.
- [Adaptive Route Portfolio](https://www.kaggle.com/code/alperen5252525/adaptive-route-portfolio-kaggriculture):
  The source code is identical to the current **Shop Router 0913**, with hash `77cf6772…`.

Additionally, seven other candidates: `1860915101`–`1860915104`, double seats with 8 matches against V42:

| Candidate | Win/Draw/Loss | Average Cash Difference |
| --- | ---: | ---: |
| [Tetsu Latest Market-Smart Farming](https://www.kaggle.com/code/tetsutani/market-smart-farming-kaggriculture) | 0/2/6 | -2,019.50 |
| [Hosen HC1](https://www.kaggle.com/code/hosen42/kaggriculture-v11-hc1-vs-h5-validation) | 0/0/8 | -26,958.75 |
| H5 on the same notebook | 0/0/8 | -26,958.75 |
| [HarvestForge X](https://www.kaggle.com/code/alperen5252525/harvestforge-x-high-throughput-farming) | 0/0/8 | -33,776.00 |
| [Sovereign Swarm](https://www.kaggle.com/code/taylorclark637/sovereign-swarm-kinematics-the) | 0/0/8 | -165,137.00 |
| [Kunal 2026 V1, self-proclaimed V3](https://www.kaggle.com/code/kunaldesale2408/kaggriculture-2026-v1) | 0/0/8 | -171,864.25 |
| [Terminal Logistics](https://www.kaggle.com/code/xuantianfengwu/kaggriculture-terminal-logistics) | 0/0/8 | -118,847.63 |

This is a small-sample initial screening, supporting reduced access priority and unable to infer win rates across all environments.
HC1/H5 source codes differ, but the accumulated action fingerprints for the four sub-variants are identical, so their results are not considered independent strategy evidence.
Tetsu's latest source code indeed differs from yesterday's V39 copy version, but this round did not exceed the current V42.
See [Complete Initial Screening](../outputs/analysis/notebook-survey-20260915/other-candidates/benchmark-report.json).

No later replaceable public successor versions were found for authors Yhay81, Rayk, Farming, Kaito, Boatlee, and Thomas; the latest default source code for Farming is already in the active pool.
Nathan's new strategy clustering notebook is replay analysis material and does not have a directly integrable agent.

## Verification and Recommendations

In this turn, 632 games each completed 719 actions, and the evaluator recorded no call exceptions, timeouts, or non-DONE states.
This does not guarantee capturing exceptions swallowed by upstream code.
By rerunning the first eight sub-variants of V43/V42 in dual-seat mode using the official **kaggle-environments 1.32.7**, for 16 games,
the final cash balances, win/loss outcomes, game states, call counts, and cumulative action fingerprints (24/96/200/400/719 steps) are all consistent.
Re-running does not constitute adding new independent strength samples; full-frame observations were not verified frame-by-frame, and this does not equate to C++ port acceptance.
See [official confirmation](../outputs/analysis/notebook-survey-20260915/official-comparison.json) and
[comprehensive validation](../outputs/analysis/notebook-survey-20260915/verification.json).

**Recommend prioritizing V43 over V42, retaining the other four scripts.** V43 can serve as a minor maintenance update;
No new strategies have been identified in this round that would significantly increase the difficulty of the opponent pool. If integrated in the future, new IDs and hashes should be frozen,
the existing native C++ execution chain should be reused, and equivalence validation should be completed.

In the training snapshot of U5268, the smooth win rates for the five scripts are approximately **96.2%–98.2%**.
This represents sampled statistics with prior and decay, and cannot replace independent testing at fixed neural checkpoints.
The current neural model's win rate against V43 was not tested, nor was the training gain from the replacement proven.
See [Training Snapshot](../outputs/analysis/notebook-survey-20260915/training-snapshot.json).
