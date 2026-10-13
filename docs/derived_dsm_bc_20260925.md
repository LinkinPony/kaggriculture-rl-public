# U1843 → Complete v5b DSM BC

**Post-status:** Stopped normally at **02:58:00 UTC** at the **585th batch / 3,364,920 supervision turns** as per user request, with full state preserved. The original epoch 4 file has been deleted according to the previous retention rules; retraining with the same data, initial Actor, seed, and hyperparameters failed to reproduce the original results bit-for-bit due to CUDA non-determinism. The user explicitly selected **retraining of epoch 4** as the new RL starting point, see
[epoch 4 → PPO explanation](derived_epoch4_ppo50_20260925.md). The original BC startup record is retained below.

The user requests direct implementation of **v5b, without running v5a or ablation experiments**. The full 5,912-dimensional supplementary features have been integrated. From the latest point where the PPO training stopped, a new BC is initialized using the U1843 Actor. The old network parameters, 286 tokens, action interface, and 384-turn memory are preserved. Four additional input projections are initialized to zero and then participate in normal BC optimization.

## Stop and Start

s82001 `agronomy-v4-m384-dsm-games-ppo50-20260924-s82001` normally stopped at
**U1843 / 235,904 games**, supervision process exit code 0. Previous Critic, Adam, RNG, PFSP, and runtime history are retained.
Parent checkpoint `checkpoints/update-001843.pt`'s SHA256 is
`eae69f6cf64a1d0d2a12e8355526d6463bee0db51ee62e4dad7d9322fb777f41`.
See [Stop Verification](../outputs/analysis/derived-dsm-bc-20260925/stop-verification.json).

**2026-09-25 02:46:29 UTC** Start new run
`derived-v5b-m384-u1843-dsm-bc100-20260925-s85001`,
run ID `a98e71c1e0f84cbf8d96223fc6ab8252`, GPU0 + GPU1.
See [Startup Log](../outputs/analysis/derived-dsm-bc-20260925/launch.json),
[Configuration](../configs/learning_derived_dsm_bc_20260925.yaml) and
[Real-time Progress](../outputs/learning/derived-v5b-m384-u1843-dsm-bc100-20260925-s85001/learning-progress.json).

The parent checkpoint's complete copy is saved in the new run `weight-transfer/parent.pt`; BC starts from the parent Actor using a newly created Adam and a new seed. BC does not optimize the Critic, and the parent Critic remains in the full copy.
The formal migration strictly verifies old parameter names, dimensions, and values; only four new projection matrices are allowed.
The Actor retains 347 tensors / 25,171,324 parameters, adding 59,904 parameters.
The Critic's homogeneous migration eligibility retains 182 tensors, adding 49,920 parameters.

## DSM Scope and Trajectory

The "DSM weight" here corresponds to the publicly accessible DSM **submitted versions**, with supervision derived from full game replays of these versions.
The official has not provided its private model parameter files. Select according to `dateSubmitted` or `2026-09-23T00:00:00Z <= date < 2026-09-25T02:20:05.042814Z`,
retain all discovered replays without filtering by win/loss, rating, game date, or cash.
Independently refreshed the version and game lists; the continuous DSM collector continues to operate as usual.

| DSM submission | UTC submission time | Collection trajectory | Retained trajectory |
| --- | --- | ---: | ---: |
| 56489014 | 09-23 09:06:37 | 90 | 90 |
| 56495569 | 09-23 14:12:33 | 132 | 131 |
| 56498734 | 09-23 16:29:38 | 143 | 143 |
| 56518845 | 09-24 10:23:01 | 112 | 112 |
| 56527482 | 09-24 17:21:48 | 98 | 98 |

Snapshot collection of **575 games**, downloaded without missing data, with no errors detected. `112769598` contains non-ACTIVE decision frames; excluded via existing complete trajectory verification, original files retained. Final **574 DSM trajectories / 412,706 turns**, all preserved turns are supervisable, q100 shows no quantity truncation. Environment seed partitioning and partition seed 62001 are maintained:

