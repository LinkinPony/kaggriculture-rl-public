# Boey continuous replay collection

**September 27, 2026 Update**: As per user instruction, `56484772` has been excluded from all active collection lists and BC data entry points. No game involving any of its seats will be collected moving forward. The current seed is now **`56521745`**; original responses and prior training records are retained solely for historical purposes. See [Cleanup and Verification Record](exclude_boey_56484772_20260927.md).

Initially seeded with the user-provided [submission 56484772 / game 112499720](https://www.kaggle.com/competitions/kaggriculture/leaderboard?submissionId=56484772&episodeId=112499720). Official submission list, episode metadata, and team records confirm the fixed team identity as **16915014 / Boey**, with the submission's `dateSubmitted` timestamped at **2026-09-23T06:08:10.517Z**. The original response and source hash are preserved in [`submission-dates/56484772.json`](../data/external/kaggriculture-boey-replays/submission-dates/56484772.json) and the corresponding `.source.json` in the same directory; the team's public submission list is stored in `bootstrap/team.json`.

Configuration: [replay_watch_boey.yaml](../configs/replay_watch_boey.yaml). Reuse existing `kagg_revue.datasets.watching.cli`, launch a separate tmux session named **`kaggle-boey-replays`**, and run in parallel with [DSM](dsm_replay_watch.md) and [M & M & P & Q](mm_pq_replay_watch.md) ongoing tasks.

The collection scope is fixed to submissions from the team **`dateSubmitted >= 2026-09-23T06:08:10.517Z`**.
Within this time range, retired versions are excluded, and eligible new versions are continued to be tracked. Official submission timestamps are used, not inference based on game timestamps or submission numbers.
Each turn, the public submissions are refreshed and eligible versions already discovered are continued to be tracked; every hour, our historical submission games are scanned, and the configuration-listed historical list is read, including DSM, M & M & P & Q, and existing Boey diagnostic records.
Earlier versions are retained only in `outside_scope` and are not included in the active dataset or download queue;
versions with unverified dates are not downloaded and are recorded as errors.

After each turn, wait for **600 seconds**, with a maximum of **200 games** to be completed; 2 download threads share a 1.5-second request interval and rate-limiting cooldown within this task. If a single turn exceeds 30 minutes, it will be retried. Deduplication is performed by episode ID, without filtering by score, cash, or win/loss; explicitly excluded are any games involving `56414341` or `56484772`, regardless of seat; entire games containing either version are not collected. Overlapping games with existing daily ZIP entries directly reference members and are retained in the dataset. The official list does not include pagination fields, and the coverage is limited to the publicly available games actually returned by these discovery sources.

Original replays, API responses, and source lists are permanently saved in the gitignored directory [`data/external/kaggriculture-boey-replays/`](../data/external/kaggriculture-boey-replays/). `manifest.json` serves as the unified entry point; `status.json` provides backend task status, `last-cycle.json` contains the summary from the previous round, `download-progress.json` tracks the download progress for the current batch, and logs are stored in `collector.log`.

**2026-09-23 15:37:36 UTC** Small-scale acceptance: Found **1 valid submission / 95 completed public games**,
Completed 3 downloads (including user-provided `112499720`), with no download failures or errors detected. All three games were at 720 frames, featuring both `DONE` players. All original and compressed SHA256 hashes, episode IDs, and Boey identities have passed verification. The two earlier versions `56311035` and `56321899` are outside the scope. 7 existing data collection regression tests passed, and both Ruff and the data collection module's mypy checks have passed. See
[Acceptance Record](../outputs/analysis/boey-replay-watch-20260923/qualification.json).
**15:39 UTC** Launched full persistent configuration, continuing historical discovery and filling in remaining replays; real-time counts are subject to the current runtime list. Process status, actual runtime configuration, archive locks, and the status of the original two tasks are available in
[Launch Verification](../outputs/analysis/boey-replay-watch-20260923/launch.json).

Start or restart from the warehouse root directory:

```bash
mkdir -p tmp/replay-watch-boey data/external/kaggriculture-boey-replays
tmux new-session -d -s kaggle-boey-replays -c "$PWD" \
  'exec env PYTHONPATH=src TMPDIR="$PWD/tmp/replay-watch-boey" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -u -m kagg_revue.datasets.watching.cli --config-name replay_watch_boey >> data/external/kaggriculture-boey-replays/collector.log 2>&1'
```

After container or host restart, a restart is required. Existing inventories can be reused, and archive directory locks prevent duplicate instances.
When stopping, send `SIGTERM` to the supervisor PID of `status.json`, and wait for normal termination;
Original files and historical records are retained.
