# Latest Random Root BC → RL, inheriting s91001 historical pool and using terminal cash difference

**Subsequent status update:** The user canceled this training on 2026-09-27; s93001 stopped normally at **U14 / 1,792 games** at **05:09:15 UTC**. The latest valid plan is
[s91001 U2137 re-BC then automatically enter 300 updates warmup RL](watch6_u2137_bc_to_rl_20260927.md).
The following content is retained as historical run records.

Stopped normally at 2026-09-27 04:55:36 UTC by s92001 BC
at turn 16,608 / 95,333,278 supervision turns.
36 epochs completed, and 120 batches of epoch 37 completed.
Latest full weights are `pretraining/shard-016608.pt`, SHA256:
`a98a3fcdff6529db9bc933bd4a7b1dc94a1f4639118a404399bb56dec8154910`.
Original BC's Adam, dual rank RNG, epoch weights, and training logs are preserved.
See [stop verification](../outputs/analysis/watch6-bc-to-rl-20260927/stop-verification.json).

## Initialization and Historical Opponents

New run: `derived-v5b-m384-watch6-ppo50-20260927-s93001`.
Actor uses the latest BC weights above to create a Critic, two sets of PPO Adam optimizers, and random seeds.
Complete v5b, 27,915-dimensional input, 384-turn memory.

The previous RL was `derived-v5b-m384-watch6-ppo50-20260926-s91001`,
stopped at **U2137 / 273,536 games**.
Fully inherited its **390 activity history strategies**: 356 external historical strategies, 34 self-originated strategies and snapshots;
added the final **U2137** not yet entered into the activity pool, SHA256:
`3200230b002527352cd2e7a02531d7e279a4b9a75a27fe4f503875960c32ac81`.
Including the current BC starting point, the initial pool consists of **392 strategies + 7 native scripts**.
Strategy capacity is **527**, retaining 136 slots for its own historical records, with a new RL snapshot added every 64 turns.

The native script continues for `ahmed_v45`, `metacounter_r1`, `shop_router_0913`, `rayk_v38_low_pressure`, `farming_v4_0914`, `ahmed_v53`, `thomas_metav4`. All inheritance strategies retain their original identity, source, and evidence of feature compatibility. Evidence from the previous PFSP game is fully preserved in the original run; the new learner starts from a fresh prior. See [Selection List](../outputs/analysis/watch6-bc-to-rl-20260927/opponent-selection.json).

## Rewards and PPO Formula

Starting from **U1**, use the previously authenticated cash difference version from the prior turn:

`reward = WDL + delta / (abs(delta) + 10000)`

`delta = own terminal cash − opponent terminal cash`; WDL is +1 for a win, 0 for a draw, and -1 for a loss.
`cash_margin={beta: 1.0, cash_scale: 10000.0}`, `cash_weight=0`.
This terminal reward is used for the policy advantage and Critic target in PPO, and the PPO loss form follows the original implementation.

Retain the effective configuration from the previous round: 64 self-play games + 64 unified PFSP per round,
the script has no dedicated quota or guaranteed allocation; Actor/Critic learning rates are **7.5e-6 / 1e-4**,
gamma = lambda = 1, no warmup; dual-GPU BF16, 48-step gradient blocks,
budget of 100,000 rounds, save full checkpoints every 4 rounds, no automatic evaluation.
See [Hydra Configuration](../configs/learning_watch6_ppo50_20260927.yaml) and
[Differences from the previous round's effective protocol](../outputs/analysis/watch6-bc-to-rl-20260927/protocol-diff.json).

## Startup and Verification

**2026-09-27 05:00:31 UTC** Launching dual-GPU RL,
run ID **`52d4d6186505476db5fcb4b2f7e7b075`**.
First, freeze the opponent pool via bootstrap and initialize a new prior, then restart U0 to enter training.
351 initial Actor tensor values match bit-by-bit with BC's 16,608th batch; input checkpoint hash verification passes.
392 policy pool member relationships, original identities, and historical origins are individually verified;
bootstrap confirms actual file paths, model structures, and boundedness of all imported weights.
7 script runtime configurations are identical to the previous round; neither the original BC nor RL ledger has been modified.
5 relevant source code modules pass Ruff and mypy checks; the training implementation has not been modified in this run.

See [Start Verification](../outputs/analysis/watch6-bc-to-rl-20260927/initialization-verification.json),
[Historical Pool Verification](../outputs/analysis/watch6-bc-to-rl-20260927/pool-verification.json),
[Startup Log](../outputs/analysis/watch6-bc-to-rl-20260927/launch.json), and
[Real-time Progress](../outputs/learning/derived-v5b-m384-watch6-ppo50-20260927-s93001/learning-progress.json).

**05:05:13 UTC** Full **U4 / 512 games** checkpoint acceptance passed, SHA256:
`46ec0d15f7d251d74d4435c5406b36fa0306c3ec99050c70996936682901f1d9`.
Actor / Critic Adam completed **4 / 16 steps**, consistent with the actual optimization records over four rounds;
Actor retains existing KL early-stop protection. 339 Actor tensor updates have been applied,
all model and optimizer states are finite, both rank RNGs are intact, and actual learning rates match the protocol.
All four rounds were allocated to 64/64, with 0 error in terminal cash difference formula across both ranks.
All PFSP sampling and post-match statistics have passed exact replay verification; U1 has actually played against the final U2137 from the previous round.
Old BC and RL ledger hashes remain unchanged; during validation, U6 was completed, and dual-GPU training continues.
See [formal operation verification](../outputs/analysis/watch6-bc-to-rl-20260927/running-verification.json),
the complete U4 is separately stored in this report directory as acceptance evidence.

After normal termination, restore from its own archived source code and complete state:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/derived-v5b-m384-watch6-ppo50-20260927-s93001
```
