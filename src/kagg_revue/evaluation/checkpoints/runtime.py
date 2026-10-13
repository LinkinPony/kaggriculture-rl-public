"""Reuse bounded inference graphs while replacing only frozen actor parameters."""

import gc
import time
from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import digest
from kagg_revue.evaluation.checkpoints.config import Options, Task
from kagg_revue.evaluation.games import _complete, _summary
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.opponents.batches import create_batch
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.inference import ActorRuntime


def _interface(layout: dict[str, Any]) -> dict[str, Any]:
    """Drop the decoder-only joint switch, which leaves native features unchanged."""
    return {**layout, "network": {**layout["network"], "joint_units": False}}


class Matches:
    """Keep two resident actors, with one graph family alive at a time."""

    def __init__(self, options: Options, manifest: dict[str, Any]) -> None:
        """Authenticate immutable inputs before allocating any CUDA inference buffers."""
        self.options = options
        self.specs = {r["name"]: r for r in manifest["candidates"] + manifest["opponents"]}
        self.payloads: dict[str, dict[str, Any]] = {}
        self.device = torch.device(options.device)
        first = manifest["candidates"][0]["name"]
        payload = self.payload(first)
        self.learner, _ = load_policy(Path(self.specs[first]["path"]), torch.device("cpu"))
        self.opponent, _ = load_policy(Path(self.specs[first]["path"]), torch.device("cpu"))
        for actor in (self.learner, self.opponent):
            actor.to(self.device).eval().requires_grad_(False)
        self.settings = RuntimeSettings.model_validate(payload["settings"]).model_copy(
            update={
                "evaluation_games": options.batch_games,
                "workers": options.workers,
                "precision": options.precision,
                "bf16_reduced_precision_reduction": False,
            }
        )
        if self.settings.ppo.temperature != 1.0:
            raise ValueError("this comparison requires the training T=1 policy")
        self.neural: NeuralMatches | None = None
        self.script: ActorRuntime | None = None
        self.names: tuple[str, str] = (first, first)
        self.temperatures: tuple[float, float] | None = None

    def payload(self, name: str) -> dict[str, Any]:
        """Load only CPU weights, never copying optimizer state onto a training GPU."""
        if name not in self.payloads:
            spec = self.specs[name]
            path = Path(spec["path"])
            if digest(path) != spec["sha256"]:
                raise ValueError(f"frozen checkpoint changed: {name}")
            raw = torch.load(path, map_location="cpu", weights_only=False, mmap=True)
            if any(not bool(torch.isfinite(t).all()) for t in raw["model"].values()):
                raise ValueError(f"nonfinite actor: {name}")
            self.payloads[name] = {k: raw[k] for k in ("model", "layout", "settings", "lineage")}
        return self.payloads[name]

    def close(self) -> None:
        """Release evaluator-owned graph workspaces without touching another process."""
        runtimes = [self.script, self.neural.runtime if self.neural else None]
        for runtime in runtimes:
            if runtime is not None and runtime.capture is not None:
                runtime.capture.close()
        self.neural, self.script = None, None
        del runtimes
        gc.collect()
        torch.cuda.empty_cache()

    def verify_weights(self) -> None:
        """Confirm that evaluation left both resident frozen actors byte-equivalent."""
        for actor, name in zip((self.learner, self.opponent), self.names, strict=True):
            expected = self.payload(name)["model"]
            if any(
                not torch.equal(value.cpu(), expected[key])
                for key, value in actor.state_dict().items()
            ):
                raise RuntimeError("evaluation mutated frozen actor parameters")

    def run(self, task: Task) -> dict[str, Any]:
        """Complete both seats of every seed and retain direct terminal WDL outcomes."""
        started = time.monotonic()
        left = self.payload(task.candidate)
        if left["layout"] != self.payload(self.names[0])["layout"]:
            raise ValueError("candidate geometry changed")
        if task.candidate != self.names[0]:
            self.learner.load_state_dict(left["model"])
        right_name = self.names[1]
        temperatures = (
            float(self.specs[task.candidate].get("temperature", 1.0)),
            float(self.specs[task.opponent].get("temperature", 1.0))
            if task.kind == "neural"
            else 1.0,
        )
        if temperatures != self.temperatures:
            self.close()
            self.temperatures = temperatures
        if task.kind == "neural":
            right = self.payload(task.opponent)
            if _interface(right["layout"]) != _interface(left["layout"]):
                raise ValueError("opponent geometry requires a separately qualified runtime")
            if right["layout"] != self.payload(right_name)["layout"]:
                self.close()
                self.opponent, _ = load_policy(
                    Path(self.specs[task.opponent]["path"]), torch.device("cpu")
                )
                self.opponent.to(self.device).eval().requires_grad_(False)
            elif task.opponent != right_name:
                self.opponent.load_state_dict(right["model"])
            right_name = task.opponent
            if self.neural is None:
                self.close()
                self.neural = NeuralMatches(
                    self.settings,
                    self.learner,
                    self.opponent,
                    sample=True,
                    learner_temperature=temperatures[0],
                    opponent_temperature=temperatures[1],
                )
            torch.manual_seed(task.sampling_seed)
            with torch.inference_mode():
                result = self.neural.run(task.seed)
        else:
            if self.script is None:
                self.close()
                self.script = ActorRuntime(
                    self.learner,
                    self.options.batch_games,
                    sample=temperatures[0] > 0,
                    temperature=temperatures[0] or 1.0,
                    precision=self.options.precision,
                    bf16_reduced_precision_reduction=False,
                )
            jobs = [
                (task.seed + i // 2, i % 2, task.opponent) for i in range(self.options.batch_games)
            ]
            batch = create_batch(self.settings, jobs)
            torch.manual_seed(task.sampling_seed)
            with torch.inference_mode():
                cash, timing = _complete(self.settings, self.script, batch, selfplay=False)
            result = _summary(cash, jobs, timing)
        self.names = task.candidate, right_name
        for row in result["games"]:
            row.update(
                candidate=task.candidate,
                opponent=task.opponent,
                group=task.group,
                phase=task.phase,
                sampling_seed=task.sampling_seed,
                temperature=temperatures[0],
                opponent_temperature=temperatures[1] if task.kind == "neural" else None,
            )
        return {
            "task": task.model_dump(mode="json"),
            "games": result["games"],
            "timing": result["timing"],
            "total_seconds": time.monotonic() - started,
            "cuda_peak_reserved_bytes": torch.cuda.max_memory_reserved(self.device),
            "cuda_reserved_bytes": torch.cuda.memory_reserved(self.device),
        }
