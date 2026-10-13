"""Complete-match falsification of the proposed BC action language."""

import json
import time
from typing import Any

import numpy as np

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.opponents.batches import create_batch
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import Settings
from kagg_revue.production.contracts import propose_contracts


def _outcomes(rows: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    cash = np.array([[row[prefix + "cash"], row[prefix + "opponent_cash"]] for row in rows])
    margin = cash[:, 0] - cash[:, 1]
    return {
        "wins": int((margin > 0).sum()),
        "ties": int((margin == 0).sum()),
        "losses": int((margin < 0).sum()),
        "mean_cash": float(cash[:, 0].mean()),
        "mean_cash_difference": float(margin.mean()),
    }


def audit(settings: Settings) -> None:
    """Run extracted plans against identical opponents, seeds and seats."""
    source = json.loads((settings.bc.source / "manifest.json").read_text())
    layout = ContractLayout.resolve(settings)
    offset = 0
    outcomes = []
    shards = []
    identity = provenance(settings)
    write_json(settings.output_dir / "resolved-config.json", settings.model_dump(mode="json"))
    write_json(settings.output_dir / "source.json", identity)
    started = time.perf_counter()
    for shard in source["shards"]:
        observations = np.load(settings.bc.source / shard["observations"], mmap_mode="r")
        raw = np.load(settings.bc.source / shard["actions"], mmap_mode="r")
        contracts = propose_contracts(observations, raw, layout)
        rows = source["games"][offset : offset + shard["games"]]
        jobs = [(row["seed"], row["seat"], row["opponent"]) for row in rows]
        batch = create_batch(settings, jobs)
        for decision, plan in enumerate(contracts):
            if layout.work:
                batch.advance_programs(
                    np.ascontiguousarray(plan), layout.spans[decision], layout.capacity
                )
            else:
                batch.advance(np.ascontiguousarray(plan), layout.spans[decision])
        cash = batch.cash()
        for index, row in enumerate(rows):
            outcomes.append(
                {
                    **row,
                    "contract_cash": float(cash[index, 0]),
                    "contract_opponent_cash": float(cash[index, 1]),
                }
            )
        shards.append(
            {
                "offset": offset,
                "games": len(rows),
                "teacher": _outcomes(outcomes[-len(rows) :], ""),
                "compiled": _outcomes(outcomes[-len(rows) :], "contract_"),
            }
        )
        print(
            json.dumps(
                {
                    "games": len(outcomes),
                    "cash": cash[:, 0].mean(),
                    "teacher_cash": np.mean([row["cash"] for row in rows]),
                    "seconds": time.perf_counter() - started,
                }
            ),
            flush=True,
        )
        offset += shard["games"]
    write_json(
        settings.output_dir / "contract-oracle.json",
        {
            "noncausal_language_audit": True,
            "source_manifest_sha256": digest(settings.bc.source / "manifest.json"),
            "provenance": identity,
            "shards": shards,
            "teacher": _outcomes(outcomes, ""),
            "compiled": _outcomes(outcomes, "contract_"),
            "games": outcomes,
            "elapsed_seconds": time.perf_counter() - started,
            "mean_cash": np.mean([row["contract_cash"] for row in outcomes]),
            "teacher_mean_cash": np.mean([row["cash"] for row in outcomes]),
        },
    )
