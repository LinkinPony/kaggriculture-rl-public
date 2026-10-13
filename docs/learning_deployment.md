# Certified Model's CPU Allocation and Full Game Eligibility

<a id="section-74c85d88a648"></a>

## Subsequent Weight Submission via Authenticated Deployment Implementation

When the same model structure, deployment source code, native observation ABI, and packaging toolchain have undergone complete qualification validation,
subsequent updates to only the training weights or selection of T=0 / T=1 may use simplified acceptance:

1. Fix the latest complete checkpoint in the training ledger, save the checkpoint and ledger snapshot, and confirm member hashes, training source code archive, and native binary identity.
2. Export the required temperature from the source code archive, and verify the checkpoint, temperature, file list, SHA256, and competition size limit for each specific submission package.
3. Each specific submission package must complete at least one full official executor game in the target Python runtime, including cold start, actions from two seats, official state, `DONE` terminal liquidation, and time limit.
4. After submission and before submission, cross-check the list as described and by package hash to confirm that each temperature is added exactly once; save the confirmation and eligibility report.

When these conditions hold and the deployment code remains unchanged, reuse the previous eager baseline, conduct multiple random seed repetitions, use the second Python version, perform repeated export comparisons, and verify full warehouse Ruff/mypy results. If there are changes to the model architecture, deployment code, native ABI, or toolchain, re-run the complete qualification validation; if a single game validation fails, first identify the root cause before submission. This streamlined process still performs individual package validation of the actual archive being uploaded, preventing the use of old weight results as evidence for new package execution.

Entrance accepts a randomly selected root or checkpoint from `outputs/learning/` for initializing members. Generate a verifiable package:

```bash
PYTHONPATH=src python -m kagg_revue.deployment.bundle
```

`deployment_bundle.yaml` specifies runtime, members, two Python ABIs, compiler, and fixed-sampling RNG.
Output is located at `outputs/deployment/` with timestamp; build report binds checkpoint, lineage, and full source code.
Archive, TorchScript actor, each native binary, and all files within packages. Build fails if source code changes occur during the build.
Allow current refactored worktree; through full archive and hash tracing, do not falsely claim origin from a clean commit.

Initialize checkpoint with reuse of root type and parent weight validation from the training side, verify declarations, retained parent checkpoint hashes, member hashes, and runtime lineage; export retained `checkpoint-root` and `input_weights` types without random initialization. Support both source types simultaneously for package checks and CPU entry points. When deploying with training archive overlay, separately record the source code identities for training and deployment, and log file differences.

The default deployment temperature remains 1; export conditional argmax using the user-specified `+deployment.temperature=0`. Within the package, `agent_profile.json` records the temperature and selection method. The corresponding eager consistency verification uses `+audit.temperature=0`. At zero temperature, directly invoke `sample=False` without performing division or action sampling; a complete game and time budget check must still be performed on the final exact package.

Memory cache coherence defaults to `rtol=1e-5, atol=1e-6`. The audit record retains the maximum absolute error, the maximum error after deducting relative tolerance, the number of comparisons exceeding the default absolute tolerance, and the first position at which this occurs; progress is saved every 64 turns. When verifying FP32 rounding differences, `+audit.cache_atol=0.000002` may be explicitly specified to define the absolute tolerance; the configuration and error values must be preserved alongside the qualification report. This setting affects only audit operations; action details and integer turn IDs still require exact identity, and submitted packages and original model computations must remain unchanged. Both the first failure and source code discrepancies in auditing must be preserved.

The memory-aware model exports explicit KV cache, preserving the memory capacity, temporal positions, and round-by-round elimination rules from training. `agent_profile.json` records memory geometry; each seat maintains an independent cache and RNG, which is reconstructed at the 0th turn of a new game, after which it only accepts consecutive observations. The submitted package uses the original model's `step()` without invoking the stateless path, otherwise historical paths are discarded. Full game eligibility is simultaneously verified against actions and each round's cache tensor, with elimination occurring when memory capacity is exceeded; the final exact package is additionally checked by the official executor for cold-start and time budget compliance.

2026-09-09 Fixed the issue where the custom `kagg_revue::decoder_layer_norm` training model, after being converted to TorchScript, could not load the submitted package in a separate process. Now, on CPU, the model is copied, and the decoder LayerNorm in the copy is replaced with a PyTorch-native LayerNorm having identical parameters, shape, and epsilon; the original model object and the fused isolation operators on the training side are preserved. The separate process now imports only PyTorch, verifying loadability and sampling under the same RNG. When building from earlier training archives, only the export fix for the current `src/kagg_revue/deployment/actor.py` should be stacked, file hash differences between the training archive and the current version should be recorded, and the exact package should be re-verified. The identity of the training source code and the deployment source code should be recorded separately.

