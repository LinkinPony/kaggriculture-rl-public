# Supplementary Feature Design: Supply and Demand, Operations, and Execution, as well as v4 Permission Reuse

Date: 2026-09-25. The original record pertains to a design proposal and offline compatibility experiment; the user subsequently requested direct implementation of the complete v5b, without ablation studies, and the new BC has now been integrated. The actual calculation methodology, eligibility checks, and training status are governed by [v5b Implementation Guidelines](derived_dsm_bc_20260925.md); the following retains the design derivation and original phased recommendations.

The goal is to delegate to the encoder the work that can be computed from the current observable state and rules, allowing the model to primarily learn resource allocation, opponent responses, and risk trade-offs. Retain the currently trained weights for operations, actions, market, memory, and value networks. The mainline remains unchanged according to [CURRENT_MAINLINE.md](CURRENT_MAINLINE.md); this proposal does not alter the pure terminal WDL reward.

## 1. Judgment and Basis

There is no current shortage of store input. The authenticated U800 deployment package indeed encodes store instances, daily consumption, product price curves, mutually visible production status, 1/2/4 daily output, remaining seasonal output for individual new assets, maintenance and transportation information.
[Actual Input Verification](../outputs/analysis/dsm-duels-20260925/shop-feature-audit.json)
Includes the change in milk demand from 7 → 13 → 19 → 25 units/day before and after the ice cream shop is unlocked.

The true burden is that the model must also autonomously combine dispersed information into:

1. After demand growth, how much of the gap can be filled by existing capacity and in-transit inventory on both sides?
2. When does a new asset begin generating sellable revenue, and what additional feed, maintenance, and labor hours are required?
3. How does increased production affect the selling prices on both sides, not just the individual gross revenue?
4. Can biologically producible items be harvested, stored, and sold in a timely manner?
5. When multiple workers compete for seeds, warehouse supplies, and the same plot of land, which tasks may be missed or delayed?

The average cash difference over the latest ten DSM direct games is approximately -5,404, with the main revenue gap in milk, goose eggs, and tomatoes.
See [DSM Diagnosis](dsm_duels_20260925.md). This supports prioritizing the design of supply-demand and expansion features.
**It does not prove that these features are the sole cause, and cannot be used to commit that adding new features will improve win rate.**
Teacher distribution, BC generalization, and PPO opponent coverage still need to be addressed independently.

### Boundary between Existing Information and New Information

| Domain | Existing in v4 | Newly added computations in this proposal |
| --- | --- | --- |
| Store | Store type, duplicate instances, unlock sequence, daily demand, next consumption timepoint | Precise time-window consumption volume, demand shock, future random store demand distribution |
| Supply | Current inventory, harvestable amount, maintenance scenario yields for 1/2/4 days | 8/12-day and remaining season curve, maintenance/upgrade scenarios, net shortage for both parties |
| Price | Selling tiers, price drop threshold, price after visible supply | Price scenarios driven by time-varying supply and demand, impact of expansion on both parties' revenue |
| Investment | Purchase price, maturity rules, ideal remaining total yield for newly placed assets | Time to first income, input materials, operation volume, break-even conditions |
| Maintenance | Water/fodder shortage, immediate gains, end-of-day losses, CARE payment timing | Marginal impact of current action on remaining seasonal output and resource cost |
| Execution | Most recent workers, most recent tasks, partial material routes, task pressure | Time remaining to complete tasks and sell, approximate task ownership, competition pressure |
| Inventory | Warehouse, backpack, total overflow prediction | Daily end-of-day losses by item/worker, sellable remainder after feed reservation |
| Opponent | Public farm, workers, cash, visible harvest and market flow accumulation | Multi-day changes, estimated quality markers; not treating hidden inventory as "known zero" |
| Market Queue | Autoregressive budget, fixed-price quantity exposure estimate | Sequential price shocks in later stages, inventory estimate after self-actions and subsequent actions |

Related implementations:
[v4 field definitions](../src/kagg_revue/native/agronomy.py),
[Commodity aggregation](../src/kagg_revue/native/csrc/production/products.cpp),
[Yield rules](../src/kagg_revue/native/csrc/production/features.cpp),
[Market budget](../src/kagg_revue/policy/grounded/budget.py).

## 2. Design Principles

### Three semantics must be separated

- **Rule Facts**: Current inventory, consumption plans of unlocked stores, biological effects of the current action, exact spot prices.
- **Scenario Conditions**: Yield, inventory pressure, and cash contribution under assumptions of continuous maintenance, timely harvesting, or enhanced care.
- **Probabilities or Estimates**: Expected value and variance of future random stores, as well as historical behavior inferred from public states.

Field name, registry, and documentation shall specify category, precondition, missing marker, unit, and clipping range.
"Maintained scenario output" must not be named "real future supply"; "conditional net cash" must not be named "guaranteed profit".
The maintained scenario is not the lower bound of output: actual output may be lower due to factors such as food shortages, labor shortages, or mortality.
The enhanced scenario is a clearly defined template and does not claim to represent a proven optimal upper bound of output.

