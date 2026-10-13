# 2026-09-16 Public Script Update Investigation

**Identify a clear version stronger than the current Ahmed V42: Ahmed V44, V45.**
Independent 32 new worlds, two-player seats, each pair of V42 achieves **62 wins, 0 draws, 2 losses**.
V45 also defeats V44 and the previous research version Revenue Lead R1 with the same score.
Against the currently frozen U1708 run, V45 records **11 wins, 21 losses**, while the current V42 achieves **4 wins, 28 losses**, resulting in a script win rate improvement of **21.875 percentage points**.
**Strongly recommend V45 as a replacement candidate for V42, entering native integration acceptance testing.**
This investigation and offline matches only; no modifications have been made to the official training script pool.

## Current Benchmark and Source

Base comes from [current mainline](CURRENT_MAINLINE.md) and official operation
`budget-q100-top10-2d-20260915-s69001/resolved-config.json`:
`ahmed_v42`, `metacounter_r1`, `shop_router_0913`,
`rayk_v38_low_pressure`, `farming_v4_0914`; the script target ratio remains at 20%.

This training snapshot is U1700, with smooth win rates across the five scripts ranging from **81.9% to 86.1%**.
It includes prior knowledge, decay, and training sampling, and thus cannot be treated as an independent, fixed win rate checkpoint.
The new run is a model randomly reinitialized on September 15; the neural gameplay results from the previous run U5312 yesterday cannot be directly applied to it. See [Training Snapshot](../outputs/analysis/notebook-survey-20260916/training-snapshot.json).

September 16 at approximately 01:07–01:09 UTC, queried `dateRun` and `scoreDescending` via Kaggle CLI to retrieve two pages of 100 entries each, consolidating **323 notebook references**, downloaded nine newly released or updated sources, obtaining eight distinct agent source codes.
This is not exhaustive; the CLI list lacks numerical competition scores, and sorting is not used to demonstrate strength.

Unexecuted notebook cells use literals, `writefile` body content, and embedded compressed package static extraction.
Originals, API metadata, source code, and hashes are preserved in
[Source List](../data/external/kaggriculture-notebook-survey-20260916/source-inventory.json) and
[Frozen Manifest](../data/external/kaggriculture-notebook-survey-20260916/manifest.json).

## Actual Changes of V44 / V45

- [Ahmed V44](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v44-winning-the-same-turn-sale-race):
  Retain V43; when observing the opponent executing the same trajectory, expand the early sale window to eight turns; when observing the opponent making an early sale, expand it to 24 turns. It primarily targets competition in markets following the same trajectory.
  Source code SHA-256: `797d9bca309d481e18cdbb675ce6d6de9967d266cbafb4c2352c68fb10264e2f`.
- [Ahmed V45](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v45-first-turn-wheat-round-trip):
  Retain V44; modify the initial turn's wheat split trade under standard rules to a single buy of 70, followed by a sell of 70.
  Market orders from both sides are executed in alternating fashion, so the effect depends on the opponent's initial turn order; it cannot be interpreted as unconditional arbitrage.
  Source code SHA-256: `2536d41ed5a00c75204b6350f1c76c54259c774cb065ba2a3a0072eedf210d94`.

The last run times of the API were September 15 **18:27 UTC / 19:51 UTC**, which does not indicate the first release date.
The `Master Engine V3` page title claims V5, but the extracted agent is byte-for-byte identical to Ahmed V44, and is not considered a separate strategy.

## Independent Confirmation of the Current V42

First, conduct an initial screening of 64 games for eight different candidates using four worlds and assigned seats for both sides.
Then, pre-fix the new seeds `1860917101`–`1860917132`, and have each of the seven non-primary candidates undergo **64 full games** of competition. The following statistics are all reported from the candidate's perspective.

| Candidate | Win / Draw / Loss | Average Final Capital Difference |
|----------|------------------|-----------------------------------|
| Ahmed V45 | **62 / 0 / 2** | **+3,253.1** |
| Ahmed V44 | **62 / 0 / 2** | **+1,660.0** |
| Tetsu Latest Version | 61 / 0 / 3 | +283.3 |
| Turn-One Market Advantage | 61 / 0 / 3 | +130.2 |
| Pipe-5 Terminal Boost | 57 / 0 / 7 | +285.8 |
| Farming V5 | 15 / 10 / 39 | −1,429.8 |
| MetaBalance V62 | 1 / 0 / 63 | −13,606.4 |

