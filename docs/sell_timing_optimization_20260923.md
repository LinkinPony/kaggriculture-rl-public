# Optimal Solutions, Stable Advantages, and Precise Optimization of Exit Timing (2026-09-23)

**Conclusion: This game has no guaranteed winning strategy, but it does have a transferable stable advantage; the optimal selling point can be precisely solved, yet its value is almost entirely derived from "selling a few steps before the opponent," and the gain is determined by the predictor's estimation of when the opponent will sell, not by the solver itself.**

- Scored by wins, draws, and losses; this game is a symmetric zero-sum game with a game value of 0, and no strategy can guarantee victory over all opponents.
  DSM won 660 out of 688 games against opponents with terminal cash at least 90,000, with its main advantage stemming from production efficiency and demand-responsive production.
- After fixing opponent orders, the selling problem can be decomposed unit-by-unit: each product is an exact dynamic programming problem for `O(K·T)`,
  warehouse and cash constraints are coupled via Lagrange multipliers, and the empirical dual gap median is 0.1%–0.7%.
- When perfectly anticipating opponent orders, only rescheduling selling times is needed, and the median terminal cash difference improves by **+4,777 to +7,672**,
  exceeding DSM's median lead over us in 25 games by 3,670.
- When relying solely on information available at the time, solving with a single prediction is essentially useless or even harmful: predicting "opponent repeats yesterday",
  our terminal cash difference changes by **−3,912 / −4,271** for us and DSM respectively. When opponent timing has ±4-step errors,
  switching to expected value over 8 scenarios still yields **+3,678 / +3,253**, improving across all 25 games.
- This analysis and documentation are provided without modifying training, rewards, code, opponent pool, or submission.

## 1. Background: Mathematical Optimal Solution and Stable Advantage

This section presents the conclusion of the previous analysis conducted on the same day. A replay of the snapshot from that time (08:13 UTC) is provided, with individual game intermediate results not archived at the time;
the market tables and pool values have been confirmed according to the engine price function this time.

### An optimal solution exists, but is not a winning solution

- This game is a finite-step (719 decisions per player), stochastic, simultaneous-move two-player game scored based on win/loss, making it 0-sum.
  By the minimax theorem and Kuhn's theorem, the game value and optimal strategy exist; the optimal strategy may require randomization.
- The engine has two symmetric positions: identical initial states; for every market transaction, both players receive the same price before executing their own trades.
  Workers and land acquisition only affect one's own farm; weeds and shops share a common random number stream, with symmetric distributions.
  DSM achieves win rates of 96.8% and 95.0% at positions 0 and 1, showing no positional advantage.
- In symmetric 0-sum games, the value is zero. Any strategy, when faced with its mirror image, has an expected score of zero.
  Therefore, **there does not exist a strategy that guarantees a win against all opponents**; the optimal strategy only guarantees non-loss in expectation.
  It cannot be computed exactly; historical pool PFSP combined with self-play belongs to a class of methods that approximate this solution.
- The leaderboard measures win rate against actual opponent populations, not the minimax value.

### Why can a stable advantage be formed?

Two farms operate completely independently, with the only coupling being a shared market inventory, plus victory determined by relative cash balance. Almost all information is publicly available:
Opponent farm (including pending harvest yields), cash balance, and market inventory are visible; only the warehouse is hidden, but can be inferred from harvests and transactions.
Both sides share the same town and face the same set of stores, and world luck largely cancels out in the cash difference.
Thus, this game is closer to "two nearly deterministic single-player optimization problems, plus a small shared market."

| Product | Drops to $1 when initial inventory is increased by how many units | Quarterly expected town demand |
| --- | ---: | ---: |
| Wheat / Eggs | Never (remains at $19 / $38 even with surplus of 1,000) | 525 / 228 |
| Strawberries / Milk / Wool | 62 / 76 / 59 | 426 / 327 / 228 |
| Tomatoes / Carrots | 529 / 842 | 228 / 327 |
| Cucumber | 158 | 30 (only in town center) |
| Fertilizer | 493 | 0 |