Retain the decomposition quantities, and then provide useful combination quantities. Do not offer only a handwritten total score, asset ranking, or buy/sell recommendation.
Net gap and net cash can be negative; legal actions must not be deleted merely because the score is negative.
New features are still used by the original BC/PPO objective learning; cash-related features do not constitute new reward terms.

### Read only the opponent's observable real state

Training, replay, and deployment share the same C++ computation implementation. The interface provides only the current public state, the player's private state, and past records.
It cannot read the opponent's warehouse/inventory, future actions, future unlocked store types, or the RNG seed.
It cannot advance the real engine or consume its random numbers in order to generate features.
When predicting, future random weeds, future land purchases, and newly acquired assets must be explicitly listed as scenario assumptions.

The opponent's publicly maintained requirements and maturity status are available; fields involving private resources shall be written as 0 and marked as `private_known=0`.
Here, the 0 is a marked missing value, not indicating that the resource is empty. Unknown values must not be represented by NaN: `0 * NaN` will still contaminate the network.

## 3. Two independently verifiable versions

It is not recommended to increase all inputs at once. First, validate the commodity operation layer most relevant to the DSM gap, then add the execution layer.
Two versions must use their own complete version names and schema hashes and cannot share the v4 identifier.

| Proposal Version | Global New | Per Product New ×9 | Per Plot New ×200 | Per Worker New ×64 | Total Input Dimensions | Compared to v4 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Current v4 | 0 | 0 | 0 | 0 | 22,003 | — |
| v5a: Core Operations | 24 | 96 | 0 | 0 | 22,891 | +888, +4.04% |
| v5b: Added Execution Layer | 24 | 96 | 20 | 16 | 27,915 | +5,912, +26.87% |

The following fields constitute the proposed schema, which has not yet been implemented in the native encoder. The index starts from 0, and the extension area is arranged in the order of `global → own/opponent board → own/opponent units → products`. In version v5a, the length of the board/unit block is 0; all shapes are validated by the version registry and cannot be inferred ambiguously from the total length.

## 4. Commodity Layer: 96 dimensions per commodity

### 4.1 Supply and Demand Time Curves: 48-Dimensional

Time window `H = {1, 2, 4, 8, 12 days, remaining season}`. Added 8 days is not arbitrary magnification: cattle, tomato, etc.
New investments have a longer output waiting period; the existing 4-day aggregation window is insufficient to directly compare expansion against demand.
All windows use a sliding time period starting from the current actionable turn and truncated at the last actionable turn.
The original semantics of the 1/2/4-day features in the old v4 are preserved; newly added fields do not silently alter the daily boundary definitions of existing fields.

Each time window continuously stores the following 8 items, totaling `6 × 8 = 48`:

| Local Index | Field | Definition |
| --- | --- | --- |
| 0 | `town_drain_known` | The exact consumption amount of currently unlocked stores and the town center within the window under the maintenance scenario |
| 1 | `own_net_supply_maintained` | The net output of the basic maintenance scenario of the own assets minus inputs, including fertilizer byproducts |
| 2 | `opponent_net_supply_maintained` | The net supply of the opponent's public assets under the same scenario |
| 3 | `own_net_supply_boosted` | The net supply under the own enhanced care/fertilization template |
| 4 | `opponent_net_supply_boosted` | The net supply of the opponent's public assets under the same enhanced scenario |
| 5 | `supply_gap_maintained` | Known demand minus the net supply under both maintenance scenarios and visible spot inventory |
| 6 | `price_maintained_scenario` | The window-end bid when the maintenance scenario supply gradually reaches its target |
| 7 | `price_boosted_scenario` | The window-end bid when the enhanced scenario supply gradually reaches its target |

**Precise calculation of consumption volume.** Let the window be a closed interval `[t,e]`, with spacing `k`:

```text
ticks(t,e,k) = floor(e/k) - floor((t-1)/k)
D[p,H] = shop_weight[p] * ticks(t,e,shop_interval)
       + 1[p != FERTILIZER] * ticks(t,e,center_interval)
```

`shop_weight` is accumulated per store instance, with a weight of 2 for each product in a store.
`t=0` requires the use of mathematical floor; direct use of C++ integer division on negative integers is not allowed.
Stores that have not been unlocked within the window are not included in `D`; their uncertain contributions are separately listed in section 4.3.

**The farm's internal demands must be included.** Net supply is defined as new products + fertilizer collected from templates minus feeding/fertilizing consumption.
Wheat may result in negative net supply even without new crops maturing, due to animal feeding; enhanced crops increase fertilizer demand.
These four components are signed quantities, scaled using signed-log. Diagnostics should additionally record gross yield, input volumes, and the number of fertilizer collection actions to avoid being able to trace repeated deductions based solely on net values. If ablation results indicate a need to expose the full decomposed quantities, a separate schema will be added.

