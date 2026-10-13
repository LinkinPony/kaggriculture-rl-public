# Vadim Vasilenko continuous replay collection

Add existing continuous collection as per user request, using [submit 56557908](https://www.kaggle.com/competitions/kaggriculture/leaderboard?submissionId=56557908) as the discovery seed. Official game metadata confirms identity as **16770421 / Vadim Vasilenko**.
The official submission time of the seed is **2026-09-25 18:39:21.930 UTC**, i.e. Beijing Time **2026-09-26 02:39:21.930**; another currently publicly submitted version **56556874** was submitted at **2026-09-25 17:46:16.653 UTC**, and both versions fall within the range.
Official response, request parameters, download time, and SHA256 are stored in [`bootstrap/`](../data/external/kaggriculture-vadim-replays/bootstrap/) and [`submission-dates/`](../data/external/kaggriculture-vadim-replays/submission-dates/).

Fixed range is the official submission time **`dateSubmitted >= 2026-09-25T16:01:00Z`**,
i.e. **2026-09-26 00:01:00 UTC+8**, inclusive of boundaries and all subsequent submissions.
This lower bound is determined by submission time; game time and first download time do not participate in date filtering.
Earlier versions are categorized under `outside_scope`; versions with unverified dates are not downloaded, and original metadata is retained.
Versions are identified by team ID, with deduplication based on episode ID, without filtering by score, cash, or win/loss.
The exclusion criteria from other collection tasks **56414341** are retained; if any seat involves this submission, the entire game is excluded.
The scope is limited to officially published lists, known versions, seeds, and actual game sessions exposed in historical records.

Configured as [replay_watch_vadim.yaml](../configs/replay_watch_vadim.yaml), reusing `kagg_revue.datasets.watching.cli`, with an independent tmux session **`kaggle-vadim-replays`**.
Wait for **600 seconds** after each turn, with a maximum of **200 games** per round completed; two download threads share a 1.5-second request interval and rate limiting cooldown within each task, scanning their own historical submissions every hour.
Local discovery sources include existing historical lists, DSM, M & M & P & Q, DECEM, Boey's activity collection list, and the initial game list from this seed submission; overlapping games from existing daily ZIPs reuse member references.

Original data is permanently stored in
[`data/external/kaggriculture-vadim-replays/`](../data/external/kaggriculture-vadim-replays/).
`manifest.json` is the data entry point, `status.json` is the task status, `last-cycle.json` is the summary from the previous round,
`download-progress.json` is the real-time download progress, and the resident log is `collector.log`.
Configuration and timezone boundary verification are detailed in
[Configuration Acceptance](../outputs/analysis/vadim-replay-watch-20260926/configuration-verification.json).

**2026-09-25 23:49:05 UTC** Small batch acceptance completed: **2 submissions / 172 public games**,
3 full replays have been downloaded and verified, 169 more need to be supplemented; download and discovery errors are both 0.
All 3 games are 720 frames, with both sides as `DONE`; seat identities, compression, and original SHA256 have all passed verification.
12 earlier submissions have been confirmed with official dates and assigned to `outside_scope`; no unverified dates remain.
7 collection regression tests, Ruff, and the collection module mypy (11 files) have passed, see
[Collection Acceptance](../outputs/analysis/vadim-replay-watch-20260926/qualification.json).

**23:49:37 UTC** Launched the persistent task with full configuration, PID **112236**.
Configuration validation, tmux process, and exclusive archive lock passed; subsequently, 169 games have been queued and replenished, with 0 errors detected.
The original DSM, M & M & P & Q, DECEM, and Boey tasks are all still running, see
[Startup Verification](../outputs/analysis/vadim-replay-watch-20260926/launch.json).
Current real-time count is based on active `manifest.json` and download progress.

Start or restart from the warehouse root directory:

```bash
mkdir -p tmp/replay-watch-vadim data/external/kaggriculture-vadim-replays
tmux new-session -d -s kaggle-vadim-replays -c "$PWD" \
  'exec env PYTHONPATH=src TMPDIR="$PWD/tmp/replay-watch-vadim" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -u -m kagg_revue.datasets.watching.cli --config-name replay_watch_vadim >> data/external/kaggriculture-vadim-replays/collector.log 2>&1'
```

Continue running after session closure; need to restart after container or host reboot. Existing inventories can be reused, archive locks prevent duplicate instances.
