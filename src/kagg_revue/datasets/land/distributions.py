"""Summarize UTC episode dates and observed historical match-rating distributions."""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.land.cli import Survey
from kagg_revue.datasets.land.metadata import enrich
from kagg_revue.datasets.land.reporting import write_csv

EDGES = (-float("inf"), 2000, 2250, 2500, 2750, 3000, 3250, float("inf"))
LABELS = ("<2000", "2000–<2250", "2250–<2500", "2500–<2750", "2750–<3000", "3000–<3250", "≥3250")


def statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Report missingness separately from quantiles over observed episode ratings."""
    values = [row["average_rating"] for row in rows if row["average_rating"] is not None]
    result: dict[str, Any] = {
        "episodes": len(rows),
        "known_dates": sum(r["date"] != "unknown" for r in rows),
        "known_ratings": len(values),
        "missing_ratings": len(rows) - len(values),
        "rating_coverage_percent": 100 * len(values) / len(rows) if rows else 0,
        "rating_sources": dict(Counter(r["rating_kind"] for r in rows)),
    }
    if values:
        result["rating"] = {
            **dict(
                zip(
                    ("min", "p5", "p10", "p25", "median", "p75", "p90", "p95", "max"),
                    map(float, np.percentile(values, [0, 5, 10, 25, 50, 75, 90, 95, 100])),
                    strict=True,
                )
            ),
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
        }
    else:
        result["rating"] = None
    result["histogram"] = [
        {"range": label, "episodes": sum(lo <= v < hi for v in values)}
        for label, lo, hi in zip(LABELS, EDGES[:-1], EDGES[1:], strict=True)
    ]
    return result


def summarize(rows: list[dict[str, Any]], provenance: dict[str, Any]) -> dict[str, Any]:
    """Compare the whole corpus, official daily subset, and fourth-land users."""
    selected = [r for r in rows if r["se_productive"]]
    daily = [r for r in rows if r["source"] == "daily"]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["date"]].append(row)
    by_date = []
    for day, group in sorted(groups.items()):
        se = [r for r in group if r["se_productive"]]
        overall, used = statistics(group), statistics(se)
        by_date.append(
            {
                "date": day,
                "episodes": len(group),
                "daily_episodes": sum(r["source"] == "daily" for r in group),
                "local_supplement_episodes": sum(r["source"] != "daily" for r in group),
                "se_episodes": len(se),
                "se_daily_episodes": sum(r["source"] == "daily" for r in se),
                "se_trajectories": sum(r["se_productive_trajectories"] for r in se),
                "known_ratings": overall["known_ratings"],
                "se_known_ratings": used["known_ratings"],
                "rating_median": overall["rating"]["median"] if overall["rating"] else None,
                "se_rating_median": used["rating"]["median"] if used["rating"] else None,
            }
        )
    return {
        "schema": "episode-date-rating-distributions-v1",
        "provenance": provenance,
        "definition": "Date is episode createTime in UTC, never a download/file date. "
        "Rating is the two-player match average: official daily avg_score, otherwise "
        "mean of both agents' recorded updatedScore. No current leaderboard ratings, "
        "terminal cash or missing-value imputation. SE means an observed crop or "
        "stocked animal in the SE quadrant. Match ratings are not the SE user's "
        "individual rating. Quantiles and histogram exclude missing ratings.",
        "all": statistics(rows),
        "se": statistics(selected),
        "daily": statistics(daily),
        "se_daily": statistics([r for r in daily if r["se_productive"]]),
        "local_supplement": statistics([r for r in rows if r["source"] != "daily"]),
        "se_local_supplement": statistics([r for r in selected if r["source"] != "daily"]),
        "by_date": by_date,
        "unknown_date_ids": [r["episode_id"] for r in rows if r["date"] == "unknown"],
    }


def markdown(report: dict[str, Any], output: Path) -> None:
    """Write the complete date table and comparable observed-rating summaries."""
    lines = [
        "# 回放日期与 rating 分布",
        "",
        "日期使用对局创建时间（UTC）。SE 子集指整局中曾在 SE 出现作物或动物的对局。",
        "",
        "Rating 为双方平均评分：daily 使用官方 `avg_score`，其余使用已有元数据中双方 "
        "`updatedScore` 的均值；不是现金，也不是 SE 使用者个人评分。缺失不填充。",
        "",
        "| 范围 | 对局 | 日期可用 | rating 可用 | 均值 | P25 | 中位数 | P75 | 最小–最大 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label, key in (
        ("全部合并", "all"),
        ("SE 子集", "se"),
        ("全部 daily", "daily"),
        ("SE daily", "se_daily"),
        ("本地独立补充", "local_supplement"),
        ("SE 本地补充", "se_local_supplement"),
    ):
        r = report[key]
        v = r["rating"]
        cells = (
            " | ".join(f"{v[k]:.1f}" for k in ("mean", "p25", "median", "p75"))
            if v
            else "— | — | — | —"
        )
        bounds = f"{v['min']:.1f}–{v['max']:.1f}" if v else "—"
        lines.append(
            f"| {label} | {r['episodes']:,} | {r['known_dates']:,} | "
            f"{r['known_ratings']:,} ({r['rating_coverage_percent']:.2f}%) | {cells} | {bounds} |"
        )
    lines.extend(
        [
            "",
            "## Rating 分箱（仅有评分者）",
            "",
            "| 双方平均 rating | 全部对局 | SE 对局 |",
            "|---|---:|---:|",
        ]
    )
    for a, b in zip(report["all"]["histogram"], report["se"]["histogram"], strict=True):
        lines.append(f"| {a['range']} | {a['episodes']:,} | {b['episodes']:,} |")
    lines.extend(
        [
            "",
            "## 日期分布",
            "",
            "| 日期 UTC | 全部对局 | daily | 独立补充 | SE 对局 | SE 轨迹 | "
            "有 rating 对局 | SE 有 rating 对局 | SE rating 中位数 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for r in report["by_date"]:
        median = f"{r['se_rating_median']:.1f}" if r["se_rating_median"] is not None else "—"
        lines.append(
            f"| {r['date']} | {r['episodes']} | {r['daily_episodes']} | "
            f"{r['local_supplement_episodes']} | {r['se_episodes']} | {r['se_trajectories']} | "
            f"{r['known_ratings']} | {r['se_known_ratings']} | {median} |"
        )
    comparisons = report["provenance"]["daily_api_rating_comparisons"]
    delta = max((abs(c["delta"]) for c in comparisons), default=0)
    lines.extend(
        [
            "",
            f"{len(comparisons)} 场同时有 daily 和 API 评分证据，平均分最大差异 "
            f"{delta:.3g}，与 daily 保留 6 位小数一致。",
            "",
            "缺失日期的 episode ID：" + ", ".join(report["unknown_date_ids"]) + "。",
            "",
            "SE 样本的缺评分比例较高，现有评分分布不能直接代表全部 SE 回放。"
            "daily 本身偏向高评分对局；不同日期、来源和对手构成也不同。",
            "",
            "逐场数据见 `episodes.csv`，逐日数据见 `dates.csv`，完整统计见 `report.json`。",
            "![日期和评分分布](distributions.png)",
        ]
    )
    (output / "report.md").write_text("\n".join(lines) + "\n")


def run(config: Survey) -> None:
    """Enrich the existing frozen collection without changing its episode membership."""
    rows, provenance = enrich(config.root, config.raw, config.output)
    report = summarize(rows, provenance)
    output = config.output / "date-rating"
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "episodes.csv", rows)
    write_csv(output / "dates.csv", report["by_date"])
    write_json(output / "report.json", report)
    from kagg_revue.datasets.land.figures import plot

    plot(report, output)
    markdown(report, output)
    write_json(
        output / "verification.json",
        {
            "unique_episodes": len({r["episode_id"] for r in rows}),
            "episode_count": len(rows),
            "daily_date_total": sum(r["daily_episodes"] for r in report["by_date"]),
            "date_total": sum(r["episodes"] for r in report["by_date"]),
            "se_date_total": sum(r["se_episodes"] for r in report["by_date"]),
            "rating_histogram_total": sum(r["episodes"] for r in report["all"]["histogram"]),
            "se_rating_histogram_total": sum(r["episodes"] for r in report["se"]["histogram"]),
            "artifacts": {
                p.name: digest(p) for p in sorted(output.iterdir()) if p.name != "verification.json"
            },
            "code": {str(p): digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        },
    )
    print(json.dumps({k: report[k] for k in ("all", "se", "daily", "se_daily")}), flush=True)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="daily_land")
def main(configuration: DictConfig) -> None:
    """Resolve the existing collection and report paths using Hydra."""
    run(Survey.model_validate(OmegaConf.to_container(configuration.survey, resolve=True)))


if __name__ == "__main__":
    main()