**Inventory shall not be double-counted.** New production excludes already mature and harvestable quantities. Visible spot inventory includes only one instance each from the player's warehouse, the player's backpack, and harvestable quantities on the ground of both sides; the opponent's hidden inventory is not included in this "visible" scenario. A positive net shortfall indicates that new demand exceeds visible supply, but does not mean the market will run out—there is still inventory in the market itself, `I`. The current deviation of the market from its target is retained in existing fields.

Price scenarios require a temporal sequence. It is not possible to directly price `I + total supply - total demand` and call it an exact prediction.
Goods are sold at different times, and a $1 floor price transaction does not increase market inventory.
Maintenance/fortification scenarios use the same delivery agreement: existing warehouses can be sold immediately, backpack items are delivered via separate accessible routes or at the next nightly return to the warehouse; ground products enter the supply queue at the earliest possible delivery time after assumed timely maintenance/harvesting.
The opponent uses only publicly available ground supply and does not inject hidden spot inventory.

Then, pressure scenarios are calculated in the order of market unit-by-unit pricing, input purchase, and consumption; within the same turn, both parties' sales follow concurrent bidding.
Items pre-reserved for self-use in spot markets are deducted from the available for-sale queue, and cannot be added again during consumption.
This represents the potential supply resulting from merging multiple individual feasible routes—**it does not guarantee that workers, capital, or warehouse capacity can be simultaneously supported**.
If the scenario overlooks shared warehouse space and limited labor resources, the output can only be referred to as a price pressure scenario and cannot be labeled as a realizable trade volume.
Specific queue rules, quantity limits, and ignored constraints must be fixed within the schema; before launch, offline error reports must be used to verify deviations.

### 4.2 Add another asset: 16-dimensional, indices 48–63

Calculate for five types of crops and three types of animals; fertilizer rows are not applicable. Candidate placements are restricted to available positions on currently unlocked plots. Structures can be freely built on empty land, but count as a construction action; land purchase or removal of currently producing assets is not implied. Select the shortest setup path among all candidates, with ties broken by plot sequence number; do not provide the model with a manually assigned profit ranking.

| Number | Field |
| --- | --- |
| 48 | `placement_valid`: Applicable candidate exists; all other fields are set to 0 when invalid |
| 49 | `setup_turns_lower_bound`: Minimum time required for purchase/withdrawal/movement/construction/placement |
| 50 | `first_sale_terminal_slack`: Distance from the first product being sold to the end of the game in terms of turns |
| 51 | `incremental_purchase_cost`: Cost of new seeds/animals to purchase; existing inventory is considered sunk cost |
| 52 | `maintained_relative_cash_delta`: Increment to the cash difference between both sides at the end of the game under maintenance scenario |
| 53 | `maintained_feed_units`: Feed required for this new asset in the remaining seasons |
| 54 | `boosted_extra_fertilizer_units`: Additional fertilizer requirement from the enhanced template |
| 55 | `maintained_service_operations`: Number of basic operations such as setup, maintenance, and harvesting |
| 56 | `boosted_extra_operations`: Increment for CARE operations, fertilization, and additional harvesting |
| 57 | `maintained_own_cash_delta`: Increment to the player's cash under maintenance scenario |
| 58 | `boosted_own_cash_delta`: Increment to the player's cash under enhancement scenario |
| 59 | `maintained_break_even_turns` |
| 60 | `boosted_break_even_turns` |
| 61 | `maintained_break_even_exists` |
| 62 | `boosted_break_even_exists` |
| 63 | `boosted_relative_cash_delta` |

The cash increment should compare the "add-one asset" and "no addition" scenarios across the entire farm under the same scenario:

```text
delta_own = own_cash_path_with_asset[-1] - own_cash_path_without_asset[-1]
delta_margin = delta_own - (opponent_cash_with_asset[-1] - opponent_cash_without_asset[-1])
```

This will retain the impact of new supply depressing the prices of existing output volumes on our side, as well as depressing the opponent's prices.
Inputs include purchases and newly added feed/fertilizer; when consuming self-owned wheat, opportunity costs from selling less wheat must be accounted for.
It is not permissible to assume future feeding costs are zero simply because inventory has already been purchased, nor to double-deduct actual expenditures against the same opportunity cost.
Fertilizer by-products are handled according to a fixed template based on whether they are collected, and the collection action is recorded.

The break-even time is the first valid selling point at which the cumulative cash increment, relative to no additional assets, becomes non-negative; if such a point does not exist, use an independent flag. Do not represent "no break-even" as "turn 0". If animals/seeds already exist, the purchase cost is zero, yet future service costs must still be borne. If no sellable products are available even at the terminal state, the remaining balance is negative and the break-even flag is 0.

These values must retain the "scenario" qualification: future employment plans and labor opportunity costs are not deterministic quantities.
v5a Does not impose a fixed wage rate or task value coefficient directly into net cash; instead, it provides operational metrics, resource gaps, and timeframes.
It does not convert a positive `delta_margin` directly into a buy rule, nor does it revise the WDL reward based on that.

### 4.3 Demand Shock and Unknown Stores: 8-dimensional, Index 64–71

