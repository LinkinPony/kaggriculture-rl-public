"""Run reproducible coverage diagnostics on daily and public submission replays."""

import csv
import io
import json
import math
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.coverage.extraction import HORIZONS, extract


class Analysis(BaseModel):
    """Locate the actual BC manifest and the separately acquired new sources."""

    baseline: Path
    public: Path
    extra_daily: list[Path]
    output: Path
    workers: int = 8
    include_public: bool = True
    reuse_daily: Path | None = None


def concentration(values: list[Any]) -> dict[str, Any]:
    """Report raw diversity and the effective number of frequent alternatives."""
    counts = Counter(values)
    n = len(values)
    entropy = -sum((v / n) * math.log(v / n) for v in counts.values()) if n else 0.0
    return {
        "n": n,
        "unique": len(counts),
        "top_fraction": max(counts.values(), default=0) / max(n, 1),
        "effective": math.exp(entropy),
        "top": counts.most_common(8),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep empirical frequencies separate from fair opponent strength claims."""
    summaries: dict[str, Any] = {}
    for channel in ("full", "units", "market", "structure"):
        summaries[channel] = {
            str(h): concentration([r["prefixes"][channel][str(h)] for r in rows]) for h in HORIZONS
        }
    return {
        "trajectories": len(rows),
        "names": len({r["name"] for r in rows}),
        "submissions": len({r["submission_id"] for r in rows if r["submission_id"]}),
        "prefixes": summaries,
        "assets24": concentration(
            [json.dumps(r["snapshots"]["24"]["assets"], sort_keys=True) for r in rows]
        ),
        "versions": dict(Counter(r["version"] for r in rows)),
        "native_first_four_exact": sum(r["native_first_four_exact"] for r in rows),
    }


def _tasks(config: Analysis) -> tuple[list[Any], set[int]]:
    baseline = orjson.loads(config.baseline.read_bytes())
    partitions = {
        int(Path(a["member"]).stem): a["split"] for a in baseline["partition"]["assignments"]
    }
    archives = [
        (Path(s["archive"]), "baseline_daily") for s in baseline["configuration"]["sources"]
    ]
    archives += [(p, "new_daily") for p in config.extra_daily]
    tasks, daily_ids = [], set()
    for path, source in archives:
        with zipfile.ZipFile(path) as archive:
            metadata = list(csv.DictReader(io.StringIO(archive.read("manifest.csv").decode())))
        for record in metadata:
            episode = int(record["episode_id"])
            daily_ids.add(episode)
            tasks.append(
                {
                    "path": str(path),
                    "member": f"{episode}.json",
                    "episode_id": episode,
                    "source": source,
                    "date": record["create_time"][:10],
                    "split": partitions.get(episode, "unassigned"),
                }
            )
    if not config.include_public:
        return tasks, daily_ids
    public = orjson.loads((config.public / "manifest.json").read_bytes())
    public_metadata = {e["id"]: e for e in public["episodes"]}
    for replay in public["replays"]:
        episode = replay["episode_id"]
        if episode in daily_ids:
            continue
        record = public_metadata[episode]
        tasks.append(
            {
                "path": replay["path"],
                "episode_id": episode,
                "source": "public_only",
                "date": record["createTime"][:10],
                "agents": record["agents"],
            }
        )
    # Enrich overlapping daily episodes with API identities instead of counting them twice.
    for task in tasks:
        if task["episode_id"] in public_metadata:
            task["agents"] = public_metadata[task["episode_id"]]["agents"]
    return tasks, daily_ids


def _histories(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[Any, list[Any]] = defaultdict(list)
    for row in rows:
        if row["submission_id"]:
            groups[row["submission_id"]].append(row)
    result = []
    for submission, selected in groups.items():
        if len(selected) < 8:
            continue
        same_history: dict[Any, list[Any]] = defaultdict(list)
        for row in selected:
            for turn, early in enumerate(row["early"]):
                same_history[(row["seat"], turn, early["history"])].append((row, early["action"]))
        witnesses = []
        comparable = 0
        for (seat, turn, _), group in same_history.items():
            if len(group) < 2:
                continue
            comparable += 1
            if len({a for _, a in group}) > 1:
                witnesses.append(
                    {
                        "seat": seat,
                        "turn": turn,
                        "n": len(group),
                        "actions": len({a for _, a in group}),
                        "episodes": [r["episode_id"] for r, _ in group],
                    }
                )
        result.append(
            {
                "submission_id": submission,
                "name": selected[0]["name"],
                "n": len(selected),
                "cash_mean": sum(r["cash"] for r in selected) / len(selected),
                "wins": sum(r["result"] > 0 for r in selected),
                "first_action": concentration([r["prefixes"]["full"]["1"] for r in selected]),
                "units24": concentration([r["prefixes"]["units"]["24"] for r in selected]),
                "structure24": concentration([r["prefixes"]["structure"]["24"] for r in selected]),
                "comparable_histories": comparable,
                "divergent_histories": len(witnesses),
                "witnesses": witnesses[:8],
            }
        )
    return {"submissions": sorted(result, key=lambda r: -r["n"])}


def run(config: Analysis) -> None:
    """Extract bounded CPU batches and preserve enough detail for follow-up analysis."""
    tasks, daily_ids = _tasks(config)
    config.output.mkdir(parents=True, exist_ok=True)
    write_json(config.output / "tasks.json", tasks)
    write_json(config.output / "resolved-config.json", config.model_dump(mode="json"))
    rows, rejected = [], []
    extractor = digest(Path(__file__).with_name("extraction.py"))
    pending = tasks
    if config.reuse_daily is not None:
        prior = orjson.loads((config.reuse_daily / "extraction.json").read_bytes())
        cached_path = config.reuse_daily / "trajectories.jsonl"
        if prior["extractor_sha256"] != extractor or prior["trajectories_sha256"] != digest(
            cached_path
        ):
            raise ValueError("cached extraction identity differs")
        cached_tasks = orjson.loads((config.reuse_daily / "tasks.json").read_bytes())
        current = {t["episode_id"]: t for t in tasks}
        for task in cached_tasks:
            expected = current[task["episode_id"]]
            if any(task.get(k) != expected.get(k) for k in ("path", "member", "source", "split")):
                raise ValueError("cached source task differs")
        for line in cached_path.read_bytes().splitlines():
            row = orjson.loads(line)
            agents = current[row["episode_id"]].get("agents", [])
            agent: dict[str, Any] = next(
                (a for a in agents if a.get("index", 0) == row["seat"]), {}
            )
            row.update(submission_id=agent.get("submissionId"), team_id=agent.get("teamId"))
            rows.append(row)
        cached_ids = {r["episode_id"] for r in rows}
        pending = [t for t in tasks if t["episode_id"] not in cached_ids]
    path = config.output / "trajectories.jsonl"
    with path.open("wb") as stream, ProcessPoolExecutor(max_workers=config.workers) as pool:
        for row in rows:
            stream.write(orjson.dumps(row) + b"\n")
        for index, result in enumerate(pool.map(extract, pending, chunksize=2), 1):
            for row in result:
                if "rejected" in row:
                    rejected.append(row)
                else:
                    stream.write(orjson.dumps(row) + b"\n")
                    rows.append(row)
            if index % 100 == 0:
                print(json.dumps({"analyzed": index, "pending": len(pending)}), flush=True)
    write_json(
        config.output / "extraction.json",
        {
            "extractor_sha256": extractor,
            "trajectories_sha256": digest(path),
            "trajectories": len(rows),
        },
    )
    summaries = {}
    for source in ("baseline_daily", "new_daily", "public_only"):
        summaries[source] = summarize([r for r in rows if r["source"] == source])
    summaries["actual_bc_train"] = summarize([r for r in rows if r["split"] == "train"])
    shortfalls = []
    for row in rows:
        for order in row["purchases"]:
            request = order["requested"]
            if (
                request[0] == "BUY_ANIMAL"
                and 0 < request[2] <= 10
                and order["committed"] < request[2]
            ):
                shortfalls.append(
                    {
                        k: row[k]
                        for k in (
                            "episode_id",
                            "seat",
                            "name",
                            "submission_id",
                            "source",
                            "result",
                            "cash",
                        )
                    }
                    | {"order": order}
                )
    write_json(
        config.output / "report.json",
        {
            "schema": "bc-coverage-diagnostics-v1",
            "summaries": summaries,
            "histories": _histories(rows),
            "small_animal_purchase_shortfalls": shortfalls,
            "rejected": rejected,
            "daily_episode_ids": len(daily_ids),
            "trajectory_sha256": digest(path),
            "limitations": [
                "Public sample is selected by team/version/seat; matchmaking is not random.",
                "Action diversity is not evidence of strength, RL, or successful adaptation.",
                "Small purchase shortfalls may be intentional; only first four turns audited.",
                "Identical visible history excludes remainingOverageTime and hidden agent state.",
                "No new BC model was trained by this analysis.",
            ],
        },
    )
    print(json.dumps({"complete": len(rows), "rejected": len(rejected)}), flush=True)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="coverage_analysis")
def main(config: DictConfig) -> None:
    """Resolve the analysis configuration without changing any training run."""
    run(Analysis.model_validate(OmegaConf.to_container(config.analysis, resolve=True)))


if __name__ == "__main__":
    main()
