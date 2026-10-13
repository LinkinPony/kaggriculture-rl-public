# Multi-source Initialization and Subsequent Online Reinforcement Learning

Refine the state course with 128 turns, yet still fails to establish a farm from the initial setup. In the next experiment, start with new random parameters, first learn fundamental actions using multiple dates and multiple sources of raw decisions, then optimize the full initial state game solely with PPO.
The research question is: After a fixed initialization cost, does increasing online RL investment improve performance in full-game play?
Do not load weights prior to receiving instructions, do not invoke a specific version of the teacher, and do not use four legacy script opponents.

## Data and Action Semantics

`datasets/demonstrations/` uses the officially persisted original ZIP 1.32.7. All 1,337 games from September 3–4 are for training, and all 664 games from September 5 are for selection; environment seeds have no overlap across dates. Both players are retained per game, without filtering training samples by final cash, win/loss, or rating. The source statistics for displayed names do not represent the number of independent strategy versions. Source code fingerprints are recorded at preparation time, with the manifest fixed to the original ZIP, individual game JSONs, encoders, and SHA256 hashes for each array.

The current private/self-owned and jointly public observations and causal history serve as input, and the action in the next record for the current turn serves as the label.
The backpack insertion order is restored based on the complete prefix; future observations are not used as features. Unit actions use the officially normalized actual operations, with market requests retaining their original order and exact quantities. Absence of units, second task, and release time are all fixed at zero.
When units executed after a turn depend on resources just transferred by preceding units, they may exceed the upfront independent support; these cases are explicitly excluded and are not modified to approximate actions. Training excludes 14/1,922,606 rows, and selection excludes 45/954,832 rows.

The quantity lexicon is composed of exact literals from training labels combined with declared exploration ranges, totaling 158 symbols. selection
No out-of-training-vocabulary quantities were found that are marked as non-coverable; none were expanded beyond the training vocabulary. The complete dataset in this instance contains no such additional exclusions.
Four complete action roundtrips and 64 official three-party audits have all passed; evidence links are located at CURRENT_MAINLINE.

## Learning and Recovery

The default entry point is `python -m kagg_revue.learning.cli`. `learning_mainline` uses a new random seed and a directory with a timestamp; `--config-name=learning_demonstrations` retains the first set of experimental recipes and the original path, and reruns should overwrite the output directory. `learning_grounded` retains the pure RL ablation. `Experiment.demonstrations` only accepts the hash of the original data list, fixed epoch/learning rate/batch budget, and does not accept model files. The geometric definition comes from `policy.settings.GeometrySettings`; data preparation does not construct PPO or BC workflow configurations.

`learning/pretraining/` trains under the same random root ledger. Data loading first confirms the complete inventory, hashes of each array, action/observation ABI, date partitioning, and isolation from online training and evaluation seeds. Each epoch iterates through all training rows once; shards and internal row ordering are shuffled by seed, and each row is processed using the average negative log-likelihood of the actual participation field. The last batch is filled with repeated indices to achieve a fixed shape, with zero row weights for padding, and actual tail rows are not discarded. During each epoch, likelihood is computed over all accessible selection rows without gradient computation.

Fix the last epoch as the initialization endpoint, without selecting the optimal epoch based on selection. AdamW states, RNG, completed shard cursors, accumulated true row counts, and epoch metrics are recorded atomically in checkpointing. SIGTERM responds after the current shard; if exactly at the end of an epoch, it completes the epoch's selection before submission. Process crashes may lose up to the unrecorded shards after the last checkpoint, and recovery will re-execute with deterministic sorting. CPU FP32 continuous/intermittent comparisons have been verified to ensure bit-level consistency of the model, optimizer, RNG, and accumulated metrics; no extrapolation is performed, with default BF16 bit-level guarantees.

Three model identities cannot be mixed used:

