# 2026-09-16: V45 Native Integration and U5629 Continuation

The user requests to designate Ahmed V45 as the official C++ opponent, retire V42, cease s69001 and move it to the opponent pool, and then restore s68001 which has already completed over 5,000 turns. The objective of this continuation is
`budget-q100-top10-2d-20260913-s68001`, Run ID
`db598303f1c047a188c6432544dad4a2`, checkpoint **U5629**.

## Native Opponents

`ahmed_v45` replace `ahmed_v42`; the origin and asset bytes of MetaCounter R1, Shop Router 0913, Rayk V38 Low Pressure, and Farming V4 0914 are preserved. The origin comparison is available in [public notebook investigation](public_notebook_survey_20260916.md).

- V45 Original Source Code SHA-256: `2536d41ed5a00c75204b6350f1c76c54259c774cb065ba2a3a0072eedf210d94`.
- [Official manifest](../data/external/kaggriculture-public-native-20260916/manifest.json): `6d66d351cc01eb3e6e58f9921de0a1842f78aee03686b0312355725e1bdf2aa8`.
- V45 Assets: `8330113029b88423ac99d257b9d21dd610c70ce8821b4584b44f12742ee6063e`.
- New `_revue_native`: `e3c7e44561e6847a19a087a21f04a61e02a2de2cffb32506f8e1ac482b6a31fd`.
- Rule Core `_revue_core` Retained: `2b947f38e5c18cda8ab03ca5c109998940feb90e6695621fc7ddd79514c4f5a3`.

Reuses the pre-compiled compiler to generate C++, training executed directly via `ParallelBatch.advance_programs`,
with no Python opponent callback per turn. The seven containers of V45 are replicated and adapted to nodes according to the reviewed V43 rules for AST authentication and normalization; the compiler adds support for a single `try: return ... / finally: ...`,
retaining recovery logic and exception priority for normal returns, strategy exceptions, and cleanup exceptions. All unsupported shapes are explicitly rejected.
V42 is retired from the current registry and new training configuration, with source, assets, and historical runs archived for retention.

## Acceptance Evidence

- [100 complete and properly paired games](../outputs/opponents/public-20260916/conformance-isolated/report.json):
  143,800 actions, along with observations, control layer diagnostics, and fork consistency.
- [25 perturbed games](../outputs/opponents/public-20260916/perturbed/report.json):
  35,950 action consistencies, with DIG injected every 37 turns.
- [Official training batch processing](../outputs/opponents/public-20260916/training/training-parity.json):
  Five opponents, dual seats totaling 10 games, 14,400 observations, 7,190 script actions, and fork consistency at step 360.
- [41 related tests](../outputs/opponents/public-20260916/pytest-final.log) passed,
  including source authentication, retirement isolation, finally exception handling, copying, reset, PFSP, and historical retention.
  Ruff, mypy and `git diff --check` passed for 774 source code files.
- [Throughput and memory](../outputs/opponents/public-20260916/throughput.json):
  8 full PASS learner games with 8 CPU workers, V45 achieving 3.289 / 3.282 seconds twice;
  stable RSS during session creation, cloning, and destruction pressure cycles. This is not a complete neural training throughput comparison.

The initial test loaded the outdated library due to pytest project root selection before the switch; rerunning with a fully isolated directory and the official installation root both yielded 41 passes. Early startup from root `conformance.log` was terminated, and formal consistency evidence uses the aforementioned `conformance-isolated/report.json`.

## Stop s69001 with historical choices

`budget-q100-top10-2d-20260915-s69001` (Run ID `7d29cd58baca4ee286e8a8e27f8deb3b`) saved completely and stopped normally at **U1758** upon receiving SIGTERM.
Parent process and three child processes exited, run lock released. Checkpoint
`checkpoints/update-001758.pt` SHA-256 is
`8e0199949ba302d341c4319c6423815f1cf2052e8d63513601931e5cae44da10`;
the optimizer step counts are 36,917 / 36,918 respectively, all tensor values are finite, and the dual-GPU RNG is complete and independent.
See [Stop Verification](../outputs/opponents/public-20260916/stop-verification.json).

Selected **29 self-version entries**: final BC, 27 regular historical snapshots, and final U1758.
The external history imported in this run will not be nested imported again.
The original target's 57 external members plus the newly added 29 result in a total of **86 external historical opponents**.
The pool capacity is expanded to **136**, retaining the target's 50 registered versions, including all 39 original self-members and
11 preserved checkpoints. Thus, all 96 original members from the original pool are retained.
See [Member Identity and Selection](../outputs/opponents/public-20260916/historical-selection.json).