| Partition | Complete Trajectory | Supervised Turn |
| --- | ---: | ---: |
| train | 552 | 396,888 |
| val | 22 | 15,818 |

All five versions retain the trajectory; 574 environment seeds across partitions show no leakage.
Array size: 23,269,822,814 bytes; all 1,722 array hashes have been verified.
Original replays are stored in `data/external/`, and the new feature arrays are stored in `outputs/datasets/`.
Future collector updates will not alter the frozen data of this turn.

Data entry: [manifest](../outputs/datasets/derived-v5b-dsm-20260923-25-train-val-q100/manifest.json),
SHA256 `292dcc954485616a55d4eb0246a6de12e93b56d580b56cdb450e0d92c12bcc24`;
[Version selection and snapshot](../outputs/datasets/derived-v5b-dsm-20260923-25-train-val-q100/source-manifests/selection.json).

## Complete Features and Calculation Methodology

Input dimension increased from **22,003 → 27,915**. Memory layout consists of the original prefix semantics at 20,595 dimensions, supplemented by 5,912 dimensions, and original action validity at 1,408 dimensions; the original field offsets and trailing validity reads remain unchanged.
The supplements are sequentially: global 24, both sides' territories 200 × 20, both sides' workers 64 × 16, goods 9 × 96.
Four bias-free projections are added before the first entity attention layer of the original token sequence; the positions of store and history tokens remain unchanged.
Complete field order is available in the [Registry](../src/kagg_revue/native/derived_fields.py),
design background is detailed in [v5 Design](derived_features_v5_design_20260925.md).

The product includes 1/2/4/8/12 days and the remaining season's six supply-demand windows, existing bilateral production maintenance/reinforcement scenarios, input consumption and visible spot inventory, shared market price pressures, relative cash and payback scenarios for new assets, store shocks, future store demand mean and standard deviation, inventory liquidation, and the public historical record of 2/4 days.
The land provides paired conditional returns for WATER/FEED/CARE/FERTILIZE, service duration, and accessibility;
the workers provide serviceable tasks, key work zones, backpack capacity, and end-of-day overflow.
The global summary includes feed capital, key labor pressure, quantities, timing, and cash conditions for land acquisition and labor hiring.
No reward terms are added, and no action hard constraints are modified.

The following statement is part of the feature definition and does not constitute a guarantee of future returns:

- It is known that store consumption is precisely calculated per turn phase, with a single item store weight of 2, and repeated store instances are cumulatively added.
  Unknown stores use only the publicly available uniform probability, with replacement distribution, and maximum unlock time of 8 stores; RNG is not read.
  Demand moments are input separately and are not treated as deterministic store inclusion in pricing scenarios.

- Biological scenarios use publicly known production rules, replenishing WATER/FEED at the earliest serviceable time point each day; enhancing additional CARE and using fertilizer after expiration. Existing one-time crops are harvested upon first harvest, while newly added one-time crops wait until either the full yield/reward window ends or the last day of marketability. Collect fertilizer byproducts; each operation is counted.
  These are capacity templates under infinite service capacity conditions; no claim is made that a worker can perform multiple services in the same turn.

- Pricing scenarios deliver outputs to separate routes at their earliest warehouse receipt time, reserving the next day's input volume, surplus sales, and purchase gaps, then deducting town consumption for the current turn. Unit pricing respects synchronized bidding from both sides and maintains a $1 floor without increasing inventory.
  It does not assume knowledge of the opponent's warehouse or backpack; the opponent's hidden spot market contribution is 0. Shared labor, warehouse space, funds, opponent's transaction queue, and future hiring are not included in this scenario condition.

- New assets are placed at the earliest available land or reusable barn space, with delays for purchase, pickup, and construction counted.
  Incremental cash from maintenance and reinforcement is recalculated relative to the baseline of existing assets in the entire game, affecting only the relevant goods, preserving squeezed pricing, self-owned feed opportunity cost, and fertilizer byproducts. Operation counts include setup and service operations, excluding full walking and DROP actions; additional time and accessibility fields are included.
  Byproducts allow recoupment before the main product; recoupment is marked as zero when no valid sale exists.