- `initial.pt`: This new random parameters set is permanently retained as the lineage root.
- `rl_initial`: Fixed demonstration budget endpoint; registered descendants under the same root serve as the **zero online RL budget** reference.
- `checkpoints/update-*.pt`: The new PPO descendant generated after this initialization is additionally recorded with online competition / transfer / optimizer step counts.

Online PPO creates its own actor/critic optimizer, without inheriting the supervision optimizer or retaining demonstration loss.
The historical pool starts at `rl_initial`, with 50% drawn from current self-play and 50% uniformly sampled from frozen historical data. Confirmation and budget
Report shows improvement relative to `rl_initial`; random initial behavior can be audited separately. The random neural anchor still provides only internal control and cannot replace mature external opponents. Under the new vocabulary, a unified opponent requires the same action ABI; old models are not loaded to serve as opponents.

## First set of protocols and pending verification items

Two independent new random seeds, 47001/47002, have been completed. Each group undergoes 4 epochs, batch size 256, and learning rate 3e-4. Subsequently, 128 × 128 full initial games are played with online LR 1e-4, selection every 16 turns, and confirmation only at the end. The PPO objective retains WDL and adds a auxiliary term of net cash / 10,000. Comparisons are performed using the same opponents and pairing seeds across different budgets. September 6 is not used as initialization or state curriculum training data for this action, but prior curriculum research in the project already utilized this day, so it cannot be claimed as a completely unseen blind test day.

The full compilation pipeline for FP32 and BF16 has passed qualification, with each group followed by 16 online games after 2,876 supervision rows.
Zero-budget selection/confirmation have both been verified as fixed demonstration endpoints. The complete two RNG runs are located at
`outputs/learning/scratch-demonstrations-s47001` and `...-s47002`, with source code fingerprints at
`7b68df7f97f41d10dea439d219043f648fef1816273549524fba2a728d4ba624`.
A unified opponent is pre-declared as the fixed 4th demonstration epoch endpoint (`pretraining/shard-000672.pt`) of these two new roots, without result-based epoch selection. A unified selection seed of 1,010,000,000 is used, with budget set to 0/16/32/64/96/128; an independent confirmation is reserved at 1,020,000,000, with 64 games per opponent, comparison at 0/128. The protocol is located at
`outputs/analysis/scratch-demonstrations-common-arena/protocol.json`.
Initialization for both roots has been completed, each with 7,690,368 supervision rows and 30,088 supervision optimizer updates. Fixed endpoints and random root hashes have been registered at `outputs/analysis/scratch-demonstrations-initialization/controls.json`.
The 8 official observation-driven mirror games at the initialization endpoint yielded an average terminal cash of 25,034.19/26,648.25; each group contains 11,520 mutual observations, complete private/public states, and backpack order consistent with the native engine. This check uses trajectories generated by the new model itself, not driven by replay labels, but is not yet evidence for Kaggle submission runs or subsequent RL extensions.
Round 16 unified selection has been completed: 47001/47002 achieved a score increase of +23.44/32.03 percentage points compared to their respective fixed initializations, with 95% confidence intervals across 32 environment seeds of [13.28, 33.59]/[22.17, 41.41].
Terminal cash pairing increased by +14,128/18,569; both groups' models at Round 16 passed full rule audits in closed-loop official runs. These represent early online gains from the two RNGs; full 128-round results and independent confirmations are provided below.
After an additional 2,048 games from Round 16 to 32, the incremental score on the unified opponent increased by +12.50/+16.41 percentage points, with 95% confidence intervals [5.47, 19.53]/[7.81, 25.00]; terminal cash on the fixed opponent also continued to rise.
To address the issue of saturation occurring only during initialization against opponents, two future checkpoints that have not yet generated the 64th round are fixed as late-stage neural opponents. Additional selection/confirmation seeds are
1,050,000,000/1,060,000,000, with the full declaration available at
`outputs/analysis/scratch-demonstrations-late-arena/protocol.json`. It remains part of the internal neural opponents and cannot replace updates to the date, or validation from multiple external sources of strength.
## Complete Budget Conclusion and Subsequent Opponents

