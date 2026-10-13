# 2026-09-19 Public Notebook Investigation

**Found publicly available scripts significantly stronger than the current V45; prioritize Thomas 2945, followed by Ahmed V49;
However, no such scripts were found to outperform the current neural model.** Thomas achieved **154–6** against five new public opponents,
while scoring **1–31** against the current U3044; V49 also achieved **1–31** against U3044, matching the win count of the current V45.
Thus, these scripts are supported as candidates for inclusion in the public benchmarks and opponent pool updates, but their claim of providing greater WDL training pressure is not supported.

The subjects under comparison are the currently training model **agronomy-v4 / s73001 / U3044**, and the current native script **Ahmed V45**. The evaluations of the old s68001 and s69001 from September 16 do not serve as substitutes for this comparison.

## Source and Fixed Benchmark

Query two pages of 100 entries each via Kaggle CLI using `dateRun` and `scoreDescending`, merging **320 notebook references**; download 16 sources, statically extracting **14 distinct codebases**.
This is not exhaustive. The list sorting does not provide numerical scores, and thus cannot be used to prove a strategy is stronger.
All original notebooks, metadata, extracted codebases, and SHA-256 hashes are preserved in
[Source Directory](../data/external/kaggriculture-notebook-survey-20260919/), see
[Source List](../outputs/analysis/notebook-survey-20260919/acquisition-summary.json).

At **02:22 UTC** with the latest complete checkpoint U3044 / **389,632 RL games**,
using CPU FP32, T=1, full **384 turn memory**. The players switch seats; in each game, the neural agent's sample seed is `2 * world seed + neural-policy seat`. Each script uses the same world seed and neural agent sample seed.
The native engine advances random states naturally, without forcing a fixed subsequent shop sequence. Checkpoint SHA-256:
`f6119ef1bed5647e2a9927c72a60c08c1470d825d8e7a23007adc7acc7c02cad`.
See [Frozen Identity](../outputs/analysis/notebook-survey-20260919/neural-reference/selection.json).

The Kaggle API returns, during this query, the earlier U2724 submission of the current model:
T=1 / **56331777: 3056.5**; T=0 / **56331731: 3049.5**.
This is not the online rating of U3044, nor does it treat ratings from different times and match opponents as direct win rates.
See [API Snapshot](../data/external/kaggriculture-notebook-survey-20260919/our-submissions.json).

## Most Worth Watching New Sources

### Thomas: The 2945 Farm, prioritize research of candidates