`last_unlock_demand_delta`、`turns_since_last_unlock`、
`future_drain_mean_8d`、`future_drain_sd_8d`、
`future_drain_mean_remaining`、`future_drain_sd_remaining`、
`unlock_before_first_new_sale`、`new_shop_demands_product_probability`。

The future store type is sampled with equal probability and with replacement from eight store types according to the public rules; it cannot be assumed that the next store is an ice cream shop.
For product p, the consumption weight of a single store sample is `w[p,s] ∈ {0,1,2}`:

```text
mu[p] = sum_s(w[p,s]) / 8
var[p] = sum_s(w[p,s]^2) / 8 - mu[p]^2
future_mean = sum_j(active_ticks_after_unlock[j] * mu[p])
future_variance = sum_j(active_ticks_after_unlock[j]^2 * var[p])
```

Enumerate only the unlock timing points that are certain to occur within the window before reaching the upper limit of 8 instances.
For example, if a new store's expected daily demand increment for milk is `6 × 3/8 = 2.25`, the actual increment can only be 0 or 6.
Enter the expected value and standard deviation; do not treat 2.25 as an actual observed demand.
Cross-product demand correlations for goods within the same store are defined by the store table; for this period, only input marginal statistics, and do not treat the goods as independent scenarios to calculate "exact" combination investment risks.

### 4.4 Inventory and Execution Aggregation: 8 Dimensions, Index 72–79

`shed_solo_liquidation_cash`、`carried_marginal_liquidation_quote`、
`carried_first_sale_turns_lower_bound`、`parallel_seed_shortfall`、
`tonight_overflow_units`、`feed_reserve_2d`、
`stock_after_feed_reserve`、`ready_harvest_operations_lower_bound`。

- The liquidation value of the backpack is calculated by first selling the warehouse, then selling the backpack items at marginal offers; these offers do not represent current sellability.
- `parallel_seed_shortfall = max(0, eligible_planters_now - own_seed_stock)`.
  This field describes the competition scenario where all currently eligible workers simultaneously cultivate this crop; it is not a decided action conflict.
  In the native rules, if the requested planting quantity exceeds the shared seed supply, all planting requests for this crop will be rejected.
- Overflow at end of day is calculated based on the existing warehouse and backpack items of the player side that will no longer be operated from this point forward; hypothetical unharvested items are not included.
  Precise attribution by product and worker requires preserving the insertion order of visible backpack entries; old caches lacking this order cannot falsely claim precise results.
- Feed reservation applies only to wheat rows with non-zero values; the price impact is calculated by subtracting known available wheat from the basic feeding demand over the next two days.
  It does not assume that the same number of workers will be hired in the future or that wheat will be harvested in time.
- `stock_after_feed_reserve` is a signed difference, directly expressing surplus or shortage of grain.

### 4.5 Multi-day Public History: 16-dimensional, Index 80–95

Two windows: the last 2 days, 4 days. 8 items in each window:

`own_visible_harvest_estimate`、`opponent_visible_harvest_estimate`、
`players_inventory_effect`、`price_change`、`history_coverage`、
`floor_censor_possible`、`harvest_attribution_ambiguous`、`producer_count_balance_change`。

`players_inventory_effect = delta_market_inventory + actual_past_town_drain`.
It is the net effect of bilateral transactions on market inventory, **not the total sales of both parties, nor the opponent's sales**;
A $1 floor price sale does not increase inventory, so the truncation marker must be retained.
Publicly reported output reductions are not always precisely identifiable as harvests: day boundary production, decay, and harvesting may occur in the same step.
When using estimated values, simultaneously mark ambiguity; do not directly infer the opponent's exact transactions from `Δinventory` and our own requested actions.

New game initiation has insufficient coverage of 2/4 days' timeline report. Historical windows cannot inherit across games; repeated observation of the same turn must not result in redundant accumulation. BC must reconstruct these states from the original replay sequence.

## 5. Global Layer: 24-Dimensional

