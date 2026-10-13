# s82001 Complete Training State Migration to v5b

**Latest Status:** **2026-09-25 15:02:18 UTC** Successfully restored dual-card RL from its complete U2349 self,
both checkpoint and archival engines have again confirmed complete v5b. See [Restoration Details](s82001_resume_v5b_20260925.md).

**Previously stopped:** Stopped normally as per user request at **2026-09-25 11:52:14 UTC**
at **U2349 / 300,672 games**, complete state preserved; latest Actor available for independent
[Boey 158 games BC](boey_56521745_bc_20260925.md). The original continued training log is retained below.

User requests to pause the current training, directly migrate `agronomy-v4-m384-dsm-games-ppo50-20260924-s82001` to the new features and resume, explicitly selecting its original learning rate **Actor 7.5e-6 / Critic 1e-4**.
Use the complete v5b, continue from the original directory and run ID `61a90ab34b384a91aa752cf4ee27cb9c`.

## Stop and Start

s86001 stopped normally at **2026-09-25 06:15:27 UTC** at **U258 / 33,024 games**,
complete optimizer, RNG, historical pool, and records preserved, see
[stop verification](../outputs/analysis/s82001-v5b-continuation-20260925/stop-verification.json).

s82001 starts at **U1843 / 235,904 games**, `checkpoints/update-001843.pt`, SHA256:
`eae69f6cf64a1d0d2a12e8355526d6463bee0db51ee62e4dad7d9322fb777f41`.
Pre-migration ledger SHA256: `7ed90bebc9534313d94bf4960d8f2f59c6fdb9bbaa37fc8af5dfe209f9dce752`.
New complete boundary `feature-revisions/0001/migrated.pt`, SHA256:
`2c6afe5df244a6afe4a191c84ba00ded0177d6fda854fdfe6c1e8c083b8e8f69`.
The migration itself does not increase training update counts; training continues from U1844 with the original seed distribution.

## Models, Optimizers, and History Pool

Input **22,003 → 27,915** dimensions, add 5,912 computed features. Retain old fields, action interface,
286 tokens and 384 turn memory. Reuse four-way zero-initialized residual projections:

| Object | Retained Tensors | New Tensors | New Parameters | Retained Adam States |
| --- | ---: | ---: | ---: | ---: |
| Actor | 347 | 4 | 59,904 | 335 parameters, average 7,372 steps |
| Critic | 182 | 4 | 49,920 | 177 parameters, average 7,372 steps |

Old parameter values, Adam first-order and second-order momentum, step counts, and hyperparameters are consistently matched. Parameter insertion alters Adam's integer indices, thus the index mapping is reconstructed based on **parameter names**; zero momentum and zero step states are initialized for the newly added four-path projections at the first gradient computation. Model initialization does not affect the already-saved dual rank RNG; the complete RNG is carried together with PFSP into the new checkpoint.

Original **333 activity strategies** (304 from external history + 29 from own starting point/snapshot), 7 C++ scripts, and
all PFSP statistics remain consistent without resetting priors. Strategy capacity remains at 440, with own history recorded every 64 turns.
Frozen history from v2/v4 continues to use identical old fields in new observations and the trailing validity block.

Pure terminal game **WDL: +1 / 0 / -1**, no cash reward; each turn consists of **64 self-play games + 64 unified PFSP games**.
Original Actor/Critic learning rates **7.5e-6 / 1e-4**, gamma = lambda = 1; dual H200, BF16,
Total budget of 100,000 turns, full checkpoint saved every 4 turns, no automatic adversarial evaluation.
Effective training protocol adds only `derived: true`, see
[Migration Configuration](../configs/learning_s82001_v5b_change_20260925.yaml).

## Compatibility and Integrity

The actual zero-projection migration of U1843 has previously been verified through CPU FP32 and full 719-turn CUDA BF16 checks:
Actor logits, actions, field weights, Critic state values/prefix values, and full memory are consistent; the new Actor projection gradients are non-zero.
This instance reuses the aforementioned evidence based on checkpoint and target native library hash; the v2/v4 generations of the old engines each have 14,400 observations of feature/action/mask and full trajectory consistency confirmed.

Re-ran 14 full integration checks with dual-seat configurations on 7 native scripts, and verified 10,066 v5b observations against core encoding.
Report binds the current native library and script asset hashes. The frozen strategy assets remain unchanged; the replaced native library now supports v5b encoding.
These are correctness checks and do not include ablation or strength evaluations.

16 targeted tests and code modifications passed with Ruff/mypy. Full CPU recovery pre-check for U1843 conducted individually per core, verifying old model parameters and Adam states; boundary reconfirmation completed, ensuring consistency in RNG, PFSP, all historical member identities, and U1844 next sampling. See
[pre-check](../outputs/analysis/s82001-v5b-continuation-20260925/preflight.json),
[script verification](../outputs/analysis/s82001-v5b-continuation-20260925/script-qualification.json), and
[migration validation](../outputs/analysis/s82001-v5b-continuation-20260925/migration-verification.json).

## Archiving and Recovery

`feature-revisions/0001` Save the ledger before migration, the original complete checkpoint hard links, the complete checkpoint after migration, the new source code, the new native library, and three qualification documents; the original source code and native library remain in their original locations.
The new boundary is registered as a retained complete recovery member, and the regular retention rules will not clip it into a file containing only Actor.

**06:30:33 UTC** Authentication source archive initiated dual-card continuation training, see
[Startup log](../outputs/analysis/s82001-v5b-continuation-20260925/launch.json).
After stopping, the same recovery entry will still be used:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-dsm-games-ppo50-20260924-s82001
```

## Actual Continuation Training Verification

**2026-09-25 06:38:57 UTC** Full validation of checkpoint **U1848 / 236,544 games**, SHA256:
`22a1089c59a358d8c60c14ca82eff952dbcab96871026919f93d2e3faae8020a`.
Replaying from migration boundary U1844–U1848, all PFSP sampling, post-match statistics, and historical pool consistency are verified;
Five turns all show 64/64, with actual rewards for two GPUs being pure WDL, and Actor LR consistently at 7.5e-6.

The 335 old Adam states of the Actor and the 177 old states of the Critic have been extended from step 7,372 to step 7,392;
Each of the 4 newly added projected Adam states has been updated at step 20, with non-zero weights and momentum.
All 339 Actor parameter tensors and all 181 Critic parameter tensors have been updated; all model and optimizer tensors are finite,
both rank RNGs are complete, and the saved Actor/Critic learning rates are 7.5e-6 / 1e-4.

The complete U1843 and original ledger hashes remain consistent before and after migration; the stopped ledger for s86001 has not changed.
The training parent process and two GPU worker processes are still running. See
[Official Verification](../outputs/analysis/s82001-v5b-continuation-20260925/resume-verification.json) and
[Ledger at Verification](../outputs/analysis/s82001-v5b-continuation-20260925/verified-state.json).