- **Wheat and eggs** are nearly infinitely elastic fallback options, with no mutual impact between the two sides.
- **Melons and fertilizer** have no store demand and are fixed pools on a first-come, first-served basis. The value of inventory exceeding the initial stock is 26,485 and 25,045, respectively. Selling 72 melons results in 16,785 for the first seller and only 9,371 for the second; when sold in alternating order, each receives 13,126.
- **Other products** have demand that depends on randomly drawn stores—for example, the probability of drawing no wool shop in 8 attempts is 34.4%.
- Transaction amounts are typically small but can disrupt fragile budget logic: in the first turn, ymg_aq trades 60 units of wheat, resulting in a $38 shortfall and the inability to purchase two seed units (see [56266758 Game Analysis](submission_56266758_matchups_20260918.md)).

### Top Games

From the DSM dataset, filter out 688 games where both parties' final cash balances are at least 90,000, replay each transaction individually, and ensure that all final cash balances match the official records.

- DSM won 660 games. In 15 games or more, all 7 opponents were suppressed by DSM, with the lowest being 11/17 against DECEM, and 31/32 against Majkel1337.
- The median cash difference was 11,871, approximately 10% of the final cash; only 6% of games had a difference within 2%, and about 17% had a difference within 5%.
- The fixed pool has been short-sold: the combined median number of "melon" shorts by both sides was 144 (pool capacity 158), with combined median fertilizer holdings at 514, and a median final fertilizer price of $9; combined median revenues for both sides were 28,596 and 26,090, respectively.
- Melon short-selling has intensified to the same turn: in 77% of games, the first melon sale occurred at step 249 (on day 10), and in 48% of games, both sides sold at the same step.
- The winning side does not win by aggressively seizing the pool. Based on the median revenue difference from product sales (with the number of leading games in parentheses):

| Product | Strong vs. Strong: Winner − Loser | DSM − Us (25 games with replay available) |
| --- | ---: | ---: |
| Strawberry | +4,210 (76%) | +1,069 (64%) |
| Tomato | +2,568 (80%) | +4,554 (92%) |
| Carrot | 0 (49%) | +2,249 (92%) |
| Wool | +1,642 (84%) | −55 (48%) |
| Melon | −3,550 (16%) | −224 (12%) |
| Fertilizer | −1,642 (26%) | −296 (40%) |

DSM has a record of 58 wins and 11 losses against us (Unknown Mother-Goose). In the 25 games with replays, DSM won 22 games. The median cash difference is 3,670; DSM's median investment is approximately 4,100 higher, with the majority of the recovered amount coming from tomatoes and carrots.
The 56468475 (s78001 U340) submitted on September 22 has a record of 0 wins and 10 losses against DSM.

### The paths listed at that time

1. **Approach the single-player production frontier.** The two farms operate independently, making "how much profit can be maximized in the absence of opponents" essentially a deterministic planning problem. Randomness is limited to 0.5% weeds and store draws per cell per day. Upper bounds can be derived at the macro level for each store sequence (what to plant, how many cells, when to buy land, how many workers to hire, when to sell—using mixed-integer programming or dynamic programming). This allows quantification of the gap between DSM and the frontier, serving as a consistent and stable BC teacher trajectory, and enabling macro-level planning while relying on the network for execution. This is the most transferable and stable source of advantage.

2. **Transition production based on store demand and opponent-visible capacity.** Each store reveals one demand every 3 days, allowing direct calculation of remaining demand; opponent crops and animals in fields are visible, enabling prediction of future supply. DSM's early lead in tomatoes and carrots falls into this category.

3. **Precise optimization of selling timing:** Explored in Sections 2–9 of this paper.

4. **Terminal solution and risk adjustment based on game outcome.** In the final one or two days, the game approaches complete information with a short number of steps, allowing for search or dynamic programming: lock in gains when leading, and actively increase variance when falling behind. This is decisive in approximately 17% of games with a score gap of 5% or less.