| Index | Field Group | Precise Definition or Boundary |
| --- | --- | --- |
| 0–5 | Actual turn length of six windows | Explicitly exposes terminal truncation to avoid treating a "12-day production" as a complete 12 days when only 2 days remain |
| 6 | `own_critical_work_lower_bound` | Number of service actions required today to prevent death or loss of function, plus a conservative lower bound for necessary movements |
| 7 | `own_critical_work_pressure` | The above lower bound divided by remaining worker turns |
| 8 | `feed_purchase_quote_2d` | Known food shortages under a two-day maintenance scenario, calculated as cost per unit at purchase price |
| 9 | `cash_after_feed_reserve_2d` | Current cash minus the above quote, signed |
| 10 | `own_visible_liquidation_quote` | Conditional clearing bid for own-visible products; no virtual selling price is added if the asset has no terminal residual value |
| 11 | `tonight_overflow_liquidation_loss` | Marginal loss in bid value from overflow products under a scenario of no action from now |
| 12 | `own_critical_unreachable_tiles` | Number of existing plots that cannot be processed by any current worker via the shortest path before the deadline |
| 13 | `opponent_critical_work_lower_bound` | Using only publicly available plots and workers, without assuming knowledge of opponent's resources |
| 14 | `next_land_available` | Whether there are still plots available for purchase |
| 15 | `next_land_new_empty_cells` | Computed according to definite unlock rules, without predicting future weed generation |
| 16 | `reusable_empty_structures` | Current number of empty structures owned; no fabrication of additional "livestock-specific land" constraints |
| 17 | `next_land_cost_per_cell` | Cost of the next plot divided by the number of newly available cells |
| 18 | `next_land_cash_shortfall_after_feed` | Funding gap after deducting maintenance reserves for purchasing the next plot |
| 19 | `next_land_first_service_delay` | Earliest turn delay after purchasing a new plot when work can first be executed on it |
| 20 | `new_tiles_today_operations_upper_bound` | Upper bound derived from remaining working time and at least two actions (planting + watering), ignoring travel, thus not a feasible commitment |
| 21 | `next_hire_cost_per_remaining_turn` | Today's wage for the next hired worker / actual remaining action turns; set to 0 when no turns remain |
| 22 | `new_hand_exclusive_critical_reach` | Number of urgent tasks where new workers can reach promptly upon confirmed birth location, while existing workers cannot |
| 23 | `new_hand_remaining_turns` | Worker appears in the market phase, deducting the portion of turns that cannot be acted upon this turn |

The lower bound for necessary movement can first use `max_task min_worker Manhattan(worker,task)`, then add the number of required service actions.
**It is incorrect to call the sum of distances from each plot to the nearest worker a travel lower bound**: a single worker can serve multiple plots sequentially along the way.
If such a summed quantity still has predictive value, it can only be explicitly named a pressure heuristic.
Land acquisition completes the turn, but planting cannot be immediately performed; locked cells are traversable and should not be treated as obstacles in pathfinding.

## 6. Execution Layer: v5b adds 5,024 dimensions

### Each plot cell has 20 dimensions, totaling 4,000 dimensions on both sides

The first 12 dimensions are based on `WATER, FEED, CARE, FERTILIZE`'s four actions, each with three items:
`applicable`, `remaining_yield_delta`, `marginal_cash_quote`.

Compare "perform once today" with "do nothing today," then use the same basic maintenance/harvesting template.
In the single CARE/fertilization control, no spontaneous make-up of actions skipped on the same day will be added; future templates will not automatically continue additional reinforcement.
CARE benefits are conditional upon the basic feeding requirement being met; fertilization benefits are conditional upon the corresponding watering requirement being met.
`applicable` indicates biological plausibility of the rules and does not substitute for the legality of actions determined by resource holdings and positioning.
Cash quotes deduct the current additional investment or its opportunity cost, but still represent no actual gain derived from a fully scheduled daily plan.

The last 8 dimensions are: `service_turns_lower_bound`, `service_deadline_slack`,
`harvest_delivery_turns_lower_bound`, `harvest_sale_terminal_slack`,
`reachable_worker_count`, `nearest_worker_critical_task_load`,
`service_material_shortfall`, `private_logistics_known`.

The urgent task load of workers on the same plot used to expose contention does not mean that the task must be assigned to that person.
Opponent resource shortages are marked with a missing indicator; the public lower bound of the path remains computable. When there is no task or no product, the value is deemed invalid by checking the old type and task mark along with the newly added applicable flag, and a 0 distance is not considered executable.

### Each worker has 16 dimensions, totaling 1,024 dimensions on both sides

The first 6 dimensions represent the number of tasks that can be completed in a timely manner under the assumption of a single trajectory today: watering, feeding, CARE, fertilizing, harvesting, planting. The count is based on specific task deadlines, not merely the Manhattan radius.

The remaining 10 dimensions: `nearest_partition_critical_tasks`, `partition_work_lower_bound`,
`carried_solo_liquidation_quote`, `drop_sale_turns_lower_bound`,
`terminal_delivery_slack`, `tonight_overflow_contribution`,
`feed_actions_supported_by_bag`, `fertilize_actions_supported_by_bag`,
`private_inventory_known`, `overlapping_critical_candidates`.

Turns are categorized by worker determinacy for statistical purposes only; draws are determined by worker ID, and the model remains free to reassign tasks as needed.
`partition_work_lower_bound` is added to the total number of required service actions in this zone, based on the lower bound of the distance to the farthest task,
without cumulatively adding backhaul routes per task. The worker's backpack has no fabricated capacity constraints proposed herein; warehouse capacity constraints are handled during actual return operations.
For empty worker slots, all newly added inputs are set to zero, while the original token mask remains unchanged.

### Terminal state and phase sequence is a hard constraint

Native sequence is: worker actions → market settlement → town consumption → decay → terminal liquidation or warehouse refill if necessary at the end of the day.
The last executed step in default configuration is **718**; step 719 is terminal observation; no further steps beyond 720 are executed to calculate returns.