- All windows expire at the last executable turn 718; after HARVEST, transportation/DROP is required, and daily end-of-day auto-warehousing occurs only in the next turn for sale. No fictitious next-day production or end-of-day drop gains are assumed on the final day.

- Accessibility is the lower bound per task route; key task zones are assigned to the nearest fixed worker; task statistics do not represent a common feasible schedule. The opponent's private resource fields are zero and marked as unknown. Overflow at end of day is halted based on current inventory, with workers and backpack entries preserved in their official insertion order; animals also occupy warehouse space.

- Two-day feed volume uses feeding events occurring within the next 48 turns from the current moment, thus potentially resulting in three feeding events across three daily segments. The commodity `feed_reserve_2d` represents total demand, `stock_after_feed_reserve` represents signed surplus, and global purchase bids only account for known surplus deficits.

- History is reconstructed from turn 0. Market net inventory effects do not equal opponent sales; floor price truncation and harvest attribution discrepancies are independently marked. Repeated observations of the same turn are not accumulated; the 2/4 day window carries an actual coverage ratio.

Count using `sign(x) log1p(abs(x))/log(1025)`; cash using `sign(x) log1p(abs(x)/100)/log(1001)`. General time divided by 719; land service/deadline difference and workers' daily work/warehouse delay divided by 24 turns per day; prices divided by corresponding base prices. Retain negative balances, do not truncate to zero.
Before native writing into FP16, verify boundedness and range.

## Training and Qualification Check

Fixed at 100 epochs without early stopping; LR **1e-4**; two H200 GPUs, BF16 computation, FP32 parameters and Adam optimizer.
Five action groups normalized and equally weighted; global 8 complete trajectories, 4 per GPU, 48 turns per gradient block,
with 384 turn memory retained across blocks. 69 training batches and 3 validation batches per epoch, totaling **6,900 Adam updates**,
39,688,800 training supervision turns; checkpoints saved every 16 batches and at epoch boundaries.
Training stops after BC completion, without automatically transitioning to PPO.

[Migration Validation](../outputs/analysis/derived-dsm-bc-20260925/compatibility.json) covers actual U1843:
In the authentication of 1,438 observations between the old native library and the new library, all old fields are byte-wise identical; in the CPU FP32 four windows and the complete 719 turns of CUDA BF16, the Actor logits/actions/field weights/memory, Critic state values/prefix values/memory are all completely consistent, with the 384-turn memory fully filled and rolled over; the four new Actor projection gradients are non-zero.
This is a compatibility and trainability qualification check, not acompetitive strength assessment or ablation study.

[Data Validation](../outputs/analysis/derived-dsm-bc-20260925/data-verification.json) extracted 10 games,
covering all versions, dates, and two partitions: 7,190 rows of array reencoding are consistent, 14,400 official replay observations are consistent,
engine state and seat visibility encoding are consistent, and the old v4 fields are consistent.
27 related tests and code modifications passed Ruff/mypy checks.

## Official Operation Verification

**02:50:39 UTC** Verifying checkpoint #64 / 368,128 training supervision turns, SHA256
`8024e2708fbbddde703695d1ee0f188507da7da29a86877295a82e48ca6a1964`.
Adam for 64 steps, LR 1e-4, full double rank RNG; model and optimizer tensors are bounded;
339 actor tensors have changed; the norms of the four newly added feature projections are non-zero. Dual-GPU worker is alive,
steady-state time approximately **0.75 seconds per batch**; the parent run ledger hash remains consistent with the state at termination.
See [Start Verification](../outputs/analysis/derived-dsm-bc-20260925/initial-verification.json) and
[Formal Run Verification](../outputs/analysis/derived-dsm-bc-20260925/formal-verification.json).

**02:51:23 UTC** Completed the 1st epoch, training NLL **0.147884**, validation NLL **0.150570**,
Entering the 2nd epoch, executed 115 / 6,900 batches. Initial compilation of training/validation paths completed; training continues.
These are supervised learning metrics and do not yet represent an improvement in win rate against DSM.

After stopping, use archived source code to restore original operation:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-u1843-dsm-bc100-20260925-s85001
```
