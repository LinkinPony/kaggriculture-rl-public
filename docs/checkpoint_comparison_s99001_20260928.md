# s99001 Weight Retention Comprehensive Win Rate Comparison (2026-09-28, Completed)

## Results

Completed **84,928 formal games** at **22:28 UTC**, with a total runtime of approximately 7 hours 20 minutes, training continuing uninterrupted.
Independent confirmation of the peak estimate is **U512: 88.84%**, with a 95% confidence interval of **87.36%–90.24%**.
U616 is at **88.65%**, U192 at **88.58%**, U128 at **88.39%**, and the submitted U588 is at **87.43%**.
U512 is only **0.19 percentage points** higher than U616; among all 16 candidate validations, no significant unique leader has been established.
The 95% confidence interval difference between the leader and each candidate includes 0, so the point estimates cannot be interpreted as a definitive strength ordering.

The top-ranked candidate is U200; independent confirmation shows that the top rank becomes U512, indicating that direct selection based on small-sample filtering is not valid.
All candidate round-robin matches: U256 wins first (59.96%), confirmed top four in large-sample head-to-head matches: U192 wins first (55.08%).
These supplementary panels have different opponent distributions; the primary metric remains the five-family equally weighted WDL score as defined below.

Complete item-by-item rankings, intervals, family-specific opponent metrics, and matrices are available in
[summary.md](../outputs/analysis/s99001-checkpoint-comparison-20260928/summary.md) and
[report.json](../outputs/analysis/s99001-checkpoint-comparison-20260928/report.json).
The frozen Actor for U512 is located at `outputs/analysis/s99001-checkpoint-comparison-20260928/actors/u0512.pt`,
with the original checkpoint SHA256 being `18644518e80572d809f2488aaf42e4d8c60e51392de66674da31605247db611a`.

## Freeze Scope

Under user requirements, within the constraint of preserving the ongoing training process, compare the current run's checkpoint that can be restored up to the freeze time, using a 5–8 hour budget. Freeze time **15:11:37 UTC**, deadline **U616**;
Candidates are **U0, 64, 128, 192, 200, 256, 307, 320, 384, 400, 448, 512, 576, 588, 600, 612, 616**.
U588 comes from a recently submitted, certified snapshot on Kaggle; U307 was discovered during a review of the PFSP revision archive, and was added after cross-checking with transition.json and previous-state.json. The rest were parsed and verified using the run ledger and physical storage hashes.
U307 was not reviewed prior to its inclusion; the seed, identity, and sample size of completed games remain unchanged.
The original protocol and change records are preserved in outputs/analysis/s99001-checkpoint-comparison-20260928/amendments/0001/.
Intermediate checkpoints already removed according to retention policy cannot be compared and are not included in "all".

Candidates, opponents, and ledger have been saved in
[manifest.json](../outputs/analysis/s99001-checkpoint-comparison-20260928/manifest.json),
detailed protocol see [protocol.json](../outputs/analysis/s99001-checkpoint-comparison-20260928/protocol.json),
real-time stage see [progress.json](../outputs/analysis/s99001-checkpoint-comparison-20260928/progress.json).

## Ranking Criteria

The primary metric is the equally weighted WDL score from five fixed opponent families: 1 for a win, 0.5 for a draw, and 0 for a loss. Each family accounts for 20%, with opponents within each family treated equally. Terminal cash is used only for diagnosis and does not enter ranking or training rewards.

| Family | Fixed Opponents |
| --- | --- |
| s82001 | U1856, U2560, U3243 |
| s91001 | U64, U1152, U2137 |
| s95001 | U64, U960, U1729 |
| s97001 | U64, U384, U590 |
| Native Script | Ahmed v45, MetaCounter r1, Shop Router 0913, Rayk v38, Farming 0914, Ahmed v53, Thomas Meta v4 |

Each of the four neural families selects three anchor points based on the earliest, middle, and latest weights from the compatibility history pool, and these anchors are fixed prior to seeing the current official results.
The number of scripts does not increase the family's weight. Additionally, a complete round-robin tournament among the current run candidates is conducted as a supplement.
All opponents are historically runnable strategies; the results do not equate to the current Kaggle private leaderboard or the overall leaderboard win rate.

## Samples and Confirmation

1. All 17 candidate pairs against 19 fixed opponents, with 32 environment seeds exchanged per pair, totaling **20,672 games**.
2. All candidate pairs play each other, with 16 environment seeds exchanged per pair, totaling **4,352 games**.
3. Filter all candidates that cannot be excluded from competing for first place within simultaneous confidence intervals, and add U588, U616, and the winner of the round-robin tournament. After deduplication, independently confirm.
   Each opponent pair completes 128 games initially;win/loss results are not read during this phase, and whether to increase the total to 192 games per pair is determined based on actual runtime.
   Incremental estimation is calculated based on the baseline runtime per game, with a 15% margin and an additional 25 minutes reserved; sampling expansion is only performed if there is sufficient time before the deadline.
   All candidates have equal sample sizes within the same phase, and ongoing runs retain their original batch identity and all evidence.
4. The top four confirmed candidates play each other in pairwise matchups, with 256 games per pair, totaling **1,536 games**.

