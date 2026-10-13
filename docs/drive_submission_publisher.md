# Export submissions to Google Drive every half hour

User requested on 2026-09-30: Currently active RL and BC systems shall generate a submission tar every half hour and upload it to Google Drive, along with regular submission instructions. The instructions must also be included in the tar file. Configuration is set to [`configs/deployment_publish.yaml`](../configs/deployment_publish.yaml), and the implementation is located at [`src/kagg_revue/deployment/publishing/`](../src/kagg_revue/deployment/publishing/).

## Behavior

- Upon startup, capture once immediately, then at every UTC hour and half-hour (30-second polling interval, so actual startup may be slightly delayed).
  In the layer below `outputs/learning/`, detect active tasks, verify runtime status, PID startup time, and run ID.
  Do not infer active models based on historical documents, file modification times, or directory names.

- For each fixed ledger `latest`, store the submitted weights, supporting RL, training-in-progress BC, and compacted inference storage.
  Fixed files are verified via hash before task publication; when training retention policy deletes old paths, previously fixed inputs remain exportable.
  Do not lock training, do not modify training protocols or checkpoints.

- After tracking task termination or completion, export the final `latest` once. For normal BC termination, this field represents the best validation epoch selected by the training process itself. Initial configurations additionally retain requests issued during active training, including s101203/s101204 completed during the implementation period.

- Default settings are FP32, T=0, single CPU inference; retain native ABIs for Python 3.11 and 3.12; compilation uses 2 tasks, low CPU scheduling priority, and CUDA is invisible to the export process. Reuse existing deployment packager.

- Decompress and verify the actual tar within a new Python process; for each ABI, invoke the initial observations from both sides via `main.agent`.
  This is a startup smoke test and does not represent a full official qualification check performed every half hour.

- Upload target is a private `gdrive:kagg-rl-revue-submissions/<run-name--time-window--status--checkpoint-prefix>/`.
  Each directory contains `submission.tar.gz`, `submission-info.txt`, `submission-info.json`, and `receipt.json`; the latter provides the final tar SHA256, a reproducible full description, and Drive file link.
  Do not create Kaggle submissions.

- `submission-info.txt/json` is also located at the top level of the tar and is protected by the package's internal manifest hash.
  The format follows the historical description: model label, s number, RL U steps or BC epoch/shard, FP32, temperature, checkpoint shortcode. The final `pkg` shortcode is appended to the external receipt's description to avoid self-referential hashing within the tar.

- Upload uses rclone `copyto --immutable --checksum`, followed by remote MD5 and size verification.
  Retry after at least 120 seconds, reusing the same file and directory; locally retain the queue and acknowledgment, and avoid resubmitting identical time periods upon restart.
Upon successful validation of each file, immediately write `delivery.json`; on subsequent failures during retry, reuse per-file credentials to avoid re-requesting already verified files.
A single failed task does not block other models. There is no remote deletion or automatic cleanup of historical packages.

## Operation and Maintenance

All tasks, packages, states, and logs are located in `outputs/deployment/drive-publisher/`. Main files:

- `supervisor.json`: Guardian process PID and child process PID;
- `status.json`: Heartbeat, pending count, next capture time, tracked training;
- `publisher.log`: Queue and transfer status; `transfer.log`: Transfer progress and rclone errors;
  `supervisor.log`: Guardian startup logs;
- `jobs/*/worker.log`: Single-package build logs; `failure.json`: Recent failures and next retry time;
- `jobs/*/uploaded.json`: Files on the remote end are verified item by item before writing is performed.

Start (root directory of the warehouse; background startup is managed by the caller):

```bash
.venv/bin/python -u -m kagg_revue.deployment.publishing.supervisor
```

Run only one turn:

```bash
.venv/bin/python -m kagg_revue.deployment.publishing.cli +publishing.once=true
```

Both guarding and service hold exclusive locks. When stopping, send a SIGTERM to the PID in `supervisor.json`; it will exit after completing the current task. After modifying the YAML configuration, stop and restart the guard process, and existing tasks will continue using the exported configuration saved at the time of capture. When a child service unexpectedly exits, the guard process restarts it 15 seconds later. The current host is the `docker-init -- sleep infinity` container, with no systemd; the service has detached from the shell session, but after the entire container is restarted, the startup command must be re-executed, and the queue can be recovered.

## Receipt

rclone has been installed independently on the server: `local/rclone`.
The dedicated configuration is `local/kagg-revue.conf`, with permissions 600, located outside the repository; the original rclone configuration is retained.
Offline refresh tokens have been obtained via browser OAuth, with scope `drive.file`, allowing access only to files created by this client.
The authorization temporary log has been deleted. Do not include configuration file contents in the repository, model packages, or public logs.

Currently using the shared OAuth client for rclone. The official announcement states that this client will be deprecated in 2026; if Google revokes access, you must configure your own Desktop OAuth client according to the [official instructions](https://rclone.org/drive/#making-your-own-client-id) and re-authorize. Failed uploads will retain the local package and retry records.

## Verification

Directed test coverage: fixed inputs remain readable after training cleanup, reject bad hashes, half-hour time window with restart deduplication, final capture at termination, reuse previously built packages upon upload failure, reject confirmation when remote checksums mismatch, and BC annotation with actual selected epoch, and rclone new and old version hash name case sensitivity compatibility.
Combined with existing deployment provenance tests, 10 test cases pass; modifications to Ruff and mypy are successful.

At 10:38 UTC on 2026-09-30, the first s101102 U156 package along with three accompanying files completed remote verification:
tar SHA256 `a616c2f8f1525cad79746f03bcfc8d20ef9ad114cbe5e00ae716de1405d70ef2`,
93,713,838 bytes; Drive MD5 matches locally, and the SHA256 returned by Drive is also consistent.
[Upload directory](https://drive.google.com/).
The first round indeed encountered the shared project `RATE_LIMIT_EXCEEDED`, after which normal recovery was achieved; therefore, retaining failed uploads and retrying is a necessary path.

Additionally, run an official full game once more on this exact tar file, Python 3.11 with dual slots both set to `DONE`, lasting 192.37 seconds.
See [Complete Report](../outputs/analysis/drive-publisher-initial-rl-20260930-py311/report.json).
The package for Python 3.12 has passed the daily loading/dual-slot initialization check; however, the additional official executor is missing `jsonschema` in the native 3.12 environment, so the full game was completed using the existing, fully dependent 3.11 environment, and it was not stated as a pass for the 3.12 full game.
