# 2026-09-14 PM Public Notebook Update Investigation

**Prioritize updating the afternoon code snapshots of Ahmed V42 and Farming V4.** The user has since requested native integration and application to training; execution status is `CURRENT_MAINLINE.md`.

This baseline is the September 12 snapshot of the currently trained Ahmed V41, MetaCounter R1, Shop Router 0913, Rayk V38 Low Pressure, and Farming V4. They have been integrated into U2665, and findings from overnight investigations are not considered as new candidates.

## Source and Version Verification

Starting from 14:17 UTC, obtained two pages of 100 entries each for `dateRun` and `scoreDescending` via Kaggle CLI, totaling **326 distinct notebook references**; additionally, investigated 8 upstream authors, downloaded 14 newly published/updated notebooks, and re-fetched 5 active sources. No notebook cell execution was performed; agent extraction was carried out from literals, compressed data, or static public output packages, followed by evaluation in the existing isolated CPU evaluator.

- [Ahmed V42](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v42-production-that-fits-the-marke): API last runtime was 09-14 12:47 UTC. Full source code SHA-256 is `728fdfb4405ba313f8b14ffb3e0f8eceaddcaa0de49e4835928d89aaf71467e9`.
- [Farming V4](https://www.kaggle.com/code/lynnsakurai/farming-score-v4-a-better-shop): The list still shows 09-12 08:31 UTC, but the latest pulled source code has changed, with SHA-256 `03e263f1a20db29d6aa3404e978b97549bdac7f81d2b7f8dea5b36a3d6e91edc`. Identity is confirmed by this source code hash; the accurate code publication time cannot be inferred from `lastRunTime`.
- The source code of the remaining four active sources remains identical to the previously frozen versions.
- The updated [Dynamic Route Agent](https://www.kaggle.com/code/reyhanksatria/kaggriculture-dynamic-route-agent) and [Master Engine V3](https://www.kaggle.com/code/guruprasaathas111/kaggriculture-master-engine-v3) export source codes are byte-for-byte identical to the current Ahmed V41; they are not two new opponents.
- Moon Counts Melons and Soil Remembers Rain both have the latest default source code as the same restored baseline of `02b1fee4...`; page updates or title changes do not indicate new strategies.
- Yhay81 remains at 0913; no updated public versions were found for Kaito, Boatlee, and Thomas in this turn.

Original documents, file-level hashes, and query ranges are available in [Source List](../data/external/kaggriculture-notebook-survey-20260914-refresh/source-inventory.json); all evaluated sources are listed in [Investigation manifest](../data/external/kaggriculture-notebook-survey-20260914-refresh/manifest-final.json). This round does not involve a full-scale public notebook exhaustive search; list ordering does not correspond to real-time leaderboard rankings.

## 896 Turns of Direct Combat

Each pairing consists of 32 seeds, with seats swapped between partners, resulting in a total of 64 games. The first round uses `1860914501`–`1860914532`; the V42 expansion panel uses `1860914533`–`1860914564`, which is frozen after observing the first-round results and before the generation of extended results. Fixed at 720 states / 719 actions, with a maximum of 10 market order limits. The original agent performing the freeze allows both sides to respond to the actual game state; it is not a fixed replay of the opponent.

| V42 Opponent | V42 Win/Draw/Loss | V42 Average Cash Difference |
| --- | --- | ---: |
| Active Ahmed V41 | 54/6/4 | +1,812.30 |
| Active MetaCounter R1 | 64/0/0 | +27,060.77 |
| Active Shop Router 0913 | 62/0/2 | +9,375.98 |
| Active Rayk V38 | 60/0/4 | +2,675.88 |
| Active Farming V4 0912 | 64/0/0 | +4,569.52 |
| New Reactive V5 | 50/14/0 | +2,291.17 |
| New Fully Dynamic Autonomous | 50/8/6 | +1,875.64 |

Latest snapshot of Farming V4 shows a performance comparison against the current legacy snapshot **62/0/2**, with an average cash difference of **+2,743.66**; against V41 **48/15/1**, an average of **+548.16**; and against V42 **4/9/51**, an average of **−1,356.56**.

Other candidate pairs V41: Reactive V5 **42/16/6**, average only **+6.16**; Fully Dynamic Autonomous **52/8/4**, average **+372.34**; [No Cow Left Behind](https://www.kaggle.com/code/nathanjacob/no-cow-left-behind-v40-autopsy-fix) **47/0/17**, average **+1,209.05**. The latter has only **2/0/62** against V42, averaging **−323.03**. Nathan's accompanying dataset API returns 403, but successfully retrieved `submission.tar.gz` from a public notebook, thus using its actual packaged `main.py` without rewriting the author's patch.

All 896 games completed 719 actions each, with the evaluator recording no call errors or timeouts. Additionally, 40 of these games were rerun using the official **kaggle-environments 1.32.7**, and the final cash balances, win/loss outcomes, action call counts, and cumulative action fingerprints (24/96/200/400/719 steps) were fully consistent. These 40 games constitute engine verification and thus cannot be considered independent strength samples; a frame-by-frame comparison of all states was not performed.

The 32 seed matchup between V42 and V41 actually produces **25/64 ordered first-two-store combinations**, with **18/64** including Yarn matches. This result is obtained by replaying actual strategies from both sides up to move 145; store RNG is dependent on field empty space and cannot be inferred from PASS games. Pair swaps cannot be treated as independent seeds; not all store combinations have been covered. V42 achieves 25 wins, 7 draws, and 0 losses in this pairing based on the total cash difference across two seats.

Results are available in [V41 Benchmark](../outputs/analysis/notebook-survey-20260914-refresh/vs-v41/benchmark-report.json), [V42 Expansion](../outputs/analysis/notebook-survey-20260914-refresh/v42-expanded/benchmark-report.json), [Farming Update](../outputs/analysis/notebook-survey-20260914-refresh/farming-refresh/benchmark-report.json), [Nathan](../outputs/analysis/notebook-survey-20260914-refresh/nathan-fix/benchmark-report.json), [Official 40-game Confirmation](../outputs/analysis/notebook-survey-20260914-refresh/official-comparison.json), and [Real-store Coverage](../outputs/analysis/notebook-survey-20260914-refresh/v42-v41-shop-coverage.json).

## Substantive Changes and Selection

**V42** retains V41's low-impact startup and supply protection, expanding Route 13 into Route 41; for the first two stores, use the old expert when Yarn is present, otherwise use the Route 0913 derived path, and accompany this with delayed requests for post-harvest processing workers already committed to crops or herds. The reserved sale window is moved from step 288 to step 216. Compared to V41, only 5 top-level functions have changed; existing native controllers and the migrated MetaCounter routing can be reused; native equivalence still requires empirical validation.

**Farming V4 New Snapshot** Adds queue recovery for day-of-weeding and replanting, optimizes selling sequence when image confirmation is completed and cash is nearly depleted, and implements a confirmation-based execution chain to replace two cows with geese in two egg-demanding stores. It provides clear improvements over existing training snapshots and has independent incremental benefits, making it suitable for concurrent updates.

**Reactive V5** primarily reserves advance windows and enhances animal survival protection, offering only a minor cash advantage over V41; **Fully Dynamic Autonomous** actually modifies only warehouse overflow sales consolidation and fertilizer sales relative to V41, rather than the fully autonomous, route-free architecture advertised in the promotional materials. Both are defeated by V42; the script pool is not prioritized for expansion in this round. Nathan also prioritizes V42.

Suggest replacing `ahmed_v41` with `ahmed_v42`, and replacing `farming_v4_0912` with `farming_v4_0914`; retain the other three active scripts and the 30/20/50 ratio. Original source code, hashes, and historical training archives shall be preserved; no silent overwrite with identical names is permitted.

These results support script upgrades, without proving the win rate of the current neural model against new scripts or the training gains from upgrading. In the U3926 snapshot, the learning agent achieves a smooth score of approximately 95.9%–98.1% against the old five scripts, which includes decay and prior knowledge, and is not an independent test of the current fixed checkpoint.
