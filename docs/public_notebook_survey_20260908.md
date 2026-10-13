# 2026-09-08 Kaggle Public Notebook Opponent Investigation

There are worthy candidates for upgrade. In the initial screening of the original four frozen scripts, Thomas achieved a router score of 95.5%, while Farming Score V4 and Kaito v58 each secured **32 wins, 0 draws, 0 losses**, and Boatlee v29 recorded **29 wins, 0 draws, 3 losses**. Thomas further achieved **24 wins, 0 draws, 0 losses** against these three new candidates, making him the top priority candidate in this small-sample direct matchup group.

This supports prioritizing independent evaluation, but does not constitute proof of superior win rate against the entire current leaderboard.

## Current Baseline and Retrieval Scope

Take [CURRENT_MAINLINE.md](CURRENT_MAINLINE.md) as reference: The original scripts were Kaito v39, Kaito v48, Boatlee v21, and Mugundh v21. The current main runtime has been changed to pure selfplay, and no modifications have been made to the training pool or training processes.
The evaluation uses the original frozen Python source code corresponding to the four C++ port versions, with identical SHA256 values compared to existing records; no re-downloads or replacement of the old baselines with upstream-modified files have been performed.

Retrieve, in real-time via Kaggle CLI, 100 public notebooks each sorted by `scoreDescending` and `dateRun`, merging into 178 distinct references; additionally, search for public entries by authors Kaito, Boatlee, and Mugundh, returning 7, 12, and 1 entries respectively. Download 6 candidate notebooks along with their metadata, without executing any notebook cells. All timestamps are the last run time reported by the API (UTC), not the initial publication date.

Original list, notebook, extracted source code, and hash are retained in
[Source Directory](../data/external/kaggriculture-notebook-survey-20260908/),
runtime identity see [Freeze List](../data/external/kaggriculture-notebook-survey-20260908/manifest.json),
all download identities see [Download List](../data/external/kaggriculture-notebook-survey-20260908/source-inventory.json).
The API list does not return specific scores; scores displayed in web search cache vary by time and version, thus they are not used to establish current strength rankings.

## Priority Candidates

