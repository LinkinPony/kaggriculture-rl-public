# User-requested latest-BC handoff to formal RL, 2026-09-16

The user explicitly requested stopping BC immediately and starting formal pure
self-play RL from the latest weights. This supersedes the remaining 100-epoch
budget, patience-based completion and validation-best checkpoint selection.

The active run `gtrxl-m384-bc100-3d-20260916-s71001` stopped normally at BC
cursor **1240**: 28 full epochs plus eight batches of epoch 29, 1,240 Adam steps
and 55,747,848 supervised row exposures. Its latest checkpoint is
`pretraining/shard-001240.pt`, SHA256
`e27260e3cd2d14e9bd121bd18c1e1a65ec0833fc1885183cc815bad96b6cfe21`.
All tensors are finite and both worker RNG states are present. Epoch 28 selection
NLL is 0.4011051655; the partially completed epoch 29 has no new full validation.

The operational Hydra entry point `learning.pretraining.complete` verifies a
normally stopped own-run BC checkpoint, the original source archive, optimizer
steps, RNG and exact progress, then records the explicit handoff. It requires
the already configured pure full-game self-play and terminal WDL protocol.
It writes the previous ledger and transition under `bc-completion/0001`, sets
`rl_initial` and `bc_final` to the **latest** checkpoint, and leaves all saved
checkpoint bytes, BC progress, model/Adam/RNG artifacts and statistical protocol
unchanged. The existing archived runtime recognizes `rl_initial` and skips BC.
The new operational helper is not a change to the runtime source archive.

Formal RL was launched through archive recovery under parent PID 2153951.
Run ID remains `247a1750dfd54ae9ba7cf4ef87537028`; runtime source remains
`ba963af53c1840ecbce59d885880b9af21304380ab1073d379aaa1297d90f6b0`.
The actor starts from the selected BC weights; critic and PPO optimizers follow
the existing fresh-RL initialization. BC Adam and RNG remain in the BC artifact.

RL uses two H200 GPUs, 128 physical games per update, pure self-play, terminal
win/draw/loss +1/0/-1 and zero cash reward. Actor LR is 7.5e-6, critic LR 1e-4,
KL 0.05 with early stopping and no rollback. Scripts and history sampling are
disabled. The existing 100,000-update budget and evaluation schedule are retained.

Ruff, full mypy (811 source files), and seven targeted BC/recovery tests pass.
See [stop request](../outputs/analysis/gtrxl-bc-to-rl-20260916/stop-request.json),
[transition](../outputs/learning/gtrxl-m384-bc100-3d-20260916-s71001/bc-completion/0001/transition.json),
and [formal launch](../outputs/analysis/gtrxl-bc-to-rl-20260916/launch.json).

The actual formal U4 checkpoint has passed verification after 512 physical
self-play games. Actor and critic optimizers have committed 13 and 16 steps,
respectively, with zero actor rollbacks. Actor encoder, temporal and fusion
parameters updated; all model and optimizer tensors are finite and both rank
RNG streams are distinct. Every worker's actual return is terminal WDL with
zero cash reward, and all sampled opponents are current-policy self-play.
The first RL checkpoint parent hash exactly matches the selected cursor-1240
BC checkpoint; BC progress, its checkpoint bytes, runtime source and protocol
remain unchanged. Training continues on both GPUs.

U4 SHA256: `418b1c3f19c4c98ac75322e1512579079fb113c156abde870d63d27a8f7f9829`.
See [formal verification](../outputs/analysis/gtrxl-bc-to-rl-20260916/formal-verification.json).
