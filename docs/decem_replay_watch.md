# DECEM Continuous Replay Collection

Using the submitted [submit 56489091 / game 112776500](https://www.kaggle.com/competitions/kaggriculture/leaderboard?submissionId=56489091&episodeId=112776500) as the seed, official game metadata and the public submission list confirm the identity as **16623559 / DECEM**.
The game was created on 2026-09-24 07:20:49 UTC, against opponent DSM.
The seed submission time was 2026-09-23 09:11:00.127 UTC; another public version is 56482350.
Official response and hash provenance are stored at
[`bootstrap/`](../data/external/kaggriculture-decem-replays/bootstrap/).

The user then specifies a lower time limit of **2026-09-23**, with the current fixed range being the official submission time **`dateSubmitted >= 2026-09-23T00:00:00Z`**, inclusive of the boundary and subsequent versions. Earlier versions, games, and download records are moved to `outside_scope` and are no longer tracked or re-downloaded; original files are preserved. Historical versions are supplemented with submission times from official metadata; versions with unverified dates are not downloaded. Versions are identified by team ID, deduplicated by episode ID, and are not filtered by score, cash, or win/loss outcomes. The exclusion criteria from other tasks, 56414341, are retained: the entire game is excluded if any seat involves it. The coverage is limited to officially published lists, known versions, seeds, and games actually exposed in the historical list configuration.

Configuration: [replay_watch_decem.yaml](../configs/replay_watch_decem.yaml).
Reusing `kagg_revue.datasets.watching.cli`, running an independent tmux session **`kaggle-decem-replays`**.
Wait **600 seconds** after each turn, with a maximum of **200 games** per round; two download threads share a 1.5-second request interval and rate limiting cooldown within each task, scanning their own historical submissions every hour.
Existing daily ZIP overlapping games are retained as member references to avoid redundant downloads.
Local sources include existing historical lists as well as DSM, M & M & P & Q, and Boey's activity collection lists.

The original data is permanently stored in
[`data/external/kaggriculture-decem-replays/`](../data/external/kaggriculture-decem-replays/).
`manifest.json` is the data entry point, `status.json` is the task status, `last-cycle.json` is the summary from the previous round,
`download-progress.json` is the real-time download progress, and the log is `collector.log`.

Before setting the date lower bound, batch acceptance completed at **2026-09-24 07:36:07 UTC**: discovered **9 submissions / 1,276 public games**,
with **16 available** (13 daily ZIP entries + 3 standalone downloads), needing to supplement 1,260 more, errors at 0.
All 16 games were successfully read, all at 720 frames, both sides marked DONE; verified DECEM seat assignments, compression, and original hashes,
ZIP member CRCs and sizes, including user-specified 112776500. 7 regression tests (collection), Ruff, and collection module mypy (11 files) passed, see
[Acceptance Record](../outputs/analysis/decem-replay-watch-20260924/qualification.json).

**07:36:54 UTC** Launching full persistent configuration, PID **3837220**.
Process, actual configuration, and exclusive archive lock have been verified; DSM, M & M & P & Q, Boey data collection, and s82001 RL continue to run. See [Startup Verification](../outputs/analysis/decem-replay-watch-20260924/launch.json).
Real-time quantities are based on the currently running manifest.

**07:40:22 UTC Fixed Lower Bound Acceptance:** Complete 10 known versions' official submission times,
where **2 versions / 319 games** match the 9/23 starting point, with 4 already available, awaiting completion of 315 more games, errors = 0.
8 earlier versions, 959 metadata entries, and 15 obtained replay records are moved into `outside_scope`;
all existing records and original files are preserved, and user seeds remain within active scope.
**07:40:53 UTC** Resume persistent data collection under the new lower bound; actual configuration and exclusive core lock verification passed.
See [Lower Bound Acceptance](../outputs/analysis/decem-replay-watch-20260924/fixed-cutoff/qualification.json) and
[Restart Verification](../outputs/analysis/decem-replay-watch-20260924/fixed-cutoff/launch.json).

Start or restart from the warehouse root directory:

```bash
mkdir -p tmp/replay-watch-decem data/external/kaggriculture-decem-replays
tmux new-session -d -s kaggle-decem-replays -c "$PWD" \
  'exec env PYTHONPATH=src TMPDIR="$PWD/tmp/replay-watch-decem" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -u -m kagg_revue.datasets.watching.cli --config-name replay_watch_decem >> data/external/kaggriculture-decem-replays/collector.log 2>&1'
```

After container or host restart, a restart is required; existing lists can be reused, but archived locks prevent duplicate instances.
