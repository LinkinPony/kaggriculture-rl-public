# Checkpoint Storage and Cleanup

Training defaults to retaining the most recent two complete checkpoints. **An additional complete checkpoint is permanently preserved every 200 RL updates**, including the Actor, Critic, two optimizers, and RNG states per rank. Permanent checkpoints are indexed by absolute update number (U200, U400, ...), and are saved even if outside the regular save cycle, without participating in rolling deletion or Actor pruning. When overlapping with the most recent two complete checkpoints, only one copy is retained; the total storage footprint of permanent checkpoints grows with training progress.
Hydra configurations are set to `checkpoint_keep_recent: 2`, `checkpoint_keep_interval: 200`;
setting the latter to `null` disables periodic permanent retention, and setting the former to `null` disables the automatic retirement limit.
Optimizers from cleaned or pruned historical checkpoints cannot be restored; checkpoints are not erroneously registered as complete when rules are enabled.
Complete checkpoint status is retained for validation best points that have not yet completed BC, ensuring that early stopping selection and recovery do not lose Adam states.

History pool, RL initialization baseline, and fixed evaluation opponents require only inference parameters. Existing checkpoints to be continued are converted to `inference/<original-checkpoint-hash>.pt`, with Critic, optimizer, RNG, and duplicate PFSP removed.
Statistics; model parameters are verified bit by bit. `members` retains the original checkpoint identity, `inference_artifacts`
Physical paths and storage hashes are independently registered, so PFSP key, probabilities, historical metrics, and parent chain remain unchanged despite compression.
When importing external historical models, inference files are saved directly; existing compact files are prioritized for hard links, with cross-file-system copies used as fallback.

Validation recovery covers only the most recent complete recovery point, the current historical pool, external opponents, and fixed control models. Historical epochs, evaluation nodes, and checkpoint revisions of configurations are no longer automatically permanently retained; retirement hashes, configurations, metrics, and source code remain preserved. The complete budget report validates historical evaluation records using the union of active members and retired hashes, without relying on the existence of old weights.

Save order is: write complete new recovery point; prepare and verify simplified opponent; atomically publish ledger; delete retired weights.
Sync all ranks with new members and storage mappings. Do not delete original files if ledger publication fails.

Training in progress uses archived source code. Modifications in the workspace do not automatically affect this process; storage migration must first properly save the stopped process, then apply only storage-related source code revisions to the original archive. The migration retains the original protocol, setting the number of full recovery points to 2 and enabling permanent retention every 200 updates, with verification of checkpoint bytes, model loading, Adam loading, dual-GPU RNG, and the next round's PFSP sampling. A subsequent migration will append storage revisions while preserving the prior revision history.

The warehouse-level cleanup entry point is:

```bash
python -m kagg_revue.learning.storage.cli storage.action=plan
python -m kagg_revue.learning.storage.cli storage.action=apply
```

`configs/learning_storage.yaml` Explicitly list the runs to retain. By default, only plans are generated; `apply`
will delete independent `outputs/` files in `.pt/.pth/.ckpt/.safetensors` that are not dependencies of these retained runs, including independent weights in other experiment, acceptance, analysis, and release directories. Training locks and recovery locks for two runs must both be idle, and each run must have an archived checkpoint with recovery eligibility. The plan records inode, size, and modification time per file, and rejects files that have changed during execution. Source data, source code archives, logs, metrics, ledgers, and packaged submission artifacts are not subject to this cleanup. After deletion, only explicitly retained runs are guaranteed to be recoverable.

The redundant weights from the original source can be deleted: historical models already imported use preserved in-place hard links within the runtime, and recovery no longer reads from the original source directory. The fixed source ledger hashes in the old configurations serve only as historical records; when creating new experiments, the source and current ledger hashes of retained sources must be re-registered, and it is not permissible to directly rerun the old startup configurations of retired experiments.