- Products dropped/placed into the warehouse by workers during this turn are available for sale in the market during this turn.
- Animals, grain, and fertilizer purchased during this turn can only be used during the next worker phase.
- Seeds are directly drawn from the shared seed inventory; there is no need to enforce a "first carry seeds back to the field" trajectory.
- Automatic returns to the warehouse that occur after the market must wait until the next actionable turn to be sold.
- On the final day, no automatic return to warehouse should be assumed as available for sale; actual availability is determined by the engine's termination condition.
- Once carrying products and at distance d from the warehouse entrance, the earliest sale can occur at `t+d`: move d times, then DROP and SELL in the same turn. The action count is d+1, with a turn delay of d; these actions cannot be mixed.

These boundaries must be incorporated into the first-sale, break-even, and terminal liquidation calculations, and not merely added as "remaining days."

## 7. Right-to-Reuse: Retain Previous Calculations, Add Zero-Initialized Residuals

Current Actor is wide 384, 16-layer, 384-turn memory; Critic is independent
[MemoryCritic](../src/kagg_revue/learning/sequences/critic.py), wide 320, 6-layer entity encoder,
retains its memory and action prefix value head. A simple memoryless Critic cannot be migrated alone.

### Do not expand existing Linear, do not increase token

Retain the existing input projections, local convolutions, full attention, memory, action head, quantity bias, and market budget network for board/units/products/global. The original projection widths are 73, 166, 91, and 200, respectively. Inject by entity type before the old tokens are formed and before they enter the first layer of entity attention:

```text
h_v5[e] = h_v4[e] + A_type[e] * z[e]
A_type starts at zero; no bias; missing workers are zeroed with the original mask.
```

The gradient of the single-layer zero matrix exists from the first turn: `dL/dA = dL/dh × z^T`.
Do not multiply by a trainable gate also initialized to zero, otherwise the matrix and gate may block gradients from flowing.
If replaced with an MLP later, use normal initialization for internal layers and zero out only the final output layer, rather than zeroing all layers simultaneously.

The token count remains at 286, with unchanged position order and attention mask.
Adding zero tokens would alter the denominator of the attention softmax, thus one cannot claim equivalence by citing "zero tokens."
Appending a zero column to the old Linear layer is mathematically equivalent under real arithmetic, but GEMM shape changes introduce additional numerical validation overhead;
An independent addition branch is easier to preserve the original weight shape and optimizer state.
It is not feasible to incorporate new fields into the shared normalization of the old inputs, which would cause the scale of existing fields to change due to dimension expansion.

v5a adds new parameters only for Actor 46,080 and Critic 38,400.
v5b adds a total of Actor 59,904 and Critic 49,920; all other original parameters and buffers retain their names, shapes, and values.
Record branch contribution norms for different semantic groups to prevent any single group's input from dominating the entire increment due to scale differences.

### Retain the location of the old ABI

v4 total width is 22,003, where the last `32×44 = 1,408` represents action validity support.
[GroundedPolicy](../src/kagg_revue/policy/grounded/model.py) and
[ContextEncoder](../src/kagg_revue/policy/grounded/encoder.py) both read it from the end of the input.

```text
v4:  [original semantic region 20,595 | support 1,408]
v5a: [original semantic region 20,595 | added 888   | support 1,408]
v5b: [original semantic region 20,595 | added 5,912 | support 1,408]

legacy_v4(x) = concat(x[:20,595], x[-1,408:])
```

Add new fields before support; maintain the original semantics bit by bit, and preserve the original support bit by bit.
New global fields cannot be inserted into the existing global block, because the old encoder uses the last 64 dimensions of that block to reconstruct the store instance.
The existing market budget maintains unchanged absolute offsets to the original inventory, prices, and cash.

The new encoder explicitly reuses old input slices and token construction, then injects an extended branch.
Version number, extended field dimensions, normalization, and schema hash are written to Layout, checkpoint, and agent_profile.
`strict=False` is silently skipped for parameter mismatches: only missing residual parameters registered as new are allowed, and each must be individually confirmed to have an initial value of zero.
A strict layout comparison of the actual loading path currently rejects v5, requiring a dedicated authentication migration entry.

### Actor, Critic, Optimizer, and History Pool are handled separately

Preferred approach: create a v5 branch with source authentication running from a fixed complete PPO checkpoint:

1. Record the hash of the source checkpoint, source code, native libraries, layout, and reward protocol.
2. Strictly copy all old Actor/Critic parameters and buffers; add only zero-initial residuals.
3. If AdamW is retained, restore the first- and second-moment estimates and step values of the old parameters according to the source archive model's parameter names and order.
   The U800 optimizer only stores parameter IDs, not names; it is not possible to directly align and load new model parameter lists.
   A name mapping must be generated from the authenticated source model, and all slot shapes must be verified. New parameters are initialized with a step value of 0.
4. Freeze the opponent's continued use of their original layouts; v5 input is explicitly projected back to v4, then processed via existing paths supporting v2.
   Verify that native version differences are consistent with game trajectories; do not simply relax `same_interface`.
5. Retain historical PFSP evidence and agent identity; whether the learner continues the same statistical sequence must be explicitly documented in the migration record.
   It is not permissible to conflate saved historical evidence with a new protocol under a restarted statistical sequence.