## Restore Configuration

[Migrate configuration](../configs/learning_public_20260916_change.yaml) binds U5629 and the new historical source state hash.
The original U5629 checkpoint SHA-256 is
`5700c91c41e6198b444ae5aa540e08f03f51ad6cb3444f57c0a8601d0370bef6`.
Retain the original Actor/Critic, optimizer, and RNG, continuing from U5630; do not reinitialize the model or perform BC.
128 games per turn, 100,000 total turns, two GPUs, 30% self-play / 20% native script / 50% historical PFSP,
and keep Actor LR `7.5e-6` / Critic LR `1e-4`.

Isolated replica `outputs/learning/public-native-qualification-20260916` completed
**12 turns / 1,536 games**, U5632 stopped normally, then restored from archived source code to U5641.
Each optimizer advanced **252 steps**, both Actor/Critic updated, all tensors finite;
Dual-GPU RNG progressed independently and stably, constant LR maintained, PFSP sampling exact replay and statistics preserved consistently.
All five official scripts participated in actual execution, with s69001's U128, U1536, and U1664 being sampled and used in practice.
The entire validation process did not alter the operational state of the official source or the U5629 checkpoint.

Additionally, 10 official complete games with the U5629 learning model: 14,400 observations,
7,190 learner features, and 7,190 script actions aligned.
See [Complete Qualification Report](../outputs/opponents/public-20260916/qualification.json),
[Checkpoint Additional Verification](../outputs/opponents/public-20260916/qualification-verification.json), and
[Native Library with Dual-GPU Loading](../outputs/opponents/public-20260916/qualification-live-runtime.json).
Qualification report bound to source code SHA-256
`3ffddbd4cee6de77b3655564f479952a4d32984e1f8060e43ad8fbe41ef23d9f`.
These verifications confirm correct integration and continuity, and no training intensity gains are claimed based on this.

Formal migration has been registered at `population-revisions/0003`, effective from **U5630**.
Qualification report SHA-256 is
`f679ba4fb5053c3fb9ee85e46a411aa26490b768444fade49b60154aac7fc08e`.
The protocol only changes for `population` and `script_population`; U5629 bytes, existing training records,
PFSP statistics, and member status are preserved; all 96 members of the original pool are retained during migration.
See [Formal Migration Verification](../outputs/opponents/public-20260916/migration-verification.json).

Initial migration validation was terminated due to an excessive default CPU thread count and no formal state was submitted; the incomplete archive was saved, then re-executed with single-threaded validation and passed successfully. The initial startup resolved the symbolic link of the virtual environment interpreter to the underlying interpreter path; this process exited normally after complete preservation on U5630, followed by continuation using the `.venv/bin/python` interpreter path as used in acceptance. No rollback or reset was performed on completed updates. See [Interpreter Path Continuity Record](../outputs/opponents/public-20260916/interpreter-restart.json).

**Formal U5632 complete checkpoint has passed verification**, SHA-256 is
`0a826cb4475c36be5763d636802c86eb0991c61ecc564b07cea6d89a2a51343a`.
Added 3 rounds / **384 games**, V45 executed **28 games** on U5632;
The U1536 of s69001 has been actually used as a historical opponent.
Each optimizer continues for **63 steps**, both Actor/Critic are updated, all tensors are finite;
Dual-GPU RNG advances independently and stably, constant LR is maintained, PFSP exact replay and saved statistics are consistent.
Checkpoint parent hashes from U5629 → U5630 → U5632 are continuous, original U5629 bytes are preserved.
New training records and new script statistics no longer use V42.

Both GPUs have passed verification via the virtual environment interpreter path, V45 native binary, and the original rule core hash validation.
Restored parent process PID 3872194, training coordination process PID 3872271, dual-GPU worker processes 3874526 / 3874527.
(These PIDs reflect the state at the time of verification.) Formal training continues; historical pools will still be maintained according to the original snapshot rules.
See [Startup Log](../outputs/opponents/public-20260916/formal-launch.json),
[Formal Continuation Verification](../outputs/opponents/public-20260916/formal-verification.json), and
[Real-time Progress](../outputs/learning/budget-q100-top10-2d-20260913-s68001/learning-progress.json).
