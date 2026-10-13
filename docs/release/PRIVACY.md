# Privacy handling

This repository was imported from a reviewed source snapshot. It retains the
complete domain code, tests, historical configurations, and research notes.
The original private repository's Git history, personal email addresses,
untracked files, credentials, logs, and training outputs were not imported.
Commits use the public GitHub identity and a noreply email address.

Local absolute paths and private Drive folder links were replaced. Machine
settings for publishing tools are supplied through environment variables or
explicit configuration. Data provenance, third-party credits, public Kaggle
submission IDs, and research results are retained. Research dates and algorithm
development records describe the project's provenance; the release does not
anonymize its public project identity.

[snapshot.json](snapshot.json) lists snapshot files with sanitized paths.
Historical data manifests and protocols still record the original artifact
hashes. Sanitized copies are not substitutes for the original authenticated
inputs.

The final model packages were separately sanitized to remove JSON build paths,
TorchScript debug paths, and obsolete ELF path strings. Local user and group
information was cleared from tar headers, and archive timestamps were
normalized. Model tensors, executable TorchScript content, and Python
inference code are unchanged.

The release review covers all Git files to be pushed, commit metadata, and
unpacked model members. External server credential files were not inspected or
copied; platform authentication was handled by the configured official
clients. The project's release tools do not change GitHub or Kaggle visibility
settings.
