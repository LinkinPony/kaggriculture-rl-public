# Daily Replay for September 6–8: Strategy Behavior and Three Types of Training Data Recommendations

2026-09-09 Download and confirm [official daily index](https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index),
Latest release date is **2026-09-08**. Download the September 8 ZIP, reusing the previously saved packages from September 6–7.
All **1,988 games, 3,976 bidirectional trajectories, and 2,858,744 decisions** have been analyzed; 81 team display names are present,
All replays are in environment `1.32.7`, 720 frames, both sides marked DONE, 1,988 distinct environment seeds.
Three dates contain 662, 663, and 663 games respectively. Original ZIP, index, and source hashes are permanently preserved in
[original list](../data/external/kaggriculture-episodes-survey-20260909/raw/manifest.json).

daily is a sample selected by the official based on the average rating per game, and does not represent all participants.
Replays do not have submission IDs; display names may include different versions, and different display names cannot be automatically considered as separate strategy sources.

## Most Worth Noting Conclusions

**SpaTaro is the strongest candidate with high variability, but RL remains unconfirmed.** The first 24 action sequences of 249 trajectories are all distinct: September 7 81/81, September 8 168/168. Within the same date and seat, the repetition rate of complete unit instruction vectors is only **4.1%**; the median coverage of known public routes is **2.2%**.
Under the same date, seat, and initial observation, the first complete action has **17–39 variants**, appearing on both dates.
This supports the hypothesis of "runtime randomization, search, or sampling-based strategies," but cannot distinguish between random scripts, multiple parallel versions, search programs, and RL.

A direct evidence comes from the September 7 seat 0 episode **106575245 / 106604850**:
The initial full observations are identical, including the same 60-second remaining time buffer; the initial wheat purchase quantities are 6 and 3, respectively.
Among the four randomly sampled SpaTaro replays, the extra time consumption is entirely concentrated on the first move, ranging from approximately 7.67 to 10.25 seconds.
Thus, the time consumption likely stems from loading or initialization, and cannot be used to claim that it performs continuous search at each step.

**ymg_aq is quite flexible, but currently resembles a candidate with a limited opening and closed-loop control.** Among 294 trajectories, only 11 types exist.
With a 24-move opening, the first move is always identical, and the unit instruction repetition rate across the entire game is **7.0%**, with publicly available route coverage at the median of **0.6%**.
All 13 groups with visible historical divergence originate from September 7, at decision steps 9–10.
This is more localized than SpaTaro's consistently varying first move and full opening sequence, suggesting the need to prioritize excluding version mixing or internal stochastic branches.

**HowardLeeTW is very strong and shows great flexibility in later stages, but RL evidence remains weak.** In 114 samples, it won **96 games (84.2%)**, with a median terminal cash of **108,274**; the unit instruction repetition rate in the first 24 steps is **97.0%**, and remains at **80.0%** from steps 24 to 71, dropping significantly thereafter.
Among 586 comparable first-day historical groups, no action discrepancies were found. It can currently be regarded as a strong closed-loop strategy candidate, but this does not allow us to determine whether it is a rule-based program or a deterministic learning strategy.

The public route family still exists, but "similar routes" cannot be equivalent to "the same script".

| Display Name | Trajectory Count | Most Similar Public Route | Median Best Unit Route Match Rate per Game | Public Controller Normalized Full Action Match Rate |
|---|---:|---|---:|---:|
| Aastik Rajan15 | 15 | farming_v4 | 100.0% | 99.6% |
| Jun_value | 22 | shop_router_0908 | 100.0% | 74.5% |
| Subin An | 13 | shop_router_0908 | 100.0% | 89.8% |
| Asterios Terzis | 13 | shop_router_0908 | 100.0% | 89.5% |
| DECEM | 12 | shop_router_0908 | 99.7% | 90.4% |

The "unit trajectory" includes only farmer/hands, preserving quantity and order, without market data.
The controller validation runs existing native scripts on the recorded real-state stream and compares farmer/hands/market;
standardizes default quantities, appends trailing PASS commands, and removes empty commands after market order limits are reached.
8 public trajectory similarity groups collectively complete validation across **182 trajectories and 130,858 decisions**,
with no trajectory showing complete consistency with the step-by-step output of the selected public controller.
Thus, it can be concluded that trajectory templates are clearly associated, but actual submissions cannot be asserted as identical, and one cannot ignore market control merely based on unit trajectories.
See [native validation](../outputs/analysis/daily-behavior-20260906-08/native-confirmation.json).

## If the training data is divided into three categories

Suggest categorizing by **behavioral mechanisms and the capabilities they require to be learned**, rather than by "script/RL" tags:

| Category | Behavioral Characteristics | Candidate Fragments in This Data | Training Value |
|---------|----------------------------|----------------------------------|----------------|
| A: Fixed Route Execution | Long action prefixes or fragments repeated, primarily executing along a predefined route | farming/shop route family execution fragments; stable opening moves by Mengfei Li, "find gaps" teams | Learn basic operations such as planting, breeding, transporting, hiring, and selling, as well as long-process workflows |
| B: Situation-Driven Adjustment | Stable opening or production skeleton, with branching based on shops, prices, inventory, opponent, and self-progress | HowardLeeTW, Otter Vibe's later stages; ymg_aq's interpretable branching; public router's routing node selections | Learn to observe states, choose routes, adjust production and sales, and correct deviations |
| C: High Variation / Exploration Candidates | Significant trajectory differences on the same day and seat; limited templates fail to cover all cases; observable historical states may still diverge | Most evident in SpaTaro; unexplained variation fragments in teams like ymg_aq are treated as low-confidence candidates | Supplement state and behavior coverage, provide multiple actionable options and exploration starting points |