Two groups each completed 16,384 online games, with selection scores against a fixed Round 64 neural opponent rising from 4.69%/3.91% to 72.66%/71.88%. In independent confirmation, the scores increased from 7.03%/2.34% to 77.34%/70.31%, with paired improvements of +70.31/+67.97 percentage points, and a 95% confidence interval of [60.94, 78.91]/[59.38, 75.78]. Complete per-game reports, incremental intervals, and figures are available at [current mainline](CURRENT_MAINLINE.md). True PPO returns after initialization have been confirmed internally by two RNGs.

The score increment interval across rounds 96→128 crosses zero, and we cannot assert that each budget segment has steadily improved. The score for the initial opponent has approached saturation; in round 128, the average mirrored cash is approximately 66,000, and it continues to seed and harvest. The two new roots, across 12 budget checkpoints, show full consistency in 96 official closed-loop games and 138,240 observations, covering the same set of 8 environment seeds. These results still do not equate to external leaderboard strength, long-term computational scaling patterns, or compliance with runtime submission requirements.

Late-date independent opponents trained with new random seeds 49001/49002, configured as `learning_later_opponents`:
September 5: all 664 games, 954,787 available labels; September 6: 662 games, 951,902 labels counting only likelihood;
followed by 64 × 128 games of PPO after four fixed epochs. All budgeted evaluations for candidates 47001/47002 were fixed prior to opponent random initialization; new opponents are not trained on candidates and are not selected based on candidate results. Training, internal selection, and confirmation seeds were 1,070,000, 000/1, 080,000, 000/1, 090,000,000.
A cross-source candidate panel was reserved at 1,100,000, 000/1, 110,000,000, still with 64 games per opponent.
The vocabulary remains unchanged at 158 symbols; the late-date list hash is `1bc344ed3aa7bd7dbdd762f44c21350565e55f0c289dcb40a2ef3c0cfc39eac0`.
This test evaluates independent training sources and the transfer of online random seeds, and does not represent a blind test date of a real external controller or the entire study.
Both opponents have been completed; official image behavior shows respective cash and gain increases from initial to final states, but final strength remains below that of the original Round 64 opponent panel. Frozen candidate independent confirmation scores are 97.66%/96.88%, with paired improvement of 59.38/65.63 percentage points, interval [50.78, 67.19]/[57.03, 74.22], supporting cross-source transfer.
Two additional new RNGs 51001/51002 have completed 512-round training and fixed-panel evaluation; the total score gains in the first 128 rounds primarily came from weaker opponents, still significantly behind the original mainline 128-round endpoint at that time. By round 384, both achieved 87.89%/80.08% on the fixed four-opponent panel and secured majority wins against both stronger endpoints; the incremental gains from 256 to 384 are all above zero.
A publicly available route/rule strategy, currently downloadable, has undergone independent external evaluation without providing training labels or opponent feedback. Internal independent confirmation over 512 rounds supports a 128→512 gain of 30.96/28.71 percentage points, interval [27.73, 34.08]/[25.59, 31.84].
The first pair of 128-round models each achieved full losses in 128 games against the original route opponents, with cash gains not yet translating into wins.
Independent confirmation of the reactive rule family EcoBot achieves 82.03%/73.44%, with both relative score intervals above zero compared to fixed initialization. The long-budget group confirms an additional 128→512 gain of 28.13/53.91 percentage points on EcoBot, interval [19.53, 36.72]/[44.82, 62.50]. The route family endpoints achieved only 2/128 and 0/128 wins, still showing no reliable winning gains.
Complete delivery and limited budget conclusions are available in [learning_results.md](learning_results.md).
Complete evidence is available in CURRENT_MAINLINE; external panel is available in [learning_public_arena.md](learning_public_arena.md).
