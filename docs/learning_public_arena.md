# Public Script Evaluation of the New Random Root Model

`learning.public_arena` only loads candidates from the current random root ledger, and public opponents come from explicitly hash-locked entries in the `data/external/` list. There are no interfaces in the training entry or population to read this list.

```bash
PYTHONPATH=src python -m kagg_revue.learning.public_arena
```

Default configuration [learning_public_arena.yaml](../configs/learning_public_arena.yaml) fixes two completed runs, with 0/64/128 budgets, 64 games per pair using identical 32 environment seeds. Repeated measurements must override `arena.output_dir` with a new `outputs/analysis/` directory to avoid overwriting original evidence.
Independent confirmation using `arena.role=confirmation`, `arena.seed=1250000000`, `arena.games_per_opponent=128`, and `arena.updates=[0,128]`; candidate training must be completed.
The full external protocol also fixes the 0/128/512 budget comparison for long-budget models, see [protocol](../outputs/analysis/scratch-public-opponent-protocol.json).
Its configuration is [learning_public_scaling_arena.yaml](../configs/learning_public_scaling_arena.yaml), run via `--config-name=learning_public_scaling_arena`; execution is rejected until the full 512-round process is complete.
Long-budget external confirmation uses starting seed 1,280,000,000, 128 games per pair, preserving budgets of 0/128/512. The primary conclusion must verify the 128→512 transition under the same random root.

The entry point archives the complete source code, model ledger/member hashes, script inventory, and sampling rules prior to the game start. Candidate exports are provided as FP32 CPU TorchScript, preserving random actions; each game uses an independent RNG of `2 * environment seed + candidate seat`. Budget pairs are assigned per game. External scripts instantiate a new module per game; both sides receive only the official side's observation. The official interpreter and native engine perform turn-by-turn confirmation of the full state. Any uncaught exceptions or state discrepancies from external scripts will result in measurement failure. This differs from the BF16 GPU evaluation runtime environment, and the results from the two cannot be mixed in paired comparisons.

