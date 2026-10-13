# Recovery of Original Source Code and Complete Training State

The current working tree might have undergone further restructure, while the runtime is still bound to the source code, configuration, and native binaries from startup. Restoring only the same runtime established from a random root in this command cannot be used to import previous weights or modify the experiment budget via the restore entry.

```bash
PYTHONPATH=src python -m kagg_revue.learning.recovery.cli \
  recovery.run=outputs/learning/<run>
```

`learning/recovery/` first checks the ledger, runtime status, source code tar members, file-by-file SHA256, native binaries, and Torch version, then re-constructs the source code in repository `tmp/learning-recovery-*`. The originally running `outputs` and persistent `data` are mapped into a separate tree; child processes load code only from archives; the working tree is not rolled back. Restoration still requires the original configuration, all member hashes, and lineage to be consistent. Active processes, completed budgets, corrupted tar paths/links, and file modifications are all rejected; a restoration lock prevents concurrent startup from the same entry point. Do not restart training due to tool observation timeouts.

The parent process forwards SIGTERM/SIGINT, waiting for the child process to stop after an atomic checkpoint, before cleaning up temporary source code.
Logs and `recovery-status.json` are permanently retained in the runtime directory. Temporary trees are cleaned without deleting models or external data.
`experiment.resume=true` from the original training entrypoint can still be used when the original configuration and working tree are identical.

**During recovery training operations, it is not allowed to delete the entire `tmp/` or any active `learning-recovery-*` directory.**
These directories are the current working directories of the training process, containing archived source code and links pointing to the real `outputs/`, and are not exhausted cache. Before cleanup, normally stop the training process and confirm that the process has exited; only remove temporary assets that are no longer in use.
On September 24, 2026, s80001 triggered a `FileNotFoundError` during progress writing due to deleting `tmp/` while running.
If the archived data, ledger, and complete checkpoints remain in the real `outputs/learning/<run>/`, the above recovery command can be used to reconstruct the running directory and resume from the last committed checkpoint; updates not saved after the checkpoint must be re-run.

Actual qualification alignment is `scratch-recovery-continuous-v1` and `scratch-recovery-interrupted-v1`:
Both start from the new seed 48002, with deterministic FP32, followed by four small data epochs and then 16 PPO episodes.
The interrupted branch actually receives SIGTERM after demonstration cursor 1; subsequently, the working tree changes, and then continues via the archival entry.
Final actor, critic, two PPO optimizers, CPU/CUDA RNG, demonstration terminal parameters/supervision optimizer/RNG,
cumulative supervision metrics and per-turn cash are exactly consistent with continuous training, exposing a total of 11,504 supervision rows.

Evidence available at [verification.json](../outputs/analysis/source-recovery/verification.json).
The archived source code is `549c270a10ce2ac1a72e31884a9eb7106dbcda4eec18c645f0a2e9a251383971`,
deterministic requirements are specified by `Experiment.deterministic=true` and FP32 settings, including
`torch.use_deterministic_algorithms(True)` and `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
The results are not extrapolated to imply default BF16 bit-by-bit consistency guarantees, and cross-Torch version exact fine-tuning is not supported.

Abnormal termination caused by source code defects can first be recorded using `python -m kagg_revue.learning.recovery.repair`, followed by restoration via the above archival recovery entry. Hydra parameter is `recovery.run=... +recovery.qualification=... +recovery.qualification_sha256=...`.
The acceptance report must match the original run ID, saved round, checkpoint hash, old/new source code hashes, and the complete protocol.
The repair entry retains the old ledger and source code, appending only `source-revisions/` and `repair_history`, without migrating training configurations, optimizers, RNG, or PFSP statistics. Real-world examples are available at [U1569 CUDA Graph Failure](budget_crash_20260912.md).
