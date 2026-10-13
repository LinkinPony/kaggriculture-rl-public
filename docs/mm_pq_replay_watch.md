# M & M & P & Q Continuous Replay Collection

Target is the Kaggriculture team **16681125 / M & M & P & Q**, based on the submission provided by the user:
[Submit 56440961, Game 111819427](https://www.kaggle.com/competitions/kaggriculture/leaderboard?submissionId=56440961&episodeId=111819427)
and cross-confirmation with the saved Kaggle official leaderboard and game metadata.

Configuration: [replay_watch_mm_pq.yaml](../configs/replay_watch_mm_pq.yaml).
Entry: `kagg_revue.datasets.watching.cli`. Wait **600 seconds** after each turn before data collection; each turn can complete up to **200 games**. Two download threads share a **1.5-second** request interval and server-side rate limiting. Each turn runs in a separate subprocess and terminates if it exceeds **30 minutes**, then retries in the next turn. A file lock ensures only one collector runs within the same archive directory.

Discover trajectory:

- Refresh the team's currently public submissions every round, while continuing to query previously discovered submissions.
- Paginate and read our own submission list hourly, scan its historical games; extract the other `submissionId` belonging to the team from `teamId=16681125`, and save the corresponding evidence episode ID.
- Import the two historical game archives explicitly listed in the configuration, recording the source file SHA256.
- The user-provided episode is always retained as the priority seed for collection.

All completed public games can be collected, with no filters for win/loss, cash, score, or date,
but subject to user-specified submission exclusion lists.
Deduplicate by episode ID; previously completed games and submissions removed from the API list are still retained in local records.
Failed entries remain in the pending collection list, with new entries prioritized over historically failed duplicates to prevent backlog and block new data.
The official episode list does not include pagination parameters, thus it cannot guarantee recovery of previously unpublished submissions or historical games not returned by the API.

Permanent original data directory:
[`data/external/kaggriculture-mm-pq-replays/`](../data/external/kaggriculture-mm-pq-replays/),
The entire directory has been added to gitignore.

| File | Content |
| --- | --- |
| `manifest.json` | Submitted turns and games, download list, participant identities and rewards, pending download IDs, failures and sources |
| `replays/<episode>.json.gz` | Complete official replay retaining all observations and actions |
| `replays/<episode>.json.source.json` | Download time, official URL, SHA256 of original and compressed files |
| `snapshots/` | Raw API responses per turn and source hashes, including our historical game list |
| `history.jsonl` | Additional saved records of startup, discovery, completion, exceptions, and stop events |
| `status.json` | Supervisor PID, runtime status, and next check time |
| `last-cycle.json` | Number of completed turns from previous round, total count, pending download count, and error count |
| `download-progress.json` | Progress of current download batch |
| `collector.log` | Background process logs |
| `resolved-config.json` | Current full runtime configuration |

New downloads are validated for episode ID and compressed file hash before being added to the list. Files that are interrupted during download and before the list is published can be verified and reused in the next turn; if the interruption occurs before the source file is published, the unverified bytes are retained and the file is re-downloaded. Registered files are not re-downloaded; existence and size are checked each turn; full scans of previous replays are not repeated.

Start in the warehouse root directory:

```bash
tmux new-session -d -s kaggle-mm-pq-replays \
  'exec env PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -u -m kagg_revue.datasets.watching.cli >> data/external/kaggriculture-mm-pq-replays/collector.log 2>&1'
```

The existing Kaggle SDK and authenticated `rl` Python are used; repository `.venv` currently does not have the Kaggle SDK installed.
Authentication is read by the existing SDK and credentials are not copied.
`tmux` session name is **`kaggle-mm-pq-replays`**, and the session continues to run after closing the conversation or terminal.
The current environment PID 1 is `docker-init`, with no available systemd/cron; **the above command must be re-run after container or host restart**, existing data and collection manifests can be directly reused.

Check the PID in `status.json`, and send `SIGTERM` to stop the supervisor and the current downloading sub-process, for example `kill -TERM <PID>`. Original replay and list are retained. Do not directly kill tmux to replace normal termination.

Collect once using the same entry to append `watch.once=true`; modify the check interval by changing the Hydra configuration's `watch.poll_seconds`, then normally stop and restart the task.

Acceptance: Real-world examples have been downloaded, 720 frames, both sides `DONE`, episode identity, original, and compressed hashes match.
Ruff, mypy, and 7 related tests passed, covering historical commit paging and mining, disappearance record retention, download deduplication, breakpoint recovery, bad file detection, failure of projects not blocking new projects, and shared rate limiting cooling. Actual repeated startup attempts were rejected.

2026-09-22 00:56 UTC Round one complete: Reviewed our **63 submissions**, identifying this team's **7 submissions, 884 public games**, with the first **5 games** successfully completed dual hashing and identity verification, with 0 failures.
Tracked submissions are `56188084`, `56206720`, `56254996`, `56281630`, `56371729`, `56414341`, `56440961`; the last two originate from the current public list, while the other five were discovered through our historical games.
**00:57 UTC** Constant data collection has been initiated in the aforementioned independent tmux sessions to continue completing the remaining replays.
Real-time counts are subject to the list in the archive directory and download progress.

<a id="section-dfa13629b0d0"></a>

## September 22: Exclude 56414341 as per user request

Configure addition of `excluded_submissions: [56414341]`. Publicly submit discoveries, local history, and one's own games.
Scanning, cache recovery, and manifest publishing all apply exclusion rules; entire games involving any seat of excluded versions.
Do not enter data collection. Save known excluded episode IDs to avoid re-introduction via seeds or restarts.

The old collector has been properly shut down. After acquiring the archive lock, the version's **10 complete replays, corresponding source files, and the historical query files saved separately for this submission** were deleted, totaling 82 files. Entries were removed from the activity list, pending download list, and retry count.
During cleanup, the number of versions and games reduced from **7 versions / 910 games** to **6 versions / 900 games**.
The daily merge entry has been uniformly updated to exclude these 10 games, bringing the current total to **17,538 games**; the actual subset used by SE is **1,471 games**, with 2 of the deleted 10 games having been used by opponents on SE terrain. Statistics, date distributions, rating distributions, and directory hashes have been updated accordingly with the explicit exclusion. Historical identities and deletion credentials are retained for traceability.

**06:54:54 UTC** Re-established persistent tasks with exclusion rules; **06:55:29 UTC** completed one round of real verification,
maintaining 6 versions / 900 games, with pending downloads, download failures, and discovery errors all at 0, and excluded versions not re-entered.
DSM parallel tasks also apply the same exclusion rules, see [DSM Collection Records](dsm_replay_watch.md).

See [deleted evidence](../outputs/analysis/replay-watch-exclusions-20260922/purge-56414341.json),
[merged directory revision](../outputs/analysis/replay-watch-exclusions-20260922/merged-catalog-revision.json),
and [verification](../outputs/analysis/replay-watch-exclusions-20260922/verification.json).
8 related tests, Ruff, and full mypy passed; new tests cover deletion followed by recovery from all discovered entry points and restart, without re-introduction, as well as conflicts between target version and seed configuration.
