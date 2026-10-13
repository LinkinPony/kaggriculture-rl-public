"""Freeze recent direct games and reconcile strategic gaps by submitted version."""

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.matchups.insights import ITEMS, load_rows, profile
from kagg_revue.evaluation.matchups.study import Study, run


class Options(FrozenSettings):
    """Select every downloaded direct game without filtering by outcome."""

    output: Path
    manifests: tuple[Path, ...]
    submissions: tuple[int, ...]
    workers: int = Field(default=4, ge=1, le=16)


def freeze(options: Options) -> Path:
    """Preserve source snapshots and authenticate the complete downloaded cohort."""
    output = options.output
    (output / "sources").mkdir(parents=True, exist_ok=True)
    tasks: dict[int, dict[str, Any]] = {}
    pending: set[int] = set()
    sources = []
    for source in options.manifests:
        raw = source.read_bytes()
        target = output / "sources" / f"{source.parent.name}.json"
        target.write_bytes(raw)
        manifest = json.loads(raw)
        replays = {row["episode_id"]: row for row in manifest["replays"]}
        sources.append({"path": str(source), "snapshot": str(target), "sha256": digest(target)})
        for episode in manifest["episodes"]:
            if not any(a["submissionId"] in options.submissions for a in episode["agents"]):
                continue
            episode_id = episode["id"]
            if episode_id not in replays:
                pending.add(episode_id)
                continue
            task = {
                **episode,
                **replays[episode_id],
                "recent_game": True,
                "recent_download": True,
            }
            if episode_id in tasks and tasks[episode_id]["sha256"] != task["sha256"]:
                raise ValueError("collectors disagree on replay bytes")
            tasks[episode_id] = task
    target = output / "selection.json"
    write_json(
        target,
        {
            "created_utc": datetime.now(UTC).isoformat(),
            "sources": sources,
            "submissions": options.submissions,
            "pending": sorted(pending - tasks.keys()),
            "tasks": sorted(tasks.values(), key=lambda task: task["episode_id"]),
        },
    )
    return target


def compare(ours: list[dict[str, Any]], peers: dict[tuple[int, int], dict[str, Any]]) -> Any:
    """Use same-game cash identities; retain volume and realized-price components."""
    if not ours:
        return {"games": 0}
    opponents = [peers[row["episode_id"], 1 - row["seat"]] for row in ours]
    own, other = profile(ours), profile(opponents)
    products = {}
    for item in ITEMS:
        volume, price = [], []
        for a, b in zip(ours, opponents, strict=True):
            sa = a["ledger"].get(f"SELL:{item}", {})
            sb = b["ledger"].get(f"SELL:{item}", {})
            qa, qb = sa.get("quantity", 0), sb.get("quantity", 0)
            ra, rb = sa.get("cash", 0), sb.get("cash", 0)
            pa = ra / qa if qa else (rb / qb if qb else 0)
            pb = rb / qb if qb else pa
            volume.append((qa - qb) * (pa + pb) / 2)
            price.append((pa - pb) * (qa + qb) / 2)
        products[item] = {
            "net_cash_gap": own["products"][item]["net_cash"] - other["products"][item]["net_cash"],
            "sales_volume_component": mean(volume),
            "sales_price_component": mean(price),
        }
    cost_saving = sum(other["costs"].values()) - sum(own["costs"].values())
    if (
        abs(sum(p["net_cash_gap"] for p in products.values()) + cost_saving - own["mean_margin"])
        > 1e-6
    ):
        raise ValueError("paired net income fails the terminal cash identity")
    procurement: dict[str, dict[str, list[float]]] = {}
    for start in range(0, 30, 3):
        procurement[str(start)] = {}
        for animal in ("GOOSE", "COW", "SHEEP"):
            procurement[str(start)][animal] = [
                mean(
                    sum(
                        purchase[2]
                        for purchase in row["purchases"]
                        if purchase[1] == f"BUY_ANIMAL:{animal}"
                        and start <= purchase[0] // 24 < start + 3
                    )
                    for row in group
                )
                for group in (ours, opponents)
            ]
    return {
        "ours": own,
        "opponents": other,
        "products": products,
        "cost_saving": cost_saving,
        "procurement_by_three_days": procurement,
        "cash_gap_by_day": [
            mean(
                row["cash_curve"][24 * d] - opp["cash_curve"][24 * d]
                for row, opp in zip(ours, opponents, strict=True)
            )
            for d in range(30)
        ],
        "opponent_versions": dict(Counter(str(row["submission"]) for row in opponents)),
        "episode_ids": [row["episode_id"] for row in ours],
    }


@hydra.main(version_base=None, config_path="../../../../configs", config_name="diagnosis_replays")
def main(config: DictConfig) -> None:
    """Produce a frozen, auditable comparison without modifying training."""
    options = Options.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    selection = options.output / "selection.json"
    if not selection.exists():
        selection = freeze(options)
    run(Study(manifest=selection, output=options.output, workers=options.workers))
    rows = load_rows(options.output)
    peers = {(row["episode_id"], row["seat"]): row for row in rows}
    ours = [row for row in rows if row["submission"] in options.submissions]
    result = {
        "selection_sha256": digest(selection),
        "all": compare(ours, peers),
        "both_three_land": compare(
            [
                row
                for row in ours
                if len(peers[row["episode_id"], 1 - row["seat"]]["board"]["first_land_turn"]) == 3
                and len(row["board"]["first_land_turn"]) == 3
            ],
            peers,
        ),
        "by_submission": {
            str(s): compare([r for r in ours if r["submission"] == s], peers)
            for s in options.submissions
        },
        "by_opponent": {
            name: compare([r for r in ours if r["opponent"] == name], peers)
            for name in sorted({r["opponent"] for r in ours})
        },
    }
    write_json(options.output / "report.json", result)


if __name__ == "__main__":
    main()
