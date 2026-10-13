# 2026-09-14 Kaggle Public Script Opponent Update Survey

Recommend prioritizing evaluation of **Ahmed V41, Shop Router 0913, MetaCounter R1**.
V41 is the strongest candidate in this round; 0913 follows a different trajectory with the lowest native integration cost; MetaCounter has publicly demonstrated the implementation of integrating the 0913 trajectory into the V39 controller. Rayk's low-market-impact opening version is suitable as a control for V41.
Source code freeze, deduplication, and direct competition were completed in this round, without modifying training configurations, native strategies, or runtime processes.

## Current Training and Investigation Scope

Take [current mainline](CURRENT_MAINLINE.md) and official operation `outputs/learning/budget-q100-top10-2d-20260913-s68001/resolved-config.json` as reference:
The script pool consists of `router_95`, `farming_v4`, `kaito_v58`, `shop_router_0908`, and `shop_router_0909`, implemented in native C++, accounting for 20% of physical gameplay; additionally, 30% self-play and 50% historical PFSP. Excludes versions of Kaito/Boatlee/Mugundh retired before September 8.

U2554's [training snapshot](../outputs/analysis/notebook-survey-20260914/training-snapshot.json)
Records the smooth win rates of the learning agent against the above five scripts as **98.03%, 97.72%, 98.20%, 98.06%, 98.37%**.
This metric includes time decay, prior knowledge, and half-point draws and serves as the basis for training sampling, not as a fixed win rate from current checkpoint independent testing.
This supports updating the script pool, but has not yet measured the strength of the current neural model against new candidates.

In real time, retrieve 100 notebooks each for Kaggle `scoreDescending` and `dateRun`, combining them into **160 distinct references**;
Additionally, query five authors—yyhay81, lynnsakurai, Kaito, Boatlee, Thomas—to download **18 publicly available source codes** and metadata. When requesting page-size 200, the service actually returns only 100; this round does not exhaust all publicly available notebooks.
The list does not return specific competition scores, so the returned positions cannot be interpreted as actual performance strength or current leaderboard rankings.

Original materials, statically extracted source code, and file hashes are saved in [Source List](../data/external/kaggriculture-notebook-survey-20260914/source-inventory.json); runnable initial screening sources are available in [Frozen manifest](../data/external/kaggriculture-notebook-survey-20260914/manifest.json).
Notebook cell executions have not been performed; the competition runs a separately extracted and dependency-checked frozen agent.
All dates below refer to API `lastRunTime`, not the initial release date, and do not individually confirm code update times.

## Candidate and Native Integration Judgment