`_revue_observation` relies solely on CPU C++, official observation transformation, feature and action execution, without a complete training engine, CUDA, or script opponents. Each seat has an independent public history and RNG state, preserving the conditional random sampling from training time, with no script fallback. The static C++ runtime library uses symbol isolation to avoid conflicts with the host's other extensions' locale settings.

Verify the exact package rather than work tree source code:

```bash
PYTHONPATH=src python -m kagg_revue.deployment.check
```

`deployment_check.yaml` defaults to the verified 51001, Round 512 portable package and its SHA256. It can also override `check.archive`, `check.sha256`, and `check.interpreter`. First, verify the complete archive and file inventory, then extract from repository `tmp/`. Launch a child process without a warehouse PYTHONPATH, running the actual package entry point. The two seats respectively cover standard file execution and Kaggle-style execution without `__file__`. The parent process provides only official observations; it progressively compares deployment features, action decoding, and the full state between official/native sides. After termination, clean up temporary extractions, retain sequential timing, module identity, and reports.

The earlier 47001, Round 128 v3 package SHA256 is `6828d6d7cc3cd765df2fd1c15fc3590db2703b9b9d226a78f8e4132b994f64d6`,
size 3,866,587 bytes. Python 3.11/Torch 2.13 and Python 3.12/Torch 2.12 each completed the same two games, with identical action trajectories SHA256, totaling 5,752 program checks and 5,760 observations.
Cross-runtime reports are available at [cross-runtime.json](../outputs/analysis/deployment-bundle/cross-runtime.json).

The timing for the above-check actions does not include entry imports. The supplementary cold-start checks directly use the official, unmodified wheel internals `Agent`, `Environment`, tool functions, and the Kaggriculture interpreter, registering only this environment:

```bash
PYTHONPATH=src python -m kagg_revue.deployment.budget
```

Each seat is fixed to an independent process on a dedicated CPU, with GPU hidden; the initial PyTorch import and inference occur within the official first-action timer. The actual `Environment.step` receives official logs, deducts additional quotas, and verifies the full season status.
The same v3 archive completes two games on both Python 3.11/Torch 2.13 and Python 3.12/Torch 2.12, totaling 5,752 program executions and 5,760 observation consistency, all seats ending with `DONE`; cash balances and action trajectories match exactly with prior seed-archive verification. Eight cold seats take 1.096–1.149 seconds for the first action, and the official 60-second extra quota remains at least 59.851 seconds in all cases; each game's total local runtime ranges from 17.86–18.56 seconds, with peak RSS not exceeding 589 MB. See [Cold-start eligibility, original report, and source code identity](../outputs/analysis/deployment-budget-v3/qualification.json).
The check environment for Python 3.12 is preserved in `local/kagg-revue-deployment-py312`, with dependency records available at [Environment Record](../outputs/analysis/deployment-budget-v3/py312-environment.json); this dependency environment is not included in the deployment package.

Current [Kaggle Docker source code](https://github.com/Kaggle/docker-python/blob/main/Dockerfile.tmpl)
Using Python 3.12 package path, supports inclusion in local compatibility matrix; this does not prove that the competition host's CPU, dependencies, or time budget match the local environment. Public environment declaration `actTimeout=1`, see
[Official environment schema](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/kaggriculture.json).
The full timing loop of the local official executor cannot replace validation on the Kaggle host execution.
The current local delivery is default updated to a fixed 512-turn endpoint of the first round, archived as
[submission.tar.gz](../outputs/deployment/scratch-scaling-s51001-u512-portable-v1/submission.tar.gz),
SHA256 `b3c22b47f70e607ce77de6f6cceef2bfeb6c2cdf5cff7c163e20f8551d362c85`.
This exact package completes two full official timing loops with cold imports under each runtime; 5,752 program executions, 5,760 observations consistent, with identical action trajectories and cash flows across both runtimes. Under concurrent local evaluation load, maximum cold action time is 2.191 seconds, subsequent actions 0.118 seconds, final additional allowance at least 58.809 seconds, peak RSS below 589 MB.
See [512-turn deployment eligibility](../outputs/analysis/deployment-scaling-s51001-u512/qualification.json).
No uploads or submissions; prior submission records do not serve as evidence for deploying a new model.
