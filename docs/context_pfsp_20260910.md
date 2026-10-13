# 26M Mainline PFSP

## Design

Keep original 26M Actor/Critic, optimizer, T=1, dual GPU, 128 games/update, 5,760 logical
batch, 2,880 execution microbatches, training seed root and 100k total budget. Counted by physical match:

| Type | Total Games | Games per GPU | Learning Trajectory per GPU |
| --- | ---: | ---: | ---: |
| Current strategy self-play | 32 | 16 | 32 |
| Historical strategy PFSP | 32 | 16 | 16 |
| Four native scripts PFSP | 64 | 32 | 32 |

The script continues for `router_95`, `farming_v4`, `shop_router_0909`, and `shop_router_0908`.
Each script must allocate at least one pair of seats per card, resulting in a global minimum of 4 games; remaining slots are allocated according to PFSP, with equal distribution per card, non-overlapping environment seeds, and balanced seat allocation between both opponents. The total number of games per round and tensor shape remain unchanged.
Each self-play game trajectory is weighted at 0.5; opponent game trajectories are frozen and only the learning side is retained, with a weight of 1.
Each round reduces from 192 learning trajectories to 160, resulting in an expected 20 logical updates for both Actor and Critic, down from the previous 24; throughput comparisons must explicitly note this change.

The history pool only accepts authenticated checkpoints from the current random root, excluding independently evaluated anchor points. During migration, up to 16 checkpoints are selected from the remaining ones, always preserving the BC endpoint and the latest 4 checkpoints; the rest are sparsely retained based on time gaps. A new snapshot is added every 64 turns; when the pool is full, the most crowded points in the earlier regions are removed to prevent the entire pool from covering only the most recent dozens of turns. The file retention policy protects all active pool members.

