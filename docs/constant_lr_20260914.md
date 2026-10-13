# September 14: Constant Learning Rate Continuation Training

The user requests to cancel the learning rate scaling triggered by KL protection and resume the current formal training.
The run directory is `outputs/learning/budget-q100-top10-2d-20260913-s68001`.

## Reasons and Changes

The original Actor LR for U1–3198 was `7.5e-6`. For U3199, all three updates within the same minibatch were rejected by KL protection; the Actor stopped early after accepting 7 steps, and the Critic completed 21 steps. In the old implementation, the LR was halved each time a rejection occurred. After three failures, the untried `9.375e-7` was retained, and `guard_lr_scale=0.125` was written into the optimizer. There was no recovery mechanism afterward.

The main line is now fixed to **Actor LR `7.5e-6`, Critic LR `1e-4`**, with values derived from
Hydra recipe analysis of `actor_learning_rate` and `critic_learning_rate`.
Main line adapter settings: `backtrack_attempts=1`, `learning_rate_decay=1.0`:

- Each Actor minibatch is attempted only once, without retrying with step size reduction.
- After update, if the KL divergence exceeds `0.01`, roll back the step parameters, Adam momentum, and step count, and halt remaining Actor updates for the current turn; the Critic continues normally. The same learning rate is used in the next sampling round.
- Archive recovery first loads the full optimizer, then restores the fixed LR specified in the configuration, removes the old `guard_lr_scale`. Adam momentum and accumulated steps are preserved, while model parameters, dual-GPU RNG, and PFSP are not reset.
- Tournament recovery and performance benchmarking share the same optimizer restoration entry point to avoid loading outdated scaling values.

The shared optimizer module can still read historical compatible decay configurations from explicit settings; the current `learning` mainline no longer enables this. Frozen historical source archives are not modified.

## Stop Points and Verification

Formally running on **U3490** after complete preservation, it stopped normally. The original checkpoint SHA-256 is
`f82da40a0f402faa9f74f34d084d609cc85b2412490a90900a83ee45bdb80bbb`.
The Actor/Critic optimizers accumulated **73,262 / 73,290** steps respectively, with all tensor bounds satisfied. Both GPUs have full and distinct RNGs; the training parent process, recovery parent process, and worker processes all exited, and both locks were released.
The original checkpoint is preserved via hard link in the analysis directory to prevent subsequent cleanup by retention policies.
See [Stop Verification](../outputs/analysis/constant-lr-20260914/stop-verification.json).

Ruff, full mypy (744 source files) and 15 related tests passed.
Regression coverage for acceptance, rejection, and non-finite value rollbacks under constant LR; restoring configuration LR and preserving all Adam states when recovering from a scaled optimizer; the restoration semantics for the old decay recipe are also maintained.
Test logs located at `outputs/analysis/constant-lr-20260914/`.

Formal U3490 checkpoint checked and restored tensor-by-tensor via CPU: network parameters and all Adam tensors, parameter groups' ownership, and other hyperparameters are consistent; only restored configuration LR and cleared old scaling flags.
See [Restoration State Verification](../outputs/analysis/constant-lr-20260914/restore-verification.json).

Dual-GPU Isolated Replica `constant-lr-qualification-20260914` completed **U3491–3494,
4 turns / 512 games**, including normal stoppage of U3492 with source code freezing and archival recovery.
Each turn uses Actor LR `7.5e-6`; both optimizers proceed for **84 steps**, with no KL rejections.
Both networks are updated, all checkpoint tensors are finite, dual-GPU RNG is advanced and remains independent;
PFSP exact replay, statistics, and checkpoint parent chain consistency are preserved, and the official source runtime remains unchanged.
`guard_lr_scale` has been fully removed from both newly saved optimizers.
See [Full Acceptance](../outputs/analysis/constant-lr-20260914/qualification.json).
This acceptance validates the training and recovery workflow and does not constitute a strategy strength assessment.

## Official Continuation

Register the new code as `source-revisions/0001`, with SHA-256 being
`13aa5f648c9c1c4b94958b7fd7af8cf48323276b81cc9f9031dfdf2f0a670205`.
Migration only updates the ledger entries for `source` and `source_directory`, and appends `repair_history`;
the original protocol, members, historical pools, existing training records, PFSP, and checkpoint bytes are preserved.
LR restores configuration values after loading the optimizer, **effective from formal U3491 onwards**.
See [Migration Verification](../outputs/analysis/constant-lr-20260914/transition-verification.json).

Double-card formal training has been initiated via the standard archive recovery entry; see
[Startup log](../outputs/analysis/constant-lr-20260914/formal-launch.json).

**Formal U3492 complete checkpoint has passed verification**, SHA-256 is
`b9be2d39a54058bb3c3172dbbd0d08fac131b798161cad5c3736eb8428e03801`.
U3491–3492 together add **256 games**, each optimizer continues **42 steps**,
cumulative Actor/Critic steps are **73,304 / 73,332**, with no KL rejections.
Both networks are updated, all tensors are finite, learning rates for the two optimizers are fixed at `7.5e-6` and `1e-4`, respectively, with no old `guard_lr_scale`.
Dual-GPU RNG progresses and remains independent, replay and saved statistics for PFSP are consistent,
checkpoint parent chain is continuous with original U3490; original training records, configurations, and external model identities are preserved.
Parent process, training parent process, and both GPU workers are all alive; formal training continues.
See [Formal Checkpoint Verification](../outputs/analysis/constant-lr-20260914/formal-verification.json).