These are the **pending verification action labels**. The causal relationships of B-class states cannot be proven solely by correlation, and C-class is not equivalent to RL. Rule scripts can enter B/C, and neural networks can enter A. The current tool outputs six descriptive screening labels; this section's three classes are recommendations for data stratification aimed at training, and the training set has not yet been reconstructed.

Division should follow:

1. **First divide the full game into training, validation, and holdout sets, then slice.** Both teams in the same game and all time slices remain within the same partition. The current seed isolation rule continues to apply. Additionally, introduce a route family holdout evaluation to check for overestimation of generalization due to repeated public routes; this is an extra evaluation design, not to mislabel ordinary seed holdout as a new strategy holdout.

2. **Use context-aware trajectory fragments as labeling units.** Begin with a 24–72 step window, preserving causal prefixes, states, and opponent information. A single team or even a single game can contain A/B/C type fragments. For scripts that start with a fixed opening and switch lines after the shop appears, the opening belongs to A, while route selection and adjustment nodes belong to B.

3. **Separately analyze unit actions and market actions.** Pair fixed unit routes with price-sensitive selling rules; the market component still retains B-class value. Do not use a strict metric such as "a single different group instruction leads to completely different steps," instead replace it with final per-unit labels.

4. **Record confidence and quality separately.** Alongside labels, retain source date, version uncertainty, similar route families, fragment stage, trajectory log count, and divergence evidence. For low sample sizes or unmodeled mechanisms, preserve soft A/B/C weights to avoid hard classification based solely on display names. Win rate, cash balance, legal action rate, and operational effectiveness are used as separate quality metrics—do not consider variability as a sign of high quality.

5. **Enforce intra-class repetition limits and inter-class sampling control.** Set upper limits on similar routes within A-class, while preserving meaningful executions under different states; B-class retains trigger states and context before and after branching; C-class fragments are first preserved and annotated, then reviewed for invalid actions and source quality. Multiple actions under the same state can serve as distribution learning material and should not be directly collapsed into a single dominant action.

If a BC first-round comparison configuration is needed, set **A/B/C = 30% / 50% / 20%** as the starting point based on decision row counting, and impose limits within each group by route family and game stage. This is an **unverified experimental suggestion**, not the optimal ratio derived from the 1,988 games analyzed; it should be compared against the current natural sampling baseline under the same budget, and evaluated using untrained opponents, seeds, and full game performance. Do not alter the existing training data or configuration based on this analysis.

## Other Useful Findings

- 46 display names covering at least 10 trajectories each, with 3,867/3,976 trajectories; among them, **31 have only one 24-move opening**, and **37 have a main opening share of at least 80%**. Performing BC solely based on frequency tends to over-weight repeated openings.

- "Flexibility" does not equal "strength": SpaTaro's sample win rate is **55.4%**, ymg_aq is **57.8%**, HowardLeeTW is **84.2%**, and Otter Vibe is **73.0% (46/63)**. Differences in opponent pools, dates, and store distributions mean these values are suitable for filtering candidate evaluation subjects, but cannot be directly interpreted as fair rankings.

- Significant daily variations are observed within the same display name: ymg_aq's three-day win-loss records are **36/43, 125/78, 9/3**, with opening counts of **3, 11, 2**. The final day having only 12 games should not be interpreted as sustained improvement in performance.

- Store distribution warrants stratified evaluation. For example, in the Jun_value sample, the 12 games with PET_CAFE have a median cash value of **79,966.5**, while the 10 without it have a median of **117,964.5**. This is a small-sample correlation influenced by other stores, opponents, and strategy versions; it is better suited to guide seed pairing validation and cannot be taken as evidence that PET_CAFE caused these losses.

- The number of display names in the samples on September 8, September 7, and September 6 were 47, 37, and 38, respectively. The sample composition changes continuously, so the overall win rate variation over three days does not solely reflect progress of the same set of strategies.

## Products and Reproduction

- [Complete Statistics Report](../outputs/analysis/daily-behavior-20260906-08/report.md)
- [Searchable and Sortable Interactive Table](../outputs/analysis/daily-behavior-20260906-08/dashboard.html)
- [Independent Behavior Chart](../outputs/analysis/daily-behavior-20260906-08/behavior.png)
- [Team CSV](../outputs/analysis/daily-behavior-20260906-08/teams.csv), [Daily CSV](../outputs/analysis/daily-behavior-20260906-08/teams-by-date.csv), [Matchup CSV](../outputs/analysis/daily-behavior-20260906-08/matchups.csv)
- [Historical Discrepancies, Opening Time Series, Economic Summary](../outputs/analysis/daily-behavior-20260906-08/diagnostics.json)
- [Machine-Readable Metrics](../outputs/analysis/daily-behavior-20260906-08/report.json), [Extraction Result Verification](../outputs/analysis/daily-behavior-20260906-08/extraction.json)

Implemented at `src/kagg_revue/datasets/behavior/`, Hydra configured as
[`configs/daily_behavior.yaml`](../configs/daily_behavior.yaml). Reproduction command:

```bash
.venv/bin/python -m kagg_revue.datasets.behavior.cli
```

Reproduce using a saved index snapshot; to retrieve data for a later date, specify a new raw/output directory via Hydra, ensuring that old indices and original source records remain reproducible. The code is validated through Ruff, full mypy (651 source files), and 3 essential tests: action format and count, trajectory statistics for same-day same-seat pairs, and alignment between initialization frames and decision actions.
