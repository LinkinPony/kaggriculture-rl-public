# Current Main Line

## Current R&D Decision

The completion criteria, evidence gaps, and code migration boundaries for the entire refactoring objective are outlined in [learning_system.md](learning_system.md).

2026-09-07 Starting two groups of **pure neural self-play credit estimation control experiments** according to the new overall refactoring objectives.
Configured as [work_neural_credit.yaml](../configs/production/work_neural_credit.yaml): both groups start from the frozen generation 51 actor, with no time-action table, BC rehearsal, teacher execution, or scripted opponents; each group plays 512 games/update, and only the critic is trained for the first three rounds, totaling 16 rounds. The only algorithm difference is the prefix advantage setting `prefix_trace_lambda`:
- `0` uses the difference between adjacent predicted values,
- `1` uses the full terminal WDL minus the current prefix baseline.
Both groups retain KL rollback after updates.

The runtime directories are `outputs/production-policy/20260907-neural-credit-mc` and `outputs/production-policy/20260907-neural-credit-td`; the operational status of each is determined by the respective `run-status.json`, `launch.json`, `resolved-config.json`, and actual processes. A pre-defined protocol, complete Python/config source code archive, and fingerprint are available at [protocol.json](../outputs/analysis/20260907-neural-credit/protocol.json).
Evaluation uses two frozen neural checkpoints, balances seat allocation, and separates training, selection, and confirmation seeds; advancement is not based on self-play with approximately 50% win rate or cash growth.

This is a diagnostic experiment and has not yet been proven to yield training benefits. The starting point and the two evaluation opponents share a common teacher source, so this experiment also cannot prove escape from teacher initialization or adaptation to the current leaderboard. The entire reconstruction objective still requires coverage by modern daily data, more diverse opponents, evidence of improved performance across training budgets and random seeds, and official runtime validation. Research incumbent and submission maintain identity below.

The previous script-based mixed training was stopped on 2026-09-07 according to user instructions. The last fully saved checkpoint is update 41. The main training process, dual rank worker processes, and compilation subprocesses have all exited, and GPU memory has been released. Stop records are available in [run-status.json](../outputs/production-policy/20260907-work-policy-search-g51-prefix-script50-t020-lr1e6/run-status.json).

This training starts from the generation 51 actor last completed by `20260907-work-policy-search`,
using a hybrid prefix PPO approach combining self-play with scripted opponents. On 2026-09-07, the `T=0.2` and actor learning rate `1e-6` are fixed according to user instructions, temperature scheduling is disabled, and the original training upper limit is retained.

Input weights are consistent with the original `update-000051.pt` run; precise source and frozen identity are referenced in [actor release](../outputs/releases/20260907-work-policy-search-ppo-start/release.json). This iteration retains the actor weights and model semantics, while reinitializing the PPO critic, two optimizers, and rank RNG; PPO counting begins at update 1, maintaining the preheating setup of training only the critic for the first three rounds.

Run binding startup with clean revision `a3505ef90a2640f470f9d086d2d3c800ac72514e`. Exact configuration is taken from
[resolved-config.json](../outputs/production-policy/20260907-work-policy-search-g51-prefix-script50-t020-lr1e6/resolved-config.json),
reproduction commands, input identity, and tmux session details are found in
[launch.json](../outputs/production-policy/20260907-work-policy-search-g51-prefix-script50-t020-lr1e6/launch.json).

Use existing script mixing ratio: 50% current self-play strategy, 50% equal-weighted Kaito v48, Kaito v39, Boatlee v21, and Mugundh v21, distributed evenly across full games and balanced seat allocation. No historical strategy mixing or BC rehearsal; periodic notebook pairing evaluation is retained. Rollback, learning rate decay, or pairing degradation auto-stop options for recovery experiments are disabled.

Exact production configuration has completed critic preheating and three consecutive double rank actor/critic updates with full checkpoint writes, no OOM; autonomous qualification, cold start, steady-state timing, and peak memory are detailed in
[qualification.json](../outputs/production-policy/20260907-work-policy-search-g51-prefix-script50-t020-lr1e6/qualification.json).

Input generation 51 actor remains frozen as control for this training. The new training checkpoint has no advancement criteria yet and still requires full paired matches and official time budget to be completed; no change to the research incumbent or formal submission in the following text.

