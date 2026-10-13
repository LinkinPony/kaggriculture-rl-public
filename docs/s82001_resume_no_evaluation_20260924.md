# Restore s82001, completely disable automatic baseline evaluation

User requests to halt s84001, restore **`agronomy-v4-m384-dsm-games-ppo50-20260924-s82001`**,
and completely disable the monitoring of the random anchor/start model automatic evaluation corresponding to "model performance".

## Pause and Resume

s84001 stopped normally at **2026-09-24 09:05:12 UTC** in **U12 / 1,536 games**,
with full checkpoint retention: `checkpoints/update-000012.pt`, two Adam optimizers, dual rank RNG, PFSP, and historical outputs preserved.
See [Stop Verification](../outputs/analysis/s82001-resume-no-evaluation-20260924/stopped-new-run.json).

s82001 started via the archive recovery entry at **09:10:46 UTC**, carrying forward the original run ID
`61a90ab34b384a91aa752cf4ee27cb9c`, resuming from **U113 / 14,464 games**.
Actor/Critic, Actor/Critic Adam each advanced **452 steps**, dual rank RNG, PFSP statistics, and
**306 historical strategies + 7 native scripts** all inherited their original states.
Starting checkpoint SHA256:
`a1f40ad6730be9ad8dbf66a133ac7bdf91274ee2475b68ee97f21c5f40e64e70`.
See [recovery starting point](../outputs/analysis/s82001-resume-no-evaluation-20260924/resume-original.json) and
[launch log](../outputs/analysis/s82001-resume-no-evaluation-20260924/launch.json).

Train protocol restored verbatim: **pure terminal WDL (+1/0/-1)**, without cash difference;
**64 self-play games + 64 unified PFSP / update** games, Actor/Critic LR 7.5e-6 / 1e-4.
This training resumes from the checkpoint of s82001 itself, without importing the BC or learning state from s83001 or s84001.

## Evaluation of Discontinuation Methods

Remove from current `learning.train` execution path directly:

- Random anchor/start point evaluation at the beginning of a new run.
- Evaluation at fixed intervals and at the last update.
- Confirmation evaluation after training budget is completed.

Simultaneously remove the additional synchronization wait triggered by evaluation interval from `CheckpointWriter`, retaining normal saving, PFSP snapshot, and final flush. This is not increasing the evaluation interval; evaluation fields in the original configuration no longer trigger matches.
Manual evaluation implementation and historical records are preserved; the monitoring page still allows access to previous results, which will not be updated with this continued training.
BC's validation set loss and PFSP's existing training game statistics remain unaffected.

Training control flow tests replace the old evaluation function with a direct error-throwing implementation, covering the new run start, evaluation boundaries per turn, recovery, and budget endpoint; these are no longer called. Together with source code revisions and checkpoint persistence tests, **12 tests pass**, modifications to Ruff, mypy, and formatting checks pass. See
[Test Record](../outputs/analysis/s82001-resume-no-evaluation-20260924/tests.log).

## Archival Revisions

Use existing `learning.recovery.repair` authentication and archive revisions to the runtime directory `source-revisions/0001`. Compared to the archived files of s82001, only modify `learning/train.py` and `learning/checkpointing/writer.py`; add control flow testing. Original source code and original ledger are preserved in the archive. Current source code SHA256: `fdd21ce6fa7df425f8f649786d7e5bf273e8712e1faf1958a4f6ec65e8465439`.

Only the ledger fields `source`, `source_directory`, and `repair_history` have changed; all other components, including training protocol, checkpoint bytes, optimizer, random numbers, pool members, and PFSP statistics, remain unchanged.
See [Revision Qualification](../outputs/analysis/s82001-resume-no-evaluation-20260924/qualification.json) and
[Revision Verification](../outputs/analysis/s82001-resume-no-evaluation-20260924/repair-verification.json).

## Restored Actual Training

**09:14:41 UTC** Successfully completed consecutively **U114–U116** without skipping or duplicate updates;
sequential PFSP sampling can be independently replayed from the original statistics of U113, with the original 306 strategies and 7 scripts remaining unchanged.
Each round consists of 64 self-play games and 64 PFSP games; the actual returns for the two GPUs are only -1/0/+1, with no cash difference terms.
The archive recovery supervision process and both GPU worker processes are operating normally; the actual execution source code contains no automatic evaluation calls, and the original evaluation file set and hashes remain completely unchanged. At the time of this verification, U116 had already completed computation, and the asynchronous ledger saving is still registered under U113.
See [Run Verification](../outputs/analysis/s82001-resume-no-evaluation-20260924/resume-verification.json).

After normal stop, continue using the same archive restore command:

```bash
CUDA_VISIBLE_DEVICES=0,1 TMPDIR="$PWD/tmp" PYTHONPATH=src \
  .venv/bin/python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/agronomy-v4-m384-dsm-games-ppo50-20260924-s82001
```
