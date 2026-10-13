# Switching Six-Party RL to WDL with Terminal Cash Difference

User requested on 2026-09-26 to modify the current RL objective to WDL plus cash difference.
Retain the existing bounded terminal cash difference definition:

`reward = WDL + delta / (abs(delta) + 10000)`

Among them, `delta = own terminal cash - opponent terminal cash`, WDL denotes a win as +1, a draw as 0, and a loss as -1.
Configured as `cash_margin={beta: 1.0, cash_scale: 10000.0}`, `cash_weight=0`.
This terminal reward is used for the policy advantage and Critic target in PPO; the PPO loss formulation remains unchanged.

This switch targets `derived-v5b-m384-watch6-ppo50-20260926-s91001`,
run ID `aefa5349e25e44ceb948971f0b86f2ce`. Retain identical runtime identity, model, Critic,
two sets of Adam optimizers, dual rank RNG, historical pool, and existing PFSP statistics.
Full v5b, 384-turn memory, self-play against 64/64, unified PFSP, Actor/Critic LR
7.5e-6 / 1e-4, dual-GPU BF16, no automatic evaluation—continue as before.

## Stop and Qualification Verification

**02:35:33 UTC** sends normal stop signal, **02:35:58 UTC** saves and stops at
**U10 / 1,280 games**. Latest complete checkpoint `checkpoints/update-000010.pt`, SHA256:
`5e9bdb901d657ee60b1ae612d1ab94bb6ca0871b7da00e9563acbbcd89659397`.
Stop ledger SHA256:
`3d092f9cd729407c47ddeb2358ed6d6cbd954bfec4a2e50d77a32dde25ba11a0`.
Actor/Critic Adam both have 40 steps, dual rank RNG complete, all tensors finite;
357 strategies, 7 scripts, and 10 PFSP evidence records preserved.
Complete boundary checkpoint is separately hard-linked and retained, see
[Stop verification](../outputs/analysis/watch6-rl-margin-20260926/stop-verification.json).

Reward revision entry uses existing `valid_root` with local parent weight verification, compatible with authentication runtime initialized from BC. Directed regression covers random start, BC start, and rejection of corrupted parent weights; passes total of 6 tests with the existing cash difference formula, passing Ruff and mypy checks.

Migration configuration: [learning_watch6_margin_change_20260926.yaml](../configs/learning_watch6_margin_change_20260926.yaml).

Independent replica `watch6-margin-qualification-20260926-v1` executes U10 to U11–U14,
after normally stopping at U12, it is restored to U14 via archival source code. The actual returns from four rounds with dual rank match the reference formula with a maximum error of **0**; both Actor/Critic Adam advance 16 steps, and all tensors are finite.
PFSP sampling and cumulative statistics achieve exact replay; checkpoint parent chain, dual-rank RNG, and original run ledger remain unchanged and pass verification.
The qualification replica is retained as evidence, and its weights are not written back to the official run.
See [Qualification Report](../outputs/analysis/watch6-rl-margin-20260926/qualification.json), SHA256:
`3403f4591ce90a971a376f1e86e165213a8fb3691798663671eeda3c6cf12289`.

## Official Reward Revision and Continued Training

Updated retention of the original running `reward-revisions/0001`, effective from **U11**.
The protocol adds only the aforementioned `cash_margin`; the original U10 checkpoint byte remains unchanged, and the model, optimizer, RNG, PFSP, historical pool, and runtime identity are preserved. Previous protocol versions, source code archives, and stopped ledgers are fully traceable.
See [Change Log](../outputs/analysis/watch6-rl-margin-20260926/transition.json) and
[Continuity Verification](../outputs/analysis/watch6-rl-margin-20260926/transition-verification.json).

**02:48:00 UTC** Resume dual-card training from original U10 via archived recovery entry.
See [Startup Log](../outputs/analysis/watch6-rl-margin-20260926/launch.json) and
[Real-time Progress](../outputs/learning/derived-v5b-m384-watch6-ppo50-20260926-s91001/learning-progress.json).

**02:51:50 UTC** Official and complete checkpoint verified: **U12 / 1,536 games**, SHA256:
`1aa23659ad143822362fe56e942b9c5b69e286ac23a62bdb009dc89420438030`.
The actual terminal returns for U11 and U12 dual rank, based on the new formula, have a maximum error of **0**; both Actor and Critic Adam have progressed from 40 steps to **48 steps**, with 339 Actor tensors and 181 Critic tensors updated.
All tensors are finite, dual rank RNG is complete, historical records and opponent pool remain unchanged, and PFSP sampling and statistical replay are precisely verified.
Verification completed at the same time with U13; dual-GPU training continues. See
[Official Runtime Verification](../outputs/analysis/watch6-rl-margin-20260926/running-verification.json).

After normal shutdown, still restore from the latest complete state of this run:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-watch6-ppo50-20260926-s91001
```
