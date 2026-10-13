# Kaggriculture RL

The complete reinforcement learning research codebase for the Kaggriculture
competition: a C++ rules engine and batched games, behavior cloning, recurrent
policies, PPO, self-play and PFSP opponent pools, evaluation, and CPU submission
export. Domain packages live in `src/kagg_revue/`. Historical experiment
configurations, tests, and research documentation are included.

## Final submission models

The two final scoring submissions are distributed through the
[Kaggle dataset](https://www.kaggle.com/datasets/linkinpony/kaggriculture-rl-final-submissions).
Model files are stored outside Git. The dataset contains two complete CPU
inference packages:

| Model directory | Kaggle submission | Configuration |
| --- | --- | --- |
| `s101701-u0250/` | 56721459 | MMPQ branch, U250, FP32, T=0, 384-turn memory, terminal liquidation |
| `s100901-u0756/` | 56721201 | DSM branch, U756, FP32, T=0, 384-turn memory, terminal liquidation |

These are sanitized distributions of the final submitted policies. Model tensors
and executable TorchScript content are unchanged. Local build paths, machine
paths in debug records, and obsolete native-library path strings were removed;
license notices were added and file hashes regenerated. The distribution tar
archives therefore have different SHA256 hashes from the original competition
uploads. Their correspondence is recorded in the
[artifact manifest](docs/release/artifacts.json) and in each package's
`release-provenance.json`.

Kaggle automatically expands the uploaded tar archives into the directories
listed above. Archive hashes in the manifest identify the pre-upload tar files;
`SHA256SUMS` at the dataset root verifies the actual downloaded files.

Download with a Kaggle account that has access to the dataset:

```bash
dataset_ref=linkinpony/kaggriculture-rl-final-submissions
mkdir -p outputs/releases
kaggle datasets download -d "$dataset_ref" -f SHA256SUMS -p outputs/releases
while read -r release_hash release_file; do
  release_destination="outputs/releases/$(dirname "$release_file")"
  mkdir -p "$release_destination"
  kaggle datasets download -d "$dataset_ref" -f "$release_file" \
    -p "$release_destination"
done < outputs/releases/SHA256SUMS
(cd outputs/releases && sha256sum -c SHA256SUMS)
```

The per-file download method above was used to verify the remote dataset. You
can also attach the dataset to a Kaggle Notebook and read either model directory
directly. The whole-dataset download endpoint returned 404 during release
preparation; per-file downloads and the uploaded models were available. See the
[remote verification record](docs/release/dataset.json).

Choose either model directory and call `agent(observation, configuration)` in
its `main.py`. Each directory includes a TorchScript actor, Python inference
code, and Linux x86-64 native observation extensions for CPython 3.11 and 3.12.
NumPy and PyTorch must also be installed. These are inference packages; they do
not contain optimizer state, the complete historical opponent pool, or training
data. See the [release notes](docs/release/README.md) for the verification scope.

## Install from source

Use Python 3.11 or later. The native core requires CMake, a C++20 compiler,
OpenMP, and ripgrep. GPU training also requires a compatible CUDA build of
PyTorch. Run these commands from the repository root:

```bash
python -m pip install -e '.[dev,analysis]'
python -m kagg_revue.native.build
kagg-revue --cfg job --resolve
```

The default build produces `_revue_core`. The full script-opponent target uses
`build.target=legacy` and additionally requires the CUDA development toolchain.
All domain modules and historical commands are retained. Release preparation
did not change the training objectives or policy algorithms.

## Training and research records

The default `learning_mainline` used by `kagg-revue` is an early research
baseline initialized from random weights. It requires separately prepared
demonstrations and does not fully reproduce the final submitted models.
The final branches use the
[U250 configuration](configs/learning_mmpq_rl_u200_cont_1gpu_20260930.yaml) and
[U756 configuration](configs/learning_s99001_dsm_ppo_20260929.yaml).
These historical configurations depend on their parent weights, datasets, and
opponent pools. The source release does not include every historical artifact.

Training defaults to pure terminal WDL rewards: win +1, draw 0, loss -1. PFSP
mastered-opponent review and predecessor evidence inheritance retain their
original settings. Cash-margin reward exceptions in specific historical runs
are documented for interpreting and restoring those protocols.

- [Current mainline and historical decisions](docs/CURRENT_MAINLINE.md)
- [Final submissions and evaluation records](docs/final_submission_20260930.md)
- [Native rules core](docs/learning_native.md)
- [Deployment workflow](docs/learning_deployment.md)
- [Archived-run recovery](docs/learning_recovery.md)
- [Privacy handling and distribution scope](docs/release/PRIVACY.md)

Links under `outputs/` in the research notes refer to original research
artifacts that are not distributed through Git. `data/external/` retains source
manifests without raw replays or encoded arrays. Sanitized manifests cannot
replace the original files authenticated by historical training ledgers;
historical SHA256 values have not been rewritten.

## Checks and contributions

```bash
ruff check src tests
mypy src
pytest -q src/kagg_revue/release/test_redaction.py
```

Run other tests according to their native-extension, GPU, and external-data
requirements. Write new training results to `outputs/`, disposable files to
`tmp/`, and reusable external data to `data/external/`. Supply credentials only
through the local environment. Do not commit tokens, service configuration, or
private download links.

## License

Original project code is licensed under [MIT](LICENSE). Third-party environment
ports, public opponents, native bindings, and runtime libraries retain their
own licenses and attribution. See [NOTICE](NOTICE), [LICENSES](LICENSES), and
the notices in the opponent directories.
