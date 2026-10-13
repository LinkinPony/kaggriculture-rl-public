# Final model distribution

This release contains the inference packages for the final scoring submissions
56721459 (s101701 U250) and 56721201 (s100901 U756). Both use FP32 inference,
T=0, 384-turn memory, and terminal liquidation.

[artifacts.json](artifacts.json) records the original competition archive
SHA256 hashes, checkpoint identities, distribution archive hashes, and
sanitization scope. Original submission files are unchanged; the new packages
are traceable distribution copies.

Kaggle automatically expands the two uploaded tar archives into
`s101701-u0250/` and `s100901-u0756/`. Archive hashes identify the tar files
before upload. Verify downloaded content using `SHA256SUMS` at the dataset
root and `manifest.json` inside each model directory.

## Verification scope

Before upload, the complete archive manifests were checked and every
TorchScript ZIP member compared. All members except `.debug_pkl` must be
byte-identical, including tensor storage and executable model code. Python
inference files are byte-identical. Native-library changes only clear obsolete
path strings with no dynamic references; active RPATH/RUNPATH entries or
symbol references cause sanitization to fail.

Using the rebuilt native rules core, the original and sanitized packages were
given identical observations for both seats over a complete season in Python
3.11 and 3.12. Actions, feature hashes, and action programs were compared at
every step. The complete season covers cache eviction beyond the 384-turn
memory window and terminal liquidation. Machine-readable results are in
[validation.json](validation.json); the dataset includes the same report.
These checks do not establish a new leaderboard score or certify the Kaggle
host's execution-time budget.

[audit.json](audit.json) describes the privacy review of source files,
compressed assets, and final inference packages, including scanner false
positives.

All 46 files in remote dataset v2 were downloaded through authenticated
per-file endpoints and checked against their SHA256 hashes; see
[dataset.json](dataset.json). The whole-dataset endpoint returned 404 during
preparation. The repository README provides verified per-file download steps.
This endpoint issue does not affect the integrity of the uploaded files.

## English documentation

All project Markdown documentation is in English. The translation retains
research records, numerical results, identifiers, and executable examples.
Section links use stable anchors. [documentation.json](documentation.json)
records the language and integrity checks. This update changes documentation
only; the previously verified source code and model packages are unchanged.

## Tools

`kagg_revue.release.bundle` accepts explicit original archive paths and SHA256
hashes through Hydra and writes distribution files to a new output directory.
It does not upload files or change platform visibility.
`kagg_revue.release.verification` checks archive structure and complete-game
behavior against the specified original packages. Original archive paths and
local interpreter paths are supplied through local configuration and are not
committed to the release repository.

## Usage limitations

The dataset provides inference artifacts without the complete training weight
history, optimizer state, or raw competition replays. TorchScript and the
native extensions require compatible runtimes. Verify SHA256 hashes after
downloading.
