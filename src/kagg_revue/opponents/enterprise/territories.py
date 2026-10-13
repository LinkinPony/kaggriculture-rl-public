"""Recompute compact, balanced service areas from the currently owned farm."""

from typing import Any

from kagg_revue.opponents.enterprise.tasks import distance


def partition(tiles: list[tuple[int, int, Any]], count: int) -> list[tuple[int, int]]:
    """Cluster crop work spatially, keeping daily walking local without route tapes."""
    points = [(x, y) for x, y, tile in tiles if not (isinstance(tile, dict) and tile.get("animal"))]
    if count <= 0 or not points:
        return []
    centers = [min(points, key=lambda point: distance(point, (4, 4)))]
    for _ in range(count - 1):
        centers.append(max(points, key=lambda point: min(distance(point, c) for c in centers)))
    capacity = (len(points) + count - 1) // count
    for _ in range(4):
        groups: list[list[tuple[int, int]]] = [[] for _ in centers]
        for point in sorted(
            points, key=lambda point: min(distance(point, c) for c in centers), reverse=True
        ):
            index = min(
                (i for i in range(count) if len(groups[i]) < capacity),
                key=lambda i: distance(point, centers[i]),
            )
            groups[index].append(point)
        centers = [
            (
                round(sum(p[0] for p in group) / len(group)),
                round(sum(p[1] for p in group) / len(group)),
            )
            if group
            else center
            for group, center in zip(groups, centers, strict=True)
        ]
    return sorted(centers)