| Notebook | Last Run (UTC) | Key Changes and Assessment |
| --- | --- | --- |
| [Thomas：95.5% Win Rate via Replay Routing](https://www.kaggle.com/code/thomastschinkel/kaggriculture-95-5-win-rate-via-replay-routing) | 2026-09-07 18:57 | Five routes and small offline fitting trees, selecting routes based on public market, store, and farm states. This turn achieved 56 full wins against four old scripts and three new candidates, prioritizing expansion of independent evaluation. |
| [Farming Score V4: A Better Shop — lynnsakurai](https://www.kaggle.com/code/lynnsakurai/farming-score-v4-a-better-shop) | 2026-09-08 02:55 | Four prefix-compatible routes, branching at 226/360/433 turns; added 72-turn budget check, worker action alignment, inventory and sales volume calculation in order of orders. This turn achieved full wins against old scripts and is retained as a strong control. |
| [Kaito v58: Minimax Closed Loop](https://www.kaggle.com/code/kaitofukami/238-238-known-streams-v58-minimax-closed-loop) | 2026-09-01 07:15 | Follow-up public version after v48; selects continuation routes and selling timing at 72/96/144/360 turns based on public state. Achieved full wins in this turn, but the original Python controller showed significantly higher runtime costs. |
| [Boatlee V29-R1: Adaptive Market Hysteresis](https://www.kaggle.com/code/boatlee/v29-r1-adaptive-market-hysteresis) | 2026-09-02 05:42 | Follow-up public version after v21; added sustained inventory pressure, price thresholds, batch selling, public market traffic estimation, similar farm protection, and gradual terminal liquidation. This turn achieved a win in 29/32, expanding coverage of market control mechanisms. |

Kaito's latest published entry is v58, Boatlee is v29; no published entries for Mugundh v21 or later were found.
The v58/v29/V4 in strategy names are distinct from the version numbers of the Kaggle notebook itself.
Farming V4 has a trajectory and implementation linkage with the evaluated Shop/Pasture projects and thus cannot be counted as an independent source family.

## Local Direct Game

Reuse the `kagg_revue.opponents.cli` and existing Hydra configuration entry, using a local native game engine.
Each new script faces four old scripts; fixed environment seed.
`1860908000–1860908003`: seat swapping per seed, 8 games per pairing, totaling **128 games**.
Additional testing of Thomas against three new candidates for **24 games**; native head-to-head cumulative total reaches **152 games**.
`episodeSteps=720`: corresponds to 719 action transitions; market order cap of 10.
Each game runs in an independent new process, with 4 CPU workers, no GPU usage.
These seeds are fixed before reading match results; all candidates and baselines show no entry anomalies or timing errors.

The table shows the win/draw/loss statistics for the new version:

| New Version | vs Kaito v39 | vs Kaito v48 | vs Boatlee v21 | vs Mugundh v21 | Total | Average Final Cash Advantage |
| --- | --- | --- | --- | --- | --- | ---: |
| Thomas 95.5% | 8/0/0 | 8/0/0 | 8/0/0 | 8/0/0 | **32/0/0** | +24,398.69 |
| Farming V4 | 8/0/0 | 8/0/0 | 8/0/0 | 8/0/0 | **32/0/0** | +23,847.75 |
| Kaito v58 | 8/0/0 | 8/0/0 | 8/0/0 | 8/0/0 | **32/0/0** | +14,558.09 |
| Boatlee v29 | 8/0/0 | 8/0/0 | 8/0/0 | 5/0/3 | **29/0/3** | +16,188.00 |

Complete turn-by-turn records, exact configurations, source code identities, and timing are available in
[Farming V4](../outputs/analysis/notebook-survey-20260908/farming-v4/benchmark-report.json),
[Kaito v58](../outputs/analysis/notebook-survey-20260908/kaito-v58/benchmark-report.json),
[Boatlee v29](../outputs/analysis/notebook-survey-20260908/boatlee-v29/benchmark-report.json),
[Thomas 95.5%](../outputs/analysis/notebook-survey-20260908/router-95/benchmark-report.json).
There are no direct matches between Farming V4, Kaito v58, and Boatlee v29; direct results of Thomas against these three are provided below.
The relative win/loss outcomes between untested pairs cannot be inferred from the average cash difference of older scripts.
The four environment seeds show high correlation with the original scripts, and 32/32 does not constitute an independent confirmation of strength across 32 distinct environments.

Reran the first two seeds of Farming V4 using the official `kaggle-environments==1.32.7`, against four previous scripts, for all dual-seat configurations totaling 16 games: all won, with both sides maintaining `DONE` status, and no anomalies observed.
Final cash balance, win/loss results, number of transitions, and action fingerprints (including the cumulative fingerprint of all 719 actions) are consistent with native results.
This is an engine-level confirmation of the same set of games and cannot be counted as a new strength sample; full state verification was not performed, and it does not qualify as cold-start resource certification for Kaggle submission hosts. See
[Official Report](../outputs/analysis/notebook-survey-20260908/farming-v4-official/benchmark-report.json) and
[Comparison Results](../outputs/analysis/notebook-survey-20260908/official-comparison.json).

Original Python single-action p99: Farming V4 approximately 0.178 ms, Boatlee v29 approximately 0.151 ms, Kaito v58 approximately 44.0 ms; median in-process loading times are approximately 0.49/9.01/599.88 ms.
Native timing across different evaluation batches is only used to estimate access cost and cannot be considered a throughput guarantee after C++ porting.

## Thomas 95.5% Router Supplement Review

2026-09-08 Execute the frozen Thomas router as per the additional evaluation requirements, without modifying its source code or fitting tree.
SHA256 is `8241246765098c50223d897739cb32076b71a303284d2e5e1c5f0fb495bb5a97`,
exactly identical to the previously downloaded `main.py` of 65,128 bytes. The original acquisition manifest remains unchanged to preserve the hash referenced in prior reports; the scope and seed of this execution are separately saved prior to the game as
[Evaluation Protocol](../outputs/analysis/notebook-survey-20260908/thomas-evaluation-protocol.json).

In addition to the aforementioned four old scripts winning all 32 games, identical four seeds, double-seat setups were used to directly compete against the new candidates:

| Opponent | Thomas win/draw/loss | Thomas average terminal cash advantage |
| --- | --- | ---: |
| Farming V4 | **8/0/0** | +38,879.00 |
| Kaito v58 | **8/0/0** | +33,561.75 |
| Boatlee v29 | **8/0/0** | +10,116.75 |

All 56 games resulted in 56 wins, 0 draws, and 0 losses, with no abnormalities in entry, calls, or timing between both sides.
Thomas's average final cash balance was 93,111.11, with an average lead of 25,736.04.
The original Python action p99 is approximately **0.0103 ms**, and the median load time is approximately **22.99 ms**;
this timing is from the native Python script, not yet ported to C++.

Official `kaggle-environments==1.32.7` confirmation of the first two seeds' full double-seat games against four legacy scripts
**16 games**: Thomas won all games, with both sides being `DONE` and no anomalies. Cash, win/loss, conversion counts, and full actions
Cumulative fingerprints and native outputs were identical. These repeated games were not counted toward new strength samples beyond 56 games, and no official confirmation was conducted for the three new candidate pairings. See
[Thomas Official Report](../outputs/analysis/notebook-survey-20260908/router-95-official/benchmark-report.json) and
[Engine Comparison](../outputs/analysis/notebook-survey-20260908/router-official-comparison.json).

The results of this work support promoting Thomas as the preferred candidate for subsequent independent evaluations, but only four environment seeds are available, and the trajectory sources are interrelated; thus, we cannot claim a 100% win rate across the entire leaderboard, nor have we reproduced the author's 44,096-panel games. This study only evaluates frozen external policies and does not use fitted parameters for initializing or training the current model.

## Other Checked Candidate and Evidence Boundaries

- [Thomas Tschinkel: 95.5% Win Rate via Replay Routing](https://www.kaggle.com/code/thomastschinkel/kaggriculture-95-5-win-rate-via-replay-routing), last executed on September 7 18:57. The byte-extracted `main.py` is 65,128 bytes, containing five routes and a fitted branch tree. The author reports achieving 95.51% win rate from 689 out-of-sample replays, 32 seeds, and dual seats across 44,096 games, previously 93.8%. This is an author's self-tested performance against replay opponents, not a reproduced full panel, nor the current leaderboard win rate. The current analysis has additionally verified 56 direct games and 16 official confirmations using the frozen script, and these results are interpreted separately from the author's self-test.
- [Ahmed notebook865729c24e](https://www.kaggle.com/code/ahmedberatozer/notebook865729c24e), last executed on September 7 22:16, ranked first in the current `scoreDescending` return list. The source code explicitly reuses the five routes from Thomas, adds a v23 control framework, sale accounting, and budget/terminal protection; the author reports three panels: 106W/14L, 145W/5L, and 104W/4L, and explicitly states that online rating ≥2800 has not yet been verified. The notebook was downloaded and inspected, but the final agent was not built, and it is not included in direct games.
- [Apex V7 God Emperor](https://www.kaggle.com/code/avioon/kaggriculture-apex-v7-god-emperor), last executed on September 4 16:27. The notebook publicly reveals C++ route strategy, budget protection, bridge code, and Python entry points, indicating potential native integration value; however, the model was not compiled or verified in this round.

Kaito v58's **238/238** is explicitly a known result from a frozen replay, representing a development regression; the author also reports updates for v57.
The match record is 2 wins, 8 draws, 2 losses. Therefore, one cannot solely rely on the title to prove the new version is superior; the direct head-to-head results from the older script provide alternative local evidence. Boatlee v29's author reports 108 regression games yielding 106 wins and 2 losses, with the panel including V19/V20/V21, Kaito v37/v48, and others; the Top-20 representative panel shows 196 wins and 20 losses. These authors' results should be interpreted separately from this independent initial screening.

## Suggestions for Future Integration

Prioritize creating a larger, independent seed panel for Thomas 95.5% router, while retaining Farming V4 and Kaito v58 as strong controls; use Boatlee v29 as a supplementary market control counterpart.
Include native C++ porting during training, following warehouse requirements to ensure behavioral equivalence, reusing existing opponent session and batch interfaces. The Kaito v58 includes multiple running controllers; the porting cost for these should be evaluated separately.
Complete this round with retrieval, source code preservation, and direct evaluation; no new strategy implementations, training configuration modifications, or deployment artifacts were added.

Candidate original `main.py` SHA256:

| Candidate | SHA256 |
| --- | --- |
| Farming V4 | `1590394cf30c8989a3e1cfdb027d89b5ccd97c2fb4cdc14959a15555b2b2361a` |
| Kaito v58 | `b041058ec187a8d0a01edc0eab8de068b53deca3e6c1973faf74ace6916ddcb9` |
| Boatlee v29 | `c4a6964cec3c1c99207c32bb1fd91e53c3ec01e6890da5734331cbeab1cc1267` |
| Thomas 95.5% | `8241246765098c50223d897739cb32076b71a303284d2e5e1c5f0fb495bb5a97` |