6. Running RNN/KV cache is not considered part of weight migration: it is reset at game boundaries or reloaded via a new encoder from historical observations.
   Even if the starting point is equivalent, the old KV cache no longer corresponds to the new weights after the first training update.

The existing `initial_weights` entry only migrates the Actor, creates a random Critic and a new optimizer, and requires complete layout equality, without directly claiming that the above scheme is satisfied.
If selecting only Actor warm start is feasible, it must be explicitly stated that the Critic/Adam is not reused; it should not be assumed that they are discarded.

### Offline Compatibility Experiment

Experiment entry: [compatibility.py](../src/kagg_revue/evaluation/features/compatibility.py),
Configuration: [features_compatibility_20260925.yaml](../configs/features_compatibility_20260925.yaml).
Reproduction: `PYTHONPATH=src python -m kagg_revue.evaluation.features.compatibility`.
Use authenticated U800 weights, native encoder within the same package, and real-game trajectories 112952251 over a window of 6 consecutive 8-turn episodes, covering opening, boundary unlocking, mid-game, and endgame phases. Insert an independent zero matrix before the old attention layer, and use limited synthetic data to populate new fields, to verify structural compatibility rather than relying on any specific feature set being exactly zero.

Verification items: old input projection, action field mask, Actor logits, Actor memory, Critic state values, prefix values, Critic memory, and non-zero gradients from the four newly added branches during the first backward pass.
See [Experiment Report](../outputs/analysis/features-v5-design-20260925/compatibility.json).
This CPU FP32 experiment with 48 real observations has passed; the maximum difference between logits and state values is 0, and the original tensors of both networks remain unchanged. The first backward pass of the newly added branches yields finite and non-zero gradients.
This experiment does not equate to the implementation of native v5 encoder, GPU/AMP consistency, full 384-turn memory eligibility, official migration loader, or win rate validation; these remain implementation acceptance criteria.

## 8. Feature Scales, Computing Power, and Data Costs

Add a new field for independent calibration, without modifying any normalization in v4. It is recommended to uniformly register the following scales:

- Non-negative item/operation count: `log1p(x) / log1p(1024)`.
- Signed item difference: `sign(x) * log1p(abs(x)) / log1p(1024)`; market net pressure can also be scaled by corresponding T,
  but each field must be fixed and cannot be re-fitted with training samples.
- Cash and cash difference: `sign(x) * log1p(abs(x)/100) / log1p(1000)`.
- Prices: retain the relative scale of base; do not directly clip wide-scope prices into the same saturated value.
- Short-term service duration/remaining term is scaled by turnsPerDay; long-term break-even/seasonal duration is scaled by the actual maximum action count.
- Ratios and probabilities remain within their natural ranges; boolean values are 0/1.

The denominators for counting and cash scaling are the scale, with no implicit hard upper limits. If clipping is applied for FP16, record the overflow rate, maximum value, and negative ratio; it should not cause most affluent states or long-range unreachable states to become the same value. Unpayable and inapplicable are separately expressed using gap and applicable flags.

Native computation should reuse `production/rules.cpp`, `pricing.cpp`, and the official market settlement functions,
avoiding manual turn-by-turn rewriting of farms, prices, and opponent strategies in Python.
Generate the remaining season curve for each asset once, and use prefix sums to read six windows, avoiding simulation for each H individually.
Biological curves are cached based on full tile state, clock, and configuration; price changes recalculate only economic readings.
Incremental updates for modified plots are aggregated, trajectory reuse leverages existing geometric calculations; cache keys must not omit CARE, fertilization, and decay timestamps.

Given the current update rate of 128 games per update, with self-play contributing approximately 192 trajectories, 719 lines, and FP16 estimation:
v5a incurs an additional **0.228 GiB/update** in raw observations, while v5b incurs an additional **1.520 GiB/update**.
This represents the raw array increment without accounting for replication, concatenation, or intermediate activations—thus not a GPU peak memory prediction.
Neither version increases the number of attention tokens; the primary additional cost arises from native derivation and observation transfer, which should be validated through actual measurement.

Record the computation time for each group during encoding; measure p50/p95, total rollout throughput, and additional time per game on the real CPU export package and current training batch. Use a 15% increase in native encoding latency and a 5% loss in overall throughput as the initial investigation threshold—these are engineering targets, not measured results. When performance is too slow, prioritize caching or reducing low-reward groups before considering increasing the budget.

## 9. Optional Follow-up: Candidate Market Actions and Resource Competition

The current MarketBudget accumulates requests with the current quote and prefix, without precisely updating unit prices or utilizing the changes to the warehouse caused by the workers' actions selected in this turn. Simply increasing static item attributes cannot fully eliminate this burden.

Subsequent enhancements may add retention of the residual zero-residual budget network, providing for the following 8 items based on the **selected market operations and candidate quantities**:
- Quantity of executable trades under the self-prefix scenario
- Total cost/income per unit
- Quote after trade execution
- Remaining inventory
- Cash shortfall
- Warehouse capacity overflow
- Remaining quantity after reserved feed allocation

