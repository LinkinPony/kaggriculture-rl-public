"""Seat-balanced pipeline groups with an explicit map back to the original tape."""

from dataclasses import dataclass

from kagg_revue.learning.collection.population import historical_games, script_games
from kagg_revue.learning.settings import RuntimeSettings


@dataclass(frozen=True)
class Partition:
    """Local settings and immutable global physical-game and learner-row indices."""

    settings: RuntimeSettings
    games: tuple[int, ...]
    rows: tuple[int, ...]
    history: int


def counts(selfplay: int, scripts: int, history: int) -> list[tuple[int, int, int]]:
    """Split frozen seat pairs intact and retain every physical game."""
    first = (selfplay // 2, 2 * (scripts // 4), 2 * (history // 4))
    return [first, (selfplay - first[0], scripts - first[1], history - first[2])]


def partition(settings: RuntimeSettings, games: int) -> list[Partition]:
    """Partition a sampled native-script/history mixture without resampling any opponent."""
    scripts, history = script_games(settings, games), historical_games(settings, games)
    selfplay = games - scripts - history
    allocation = settings.ppo.script_allocation
    if scripts and (not allocation or any(count % 2 for _, count in allocation)):
        raise ValueError("pipelining requires an explicit seat-balanced script allocation")
    script_parts: list[list[tuple[str, int]]] = [[], []]
    script_indices: list[list[int]] = [[], []]
    offset = selfplay
    for name, count in allocation:
        first = 2 * (count // 4)
        for slot, (start, size) in enumerate(((0, first), (first, count - first))):
            if size:
                script_parts[slot].append((name, size))
                script_indices[slot].extend(range(offset + start, offset + start + size))
        offset += count
    self_start, history_start = 0, selfplay + scripts
    result = []
    for slot, (own, _, frozen) in enumerate(counts(selfplay, scripts, history)):
        selected = script_indices[slot]
        indices = (
            *range(self_start, self_start + own),
            *selected,
            *range(history_start, history_start + frozen),
        )
        if not indices:
            raise ValueError("pipeline groups must each contain physical games")
        rows = (
            *range(2 * self_start, 2 * (self_start + own)),
            *(selfplay + index for index in selected),
            *range(selfplay + history_start, selfplay + history_start + frozen),
        )
        public = settings.script_population
        if public is not None and selected:
            public = public.model_copy(
                update={
                    "fraction": len(selected) / len(indices),
                    "agents": tuple(name for name, _ in script_parts[slot]),
                }
            )
        old_history = settings.ppo.history
        local = settings.model_copy(
            update={
                "script_population": public,
                "ppo": settings.ppo.model_copy(
                    update={
                        "population": "script_mix" if selected else "self_play",
                        "script_fraction": len(selected) / len(indices),
                        "script_allocation": tuple(script_parts[slot]),
                        "script_opponents": tuple(name for name, _ in script_parts[slot]),
                        "history": old_history.model_copy(
                            update={"fraction": frozen / len(indices)}
                        )
                        if old_history is not None and frozen
                        else None,
                    }
                ),
            }
        )
        if (script_games(local, len(indices)), historical_games(local, len(indices))) != (
            len(selected),
            frozen,
        ):
            raise ValueError("pipeline fractions lost a physical game during integer conversion")
        result.append(Partition(local, indices, rows, frozen))
        self_start += own
        history_start += frozen
    if sorted(index for part in result for index in part.games) != list(range(games)) or (
        sorted(index for part in result for index in part.rows)
        != list(range(2 * selfplay + scripts + history))
    ):
        raise ValueError("pipeline must cover every physical game and learner row exactly once")
    return result