Final independent confirmation expanded to 192 games per pair, totaling 58,368 games. The sampling decision was made at 20:46:49 UTC.
Base confirmation cumulative workload: 43,867.88 worker-seconds, with an additional estimated 5,483.48 seconds, and 8,350.33 seconds remaining;
complies with the registration time rules, and no post-decision review of match outcomes was conducted. See `confirmation-extension.json`.

Step 3, revised at **17:15 UTC** after filtering: except for U0, the 16 candidate overlapping intervals still overlap with the leader's interval, thus expanding the original top six plus the control scheme to include all potentially competitive candidates. No confirmation data has been generated as of this revision. Filtering results and protocol history are available in `amendments/0002/`; this adjustment is not described as having been pre-registered prior to filtering.

The main panel clusters by environment seed, bootstraps the two exchanged positions and all opponents, using 8,192 resamples.
Final results simultaneously report score intervals for each candidate, pairwise differences between the leader and other candidates, and a unified interval covering all candidate pairs.
Data filtering and confirmation are separated, and the ordinary interval of the top-ranked candidate is not treated as independent evidence.
The maximum point estimate in the confirmation phase does not automatically imply significant superiority over all weights; if differences are not resolvable, competing candidates are explicitly listed.

Environment seed partition: filter `9300000000+`, candidate round-robin `9310000000+`,
confirm `9320000000+`, final matchup `9330000000+`; none are used for sampling in this training session.
Inference uses **T=1, CUDA BF16, complete 384-turn memory**, without altering training parameters or checkpoints.

## Resource Protection and Verification

Two independent evaluation processes per GPU, with each process limited to 2.5% of GPU memory (approximately 3.5 GiB) by PyTorch's memory allocator; the total per GPU is capped at 5%, below the 6% limit observed during single-process trials.
CPU inference uses 2 threads, native batch processing uses 4 threads; evaluation processes operate with lower CPU scheduling priority.
Every 5 seconds, the supervisor checks the training PID, status, progress, and remaining GPU memory. If any GPU has less than 12 GiB of idle memory, the training heartbeat has stalled for more than 15 minutes, an evaluation process fails, or the evaluation reaches the **23:06 UTC** deadline, the supervisor terminates the evaluation process group. The training process and its configuration remain unaffected—no termination, signaling, or modification occurs.

864 turns of technical runs passed: after weight switching, the results of repeated neural/script games are identical, verifying graph reuse and memory reset;
32 neural batches take about 38 seconds, 64 batches about 65 seconds. When two evaluations are run concurrently, the minimum VRAM remaining is **28,281 MiB**;
Training progressed from U622 to U629; with four-process concurrent runs, it advanced from U641 to U644;
64 neural batches take about 80 seconds, and results of repeated games are consistent across each GPU/process, with minimum VRAM remaining at 25,989 MiB.
Technical runs are not counted toward official rankings.
New code passed Ruff and mypy; both tests cover family weights, missing seats, duplicate games, expanded sample identities, and seed retention.
Evidence available at [qualification.json](../outputs/analysis/s99001-checkpoint-comparison-20260928/qualification.json).

Further file-by-file verification confirms that the source code related to 879 strategies, native engines, opponents, and evaluation base paths is completely consistent with the currently valid training archive; Torch version and native binaries are also identical; see [runtime-identity.json](../outputs/analysis/s99001-checkpoint-comparison-20260928/runtime-identity.json).
Retain the existing evaluation implementation: neural opponent path K/V caching is FP32, script path K/V caching is BF16, both employing CUDA BF16 mixed-precision computation; all candidate paths for the same opponent type use the same path.

Evaluation uses an independent frozen source code and verified native binaries, performs atomic preservation of complete game results in batches, and allows continuation from previously completed batches.
Entry point is `src/kagg_revue/evaluation/checkpoints/pipeline.py`, configured as
`configs/evaluation_checkpoints_study.yaml`; the code and all runtime outputs are retained.

Final independent verification of 29 Actor hashes, identities/rounds/seeds/seats for all 1,419 batches across all stages, and terminal win/loss outcomes;
Additionally, re-aggregate all family means and overall mean using standard Python, confirming consistency with the official report.
4,948 official health records maintain the same training PID, with monotonic progress advancing to U1002, concluding at the latest saved checkpoint U1000;
Current training protocol, source code, native engine, and frozen ledger are consistent.
Minimum idle GPU memory: **25,989 MiB (25.38 GiB)**, maximum training heartbeat interval: **86.9 seconds**,
After evaluation, idle GPU memory on the two GPUs is respectively **30,572 / 31,110 MiB**.
See [completion-verification.json](../outputs/analysis/s99001-checkpoint-comparison-20260928/completion-verification.json).

After all evaluation processes have exited normally, three `tmp/` runtime images and task-specific graphics caches have been cleaned up; the permanent source code archive, native binaries, script resources, frozen Actors, and per-game evidence are retained in the analysis directory. The final independent code verification and displayed source code are separately saved with `audit-source.py` and `presentation-source.py`, and will not be conflated with the frozen inference source code that generates game sessions.