Prioritize the direction of more difficult opponents, referencing [AlphaStar paper](https://www.nature.com/articles/s41586-019-1724-z).
The following ratios, priors, decay rates, and pool management are engineering choices of this project, not reproductions of the paper's parameters.

The learning team's score estimate is `p = (recent wins + 0.5 × recent draws + 4) / (recent games + 8)`.
Evidence decays with a 128-update half-life, capped at an effective sample size of 256, to avoid long-term accumulation causing statistical sluggishness.
Frozen models are identified by checkpoint SHA-256 hashes, with script bindings tied to a declared source list.

- Historical sampling: 20% uniform exploration + 10% latest snapshot + 70% normalized `(1-p)^2`.
- Remaining script seat pairs: 20% uniform exploration + 80% normalized `(1-p)^2`, with additional minimum coverage.
- Unplayed opponents start from 50% prior belief; draws count as half points. Use training game feedback, with no additional online evaluation budget.
- In each turn, select only one historical model; all historical matches form a single continuous batch; the selection probability is over the entire historical batch, not treating 32 games as 32 independent opponent samples.

## Throughput and Recovery

Retain native C++ scripts and original historical seat routing, without per-turn Python strategy callbacks.
Each GPU has only two fixed-shaped inference graphs: 80 rows for the learning side, 16 rows for the frozen side; the number of historical model graphs does not increase.
The two graphs are executed concurrently in different CUDA streams, with a final shared causal synchronization.
Parameter conversion within graphs disables autocast caching, and reuses the original graph after switching frozen weights.
Historical weights are cached in main memory by authenticated hash; if the same model is drawn again, weight copying is skipped.

PFSP uses independent NumPy RNGs determined by random seeds and update numbers, without consuming Torch's action sampling stream. The two GPUs first merge the full game results, then each performs an identical statistical update.
Statistics are stored in an atomic ledger and a complete checkpoint; upon recovery, both are cross-verified to ensure consistency. Thus, in the event of an abnormal interruption, any uncommitted PPO updates along with the corresponding PFSP feedback are discarded, preventing double accounting or the use of future feedback.
The pool members along with their hashes, actual opponents per round, scores before selection, sampling probabilities, and actual script game counts are all auditable.

WebUI reads historical pools, scores, and next-round probabilities from small real-time status files, while curves are still read from submitted metrics. Changes in the number of games per round in PFSP will not be incorrectly reported as recipe switches, nor will the smoothing curve be continuously truncated; a true transition from an old recipe to PFSP still generates a boundary. Training scores vary with the sampling distribution and are used only for diagnostics, not equivalent to strength improvements on a fixed panel.

## Entry and Acceptance

Hydra configuration: [learning_context_pfsp_change.yaml](../configs/learning_context_pfsp_change.yaml).
Implementation located at [learning/matchmaking](../src/kagg_revue/learning/matchmaking/).

Originally running on U3780, it has been normally stopped. Complete checkpoint SHA-256:
`7e60cf8334c5903856605c07a203a2b8ea64d109e94c56f4b4167b3499b46d5b`.
See [Stop Verification](../outputs/analysis/context-pfsp-20260910/stopped.json) and
[Old Recipe Throughput Baseline](../outputs/analysis/context-pfsp-20260910/baseline.json).

1. [Serial/Parallel Inference](../outputs/analysis/context-pfsp-20260910/inference.json):
   4 groups of complete 64 games per GPU, with two execution methods totaling 512 games and 256 distinct environment seeds.
   Observations, actions, log-probabilities, rewards, weights, and terminal cash are bit-by-bit consistent. Median steady-state sampling time reduced from 6.949 to 6.075 seconds, achieving approximately a 14.4% throughput improvement.

2. [Real PPO with Archive Recovery](../outputs/analysis/context-pfsp-20260910/qualification.json):
   1,024 games from U3781–U3788; after normal termination of U3784, training continued using archived source code. All sampled replay data based on pre-selection statistics match actual selections and final ledger; each optimizer advances 160 steps, with changes observed in both Actor and Critic networks. All checkpoint tensors are bounded, and both GPU RNGs are fully preserved.

3. [Throughput Summary](../outputs/analysis/context-pfsp-20260910/qualification-summary.json):
   Excluding initial startup and warm-up rounds U3781/U3785, the remaining 6 rounds have durations ranging from 25.73 to 26.31 seconds, with a median of 26.25 seconds. The old recipe's median duration over the last 32 rounds is 29.38 seconds, with the same 128 games per update. The new recipe achieves an 11.9% improvement in physical game throughput. Peak allocated GPU memory is approximately 95.28 GiB per card.

4. 52 related Python regressions and 12 frontend checks passed; full Ruff pass, mypy passed 690 files. Checks cover score decay, sampling consistency, stop recovery, minimum seat coverage, historical pool retention, protocol compatibility, native seat routing, and WebUI curve thresholds.

5. [Migration Verification](../outputs/analysis/context-pfsp-20260910/transition-verification.json):
   The original checkpoint, optimizer, and RNG files remain byte-for-byte identical; all registered members are preserved; the protocol changes only in `population`. The historical pool is reselected under new rules, with the old pool list and entire old ledger saved in `population-revisions/0004/previous-state.json`.

6. [Official Launch](../outputs/analysis/context-pfsp-20260910/formal-launch.json):
   GPU0 + GPU1 continue from formal U3780; weight validation of the replica did not enter formal training.
[Chromium validation page](../outputs/analysis/context-pfsp-20260910/webui-qualification.json)
No script errors.
7. [Formal U3784 checkpoint](../outputs/analysis/context-pfsp-20260910/formal-verification.json):
Both networks are updated, each optimizer advances 80 steps, all tensors are finite, dual-GPU RNG is complete and distinct, PFSP sampling and statistical replay pass. Formal U3782–3784 training times are 26.08 / 26.28 / 26.22 seconds.
8. [Formal WebUI](../outputs/analysis/context-pfsp-20260910/webui-formal.json): Real Chromium
Checked 16 rows of historical pool, historical score curves, and script allocation probabilities; no script errors were found, and the dynamic field counts for U3781–3784 record the protocol boundary only once at U3781.

Formal training continues to run. After normal shutdown, restore using the original entry point:

```bash
CUDA_VISIBLE_DEVICES=0,1 .venv/bin/python -m kagg_revue.learning.recovery.cli recovery.run=outputs/learning/context-26m-20260908-s62001
```
