# Native Rule Core of the New Mainline

New training, data encoding, and evaluation using `_revue_core`. It includes rule engine, public observation encoding, action execution, pure neural self-play batches and prefix replay, without compiling four versioned scripts. The default build command is:

```bash
PYTHONPATH=src python -m kagg_revue.native.build
```

Hydra is configured as [native_build.yaml](../configs/native_build.yaml) and supports `build.jobs=16`.
The target uses C++ and OpenMP and does not require a CUDA compiler; GPU training still uses CUDA-enabled PyTorch.
The build cache is located at `tmp/native-build/core`, and the binary is installed to `src/kagg_revue/native/`.
The [build report](../outputs/native/core/build.json) saves all compilation units, source code snapshots, commands, and binary hashes;
source code changes during the build process will prevent installation.

The currently verified core SHA256 is
`802d32a930242b897dddbd4f5533435a7e9a970521ca26d6d63367e251dfcb7f`.
It exports `Engine`, `ContractSession`, `SelfPlayBatch`, and `parallel_spec`.
Batch construction only accepts environment, seed, seat, unit upper limit, thread count, and quantity table parameters; it does not accept teacher or script opponent parameters.
The retained `advance_programs(..., selfplay=True)` is compatible with shared callers and rejects `False`.

The shared engine packaging is located at `native/csrc/core/`, and the old script factory is located at `parallel/legacy.cpp`.
The isolation import check at `learning.train` confirms that `_revue_native`, `production`, or versioned teachers will not be loaded.
In the 19 compilation units of [Compilation and Linking Check](../outputs/analysis/native-core-extraction/linkage.json):
No versioning strategy is present, and the retrieved script symbols and teacher strings are empty.

The old tool still explicitly uses `_revue_native`; `build.target=legacy` can be used to build a complete old target when needed.
Deployment adopts another minimal `_revue_observation` extension, see [Deployment Instructions](learning_deployment.md).
The full duration of the 51001/51002 long-budget experiment has used the source code and original binary `ab3a125f34b0c148efba722ee9003ce69e8cd197d1135be7b288dcb5ed377137` archived at startup; these runtime processes were not replaced.
New runs initiated from current code record, archive, and restore `_revue_core` itself.

## Validation Scope

[Qualification Index](../outputs/analysis/native-core-extraction/qualification.json) Summarizes the following evidence:

- [64 game official replays](../outputs/analysis/daily-20260906-core-native-audit/report.json): 92,160 observations consistent, including private backpack order.
- [8 complete neural trajectories](../outputs/analysis/native-core-neural-qualification-v2/report.json):
  Step-by-step verification of new and old batches, public observation encoding, and fixed official interpreter; 11,504 strategy features align with 11,520 official observations, including terminal states. Additionally, 8 prefix replay channels and 4 forked next-step paths from repeated parent channels were checked.
- [Fully random root flow](../outputs/learning/scratch-native-core-qualification-s52001/qualification.json):
  FP32, uncompiled strategy, completed 16 online games after 2,876 demonstration steps and 24 supervision updates, with 4 actor updates and confirmations.
- [Archive recovery](../outputs/analysis/native-core-extraction/recovery.json): After working tree changes, only the archive core was installed in isolated source code, verifying the original ledger, latest model, two PPO optimizers, and RNG archive; no additional training or modified runs were appended.
- 14 new mainline-related tests and 29 independent compatibility tests for the old extensions passed; mypy passes for Ruff and 598 source files.

This coverage of rule and process consistency for the tested trajectory is not a full-state equivalence proof or model strength evidence. The recovery check for the new core does not include re-executing bit-by-bit fine-tuning after interruption; the prior deterministic FP32 true SIGTERM reference remains preserved in [Recovery Notes](learning_recovery.md). The original route's publicly stated conclusion of complete defeat against the opponent's strategy still stands and cannot be substituted by these engineering validations.
