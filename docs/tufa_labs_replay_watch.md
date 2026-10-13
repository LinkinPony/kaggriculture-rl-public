# Tufa Labs Continuous Replay Collection

Starting from the submission of [56642914 and game 114912906](https://www.kaggle.com/competitions/kaggriculture/leaderboard?submissionId=56642914&episodeId=114912906), collect publicly available replays for this version and all subsequent updated versions. Official metadata confirms the team as
**16621497 / Victor @ Tufa Labs**, with submission timestamp
**2026-09-28 13:56:46.353 UTC**, i.e. Beijing time **2026-09-28 21:56:46.353**.
Official responses, requests, retrieval times, and SHA256 hashes are stored in
[`bootstrap/`](../data/external/kaggriculture-tufa-labs-replays/bootstrap/).

Configured as [replay_watch_tufa_labs.yaml](../configs/replay_watch_tufa_labs.yaml),
fixed lower bound **`dateSubmitted >= 2026-09-28T13:56:46.353Z`**.
Discover subsequent versions by stable team ID, filter by official submission time, and deduplicate by episode ID.
Earlier versions and versions without confirmed dates are moved to `outside_scope`, with original metadata preserved.
The currently public old version **56631037** is outside the scope; seed **56642914** is within scope.
Retain existing global exclusions **56414341, 56484772**; if any seat is involved, the entire game is excluded.
No filtering by score, cash, or win/loss; coverage is limited to publicly exposed games from official interfaces and historical lists.

Reuse `kagg_revue.datasets.watching.cli`, operate in independent tmux session
**`kaggle-tufa-labs-replays`**. After each turn, wait for **600 seconds**; each turn can at most complete up to **200 games**;
Two download threads share a 1.5-second request interval and rate limiting within each task, scanning their own historical submissions every hour.
Local discovery sources include existing historical lists, DSM, M & M & P & Q, DECEM, Boey, Vadim's activity list, and the official game list from this seed; overlapping games from existing daily ZIPs reuse member references.

The original data is permanently stored in
[`data/external/kaggriculture-tufa-labs-replays/`](../data/external/kaggriculture-tufa-labs-replays/).
`manifest.json` is the data entry point, `status.json` is the persistent status, `last-cycle.json` is the most recent completed round,
`download-progress.json` is the intra-round download progress, logs are in `collector.log`; the entire archive directory has been added to Git ignore.

**2026-09-28 22:55:25 UTC** First verification: **1 submission / 102 games completed in public matches**,
Downloaded **3 games** (including user-specified **114912906**), pending completion of **99 games**, with discovery and download errors both at 0.
All 3 games are **720 frames, both sides marked DONE**; replay ID, team identity, compression, and original SHA256 have passed verification.
4 earlier submissions have been confirmed for date and moved into **`outside_scope`**; no unverified dates remain.
The first verification temporarily uses **`once=true / downloads_per_cycle=3 / scan_own_history=false`**;
Ongoing tasks use the full parameters from the configuration file, automatically continuing to complete missing games and detecting subsequent updates.

Configuration boundary validation, existing 8 item data collection tests, Ruff and data collection module mypy (11 files) passed.
See [Configuration Acceptance](../outputs/analysis/tufa-labs-replay-watch-20260928/configuration-verification.json),
[Playback Acceptance](../outputs/analysis/tufa-labs-replay-watch-20260928/qualification.json), and
[Startup Validation](../outputs/analysis/tufa-labs-replay-watch-20260928/launch.json).
Real-time quantities are based on active manifest and download progress.

Start or restart from the warehouse root directory:

```bash
mkdir -p tmp/replay-watch-tufa-labs data/external/kaggriculture-tufa-labs-replays
tmux new-session -d -s kaggle-tufa-labs-replays -c "$PWD" \
  'exec env PYTHONPATH=src TMPDIR="$PWD/tmp/replay-watch-tufa-labs" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -u -m kagg_revue.datasets.watching.cli --config-name replay_watch_tufa_labs >> data/external/kaggriculture-tufa-labs-replays/collector.log 2>&1'
```

Continues to run after interactive session closure; requires restart after container or host reboot. Existing inventory can be reused, exclusive lock rejects duplicate instances.