5. **Measure non-transitivity within the self-strategy pool.** Conduct cross-game matchups among candidate strategies, then perform transitivity/cycle decomposition ([Balduzzi et al. 2019](https://arxiv.org/abs/1901.08106)). If the cyclic component is small (DSM's performance suggests this), investment should focus on a single dominant strategy and planning, rather than expanding the diversity of the historical strategy pool.

### A Path That Cannot Be Traversed

- **Winning strategy**: Does not exist in symmetric zero-sum games.
- **Predicting random numbers**: The seed is hidden from players; daily shop draws also depend on the number of empty spaces held by both sides that night, as each empty space consumes one random number. The presence or absence of weeds per cell per day contains approximately 0.045 bits of information, while each shop draw contains about 3 bits of information. Theoretically, observations over ten days are sufficient to uniquely determine a 31-bit seed; however, brute-force search would require about 6,400 core-seconds, far exceeding the total time budget of approximately 780 seconds per game. Moreover, the seed is deliberately concealed, making its exploitation carry significant risk. Section 6.2 further shows that future shop sales have little value.
- **Pure market arbitrage**: Buy prices are set based on inventory after trade execution, and sell prices are based on inventory before trade execution. When market conditions remain unchanged, a buy-and-sell cycle results in a net zero return; the only items that can be repurchased are wheat and fertilizer, and the warehouse's 100-cell capacity limits hoarding.

## 2. Engine Rules for Determining Sale Value

All of the following have been verified against the official 1.32.7 engine source code.

- **Price**: Determined solely by the market inventory of the product; the higher the inventory, the lower the price. Initial inventory I0 = 10,000.
  Selling is priced based on inventory before trade execution. When theexecution price exceeds $1, inventory increases by 1; if theexecution price is exactly $1, inventory does not increase.
  Only wheat and fertilizer can be bought back, priced based on inventory after purchase (inventory − 1).

- **Matching**: Each side may place up to 10 market orders per turn, with HIRE and BUY_LAND also occupying slots.
  For the i-th slot, orders are first processed in player order for HIRE / BUY_LAND, followed by sequential unit-by-unit matching for SELL / BUY:
  Each round, both sides receive a quote for one unit based on the same inventory, and trades are executed sequentially.
  Thus, the party with the earlier slot position sells first within the same turn. When both sides sell the same product at the same slot, they trade 1:1 at the same price, alternating turns.

- **Town Consumption**: Occurs after each market round.
  When `step % 4 == 0`, each unlocked shop instance consumes once; single-product shops (wool shop, pet café) consume 2 units each, while other shops consume 1 unit per product;
  When `step % 24 == 0`, the town center consumes 1 unit of each product except fertilizer.
  Shops are randomly drawn with replacement at the end of days 2, 5, ..., 23, with a maximum of 8 instances.

- **Warehouse**: Only items in the warehouse can be sold, with a maximum capacity of 100. DROP actions are stored during the unit action phase (before the market), and any excess is discarded immediately. Thus, items dropped during the current turn can be sold during the same turn. At the end of each day, inventory is automatically stored after the market, also capped at 100; these items can only be sold starting from the next turn.

- **Deadline**: The final processing step occurs at turn 718 (719 actions per side), after which the remaining inventory value is 0.

## 3. Mathematical Structure

**Unit-by-unit breakdown.** Let `B(t)` be the inventory trajectory after removing all of our sales, determined by opponent orders and urban consumption.
If our k-th sold unit is settled at step t, its price is `p(B(t) + k − 1)`, which depends only on `(k, t)`.

When there is no opponent, sell later is better. At this time, `B` is monotonically non-increasing (with only consumption); each unit should be sold as late as possible, except that warehouse and cash constraints force early selling. Doing so when there is an opponent is disastrous (see Section 6.1).

The cash difference can also be precisely decomposed. If my unit k sells before opponent unit u, the inventory of u increases by 1 and the price drops by one level when u settles:

```text
cash difference = constant + Σ_k [ p(B(t_k) + k − 1) + D_k(t_k) ]
D_k(t) = Σ_{u: t_u > t} [ p(b_u + k − 1) − p(b_u + k) ]
```

Here, `b_u` is the inventory at the time opponent unit u is sold, excluding our sales. The constant is the negative of the opponent's revenue without our influence.
The derivation uses only this fact: we sell units in chronological order, so if unit k is sold before u, the preceding k − 1 units are also sold before u.
Except for the $1 price floor, this is an exact identity; within the same step, the opponent is processed first.

**Exact Dynamic Programming for a Single Product.** Units are sold in chronological order, `t_1 ≤ … ≤ t_K`; the selling time of the k-th unit is not earlier than `a_k`, and `a_k` is obtained as the suffix minimum of the available quantity (cumulative sold plus current inventory). Let `v_k(t)` denote the value inside the brackets of the above expression:

```text
F_k(t) = v_k(t) + max_{t' ≤ t} F_{k−1}(t'),   t ≥ a_k
```

Implemented using prefix maximum, complexity `O(K·T)`.

Products are coupled using shadow prices.

- Warehouse constraint written as "cumulative sales ≥ L(t) by step t", multiplier `λ(t) ≥ 0`;
  Effect is to reward each unit sold at step t with bonus `Σ_{s ≥ t} λ(s)`.
- Cash constraint written as "cumulative revenue ≥ C(t) by step t", multiplier `μ(t) ≥ 0`;
  Effect is to multiply the price by `1 + Σ_{s ≥ t} μ(s)`.
- After relaxation, each product is solved independently; multipliers are updated using Polyak's subgradient method, and feasible solutions are obtained via greedy repair.
  `λ` and `μ` are the shadow prices of warehouse and cash, respectively.

**Exact under uncertainty.** For an open-loop plan, the cash difference is the sum of the individual `v_k(t_k)` units, and the expectation can be taken term by term. Replace `v_k(t)` with the scene-averaged `v̄_k(t) = (1/S) Σ_s v_k^(s)(t)`; within the same dynamic programming framework, the exact optimal expected cash difference is obtained. Each step's re-solution corresponds to a receding-horizon MPC. If direct optimization of win rate is desired, iteratively re-solve by weighting scenarios according to `w_s ∝ φ(m_s / σ)`, where `m_s` is the terminal cash difference in scenario s, and `φ` is the normal density. Each round still employs the same dynamic programming formulation.

## 4. Experimental Method

### Sample

- **Same-game samples**: 25 games involving our side against DSM (2026-09-19 18:13 to 09-23 08:17 UTC), selected by randomly drawing with fixed seed from 26 replayable games available at analysis time, sharing 24 games with the 25 games in Section 1. Our side submitted 56468475 in 11 games, 56417993 in 6 games, and the rest were 56447050 (3), 56360218 (2), 56463811 (2), and 56401905 (1). In these 25 DSM games, DSM won 23 games, with a median cash difference of 3,670.
- **Strong opponent samples**: 80 games excluding our side, where both sides ended with at least 90,000 cash (2026-09-17 16:25 to 09-23 06:45 UTC), involving 63 distinct opponents; DSM won 78 of these games.

### Replay, Simulation, and Counterfactuals

- Replay actions from both sides using the native engine `Engine(seed, configuration)` and `step_with_trace` based on their recorded logs, gradually tracking initial inventory, unlocked shops, each market order (slot, type, requested quantity, traded quantity, cash change), step-end cash, step-end warehouse, and peak warehouse during the step.
- A standalone step-locked market simulator has step-by-step reproduced the inventory and transaction cash flow for all 105 games.
- For counterfactual scenarios, only the selling orders of the studied positions are reorganized: all SELL orders are removed, while other orders from the same side, all opponent orders, and shops are preserved. Production is fixed, and the earliest possible selling time per unit is determined by minimizing the suffix of the cumulative sales plus step-end warehouse inventory. All new self-side sales within the same step are placed after all step-locked orders.
- Warehouse constraint: the excess inventory held beyond the actual level does not exceed `100 − max(current-step peak, next-step peak)`.
- Cash constraint: the actual cash balance plus the change in cumulative revenue under the model must not fall below `min(200, actual cash)`, ensuring that all actual purchases are financially feasible.
- Evaluations are performed by precisely re-simulating all transactions for both sides, reporting changes in own-side revenue, opponent-side revenue, cash difference (the difference between the two), and the minimum cash under the counterfactual scenario.

### Solution

- Unit-by-unit dynamic programming for each product; warehouse and cash constraints are relaxed using Lagrange multipliers, with Polyak step size set to `1.5 ×(dual value − best feasible value)/ ‖subgradient‖²`.
- Feasible solutions are obtained via greedy repair through forward scanning: for warehouse shortages, prioritize units that incur the smallest loss in value when scheduled earlier; for cash shortages, prioritize units that incur the smallest loss per dollar when scheduled earlier.
- Perfect foresight of up to 80 turns is performed once, using the actual selling plan as the initial feasible solution; daily re-solution is conducted for up to 40 turns.

### Daily Re-solution

At the start of each day (steps 0, 24, ..., 696), construct a predictive world: prior to these steps, use real historical data; thereafter, our non-sell orders are based on actual values. Stores are fixed as unlocked (except under the omniscient condition), and opponent orders are predicted according to the following table.
Solve from the current state to terminal liquidation, executing only the day's sell orders; re-solve the next day, and finally evaluate precisely in the real world.

| Mode in Results | Opponent's Future Orders |
| --- | --- |
| `oracle_full` | Real orders, store also uses real future orders, used to validate the re-solution process itself |
| `oracle` | Real orders |
| `jitter{w}x{S}` | Real orders, each order independently shifted by [−w, w] steps (truncated between current step and step 718); each re-solution resamples S versions, S = 8, and takes the average of the price and value matrices |
| `early4` / `late4` | Real orders, but considered to occur 4 steps earlier / later |
| `volume` | Real daily sales volume for each product, uniformly distributed across the 24 steps of the day |
| `repeat` | Daily orders repeat the previous day's orders, with day 0 considered to have no orders |
| `stock` | `repeat`, then evenly sell out the opponent's current inventory over the remaining days |
| `silent` | No orders anymore |
| `asap` / `after_drain` | No prediction: sell upon arrival / wait until the next store consumption after arrival (`t % 4 == 1`) |

## 5. Results: Upper Bound of Perfect Prediction

One-time solution: opponent orders, stores, and our production are fixed, satisfying warehouse and cash constraints.

| Group | Seats | Median Actual Sales Revenue | Optimized for Own Revenue: Own / Opponent / Cash Difference | Optimized for Cash Difference: Own / Opponent / Cash Difference |
| --- | ---: | ---: | --- | --- |
| DSM (All) | 105 | 144,579 | +9,894 / +7,150 / +2,498 | +7,207 / −148 / **+7,672** |
| DSM (Same Game) | 25 | 129,513 | +8,707 / +7,831 / +628 | +5,377 / −373 / **+4,777** |
| We | 25 | 121,377 | +10,561 / +9,143 / +962 | +6,023 / +642 / **+5,447** |
| Other Strong Teams | 80 | 138,710 | +9,146 / +7,364 / +2,014 | +5,892 / −275 / **+6,954** |

- When optimizing cash margin, all 210 positions improve. When only optimizing our own revenue, the opponent nearly takes the same amount, resulting in only minor improvements in cash margin; thus, WDL requires a relative target.
- Revenue is concentrated in products with steep price curves in overcapacity segments. When optimizing cash margin, the median incremental revenue for our side is milk +1,488 to +2,329, strawberry +1,193 to +1,653, wool +435 to +1,564, and all other products have increments of no more than approximately 220.
- Removing warehouse and cash constraints and optimizing only our own revenue, the optimal strategy is to stockpile as much as possible toward the end: our side gains 42,000 to 45,000, the opponent gains 54,000 to 57,000, cash margin decreases by −7,017 to −15,872, and severely violates cash constraints. Stockpiling effectively gives money to the opponent; the warehouse capacity remains a continuously active constraint.
- Dual gap median: optimizing revenue yields 0.62%–0.66%, while optimizing cash margin yields 0.12%–0.19%. The constrained solutions have a minimum cash 5% quantile of −171 to −352 under exact simulation, indicating cash approximation error.

## 6. Results: How much can be obtained with only the information available at the time

![Sale Point Value and Opponent Point Prediction Quality](../outputs/analysis/sell-timing-20260923/sell-timing-value.png)

### 6.1 Causal Decomposition Across 25 Games in the Same Match

Daily reanalysis, median change in cash difference (parentheses indicate the number of positions among the 25 that improved):

| Condition | Us | DSM |
| --- | ---: | ---: |
| Omniscient, including future store state | +5,435 (25) | +4,850 (25) |
| Opponent orders known, store only knows unlocked items | +5,378 (25) | +4,619 (25) |
| Opponent time point ±2 steps, average over 8 scenarios | +4,500 (25) | +3,722 (25) |
| Opponent time point ±4 steps, average over 8 scenarios | +3,678 (25) | +3,253 (25) |
| Opponent time point ±8 steps, average over 8 scenarios | +2,175 (23) | +1,112 (22) |
| Opponent time point ±12 steps, average over 8 scenarios | +1,150 (20) | −17 (12) |
| Opponent time point ±2 steps, single-point prediction | +1,307 (23) | +1,221 (14) |
| Opponent time point ±4 steps, single-point prediction | +337 (15) | −380 (10) |
| Opponent time point ±12 steps, single-point prediction | −1,337 (3) | −2,220 (2) |
| Opponent orders believed to be 4 steps early | +247 (15) | −1,022 (10) |
| Opponent orders believed to be 4 steps late | −2,267 (3) | −3,738 (1) |
| Only know opponent's daily actual sales | +967 (19) | −373 (10) |
| Sell immediately upon arrival | −805 (7) | −1,597 (2) |
| Wait until next store consumption after arrival | −3,415 (0) | −5,150 (0) |
| Opponent repeats yesterday's sales and evenly distributes current inventory | −3,544 (0) | −4,026 (0) |
| Opponent repeats yesterday's sales | −3,912 (1) | −4,271 (0) |
| Opponent stops selling | −11,180 (0) | −10,864 (0) |

### 6.2 Interpretation

- **The solution process itself is correct.** Under full knowledge, daily re-solution (±5,435 / ±4,850) matches one-time solving (±5,447 / ±4,777).
- **Future stores are nearly worthless.** Knowing only the unlocked stores results in a loss of only 57 / 231; inferring random number seeds for selling purposes is unnecessary.
- **The precision of opponent timing determines everything.** The true opponent count is fully known, with only noise added at timing points. Across 8 scenarios, the retention of "opponent order known" gains drops to approximately 84% / 68% / 40% / 21% (ours) and 81% / 70% / 24% / 0% (DSM) when timing noise is ±2 / ±4 / ±8 / ±12 steps. Knowing daily sales only performs as well as ±12 steps.
- **Expectation over the prediction distribution must be taken.** Single-point predictions perform significantly worse than the 8-scenario average: near zero at ±4 steps, negative at ±12 steps. This is because the value function has a cliff at the opponent's trade moment—selling one step earlier is first-mover advantage, one step later means trailing the opponent. Single-point predictions place units precisely at the cliff edge, where slight timing deviations cause drops; averaging across multiple scenarios blurs the cliff into a slope, allowing the planner to naturally incorporate a lead time commensurate with uncertainty.
- **Failure modes are identical.** The planner delays sales to wait for town consumption, causing the opponent to sell first at a higher price. Under single-point and naive prediction, the opponent's revenue median increases by +1,880 to +4,558 ("opponent does not sell" increases by +14,056 / +14,974); in contrast, the 8-scenario average shows only an increase of +16 to +1,067 at ±2 / ±4 steps.
- **The timing of the existing two strategies is already quite good.** Both outperform the "on-arrival sell" strategy and the naive planner. The remaining margins are similar (+5,447 vs. +4,777), so timing of sales is likely not the primary reason DSM outperforms us. However, this margin is still larger than DSM's median lead over us in these 25 games by 3,670.
- **Gains span the entire season.** Under the "opponent order known" condition, random checks of two games across four positions show that our revenue fluctuates by approximately ±2,000 daily from day 7 to day 29, with the final day's contribution ranging from −167 to +4,813.
- **Hourly timing alone cannot locate opponents.** Both strategies sell in about 40% of steps (median at 290 / 297 steps), with sales concentrated at hour 0 (DSM: 17.4%, ours: 14.6%) and hour 22 (15.0% / 10.5%), with the rest spread out.
- **The magnitude of first-mover advantage.** The slope in the linear region above initial inventory for strawberries is approximately $1.92 per unit. Both sides sell 30 units from initial inventory; first-selling gains $1,727 over later-selling, with cash difference fluctuating by $3,454; delaying by one consumption cycle (reducing inventory by 4 units) yields only an additional $230.
- **Cash approximation.** The 5th percentile of the minimum cash under various conditions ranges from −187 to −761;
  "Wait until the next consumption" performs the worst (we at −1,156, DSM at −786), actual implementation requires a buffer.

## 7. C++ native system design

Computation is not the bottleneck; all algorithms can be implemented in native C++. The design focus is on the opponent sale predictor and the planner that computes expectations over distributions.

### Observe opponent selling (each step, microsecond-level)

- Except for wheat, fertilizer, and a $1 transaction, the opponent's selling volume per step per product equals the change in public inventory minus our sales, plus town consumption, allowing for precise back-calculation; wheat and fertilizer additionally require integration with changes in the opponent's public cash.
- The code reserves `opponent_shed_estimate` input (`src/kagg_revue/native/csrc/actor_encoding.hpp`'s `SeatView`), but the training batch, deployment session, and Python caller invoking it have not filled in the values—**it is currently always 0**.
  A new estimator must be created to maintain the opponent's warehouse and on-hand inventory based on harvests from their farmland, worker positions, and the back-calculated transactions.
- The opponent's farm publicly reveals: mature crops, recently harvested plots, and worker distance from the warehouse—these are all signals indicating "soon to be sold."

### Opponent Sale Predictor (determining the upper limit part)

- Output sampled trajectories for future step-by-step sales volumes of each product: near-term steps (24–48 steps) with gradually refined granularity, while distant-term forecasts require only daily-level volume estimates.
- Training data uses all games from `data/external/kaggriculture-dsm-replays/` and our own games, conditioned by team characteristics, or adapted online within a game based on the opponent's behavior in the days prior.
- Variants of the publicly available notebook scripts can directly use existing native scripts to forward-simulate scenarios from estimated states.
- Acceptance focuses on cash differences in counterfactual replays rather than likelihood. Following the curve in Section 6.2, near-term point errors should retain approximately 80% accuracy within ±2 steps and approximately 70% accuracy within ±4 steps.

### Planner (re-solve at each step)

- Sample 16–64 scenarios per step, replay the baseline inventory trajectory one by one, compute average unit price and value matrix, then run dynamic programming and Lagrange multipliers; initialize the multipliers using the values from the previous step.
- Scale is approximately 1,800 units × 719 steps × 32 scenarios, estimated at 0.1–0.2 seconds per step (unmeasured).
  Current network cold start takes about 1.63 seconds, and subsequent steps take no more than 0.401 seconds (see [current mainline](CURRENT_MAINLINE.md)), leaving room within a 1-second time limit.
- Output the quantity of each product sold and slot ordering at each step: products in competition are prioritized to the front.
  In the experiment, all our own sales at the same step are placed behind the opponent's, thus slot priority yields additional gains.
- Cash constraints require the strategy to plan future expenditures: first, retain a typical amount of spending for several hours; a better approach is to treat the shadow price of cash as a feature for the strategy.
- Win rate target: using scenario-weighted iteration as described in Section 3, reduce variance when leading, and increase variance when falling behind.

### Terminal Module (last 1–2 days)

- Both sides must liquidate their positions before move 718; the remaining holdings can be roughly estimated, forming the strongest structural segment.
- When targeting cash differential, the first mover's value doubles; both sides desire to liquidate earlier than the opponent, causing the equilibrium liquidation time to shift forward;
  the extent of this shift depends on the ratio of the first mover's gain to the cost of premature liquidation, requiring separate solution.
- Approach: respond optimally to the opponent's experience-based terminal distribution, simultaneously solve a small-scale simultaneous-action game for defensive purposes, and adjust risk according to the current lead.

### Access Methods (from basic to advanced)

1. **Execution Layer for Selling**: The strategy makes normal decisions; the planner covers SELL quantity and slots, and is validated quickly.
2. **Planner-Tuned PPO**: Adjust planting, procurement, and cash flow rhythms to adapt to the new selling approach; use a cheaper, low-scenario, daily-restarted version during training.
3. **Distillation or Features**: Use the planner's output and shadow prices as supervision or input for market heads.

None of these change the training reward; the cash difference is merely an internal agent objective of the planner, ultimately evaluated by win/loss.

### Verification Trajectory

1. Replay of counterfactuals: Replace the "known orders plus noise" predictor in Section 6.1 with the real predictor, and report the median cash difference and number of improved games for the same game pairings.
2. Native closed-loop A/B: Pair seeds, compare the native scripts (`ahmed_v53`, `thomas_metav4`, etc.) against historical strategies, using WDL as the evaluation metric. This step tests whether opponents respond to price changes and how cash constraints interact with other strategy actions.
3. Final submission to Kaggle.

## 8. Limitations

- Opponent orders are fixed and do not trigger price changes in our side; our production and procurement are also fixed.
- Within the same turn, all our sales are scheduled after the opponent's actions—this is a conservative approach.
- Cash constraints are approximated using model prices, with occasional gaps of several hundred dollars in minimum cash.
- Goods automatically inventoried at the end of the day may be sold one step earlier in the model; when prices reach $1, transactions do not add to inventory and are instead discretized at that point—this is an approximation.
- Revenue evaluation is always based on exact simulation.
- Causal decomposition covers only 25 game pairings. Under point noise conditions, the number and types of opponent actions are known, so the curve illustrates "how much revenue can be gained by improving prediction accuracy," and does not represent achievable revenue in practice.
- Experiments re-solve only once per day; each step re-solution can utilize the most recently observed opponent trades, leading to better expectations, though this has not been verified.
- The game statistics in Section 1 come from a snapshot of another list from the same day; intermediate results of individual games are not archived.

## 9. Recommended Next Steps

1. First, build an opponent sell predictor and measure its temporal error over the next 24–48 steps on replay; this number essentially determines the upper bound of this trajectory.
2. Implement a real estimate for `opponent_shed_estimate` (currently always 0) — this input is also useful for existing strategies.
3. After the predictor meets its performance target, port the planner to native C++, initially conducting a native closed-loop A/B test using the sell execution layer.

## Data and Reproduction

- Replay: [DSM Replay List](../data/external/kaggriculture-dsm-replays/manifest.json),
  `own_submission_ids` marks our submission. After analysis, the list continues to grow; samples are based on the episode number in the result files.
- Rules: [Official 1.32.7 Engine](../data/external/kaggriculture-reference-1.32.7/kaggriculture.py)
  and its [Configuration](../data/external/kaggriculture-reference-1.32.7/kaggriculture.json).
- Results, one row per seat, including income changes for both sides, minimum cash, and product increments:
  - [Perfect Foreknowledge: 25 Games in the Same Match](../outputs/analysis/sell-timing-20260923/perfect-foresight-paired.json)
    and [Strong Team: 80 Games](../outputs/analysis/sell-timing-20260923/perfect-foresight-strong.json),
    including two objectives, presence or absence of constraints, and duality gap.
  - Daily re-solution: [Opponent Orders Known](../outputs/analysis/sell-timing-20260923/replan-oracle.json),
    [Naive Prediction](../outputs/analysis/sell-timing-20260923/replan-naive.json),
    [Prediction Variant](../outputs/analysis/sell-timing-20260923/replan-forecast-variants.json),
    [Temporal Noise](../outputs/analysis/sell-timing-20260923/replan-timing-noise.json),
    [No Prediction Baseline](../outputs/analysis/sell-timing-20260923/forecast-free.json).
  - [Figure in this Paper](../outputs/analysis/sell-timing-20260923/sell-timing-value.png).
- Implementation: One-off prototype (Python with native `Engine.step_with_trace`), cleaned up after running `tmp/`, and not entered into `src/`.
  `repeat` / `silent`, after fixing defects in the prototype constraint repair steps, rerun: the median cash difference is basically consistent with that before the fix
 (`repeat` individual position changes do not exceed 699), the 5th percentile of the lowest cash for `repeat` improves from approximately −3,200 to −6,300 to about −690; the reconstructed prototype successfully reproduces the original results on a per-position basis for the 50 positions in the `oracle` group.
Formal reproduction or extension should be implemented under `src/kagg_revue/evaluation/` and accompanied by a Hydra configuration.