[Notebook](https://www.kaggle.com/code/thomastschinkel/the-2945-farm-96-vs-the-top-10-public-bots),
API last run time **September 19 00:15 UTC**.
Source code `bfee70e9daaebeae0737a880f1df8f1c60d0783c59af620136cc0d28ef482bc7`.

Retain the V39/V40 route foundation, but introduce significant adjustments in production and labor: safe initial setup; predict opponent sales based on observable market changes; substitute carrots for wheat when the route can complete watering and harvesting; adjust herds based on both parties' production capacity and store conditions; expand sheep populations earlier and reduce the number of workers required for expansion; harvest animals nearing full capacity; protect warehouse space during midnight.
Compared to merely adjusting only the early sale timing, this approach covers a broader range of behavioral changes.

The author explicitly discloses that the script achieved a record of 0–36 against seven of the top ten teams online, and analyzed the insufficient mid-to-late stage tomato production capacity and labor planning. This is self-reported by the author and cannot be considered as local empirical validation; the "96%" in the title should not be interpreted as the win rate against private top-ten models.

### Ahmed V49: Direct upgrade candidate for current V45

[Notebook](https://www.kaggle.com/code/ahmedberatozer/kaggriculture-v49-funded-sale-timing-and-worker),
API last run time **September 18 21:26 UTC**.
Source code `7d5777978465a2dd18b85fbef9d354d3cc9e008c279630e7655e5a517058b960`.

Compared to V45, the changes are cumulative: V46 corrects the initial-round procurement and wheat trading, and adds early selling; V47 introduces market coordination, overflow protection, and livestock-related store logic; V48 removes invalid sell orders and consolidates cash sales of the same product. In this V49, demand protection-based 14-step early selling and worker recovery are retained, and future sales previously protected are released when current cash is sufficient to cover a conservative procurement budget plus a 1,000-unit reserve. These mechanisms remain patchwork adjustments to the route strategy and cannot be generalized into a new general planner.

### Other candidates

- [Tetsu: Demand-Preserving Turn Sale Timing](https://www.kaggle.com/code/tetsutani/demand-preserving-turn-sale-timing):
  The latest source code is v65; the safe sale window has increased from 13 to 14 steps; it returns to 3 steps when two bakeries are already present, indicating that the yarn shop provides protection for long-term wool sales. Suitable for studying the timing of sales and conditions for inventory retention.
- [First in Line](https://www.kaggle.com/code/alperen5252525/kaggriculture-first-in-line-stock-into-income):
  Retains the V48 base; primarily sets the advance sale step to 8. It cannot be considered an independent new production strategy.
- [Melon Threshold Squeeze](https://www.kaggle.com/code/goodpjw2008/kaggriculture-melon-threshold-squeeze-2749):
  Involves small-scale round-trip transactions in the first turn, wheat squeezing in the second turn, and early sale, targeting the cash threshold for procurement in the same source script. Has value for early-game disturbance resilience testing, but its mechanism does not guarantee effectiveness across different opening configurations for neural models.

## Current V45: All six primary candidates are clearly superior

First, conduct an initial screening using four worlds and initial seat assignments for 14 different source codes. Then, pre-fix **32 new worlds**
`1860919201`–`1860919232`, completing **64 full games** for each of the six main candidates.
The following statistics are reported from the new script's perspective; funding differences are for diagnosis only and are not used as training rewards.

| Candidate | Win / Draw / Loss | Average Final Capital Difference |
|---|---:|---:|
| Thomas 2945 | **64 / 0 / 0** | **+5,537.8** |
| Ahmed V49 | **64 / 0 / 0** | +2,502.1 |
| Ahmed V48 | **64 / 0 / 0** | +2,570.8 |
| Tetsu v65 | **64 / 0 / 0** | +2,442.1 |
| First in Line | **64 / 0 / 0** | +2,800.2 |
| Melon Squeeze | **64 / 0 / 0** | +2,295.7 |

Thomas's average funding gap in the world seed clustering bootstrap 95% interval is **[+4,334, +6,937]**;
V49 is **[+2,050, +2,985]**. Dual seats are not independent worlds, and a sample of all wins is not proof of overall victory.
See [confirmation game](../outputs/analysis/notebook-survey-20260919/confirmation-v45/summary.json),
[statistics](../outputs/analysis/notebook-survey-20260919/script-statistics.json).

During the initial screening, Pipe-8, although defeated V45 8–0, gained only **1 yuan** per game; Farming V5, Jaxa Open10, and Salem all suffered 0–8 records. Farming V5 shares the same frozen source code as September 16, with no new version changes.

## Between New Scripts: Thomas has the greatest advantage

Additionally use **16 new worlds** `1860919401`–`1860919416`, with each opponent having a double seat for 32 games.
The following statistics are presented from **Thomas**'s perspective.

| Opponent | Thomas win/draw/loss | Thomas average terminal cash margin |
|---|---:|---:|
| Ahmed V49 | **30 / 0 / 2** | +3,800.0 |
| Ahmed V48 | **32 / 0 / 0** | +4,030.2 |
| Tetsu v65 | **30 / 0 / 2** | +4,117.3 |
| First in Line | **30 / 0 / 2** | +3,774.5 |
| Melon Squeeze | **32 / 0 / 0** | +5,047.0 |
| Total | **154 / 0 / 6** | +4,153.8 |

The strict win rate of the sample is **96.25%**. This is the result from five specified public opponents and the same group of 16 worlds, and it cannot be equated to the win rate across 160 independent worlds or against all opponents online.
See [Complete Comparison](../outputs/analysis/notebook-survey-20260919/confirmation-thomas/summary.json).

Also fix 16 new worlds `1860919501`–`1860919516` comparison V49 versus its relatives:
V49 versus V48 is **32 / 0 / 0**, versus Tetsu v65 is **22 / 8 / 2**,
versus First in Line is **24 / 0 / 8**. Thus, V49's upgrade value has direct match support,
not merely due to a newer version number. See
[V49 Comparison](../outputs/analysis/notebook-survey-20260919/confirmation-v49/summary.json).

## Confirmation of the Current Model

Neural confirmation uses another 16 new worlds `1860919301`–`1860919316`, with V45, Thomas, and V49 each playing double seats for 32 games. The following statistics are all from the **script side** perspective.

| Script | Wins / Draws / Losses vs U3044 | Win Rate | Average Final Capital Difference |
|---|---:|---:|---:|
| Active Ahmed V45 | **1 / 0 / 31** | 3.125% | −12,301.2 |
| Thomas 2945 | **1 / 0 / 31** | 3.125% | −9,246.7 |
| Ahmed V49 | **1 / 0 / 31** | 3.125% | −12,191.0 |

Thomas's funding gap relative to V45 improved by **+3,054.5**, with a 95% bootstrap confidence interval for the world seed cluster: **[+722.1, +5,719.3]**; however, the outcomes of the 32 games were identical across all matches. It narrowed the gap, but did not increase wins in this sample, and thus cannot equate improvements in cash metrics to pure terminal WDL improvements.

The funding gap improvement of V49 is only **+110.2**, corresponding to the interval **[−3,210.1, +3,225.2]**.
It converts a loss from V45 into a win and turns V45's only win into a loss, leaving the net number of wins unchanged.
This indicates it can provide different match scenarios, but it does not prove the overall difficulty has increased.

See [Complete Neural Confirmation](../outputs/analysis/notebook-survey-20260919/neural-confirmation/summary.json),
[Pairing Statistics](../outputs/analysis/notebook-survey-20260919/neural-statistics.json).
Conclusions are limited to a fixed checkpoint, 16 worlds, and CPU FP32 / T=1 inference; no evaluation of T=0, and no generalization of finite-sample conclusions to all public notebooks or online opponents.

## Suggestions

1. **Prioritize Thomas 2945 as the new public evaluation benchmark and training pool candidate.** It demonstrates the clearest advantages over the specified new public panel and involves a wide range of behaviors related to production, labor, warehousing, and markets.
2. **V49 is proposed as a successor candidate to V45.** Direct advantages over V45 and V48 have been confirmed; however, the win rate for current learners has not improved. If integrated, source code freezing, C++ generation, full action equivalence, and batch processing acceptance are still required. Native integration qualification has not been completed or claimed in this instance.
3. Tetsu, First in Line, and Melon Squeeze can be used for specialized evaluations of selling timing or opening pressure. It is not recommended to expand the formal pool solely based on notebook titles, version numbers, or the number of derivatives sharing a common base.

If the goal is to find publicly available scripts that can defeat the current model in most games, no such scripts have been identified in this investigation.
Replacing older public opponents might improve coverage, but long-term RL gains still require separate validation.

## Evaluation Accuracy and Limitations

- **The entry point must follow Kaggle's last callable.** V47 is `_y_agent_shopherd`, V48 / First in Line is `_e335_agent`, V49 is `_e346_agent`. Directly importing the function named `agent` would evaluate an old internal strategy. This version uses the official 1.32.7 wheel loading function to validate 14 candidates in one game each, with **10,066 actions** completely matching.
- The saved actions from 12 script games and 10 neural initial screening games were fed into the official 1.32.7 interpreter, resulting in **31,680 step observations** and full final cash balances matching exactly. This is a replay verification and does not add independent strength samples.
- U3044 exported actions and sampling RNG match the original eager model over a full real trajectory, with **719 actions** and RNG samples in alignment, and 31 time points of KV cache passing tolerance checks, covering memory eviction after 384 turns. The codebase matches the training source archive, including 569 strategies and original source code files.
- Download sources contain duplicates: Sunil V8 and Ahmed V48 are byte-for-byte identical; Guru's two notebooks are byte-for-byte identical. Guru and V48 have identical trajectories in the initial screening, but differ in source code bytes, so they cannot be considered equivalent across all states.
- In the neural initial screening, each of the five versions achieved 0–4 in four games each; Tetsu and First in Line only reached this small sample size. Their four-game results are not considered reliable win rate estimates. The confirmation phase and initial screening results are reported separately.
- The first initial screening was terminated by the runner due to Salem accepting only one parameter; a complete summary was not written. After supplementing and adapting the call signature, all candidates were fully re-run. The final choice is `screen-v45-fixed`, with failed batches not counted as valid samples.

See [Official Entry Verification](../outputs/analysis/notebook-survey-20260919/official-loader-verification.json),
[Script Official Replay](../outputs/analysis/notebook-survey-20260919/script-official-replay.json),
[Neural Official Replay](../outputs/analysis/notebook-survey-20260919/neural-official-replay.json),
[Export Verification](../outputs/analysis/notebook-survey-20260919/export-verification.json),
[Model Source Code Verification](../outputs/analysis/notebook-survey-20260919/model-source-verification.json).

The offline runner is [evaluation/notebooks.py](../src/kagg_revue/evaluation/notebooks.py), using [Hydra configuration](../configs/notebook_survey.yaml); the seed, opponent, model, and source code identity for each phase are preserved in the corresponding `protocol.json`. A total of **868 valid, complete games** have been completed, excluding failed initial screening batches, repeated action verification, and official interpreter replay. The 868 games cannot be considered as 868 independent worlds.
The new runner passes Ruff and full mypy checks on **858 files**.
Formal training continues with the original configuration, C++ opponent pool, and pure terminal WDL rewards.