A public trajectory and rule family is selected this time:
[Shape the Shop Work the Pasture](https://www.kaggle.com/code/tetsutani/shape-the-shop-work-the-pasture-kaggriculture).
The original notebook was not executed; the `main.py` string literal at cell index 9 is decoded, matching the notebook's built-in SHA256 exactly. The compressed payload contains only the action trajectory, and the code imports only base64/json/zlib.
The complete notebook, metadata, trajectory decoding, and inventory are permanently preserved in
[Data Directory](../data/external/kaggriculture-public-agents-20260907/manifest.json).
The current public file does not equate to verified leaderboard scores, and other derivative versions of the same trajectory do not count as separate strategies.

The first technical review at turn 0 reported differences in the `market.params` field: refeeding the native complete configuration into the official interpreter treats default market parameters as explicit overrides, altering the observation field. The evaluation entry has been changed to faithfully pass through the original configuration, without removing fields or relaxing state validation. The fixed [16-game qualification](../outputs/analysis/scratch-demonstrations-public-qualification-v2/comparison.json) passed 23,040 observations; the two sub-mini-batches are not used to demonstrate strength.

The complete [selection](../outputs/analysis/scratch-demonstrations-public-arena/comparison.json) and [confirmation](../outputs/analysis/scratch-demonstrations-public-confirmation/comparison.json) have both concluded, with 384/512 games respectively. All budget points suffered complete losses; in independent confirmation, the cash of the two 128-turn models increased from their initial values of 23,839.62/21, 230.32 to 64,049.81/62, 601.67, but the opposing team's cash remained at 93,378.05/94, 632.84. This result supports operational profitability but does not support improved victory from this external strategy.

Here, we measure the correctness of full games and external opponent returns; Kaggle host resource budget remains unverified.

The [0/128 selection baseline](../outputs/analysis/scratch-scaling-public-arena-128/comparison.json) for Xinchang budget has also been completed, with all four points failing 64 games each. The 128-turn cash balance is 57,183.31/50, 897.88; external opponent values are 99,028.19/106,730.55. Both runs show relative initial cash gains, with no wins yet. The original protocol and training recipe are retained, and the 512-turn terminal evaluation is assessed under the original protocol without adjusting rewards or learning the opponent based on these external results.

<a id="section-4eee0c2ff2de"></a>

## Revenue and Production Diagnosis

Evaluate the current additional recording of actual market settlements between both parties, submitted unit operations, progressive production state counts, and daily inventory snapshots.
The observer is located at `evaluation/accounting.py`, does not provide any additional input to the strategy, and does not call random number generators.
The number of submitted operations does not equal the number of successfully executed operations; crop, animal, and inventory counts are not converted into assumed realizable revenues.
Daily snapshots are collected at the start of each day, at which point the rules have cleared the previous day's workforce; workforce utilization should be based on the cumulative value of `unit_turns`.

First, complete 16 qualification rounds on the two original seed environments, then retest the full 0/128 panel, totaling 256 rounds across 32 original environment seeds. After the new core and financial records are activated, all complete action hashes, cash flows, outcomes, and original measurements remain consistent. 368,640 official observations match exactly, and all per-seat financial balance equations hold true. See
[Complete Verification](../outputs/analysis/scratch-demonstrations-public-accounting/qualification.json).
This is a diagnostic replay of existing games, adding no independent strength samples and not altering the original confirmation conclusions.

The average outcome of turn 128 is:

| Training seed | Candidate / Opponent revenue | Candidate / Opponent market expenditure | Final cash difference |
| --- | --- | --- | ---: |
| 47001 | 102,319.31 / 128,362.39 | 34,886.94 / 29,759.81 | -31,170.20 |
| 47002 | 95,866.41 / 128,352.28 | 31,830.66 / 29,740.50 | -34,576.03 |

These two sets of discrepancies mainly reflect a shortfall in sales revenue of 26,043.08/32,485.88, along with additional expenses of 5,127.13/2,090.16. In Turn 360, both sides had an average cash balance of approximately 22,000, after which the gap continued to widen. The number of turns occupied by candidate crops and the unit usage have nearly reached those of the opponent, while animal occupation remains low, and actual revenue is still behind; these are observed operational differences, and thus cannot be used to conclude that any single operational change can eliminate the gap. Under the same publicly available strategy, prices and revenues vary depending on the specific candidate, and the opponent's cash balance cannot be treated as a fixed counterfactual.

See the complete project and item breakdown in [Revenue and Expenditure Summary](../outputs/analysis/scratch-demonstrations-public-accounting/figures/summary.json),
cash changes over the season are shown in [Curve](../outputs/analysis/scratch-demonstrations-public-accounting/figures/cash-trajectories.png).
Plots and JSON can be reconstructed via `PYTHONPATH=src python -m kagg_revue.learning.accounting`;
Hydra configuration is set to [learning_accounting.yaml](../configs/learning_accounting.yaml).
Mypy passes for Ruff and 600 source files; this workflow validation uses the aforementioned complete game and prior trajectory confirmation.

<a id="section-cedebee1e8bf"></a>

## Supplementary Reactive Rule Family

To increase coverage of different implementations, on 2026-09-07, [EcoBot v7](https://www.kaggle.com/code/premaananda108/economics-driven-rule-agent-ecobot-v7-arena) was obtained from a public notebook.
The API record shows the last execution on September 1. The text at cell index 2 of `%%writefile main.py` was extracted verbatim,
the original notebook was not executed, and the file SHA256 is
`0dc02e03c94ef60c06b5093efc2e2fd0530aa6eea20df507a90b90d6651bd067`.
The code only imports standard libraries, computes returns and work trajectory based on observations; no external models, fitted trees, encoding trajectories, file/network calls were found. The original notebook, metadata, extract, and source hash are retained in
[Data Registry](../data/external/kaggriculture-public-rules-20260907/manifest.json).
Another version of Structured Economic Policy is explicitly stated to be a derivative of Kaito v58, and was neither executed nor incorporated into new family coverage.

Fix measurement results prior to [Supplementary Agreement](../outputs/analysis/scratch-public-rules-protocol.json):
First model selection uses 1,340,000,000, budget 0/64/128, 64 games per point; independent confirmation
Use 1,350,000,000, budget 0/128, 128 games per point. Long-budget group reserved separately
1,360,000, 000/1, 370,000,000, all with budget 0/128/512, still primarily using the 128→512 ratio per root.
Configured as [learning_public_rules_arena.yaml](../configs/learning_public_rules_arena.yaml) and
[Long-budget Configuration](../configs/learning_public_rules_scaling_arena.yaml). Original route opponents and their agreements remain unchanged,
opponents reported separately by category.

[16 games qualifying](../outputs/analysis/scratch-demonstrations-public-rules-qualification/comparison.json)
23,040 official observations have passed verification and financial reconciliation; its two seed entries cannot prove strength.
The first complete selection and independent confirmation have both concluded, with 384/512 games and 552,960/737,280 official observations fully consistent, and all per-seat financial balances verified and balanced. This opponent is solely for evaluation; its current ranking strength has not been validated, and it does not claim to have no source association with all daily label authors.

| Training seed | Selection 0 / 64 / 128 round win rates | Independent confirmation 0 → 128 round win rates | Confirmed paired increment and 95% interval |
| --- | --- | --- | --- |
| 47001 | 4.69% / 60.94% / 82.81% | 2.34% → 82.03% | +79.69 percentage points [72.66, 86.72] |
| 47002 | 0% / 62.50% / 67.19% | 0.78% → 73.44% | +72.66 percentage points [64.06, 81.25] |

confirmation: 128 games per budget point, 64 environment seeds; terminal win counts are 105/128 and 94/128, with no draws.
Candidate terminal cash values are 83,837.07/83,332.35 and 65,537.55/64,783.20 for the same EcoBot.
Relative increases in cash compared to fixed demonstration terminal points are 57,758.55 [52,550.93, 63,324.08] and 59,006.73 [53,153.55, 64,834.66]. See
[complete selection](../outputs/analysis/scratch-demonstrations-public-rules-arena/comparison.json),
[independent confirmation](../outputs/analysis/scratch-demonstrations-public-rules-confirmation/comparison.json), and
[confirmation cash curve](../outputs/analysis/scratch-demonstrations-public-rules-confirmation/figures/cash-trajectories.png).

The percentage point increments for the 64→128 selection are +21.88 [9.38, 34.38] and +4.69 [-10.94, 21.88]; the latter interval crosses zero, so we cannot claim stable improvement across each budget segment. Both cash increments are positive, at 11,474.98 [6,343.42, 16,780.68] and 7,166.38 [441.93, 13,872.15]. These results support the actual external gains of the supplementary family; the complete defeat of the original route's opponents and the longer budget issue remain separately unaddressed.

The long budget group's [0/128 baseline](../outputs/analysis/scratch-scaling-public-rules-arena-128/comparison.json) on EcoBot has also been completed, with four points each running 64 games, totaling 256 games and 368,640 official observations all passing confirmation. Score for 51001 increased from 0% to 60.94%, with a pairing interval of [48.44, 73.44] percentage points, and cash rose from 23,645.36 to 73,971.13; for 51002, the score increased from 0% to 29.69%, with an interval of [20.31, 40.63], and cash rose from 10,652.86 to 63,664.16.
This uses the pre-determined selection seed of 1,360,000,000. The initial strength differences between the two are clearly evident. We are still awaiting the results of the 128→512 expansion and independent confirmation. Both have now been completed, as detailed below.

## Complete External Results of 512 Turns

Each family has 384 selection games, 768 independent confirmations, all with full official status verification and detailed cash reconciliation per seat. The source code fingerprint is
`af0df2947bb8706c2ffda351d0852ebfb3e45eced8a7a06316b7456412d1f125`, using a standalone native core.

In EcoBot confirmation, 51001 increased from 63.28% to 91.41% (117/128 wins), and 51002 increased from 42.97% to 96.88% (124/128 wins). The increment from 128 to 512 is 28.13/53.91 percentage points, with paired 95% intervals [19.53, 36.72]/[44.82, 62.50]. Cash increased by 24,180/26,931, with intervals [19,198, 29,351]/[22,637, 31,115]. See [EcoBot Confirmation](../outputs/analysis/scratch-scaling-public-rules-confirmation/comparison.json) and [Operational Reconciliation](../outputs/analysis/scratch-scaling-public-rules-confirmation/figures/summary.json).

Trajectory family confirmation achieved only 2/128 and 0/128 wins with score increment intervals of [0.00, 3.91] and [0.00, 0.00] percentage points, respectively, and failed to meet the late-game winning criterion based on two random roots. Although cash increased by 14, 255/16,957, it still lags behind the opponent. See [Trajectory Confirmation](../outputs/analysis/scratch-scaling-public-confirmation/comparison.json) and [Operational Ledger Review](../outputs/analysis/scratch-scaling-public-confirmation/figures/summary.json).
Each family is interpreted separately; the complete table and protocol identity are available in [Conclusion Index](../outputs/analysis/scratch-scaling-conclusion/report.json).

The 0/128 of 256 legacy trajectories, cash, results, and official observations from each family have been consistently verified.
The TorchScript type indices of the second exported class vary with export order, so archived SHA values do not need to be identical; they have been separately validated against the original archive hash, fully consistent forward code, and all frozen constants. See
[Route Re-testing](../outputs/analysis/scratch-scaling-public-arena/repeated-points.json) and
[EcoBot Re-testing](../outputs/analysis/scratch-scaling-public-rules-arena/repeated-points.json).
These repeated trajectories are not considered as new independent samples.