No access to the opponent's unknown orders in this turn is permitted.
The opponent's simultaneous trading still causes a discrepancy between the self-prefix scenario and the actual settlement, hence it is referred to as the self-prefix scenario, preserving the original legal action space.

Competing actions such as shared seed usage, warehouse pickup, and harvesting within the same grid can be evaluated and diagnosed after the complete worker actions are selected, in conjunction with subsequent market context. If it is desired for workers selected later to see the resource consumption of workers selected earlier, this would alter the current parallel decoding condition structure and should be treated as a separate architectural experiment, not incorporated into the static feature extension of this preservation function.

This phase is not counted toward the v5a/v5b dimensions or parameter budget and requires separate definition of GPU computation, quantization, and CPU deployment consistency.
It is not recommended to generate massive candidate tensors of `worker × plot × commodity × quantity × time` per turn.

## 10. Implementation and Acceptance Sequence

### Step one: Contract and migration

Freeze the fields table, version number, scale, and scenario conventions; achieve native training/deployment/replay source-code consistency.
Implement explicit v4 projection and allow list-based parameter migration. Maintain the original run unchanged, and create a new experiment directory with source tracking.
BC data is re-encoded from original replays: old FP16 arrays cannot recover all historical data, entry order, and unretained states.
Existing action labels, trajectory ownership, and training/validation splits can be reused.

### Step two: Rules and visibility validation

Add only necessary boundary checks for the new logic, reusing the existing native engine comparison:

- Repeat store, single-item double consumption, tick phase, no store, fertilizer, terminal truncation.
- Purchase/hire/buy land after worker phase; DROP occurs before market, auto-return after market.
- Seed dies from lack of watering on the same day; animal CARE/feeding timing, crop decay and harvest are not double-counted.
- $1 floor price, banker's rounding, concurrent orders from both sides, zero profit from buying and immediately selling the same item.
- Simulate changing the opponent's private state while keeping the observer's own visible state unchanged; new inputs must remain unchanged.
- Alter future RNG/actions but keep current and historical visible states identical; deterministic features must remain unchanged.
- Price scenarios are matched item by item against declared scenario settlement mechanisms; do not predict "necessarily equal" conditions based on real future game outcomes.

Zero-branch migration with re-covering of complete turn sequence, dual seat configuration, historical pool v2/v4, CPU FP32, training precision, compilation path, checkpoint saving/loading and Adam slot; finite sample passes non-replacement qualification validation of full path.

### Step three: Feature ablation and training

First run v5a. Fix the same source weights, data split, training budget, opponent pool, and WDL reward, and compare:

1. Original v4; and control groups with added structures but extended input always suppressed.
2. Enable only known demand, supply curves, and net gaps.
3. Re-enable new asset scenarios, resource reservations, and stochastic store statistics.
4. Add multi-day historical data; evaluate v5b plot/worker layers only after revenue is established.

Freeze the old main trunk temporarily to enable short-term branch adaptation, then jointly train with a smaller main trunk learning rate; the duration of freezing is determined by validation results and is not defaulted to long-term BC. If adopting this two-stage optimization approach, the optimizer's processing must be explicitly documented in the source record. When needed, use the distribution of the old model as a short-term anchor point, serving as a clearly specified regularization term, without silently modifying the PPO target or rewards.

Offline analysis of BC validation NLL, expansion behavior response, feature saturation rate, gradient, and branch contribution, stratified by product, store type, and stage.
For each observation, mask different newly added groups separately and check changes in output distribution; for legally unlocked stores, recompute all related features and verify whether there are responses in supply-demand, pricing, and expansion decisions. Note that attention weights and non-zero gradients only indicate the existence of computational paths and cannot alone prove that a particular group of features has decisional value—final validation must rely on ablation studies and actual game outcomes.
Split by full game and submission version to avoid shared trajectories or adjacent segments between both sides across training/validation splits.
Improvement in BC NLL is only evidence of learning; responses to counterfactual actions in replay should not be considered as "winning DSM".

Official games use fixed seeds and alternating pairing; report wins/draws/losses and uncertainty in pairing differences.
Cash, output, price, idle land, feeding/harvesting failures, and overflow serve as diagnostics.
For DSM, if no original policy is runnable, only retained replay can be used to validate imitation/response; claiming offline execution of a real DSM is not permitted.
Evaluate cross-distribution performance of random store types: high milk demand, high tomato demand, low livestock demand, and repeated single-item stores.

The mainline has removed automatic periodic evaluation. The eligibility and ablation of this proposal are explicit offline experiments; it should not be re-introduced into training with automatic evaluation through feature modifications, nor should the ongoing training or submissions be prematurely modified.

### Recommended landing point

First deliver the 888 operational core and strict weight migration of v5a, enabling the model to directly observe key combinations of supply-demand and expansion volumes.
Then use the route, deadlines, and contention features of v5b to convert potential gains into actual revenue.
Separate experiments for complex market prefix actuarial calculations and worker decoding modifications, ensuring each step is attributable and original weights remain reusable.