The strict win rates for V44 and V45 are both **96.875%**. Based on world seed clustering bootstrap analysis, the 95% confidence intervals for average capital difference are **[+1,261.5, +2,077.4]** and **[+2,579.7, +4,114.4]** respectively; after combining the two slots, 32/32 and 31/32 of the world leaders are achieved. The two slots are not independent worlds, and the intervals are not estimates of ranking scores.

Fields of Fortune has 0 wins and 8 losses in the initial screening, with an average funding difference of −145,621.3 and has not been expanded.
The latest source code for all other candidates has been distinguished from yesterday's version, and no previous evaluation has been used to replace this competition.
See [confirmation of the game](../outputs/analysis/notebook-survey-20260916/confirmation-v42/benchmark-report.json),
[clustering statistics](../outputs/analysis/notebook-survey-20260916/confirmation-statistics.json), and
[pre-announced expansion seeds](../outputs/analysis/notebook-survey-20260916/expanded-protocol.json).

Using the same 32 confirmation worlds and both seats, also compare the two candidates against their active script counterparts from the same families:

| Candidate against current version | Win / Draw / Loss | Average terminal fund difference |
|---|---:|---:|
| Farming V5 against Farming V4 0914 | **28 / 34 / 2** | **+75.5** |
| MetaBalance V62 against MetaCounter R1 | 0 / 0 / 64 | −15,875.4 |

Farming V5, after averaging over two seats, shows 14 world-leading, 18 tied, and zero laggards, with a funding gap of
95% of the seed bootstrap range being **[+35.3, +127.2]**.
It can be considered a candidate for minor maintenance upgrade, but it has not demonstrated superior performance over the current neural model.
Its disadvantage compared to V42 cannot substitute for direct comparison with prior versions in the same series; similarly, MetaBalance cannot be inferred to outperform MetaCounter solely based on its funding gap against V42.
See [Successor Comparison Statistics](../outputs/analysis/notebook-survey-20260916/successor-statistics.json),
[Farming Game Results](../outputs/analysis/notebook-survey-20260916/farming_v5-vs-predecessor/benchmark-report.json) and
[MetaBalance Game Results](../outputs/analysis/notebook-survey-20260916/metabalance_v62-vs-predecessor/benchmark-report.json).

## The remaining four active scripts: Advantage dependent on opponent

Additionally, pre-fix 16 world slots `1860917201`–`1860917216`, with two seats per opponent.
Each cell represents a candidate outcome of win/draw/loss for oneself, totaling 128 games across all versions.

| Opponent | V42 | V44 | V45 |
|---|---:|---:|---:|
| MetaCounter R1 | 32 / 0 / 0 | 32 / 0 / 0 | 32 / 0 / 0 |
| Shop Router 0913 | 30 / 0 / 2 | 30 / 0 / 2 | 30 / 0 / 2 |
| Rayk V38 | 30 / 0 / 2 | 30 / 0 / 2 | 30 / 0 / 2 |
| Farming V4 0914 | 28 / 1 / 3 | 30 / 0 / 2 | 30 / 0 / 2 |
| Total | **120 / 1 / 7** | **122 / 0 / 6** | **122 / 0 / 6** |

The draw score percentages for V44 and V45 have both increased from V42's **94.14% to 95.31%**,
but the funding difference changes differ: V44 relative to V42 shows an average of **+223.0**, within the 95% interval **[−39.5, +584.4]**; V45 shows **−4,279.7**, within the interval **[−5,294.6, −3,326.1]**.

The decline in V45 is primarily due to MetaCounter: it remains undefeated, but the average lead has dropped from V42's **26,061.1** to **4,290.3**; under the same world and seat conditions, its own funds have decreased by 16,433.0, while the opponent's funds have increased by 5,337.8.
Therefore, one cannot assert that V45 is stronger than all strategies based on its advantage over V42.

See [Complete Panel](../outputs/analysis/notebook-survey-20260916/common-panel/summary.json) and
[Pair Changes](../outputs/analysis/notebook-survey-20260916/common-panel-paired-statistics.json).

## Relationship with the Self-developed Version of Yesterday

Using the same confirmed seed for 32 worlds, both player seats, and all strategies reacting according to actual observations:

| Game | Former win / draw / loss | Former average cash margin |
|---|---:|---:|
| V45 vs V44 | 62 / 0 / 2 | +1,593.1 |
| Revenue Lead R1 vs V44 | 12 / 0 / 52 | −1,449.3 |
| Revenue Lead R1 vs V45 | 2 / 0 / 62 | −2,942.2 |

R1 uses the V43 base from yesterday's freeze with a six-step advance and sell order sorting recipe.
A new V45 image control is added: 4 wins, 56 draws, 4 losses, with an average capital difference of zero across the two seats.
Thus, the conclusion from yesterday that "R1 outperforms the public script" remains valid for the original panel, but it no longer represents the latest public opponents.
See [Comparison Record](../outputs/analysis/notebook-survey-20260916/v45-comparators/summary.json).

