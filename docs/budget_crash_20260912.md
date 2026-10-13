# U1569 CUDA Graph Fault and Recovery

Run: `outputs/learning/budget-26m-20260911-s66001`.

## Fault Evidence

2026-09-12 06:53:32 UTC, rank 0 reports at the historical opponent sampling synchronization point of U1569:
`CUDA illegal memory access`. The parent process terminates another worker, writing "failed" at 06:54:03.
The last complete save point is **U1568**, with 200,704 physical games completed.
All tensors of the model, Critic, and two optimizers are finite; the dual-GPU RNG is complete and distinct,
checkpoint SHA256 matches the ledger, and PFSP checkpoint statistics match the ledger.

U1569 drew the prior `context-26m-20260908-s62001`'s U4302.
Each-card 42 inference graphs in this vocabulary last used at U1514; U1536 performed rank 0 cycle evaluation, and then this graph was not used again until U1569. The new process directly resumed the original U1568's state, enabling it to complete U1569–1570, indicating that individual checkpoints and the current input batch are insufficient to reproduce the accumulated graph lifecycle state from prior runs.

## Causes and Fixes

Current Torch is `2.13.0+cu130`, Git version
`cf30153c4c131c8164ee7798e5022d810682e2cb`.
The old implementation invoked `torch.cuda.Stream()` for each ActorRuntime, but this API uses a pooled approach:
Native consecutive 65 allocations involve only 32 distinct underlying streams, with 0/32/64 allocation pointing to the same stream.
Thus, long-term training graphs, cached historical opponent graphs, and temporary evaluation graphs may share the same capture stream.

This Torch version invokes `clearCublasWorkspacesForStream` when destroying a CUDA Graph, simultaneously releasing cuBLAS workspaces referenced by other live graphs on that stream.
In a native small-scale GEMM replay, destroying temporary graphs reused across two streams and releasing idle caches results in `CUDA unspecified launch failure`. A similar mechanism exists upstream in the [fault record](https://github.com/pytorch/pytorch/issues/193402).

The above mechanism aligns with the officially running rank, evaluation boundaries, and failure upon first reuse of an old graph, constituting a high-confidence diagnosis.
The original process does not record low-level stream pointers, making it impossible to post-hoc verify which two graphs actually collided; the asynchronous CUDA stack also cannot independently identify the specific kernel that failed. No claim is made about fully reproducing the complete training session as deterministic.

`policy/capture.py` creates a dedicated nonblocking CUDA stream for each inference graph to bypass the loop pool.
When destroyed, it first synchronizes, resets the graph and its workspace, and then destroys the stream; training, historical opponents, and evaluation all use this implementation.
`policy/inference.py` uses this implementation. The sampling distribution and training configuration remain unchanged.
`cuda-bindings` already exists in the current Torch environment and will directly rely on explicit registration.

Add a source-only repair entrypoint `learning/recovery/repair.py`: bind verified source code, original checkpoint, and complete protocol, archiving the old ledger with the new source code to `source-revisions/`, updating only the source code identity and repair records. Subsequently, continue using the original archiving recovery entrypoint to fully optimize the optimizer and per-GPU RNG.

## Verification and Recovery Records

- GPU Return: After creating and destroying 40 independent temporary graphs, the replay results of the long-term GEMM graph are element-wise correct.
- 14 related Python checks passed, including fixes for protocol mismatch in entry rejection, state retention, and PFSP.
- Full source code passed Ruff, mypy (721 files), and formatting checks for modified files.
- Dual-GPU replica completed U1569–1576, totaling 1,024 games, with normal stop at U1572 and recovery from source code archive.
  The Actor/Critic each advanced 176 steps, with zero KL rejections; all checkpoint tensors are finite, and PFSP sampling replay, checkpoint/ledger statistics are consistent. Both GPU CUDA RNGs advanced and remained independent; in the 5-round window of self-play, 224 out of 640 games were achieved, maintaining 35% of the target. This verification only demonstrates engineering workflow and is not a strategy strength assessment.

The same U1568 runs the original code and the patched code in separate processes, and the sampling results of U1569 are completely identical. Differences in optimizer values then appear, and some game outcomes of U1570 also differ; the current configuration is non-deterministic BF16. We do not claim bit-level training equivalence here. A field-by-field comparison is preserved in
[Field-by-Field Comparison](../outputs/analysis/budget-crash-20260912/baseline-comparison.json).

Fault diagnosis (../outputs/analysis/budget-crash-20260912/diagnosis.json),
Original exception stack (../outputs/analysis/budget-crash-20260912/failure-traceback.txt),
Dual-GPU acceptance verification (../outputs/analysis/budget-crash-20260912/qualification.json).
The complete checkpoint U1568 used for recovery is also preserved via a hard link in the analysis directory to avoid being cleaned up according to the normal retention policy.

Formally fixed registration under `source-revisions/0001`, source code identity as
`4adb98a4e7716183db323f52b041bff0fb09229ea8f192c4e8915736eeed501f`.
Field-by-field verification only modifies `source`, `source_directory` and appends `repair_history`;
Original protocol, registered model, checkpoint bytes, all historical records, and PFSP statistics are retained.
At 08:41:28 UTC on 2026-09-12, dual-GPU formal continuation training was initiated via the original recovery entry.
See [State Transition Verification](../outputs/analysis/budget-crash-20260912/transition-verification.json) and
[Formal Launch](../outputs/analysis/budget-crash-20260912/formal-launch.json).

**Formal U1572 complete checkpoint has passed verification**: 512 new games added for U1569–1572,
Actor/Critic each advanced 88 steps, zero KL rejections, all model/optimizer tensors are finite,
checkpoint parent chain is continuous with original U1568, PFSP replay and saving statistics are consistent, and both GPU CUDA RNGs have advanced and differ.
Two-GPU workers are alive, WebUI status is `running`, formal training continues.
See [formal recovery verification](../outputs/analysis/budget-crash-20260912/formal-verification.json).
