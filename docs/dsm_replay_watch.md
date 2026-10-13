# DSM Continuous Replay Collection

Using [submission 56444344 / game 111918050](https://www.kaggle.com/competitions/kaggriculture/leaderboard?submissionId=56444344&episodeId=111918050) as the seed, the official episode metadata and leaderboard have confirmed that the fixed team identity is **16732748 / DSM**.
The currently public list also includes the more recent `56454259`. Team ID is used to identify historical versions; for example, early replays show a team named `masspeaks`, but its API game metadata still associates that seat with team 16732748.

Reuse `kagg_revue.datasets.watching.cli`, configured as
[`configs/replay_watch_dsm.yaml`](../configs/replay_watch_dsm.yaml).
Run independently in a tmux session **`kaggle-dsm-replays`** for concurrent data collection from M & M & P & Q.
After each turn, wait 600 seconds. Each turn downloads up to 200 games, with 2 download threads sharing the same task, using a 1.5-second request interval and Retry-After cooling. Rescan our own historical submissions every hour.

Sources of discoveries include the currently released version of DSM, previously discovered older versions, user seeds, and six local historical lists. The continuously updated list maintained by M & M & P & Q is also a source for identifying historical opponent versions of DSM.
**The current submission scope is fixed at `dateSubmitted >= 2026-09-17T00:00:00Z`**, with the starting point designated by the user on September 22 and will not advance forward with subsequent dates; older versions meeting the criteria are continued to be tracked even if they disappear from public lists, and new submissions are likewise included. The official public `EpisodeService/ListEpisodes` returns the original `dateSubmitted` of historical submissions, with responses and sources saved to `submission-dates/`; versions with unverified dates are not downloaded and are recorded as errors, without inferring dates from game times, file timestamps, or submission numbers.

Each turn checks the existing official daily ZIPs in `data/external/`, reusing the replays from within based on episode ID.
**Overlapping games are retained in the DSM dataset and counted as available**; in `replays`, they are recorded as `storage: daily_zip`, `path`, `member`, ZIP member CRC, and size; upon reading, the specified ZIP member is directly opened. These games no longer require independent downloads of `.json.gz`. Newly added local daily packages will be automatically included in reuse in the next turn. Existing independent replays continue to be reused; only games lacking a local source are added to the download queue.

Previously identified versions prior to the starting point, game records, and download logs are moved into manifest's `outside_scope`, with original files retained for traceability and no longer tracked or re-downloaded. Activities `submissions`, `episodes`, and `replays` contain only records meeting the fixed starting point criteria. Deduplication is performed by episode ID, without filtering by score, cash, or win/loss; `56414341` explicitly excluded by users takes effect for all seats, and any full-game involving it is excluded from this task. The official list lacks pagination fields, and the coverage is limited to the public games actually returned by these sources.

The original data is permanently stored at
[`data/external/kaggriculture-dsm-replays/`](../data/external/kaggriculture-dsm-replays/).
`manifest.json` is the unified entry point for submissions, games, and downloaded files; `status.json` represents the ongoing task status,
`last-cycle.json` is the summary of the last completed game, and `download-progress.json` shows the real-time download progress of the current batch.

Adjust collection records before the fixed starting point:

**2026-09-22 06:47:35 UTC** First batch validation completed: 13 related submissions, 1,936 public games played.
Prioritized download of 3 episodes (including user-provided episode), 0 failures. All three episodes were 720 frames, both sides marked DONE.
SHA256 of original and compressed files, episode ID, and official team ID verified successfully.

**06:54:54 UTC** Full persistent configuration initiated; continuing to scan historical data and supplement remaining replays.

**07:03:43 UTC** First full configuration collection completed: 23 related submissions, 3,867 public games played.
Cumulative downloads: **203 games**, 3,664 games remaining to download. Download failures and discovery errors are both 0.
Real-time scale based on currently running manifest.

**07:13:54 UTC Fixed Starting Point and daily Reuse Verification:** Verified the official submission dates for 23 known versions, of which 12 meet the starting criteria. The activity dataset consists of **1,461 games**, with **524 available**, including **520 games directly referenced from daily ZIP files** and 4 games using standalone replays, with **937 games pending download**. No download failures or errors were found. All 520 entries for member localization and CRC/size have passed verification, and one game was randomly sampled from each of the 5 daily ZIP files to validate episode ID, team display names, and both sides' DONE status. All overlapping games have been retained, and no duplicate `.json.gz` entries were found. The metadata from 11 earlier versions, 2,411 game records, and 202 download logs have been moved into `outside_scope`, with original files preserved. The resident configuration has been restored, with up to 200 games replenished per turn.

7 test collection tests, Ruff, and full mypy (930 source files) passed. New tests cover fixed-start boundary conditions, game duration cannot replace submission time, future versions and restarts, historical file retention, dataset member retention after daily reuse, avoidance of duplicate downloads, and detection of newly added daily packages in the next round. See [Fixed Start and Reuse Verification](../outputs/analysis/dsm-replay-watch-20260922/fixed-cutoff-qualification.json).

Acceptance product:
[`outputs/analysis/dsm-replay-watch-20260922/qualification.json`](../outputs/analysis/dsm-replay-watch-20260922/qualification.json).

Restart command:

```bash
mkdir -p tmp/replay-watch-dsm
tmux new-session -d -s kaggle-dsm-replays -c "$PWD" \
  'exec env PYTHONPATH=src TMPDIR="$PWD/tmp/replay-watch-dsm" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -u -m kagg_revue.datasets.watching.cli --config-name replay_watch_dsm >> data/external/kaggriculture-dsm-replays/collector.log 2>&1'
```

After container/host restart, the task must be restarted; existing files and metadata can be reused, and archive directory locking prevents duplicate instances.