## Current New Model: V45 Shows Greater Match Pressure

From the running `budget-q100-top10-2d-20260915-s69001` authentication freeze **U1708**,
retain original actor weights, exported TorchScript actor, and source hash.
Model uses **CPU FP32, temperature 1**, with a random seed per game set to `2 * world seed + neural-policy seat`.
Pre-fix 16 new worlds and opposing seats for `1860917301`–`1860917316`,
three scripts totaling 96 games; compare each version under identical worlds, seats, and neural random seeds.

| Script | Script Wins / Draws / Losses | Script Win Rate | Script Average Fund Difference |
|---|---:|---:|---:|
| Active V42 | 4 / 0 / 28 | 12.50% | −8,158.1 |
| V44 | 4 / 0 / 28 | 12.50% | −8,014.7 |
| **V45** | **11 / 0 / 21** | **34.375%** | **−4,576.5** |

V45 relative to V42:

- Originally eight losses are converted to wins, and one win is converted to a loss, resulting in a net increase of seven victories.
- The win rate improves by **21.875 percentage points**, with a 95% confidence interval from the world seed clustering bootstrap analysis of **[+3.125, +40.625] percentage points**.
- The funding advantage improves by **+3,581.6**, with a 95% confidence interval of **[+1,192.7, +6,178.1]**.
- The average self-funding increases by **6,866.1**, while the neural opponent's funding increases by **3,284.5**; thus, the relative improvement cannot be simply attributed to reducing the opponent's gains.

The funding difference between V44 and V42 improved by only 143.4, within the interval [−36.7, +349.0], with no win-loss reversal.
This supports prioritizing testing V45's training integration, rather than simply integrating V44 due to version number increment.
The conclusion is limited to a current checkpoint, 16 worlds, and the above reasoning patterns; it has not been proven that changing the script will improve long-term RL convergence or leaderboard performance. V45 still loses more often against neural model in most games.

See [Freeze Model](../outputs/analysis/notebook-survey-20260916/neural-reference/manifest.json),
[Full Neural Combat](../outputs/analysis/notebook-survey-20260916/neural-u1708/summary.json) and
[Pair Statistics](../outputs/analysis/notebook-survey-20260916/neural-paired-statistics.json).

Recommendation order: **V45 takes precedence as a candidate for replacement of V42 in acceptance criteria**; Farming V5 falls under minor maintenance candidates, and its value to the current neural model has not yet been assessed; the other three active scripts remain in place to maintain opponent differentiation.
V44, Pipe-5, Tetsu, and Turn-One may be retained for offline comparison; MetaBalance V62 does not support upgrades.

## Validation Scope

Run the official `kaggle-environments==1.32.7` to re-execute the first four confirmed seeds of V44 / V45 versus V42,
with a total of **16 games** across two seats. The final balances, win/loss results, states, call counts, move counts, and cumulative action fingerprints at 24 / 96 / 200 / 400 / 719 moves are all identical.
Re-running does not add independent strength samples, nor does it constitute C++ port acceptance.
See [official confirmation](../outputs/analysis/notebook-survey-20260916/official-comparison.json).

Export the actor's 30 real observations from a complete sequential replay, producing action program tensors that exactly match those of the original eager model under the same RNG. Additionally, feed three scripts with the first world state and both players' seats across six saved games into the official 1.32.7 interpreter for full replay; the 180 saved neural player observations and final balances are entirely consistent. This is a replay verification, not an additional independent game. See [Export Verification](../outputs/analysis/notebook-survey-20260916/neural-export-verification.json) and [Neural Game Official Replay](../outputs/analysis/notebook-survey-20260916/neural-official-replay.json).

A total of **1,376 local games** were executed (including mirrored control), plus the aforementioned 16 fully replayed official games and six official interpreter replays with saved actions; the total number of games cannot be considered as an equivalent number of independent worlds.
All games completed 719 actions; the evaluation runner did not record any failures; source code hash, report links, and official script manifest identities have been confirmed. See [Total Verification](../outputs/analysis/notebook-survey-20260916/verification.json).
The absence of failures in the runner does not guarantee that upstream script internal exceptions handled by the script itself have been captured.

All evaluations use CPU; no changes have been made to the official training process, weights, script manifest, or native libraries.
If training is integrated, the existing source code freezing, C++ generation, action-by-action equivalence verification, and archive migration workflows should continue to be used.
No new or modified implementation code has been added.
