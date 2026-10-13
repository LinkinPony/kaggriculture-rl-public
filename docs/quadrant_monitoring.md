# PPO Quadrant Behavior Monitoring

From the complete training trajectory, statistically track the behaviors of NW, NE, SW, and SE, and display them on the existing training monitoring page.
The overview will include the elephant territory acquisition rate, production utilization rate curves, and the SE indicator card; the diagnosis page will provide idle rate, rounds of land purchase, and maximum production cells; the resource page will show the time spent in each quadrant this round.

## Statistical Scope

Denominator is the number of **learning agent trajectories** in this turn: one trajectory is counted for each side in the game, and for historical models or scripts, only the learning agent's trajectory is counted.
For dual-card and sampling group setups, raw counts are first merged before computing the ratio. Actions from the frozen opponent are not included.

| Metric | Definition |
| --- | --- |
| Acquisition rate / Unlock rate | The proportion of trajectories in which the quadrant was actually unlocked during the game; NW starts with ownership |
| Construction rate | The proportion of trajectories in which crops, chicken coops, or pastures were ever present |
| Production utilization rate | The proportion of trajectories in which crops were present, or animals were placed in facilities |
| Post-purchase underutilization rate | The proportion of trajectories that were unlocked but never exhibited any production activities, out of the total learning agent trajectories |
| Average turn to acquisition | The average turn at which the first observation of unlock occurs within unlocked trajectories; 1 represents the turn after the first action settlement |
| Maximum production cell count | For each trajectory, take the maximum number of production cells across the game, then average across all learning agent trajectories; unused cells are counted as 0 |

Production usage does not require prior harvest and is not equivalent to profit. Empty facilities count only as construction.
The statistics include the initial state, the state at each turn, and the settlement state after the final action, thus ensuring that crops that appear and then disappear during the game are not missed, and land purchases made in the final turn are properly accounted for. Different PFSP opponents, environment seeds, and model states all affect the ratio; this curve is for training behavior diagnosis, not for fixed opponent evaluation.

## Implementation and Performance

Reuses the existing learning agent board tensor during sampling; each rank performs batch reduction at the end of each turn;
encodes terminal features once additionally, without invoking Python to read full observations turn-by-turn, without running separate game evaluations.
Statistics do not consume random numbers, do not modify strategy parameters, rewards, gradients, or PFSP; native binary remains unchanged.
Sparse decisions or trajectories starting from mid-game do not generate these full-game metrics; historical missing data is not displayed as 0.

Indicators are stored in the `metrics.jsonl` and `land` fields of the submitted checkpoint ledger; each worker retains the original count, and the web interface reads `rl/land/...`. `rollout.quadrant_monitor_seconds` contains terminal encoding, seat reassignment, and statistics, with the dual-card aggregation time taken from the slower side.

Using U60 weights and T=1, across 30 learning trajectories from 22 complete native games, each with 720 states, the statistics for all quadrants and direct native state readings are completely consistent; CUDA random states remain unchanged. In this dataset, SE unlock and production are both 7/30, with an average round for land purchase of 272.29.
Independent batch reduction is repeated 20 times, yielding a median of **7.55 ms** and a maximum of **7.58 ms**; this measurement does not include terminal liquidation encoding. The additional overhead in a full training run should be determined based on the resource monitoring page and integrated acceptance records.

See [Native State Comparison and Performance Log](../outputs/analysis/quadrant-monitor-20260923/measurement-verification.json).

## s80001 Integration and Enablement

Originally running on **U89**, it was properly saved and stopped. An independent replica completed four full two-GPU updates for U90–U93. After stopping at U91, it was restored from archived source code to U93, and all components—including Actor/Critic optimizers, dual rank RNG, checkpoint parent chain, and PFSP sampling replay—passed validation. The number of trajectory samples per learning round was 168, 168, 164, and 168, matching the actual opponent distribution on a per-item basis; the original two-GPU counts, ratios, and calculations excluding frozen seats were all confirmed consistent.

Statistical overhead in full training (including terminal encoding and seat reassignment):

| Scenario | Additional Time | Percentage of Training Time in Round |
| --- | --- | --- |
| Stable Round U91 | 5.44 ms | 0.01296% |
| Stable Round U93 | 5.73 ms | 0.01364% |
| First Round after Two Process Starts | 135–136 ms | Approximately 0.12–0.16% |

The above is short-term measurement on current hardware; the long-term curve will continuously display actual runtime. Enablement requires one normal save and restart; adding monitoring does not increase independent game evaluation and does not alter optimization steps.

Use an authenticated recovery procedure for code revisions, extend this procedure to properly authenticate checkpoint roots transferred from BC,
including validation and retention of local parent weight copies. The original code and state remain in the archive; only the code identity and revision records change, while U89 checkpoint, run ID, full protocol, historical pool, and existing PFSP win/loss records remain unchanged.
See [Complete Recovery Qualification](../outputs/analysis/quadrant-monitor-20260923/qualification.json),
[Count and Overhead Verification](../outputs/analysis/quadrant-monitor-20260923/integration-metrics-verification.json), and
[Original Run Activation Verification](../outputs/analysis/quadrant-monitor-20260923/activation-verification.json).

Full checkpoint and web verification passed for **U92** after original run recovery: Actor/Critic optimizers advanced 9 steps, tensor finite, double rank RNG complete, PFSP can be precisely replayed. In this round's **164 learning trajectory entries**, **42 trajectories involved purchasing and using SE (25.61%)**, with web values matching the ledger exactly; no script errors found in browser, and all overview cards, curve charts, and resource page timing graphs have been verified. Training continues to U94 upon acceptance.
The statistical execution times for original runs U91 and U92 were **5.49 / 5.38 ms**.
See [actual training acceptance](../outputs/analysis/quadrant-monitor-20260923/live-verification.json),
[browser acceptance](../outputs/analysis/quadrant-monitor-20260923/browser-verification.json), and
[page screenshots](../outputs/analysis/quadrant-monitor-20260923/dashboard.png).