Local closed-loop research incumbent follows an event-driven trajectory of PPO: the actor decides whether to deviate only at five synchronized trajectory forks.
Freeze the Kaito proposal; Kaito remains responsible for turn-by-turn legal execution, weeds repair, clone pre-sale, and terminal liquidation. The precise strategy identity is
checkpoint update 275 (SHA-256 `a69d1160632a366d184c322fb7b2e73c22b87034308ef81d76655f7567d8a8a5`) plus deployment prior threshold `prior_logit=6.0`; training bound to clean revision `aaa449d816258927083b9ab63090c032abcdff45`.
The training reward is `candidate W/D/L - Kaito DIRECT W/D/L` with the same seed, same seat, and same opponent; the actor's weight is zero prior to the first deviation, without cash rewards or entropy forcing intervention.

In a complete 384-game set of matches with selection seeds `76000..76047`, four frozen opponents, and dual seats, the candidate is `281/39/64`, DIRECT is `263/56/65`, and per-game pairing is `18 better / 362 same / 4 worse`; the average terminal cash is `89,949.341`, provided solely for diagnostic purposes. Non-overlapping extension confirmation uses seeds `76200..76391`, totaling 1,536 games; the candidate is `1078/217/241`, DIRECT is `992/288/256`, and per-game pairing is `86 better / 1434 same / 16 worse`. The candidate shows a net gain of +14 and +8 wins respectively on Boatlee and Mugundh with no degradation, remains unchanged against Kaito v39 on a per-game basis, and performs as `64 better / 304 same / 16 worse` against Kaito v48. The selection and confirmation reports are located at `outputs/evaluation/20260830-event-route-ppo-checkpoint275-prior6-selection-v1/evaluation-report.json` and `outputs/evaluation/20260830-event-route-ppo-checkpoint275-prior6-confirmation192-v1/evaluation-report.json`, with SHA-256 hashes of `73e34e7618e5cc65ae243ceb7c8cbbcefab115e5fc3a0efa886793ba06d30165` and `cc0c0cdae05a85b8ce7b7d3d92e2ddb7a7b9eb199e34fcbe1cbbfd4254610e3c` respectively.

The formal candidate language audit of six synchronized trajectories shows a turn-wise upper bound relative to DIRECT as `73 better / 311 same / 0 worse`; this upper bound only proves cyclic complementarity in the trajectory space and does not possess strategic or advancement authority. The report is located at `outputs/evaluation/20260830-kaito-route-library-selection-v1/evaluation-report.json`, with SHA-256 of `4ee30b5156f287a850b30b65cc071f8c5043b0dc8601f0f029f7dc1f10574470`.

CPU reference runtime matches native specified route execution turn-by-turn on 128 games, 92,032 official observation calls;
Accounting for `actTimeout=1s`, `remainingOverageTime=60s` shows no errors, p99 is `0.153ms`, and the maximum is `4.561ms`.
Audit report located at
`outputs/evaluation/20260830-event-route-ppo-checkpoint275-prior6-runtime-audit-v2/runtime-audit-report.json`,
SHA-256 is `fa310435a4e0228cf05cfbbca7db47ba130ee077554eda41db4f942faf35dbc2`. This gate verifies the action semantics and time budget of the local native official-rule parity backend; the official Kaggle engine parity, submission package build, and fresh-process official competition have not yet been completed, therefore the research incumbent has not changed the official submission path.

## Current Deployment Decision

2026-09-07 Submit the work-v1 actor with the latest complete update 10 at freeze time, as per user instruction. Execution source is
`20260907-work-policy-search-g51-prefix-script50-t020-lr1e6`, deployment execution uses FP32 argmax.
Version tag is `work-search-g51-20260907-u10`; frozen weights, training source, and archival identity are seen in
[release.json](../outputs/releases/20260907-work-search-g51-ppo-u0010/release.json). Build source is
clean revision `a3505ef90a2640f470f9d086d2d3c800ac72514e`; actual export configuration and dual Python ABI runtime identity are seen in [build record](../outputs/kaggle-submission/20260907-work-search-g51-ppo-u10/build-report.json).

Kaggle has received submission `56080043`. Server status, score snapshot, and submission confirmation are available at
[Submission Record](../outputs/kaggle-submission/20260907-work-search-g51-ppo-u10/competition-submission-56080043/submission-record.json).
Training has been stopped as per user instruction at the last fully saved update 41; this submission continues to use frozen weights from update 10.

Precisely archived the local dual-sitting full season and passed the official `1s + 60s overage` budget review; final cash outcomes for the two games against PASS were 96 and 69, see
[Archival Verification](../outputs/kaggle-submission/20260907-work-search-g51-ppo-u10/local-validation/submission-validation-report.json).
In the 180 planned turns per seat, the exported model's actions matched exactly those of the original FP32 actor, see
[Export Consistency](../outputs/kaggle-submission/20260907-work-search-g51-ppo-u10/trace-parity.json).

This is the user-specified current model submission, without changing the research incumbent status. The current strategy development decision is seen above.