| Candidate and Source | Last Run UTC | Substantive Changes in Source Code | Access Judgment |
| --- | --- | --- | --- |
| [Ahmed V41 — Review Candidate](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v41-review-candidate) | 09-13 22:21 | 13 routes; low market impact opening; reserved funds for next day's workers; seed constraints; collecting food before feeding; using proceeds from selling previously stored goods to replenish inventory; retaining production, storage, and terminal control | **Preferred strong opponent**. Approximately 332 KB, about 3,000 lines excluding constant compression, 126 source code functions; requires porting an entire stateful control chain, high cost |
| [Shop Router 0913](https://www.kaggle.com/code/yhay81/shop-router-0913) | 09-13 09:39 | **29 complete 719-step routes, 64 ordered store pairs**; route selection at step 144, transition to shared terminal route at step 648 | **Priority to supplement**, low cost. Execution logic is short, primarily handling new assets, route mapping, and state semantics; it provides a simplified version without weeding, inventory correction, early selling, or terminal collection |
| [MetaCounter R1 — Scored Agent](https://www.kaggle.com/code/alperen5252525/kaggriculture-metacounter-r1-scored-agent) | 09-13 22:03 | **41 routes**: use V39 if the first two stores include Yarn Store, otherwise use derived routes from 0913; delays application of auxiliary workers for tomatoes/herds already invested, aligning with existing worker scheduling in new routes | **Priority to supplement**. Exposes specific implementation of new routes combined with old controllers; standalone porting is costly; if V39/V41 shared controllers are ported first, subsequent incremental effort is minimal |
| Default agent of [Rayk — Rank Your Agent](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-rank-your-agent) | 09-13 16:13 | Actually bundles `v38_low_pressure_opening_20260913`; retains V38 multi-route logic, only changes initial market action from buying 13, buying 30, selling 30 wheat to buying 5, buying 10, selling up to 60 | **Strong benchmark/alternative**. Not just a ranking tool; source code is complete, but shares origin with V41 and has similar opening strategy; default high-weight inclusion provides limited value  |
| [Ahmed V39 — Ready Before the Rush](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v39-ready-before-the-rush) | 09-13 09:37 | Production calendar feeding, grain refill cap, protection plan harvesting, pre-stocking for full market order turns | **Baseline and shared transplantation foundation**. This round performs notably worse than V41; not to be prioritized simultaneously at the highest level |
| [Farming V4, latest source code by name](https://www.kaggle.com/code/lynnsakurai/farming-score-v4-a-better-shop) | 09-12 08:31 | Currently controls route 13; retains a 4-yuan labor budget for the next day in the last six steps, and uses hourly 22/23 to rescue escaped animals; differs from our frozen four-route version | **Secondary candidate**. There is genuine improvement, but not merely a patch replacing two protection functions; this new candidate performs weakly in this round and should be frozen with a new ID; silent override of the old hash is not permitted |
| [Reactive V4 — aurax7](https://www.kaggle.com/code/aurax7/kaggriculture-shop-router-reactive-v4) | 09-13 04:30 | V38-based production and market control, plus animal survival protection near the boundary | **Secondary candidate**. Performs below V39, V41, and MetaCounter in this round; strategy family overlap exists |
| [A Smaller Market Shock](https://www.kaggle.com/code/dmitriigluzdov/kaggriculture-a-smaller-market-shock) | 09-12 02:32 | Retains the 0909/Moon route; shifts sales forward by 3–5 steps; adjusts pure SELL list order based on "potential losses from opponent selling half their batch first" | **Retain for research comparison, not prioritized for integration**. The mechanism differs, but this round is outperformed by all new candidates; porting from existing 0909 requires supplementing Moon production and sales accounting layers, with moderate cost |

Preserve the distinction between public version 0913 and the older 0909: applying the 0909 fixes directly to the new routes creates a new strategy, which cannot be called an equivalent port of the original. MetaCounter already contains concrete source code for such a combination and can serve as a separate candidate.
0911 Simple has 14 routes and 64 shop pairs. Its author explicitly states that the public version is weaker than the private submission and omits runtime corrections.
0913 is newer and has more routes, so 0913 is prioritized in this round. The private submission's ranking must not be attributed to the simplified public version.

## Local Direct Match

Four seeds are pre-selected: `1860914001`–`1860914004`, with each pairing swapping positions between sides.
Default: 720 states / 719 actions per game, up to 10 market orders per turn, native engine is the certified `d7149aeb96acbeb954764120196fc9efdee524aa8004c184fecb6df16f1f7dad`.
The competition uses a frozen original Python agent; this does not constitute turn-by-turn Python integration during training.

The first two stores are Pizza/Yarn, Pizza/Bakery, Brunch/Smoothie, and Smoothie/Farmers.
Only covers the **4/64 store pair**, one of which contains the Yarn Store;
[Store sequence](../outputs/analysis/notebook-survey-20260914/seed-shops.json) is retained.
Repeated pairings cannot be summed independently by environment count.

| New Candidate | vs. Thomas 95.5, Win/Draw/Loss | vs. Shop 0909, Win/Draw/Loss | Eight-Candidate Round-Robin, Win/Draw/Loss | Original Python Action p99 |
| --- | --- | --- | --- | ---: |
| **Ahmed V41** | 8/0/0 | 8/0/0 | **52/0/4** | 4.329 ms |
| **Rayk Low Market Impact Opening** | 8/0/0 | 8/0/0 | **44/0/12** | 4.239 ms |
| **MetaCounter R1** | 8/0/0 | 8/0/0 | **38/0/18** | 3.656 ms |
| Ahmed V39 | 8/0/0 | 8/0/0 | 28/0/28 | 4.172 ms |
| **Shop Router 0913** | 8/0/0 | 8/0/0 | **28/0/28** | **0.004 ms** |
| Reactive V4 | 8/0/0 | 8/0/0 | 20/0/36 | 4.147 ms |
| Farming V4 Latest | 8/0/0 | 8/0/0 | 14/0/42 | 1.265 ms |
| A Smaller Market Shock | 8/0/0 | 8/0/0 | 0/0/56 | 0.224 ms |
| Shop Router 0911 Simple | 8/0/0 | 8/0/0 | Did not participate | — |

A total of **368 native games** were effectively conducted: 72 games from each of two previous opponent groups, and 224 games from the eight-candidate round-robin tournament.
719 actions were completed on average, with no call exceptions. The p99 latency originates from the round-robin tournament, involving the local CPU, 8 evaluation workers, and other concurrent tasks;
this does not represent the throughput after C++ porting, nor does it include GPU learning phases. When porting to V41, special attention should be paid to the terminal planning cost inherited from the original implementation.

Key pairing outperforms average cash:

- V41 vs V39, Rayk, MetaCounter each **8/0/0**; vs Farming the latest version **7/0/1**.
- V41 vs 0913 has only **5/0/3**, with an average cash differential of **+456**; 0913 is the most competitive script against V41 in this round.
- MetaCounter vs 0913 is **6/0/2**, indicating meaningful differences in candidate pairings that warrant retention.
- Although V41 has won all 8 matches against Rayk, the average lead is only **447.5**; further environmental validation is still needed.
- Several high-market-impact opening versions show cash differentials of approximately 95,000–100,000 against the old 0909; V41, Rayk, and 0913 lead by only about 5,000–7,000, but perform stronger in the new candidate round-robin. Therefore, candidate rankings based on cash differentials against older scripts are not valid.

Official **kaggle-environments 1.32.7** confirmation of 40 games from the above pairing:
The final cash balances, win/loss outcomes, number of trades, and cumulative action fingerprints are consistent with native execution.
This is a repeated engine validation of the same set of games and does not constitute new strength samples; full state step-by-step verification was not performed, and native C++ strategy porting or resource limits of Kaggle submission hosts were not validated.

Additionally, regarding [Adaptive Land Allocator](https://www.kaggle.com/code/xuantianfengwu/kaggriculture-adaptive-land-allocator),
two seeds were run in the official environment with dual seats over **4 games**, against Thomas (0/0/4), averaging a lag of 96,270;
it is currently insufficient as a strong training opponent. Its earlier 8 native games failed to import due to missing `kaggle_environments`, and these are not counted in win/loss records; the empty timing array also triggered exceptions in the existing aggregation function. The original records are complete and have been separately saved with valid game summaries. The official tests have been rerun using the existing installed 1.32.7 interpreter, without modifying candidate or training environments.

Reports and Evidence:
[Thomas's Original Records](../outputs/analysis/notebook-survey-20260914/vs-router95/match-games.json),
[Effective Aggregation and Exclusion Reasons](../outputs/analysis/notebook-survey-20260914/vs-router95/completed-summary.json),
[Regarding 0909](../outputs/analysis/notebook-survey-20260914/vs-shop0909/benchmark-report.json),
[New Candidate Round-Robin Tournament](../outputs/analysis/notebook-survey-20260914/candidates-roundrobin/benchmark-report.json),
[Official Thomas Review and Land Strategy](../outputs/analysis/notebook-survey-20260914/official-check/benchmark-report.json),
[Official 0909 Review](../outputs/analysis/notebook-survey-20260914/official-shop-check/benchmark-report.json),
[Detailed Match-by-Match Comparison of 40 Games](../outputs/analysis/notebook-survey-20260914/official-comparison.json).

## Author Disclosure and Code Deduplication

The V41 author reports **3144/3200 wins** on an independent panel of 50 runnable public strategies, and wins in all 128 games against each of V39 and V40. However, the score improvement interval on the new elite replay panel is **−1.14 to +12.22 percentage points**, and the author explicitly states that the confirmation threshold was not met.
Replay opponents cannot respond to changes in the opening. These results must be interpreted separately from this round's direct matches and cannot establish the current leaderboard win rate or score.

Rayk author reports a low market impact opening achieving **630/640 wins** with 32 opponent pools, 10 seed, and dual seat reserved panel.
This codebase confirms it includes a complete default agent; different webpage titles do not imply two distinct strategies.

Specific deduplication results:

- `main.py` in both `tetsutani/market-smart-farming-kaggriculture` and `renjistarfall/kaggriculture-best-agent` is byte-for-byte identical to Ahmed V39, with the same SHA-256 value of `708c7485fa964853b193f175dcd83020602c005e159ce82e38dc350b22e970c8`.
- The default agent packaged in `degnonguidi/kaggriculture-utils-v1` is byte-for-byte identical to Rayk, with a SHA-256 hash of `8f03b16618586e1d9a55c38d5232ea61729b82cdc5abcf383cca73227d4875b5`.
- The source code difference between `reyhanksatria/kaggriculture-dynamic-route-agent` and Rayk consists solely of the line `_R42_OPENING`, which has been restored to "buy 13, buy 30, sell 30"; it is not an independent new control framework.
- MetaCounter, although extensively inheriting from V39, actually replaces the routing trajectory, store routing, and two production labor time conditions, thus achieving substantive incremental improvements and cannot be excluded alongside pure replication entries.
- Kaito's latest publicly released version remains v58, Boatlee remains at v29, and Thomas remains at 95.5% Router; none of these three authors have found a publicly available replacement version more up-to-date than the current investigation.
- The last runtime of Farming V5 is **09-01**, earlier than the same author's V4 version on 09-12.
  It has been statically unpacked and confirmed to be another implementation of Kenjo/Niklita's replay trajectory with cow and sheep substitutions, differing in entry point and multi-file structure; it was not run in this round and is not considered a strong successor to the latest V4 version based on version number.
- [Island GA](https://www.kaggle.com/code/destbreso/island-ga-an-owned-schedule-is-a-moat) explicitly does not disclose search-derived trajectories, as it constitutes methodological data and cannot be directly used as a complete opponent interface.
- [Structured Economic Policy](https://www.kaggle.com/code/pilkwang/kaggriculture-structured-economic-policy) states it only performs initial action calls and zero full games, and does not support priority over already tested candidates.

## Sequential Integration Order

1. **First, evaluate the current neural checkpoint using V41, 0913, and MetaCounter against fixed benchmarks**, expanding coverage of unused seeds, both player seats, Yarn/non-Yarn configurations, and store variants. Current evidence comes from initial screening between scripts and is still insufficient to prove they can challenge the current model.
2. The engineering order can begin with a **small-scale native implementation of 0913**, followed by porting the shared controller for V41, and then incorporating MetaCounter's route and task assignment differences. All strategies will reuse existing
   `create_native_opponent_session` → `create_batch` → `ParallelBatch.advance_programs`.
3. V39, Rayk, and the new Farming V4 are retained as regression/backup options; homologous versions are controlled by family-level total sampling weights to prevent multiple replicated or approximated strategies from each obtaining the same uniform exploration baseline and thereby consuming the effective training budget of genuine opponents.
4. After confirming action-state equivalence, perturbation recovery, reset/fork independence, and batch mixing throughput, the formal script pool and runtime archives will be migrated. The existing 30/20/50 ratio is unnecessary to change merely due to variations in candidate numbers.

The above is candidate priority and evaluation recommendations, not the completed training integration or current model win rate conclusion.
