"""Publish episode- and seat-level counts with explicit land-use definitions."""

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json

KINDS = ("unlocked", "developed", "productive")
DEFINITIONS = {
    "unlocked": "SE occurs in observed unlocked_quadrants at least once.",
    "developed": "An SE tile contains PLANT, COOP, or PASTURE at least once; weeds excluded.",
    "productive": "An SE tile contains a PLANT or a COOP/PASTURE with an animal at least once. "
    "This records productive occupancy, not proof of harvested output or profit.",
    "decision_turns": "Own seat is ACTIVE and has a following replay frame; initial frame "
    "included, terminal frame excluded. Counts are per seat, not per unit.",
    "episodes": "Distinct EpisodeId; an episode qualifies when either seat qualifies.",
    "complete": "Both statuses DONE and frame count equals configured episodeSteps.",
    "scope": "Every saved observation in each available replay, including incomplete episodes. "
    "Complete-only counts are also reported; display names do not identify policy versions.",
}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Deduplicate episodes independently of per-player trajectory counts."""
    result: dict[str, Any] = {
        "episodes": len({row["episode_id"] for row in rows}),
        "trajectories": len(rows),
        "complete_episodes": len({row["episode_id"] for row in rows if row["complete"]}),
        "complete_trajectories": sum(row["complete"] for row in rows),
    }
    for kind in KINDS:
        chosen = [row for row in rows if row[f"se_{kind}"]]
        episodes = len({row["episode_id"] for row in chosen})
        result[kind] = {
            "episodes": episodes,
            "trajectories": len(chosen),
            "episode_percentage": 100 * episodes / result["episodes"] if rows else 0,
            "trajectory_percentage": 100 * len(chosen) / len(rows) if rows else 0,
            "decision_turns": sum(row[f"{kind}_decision_turns"] for row in rows),
            "observation_frames": sum(row[f"{kind}_frames"] for row in rows),
        }
    return result


def grouped(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    """Summarize exact dates, provenance classes, or display names."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row[key]].append(row)
    return [{key: value, **summarize(group)} for value, group in sorted(groups.items())]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write a directly filterable, UTF-8 table with deterministic columns."""
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def render(output: Path, manifest: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    """Save statistics and filtered catalogs suitable for later replay selection."""
    failures = [item for item in results if "error" in item]
    rows = sorted(
        [row for item in results for row in item.get("rows", [])],
        key=lambda row: (int(row["episode_id"]), row["seat"]),
    )
    latest_date = manifest["daily_dates"][-1]
    latest = [row for row in rows if row["date"] == latest_date]
    daily = [row for row in rows if row["source"] == "daily"]
    report = {
        "schema": "fourth-quadrant-survey-v1",
        "definitions": DEFINITIONS,
        "source_catalog": manifest["catalog"],
        "source_frozen_at_utc": manifest["frozen_at_utc"],
        "latest_date": latest_date,
        "expected_episodes": manifest["unique_episodes"],
        "all": summarize(rows),
        "daily": summarize(daily),
        "latest_daily": summarize(latest),
        "complete_only": summarize([row for row in rows if row["complete"]]),
        "by_source": grouped(rows, "source"),
        "by_date": grouped(daily, "date"),
        "by_team": grouped(rows, "name"),
        "daily_by_team": grouped(daily, "name"),
        "latest_by_team": grouped(latest, "name"),
        "failures": failures,
    }
    write_csv(output / "trajectories.csv", rows)
    write_csv(output / "se-productive-trajectories.csv", [r for r in rows if r["se_productive"]])
    write_csv(output / "se-unlocked-trajectories.csv", [r for r in rows if r["se_unlocked"]])
    tasks = json.loads(Path(manifest["catalog"]["path"]).read_text())
    by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_id[row["episode_id"]].append(row)
    for kind in KINDS:
        filtered = [
            {**task, "seats": [r["seat"] for r in by_id[task["episode_id"]] if r[f"se_{kind}"]]}
            for task in tasks
            if any(r[f"se_{kind}"] for r in by_id[task["episode_id"]])
        ]
        write_json(output / f"se-{kind}-catalog.json", filtered)
    lines = [
        "# Daily episode 合并与第四块地统计",
        "",
        f"最新官方 daily：**{latest_date}**；本地 daily 覆盖 "
        f"{manifest['daily_dates'][0]} 至 {latest_date}。",
        "",
        "按 episode ID 去重，两个玩家分别计算轨迹；只要一方符合，对局计数加一。",
        "检查整局所有观测，SE 为棋盘右下象限。作物或动物占用不等同于已有收获或利润。",
        "",
        "| 范围 | 对局 | 轨迹 | 解锁 SE 对局 / 轨迹 | 建设 SE 对局 / 轨迹 | "
        "作物或动物占用 SE 对局 / 轨迹 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, key in (
        ("最新 daily", "latest_daily"),
        ("合并 daily", "daily"),
        ("全部合并", "all"),
        ("全部合并中的完整对局", "complete_only"),
    ):
        value = report[key]
        cells = " | ".join(
            f"{value[k]['episodes']:,} / {value[k]['trajectories']:,}" for k in KINDS
        )
        lines.append(f"| {label} | {value['episodes']:,} | {value['trajectories']:,} | {cells} |")
    lines.extend(
        [
            "",
            f"分析失败：{len(failures)} 场。非完整对局："
            f"{report['all']['episodes'] - report['all']['complete_episodes']} 场。",
            "",
            "解锁：观测中 SE 已解锁。建设：SE 曾有作物、鸡舍或牧场，排除杂草。",
            "生产占用：SE 曾有作物或已经放入动物的鸡舍/牧场。空设施仅计入建设。",
            "",
            "## 来源与逐场明细",
            "",
            f"- 原始整合清单：`{manifest['catalog']['path']}`。原包保留原位置，索引引用复用。",
            f"- {manifest['duplicate_daily_archives']} 份重复日包已核验哈希一致；"
            f"{manifest['duplicate_local_replays']} 份单独回放按 ID 去重。",
            "- `report.json`：总计、逐日、队伍和来源分组。",
            "- `trajectories.csv`：全部轨迹及首次解锁/建设/生产占用帧。",
            "- `se-productive-trajectories.csv`：第四块地生产占用轨迹。",
            "- `se-productive-catalog.json`：对应去重对局、席位及原始文件定位。",
            "",
            "## daily 逐日",
            "",
            "| 日期 | 对局 | 解锁 SE 对局 / 轨迹 | 生产占用 SE 对局 / 轨迹 |",
            "|---|---:|---:|---:|",
        ]
    )
    for day in report["by_date"]:
        lines.append(
            f"| {day['date']} | {day['episodes']} | "
            f"{day['unlocked']['episodes']} / {day['unlocked']['trajectories']} | "
            f"{day['productive']['episodes']} / {day['productive']['trajectories']} |"
        )
    lines.extend(
        [
            "",
            "## daily 中第四块地生产占用最多的显示名",
            "",
            "| 显示名 | 总轨迹 | SE 生产占用轨迹 | 比例 |",
            "|---|---:|---:|---:|",
        ]
    )
    teams = sorted(
        report["daily_by_team"], key=lambda r: r["productive"]["trajectories"], reverse=True
    )
    for team in teams[:15]:
        value = team["productive"]
        lines.append(
            f"| {team['name'].replace('|', '/')} | {team['trajectories']} | "
            f"{value['trajectories']} | {value['trajectory_percentage']:.2f}% |"
        )
    (output / "report.md").write_text("\n".join(lines) + "\n")
    report["artifacts"] = {
        p.name: digest(p)
        for p in sorted(output.iterdir())
        if p.suffix == ".csv" or p.name.endswith("-catalog.json")
    }
    write_json(output / "report.json", report)
    return report
