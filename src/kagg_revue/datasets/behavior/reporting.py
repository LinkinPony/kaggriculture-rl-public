"""Write portable tables, a searchable HTML report, and a standalone figure."""

import csv
import html
import importlib
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import orjson

from kagg_revue.datasets.behavior.metrics import Hashes

LABELS = {
    "near_fixed_route": "近固定路线",
    "public_route_family": "公开路线族／多路线",
    "stable_backbone": "稳定骨架＋局部分支",
    "fixed_opening_variable_later": "固定开局、后程变化",
    "high_variation_unresolved": "高变化，机制未定",
    "insufficient": "样本不足",
}


def _percent(value: Any) -> str:
    return "—" if value is None else f"{value:.1%}"


def _flat(team: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": team["name"],
        "category": LABELS[team["category"]],
        "trajectories": team["trajectories"],
        "external_games": team["external_games"],
        "win_fraction": team["win_fraction"],
        "cash_median": team["cash_median"],
        "unit_agreement": team["pair_agreement"]["units"],
        "raw_agreement": team["pair_agreement"]["raw"],
        "reference_union_median": team["reference_union_median"],
        "reference_single_median": team["reference_single_median"],
        "opening24_distinct": team["prefix_unit_routes"]["24"]["distinct"],
        "opening24_largest_fraction": team["prefix_unit_routes"]["24"]["largest_fraction"],
        "full_unit_routes": team["prefix_unit_routes"]["719"]["distinct"],
        "same_history_conflicts": team["histories"]["conflicting_history_groups"],
    }


def _table(teams: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| 队伍显示名 | 轨迹 | 单位动作重复率 | 公开路线覆盖 | "
        "24步开局数 | 对外胜率 | 现金中位数 | 行为分组 |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for team in teams:
        name = team["name"].replace("|", "\\|")
        lines.append(
            f"| {name} | {team['trajectories']} | "
            f"{_percent(team['pair_agreement']['units'])} | "
            f"{_percent(team['reference_union_median'])} | "
            f"{team['prefix_unit_routes']['24']['distinct']} | "
            f"{_percent(team['win_fraction'])} | {team['cash_median']:,.0f} | "
            f"{LABELS[team['category']]} |"
        )
    return lines


def _markdown(report: dict[str, Any]) -> str:
    teams = report["teams"]
    lines = [
        "# Kaggriculture 最近三日行为分析",
        "",
        f"日期：{report['dates'][0]['date']} 至 {report['dates'][-1]['date']}（UTC）。"
        f"全量 {report['episodes']:,} 场、{report['trajectories']:,} 条双方轨迹、"
        f"{report['action_turns']:,} 次决策，{len(teams)} 个显示名。",
        "",
        "[重点结论与三类训练数据建议](../../../docs/daily_behavior_20260909.md)。",
        "",
        "官方 daily 按对局平均 rating 选取较高分比赛；这里的覆盖率和胜率只描述下载样本，"
        "不能当成全体参赛者占比或当前排行榜。显示名不是 submission ID。",
        "",
        "## 如何读指标",
        "",
        "- 单位动作重复率：同一显示名、UTC 日期、席位、配置内，两条不同轨迹在相同决策步"
        "给出相同单位指令的概率，再按可比较轨迹对数加权。保留单位次序和数量参数，"
        "只统一缺省动作和尾部 PASS。它不表示在相同状态下的重复率。",
        "- 公开路线覆盖：每一步与本地 5 份公开脚本资产中任一路线的单位动作匹配，"
        "先算每局覆盖率，再取队伍中位数。这个宽松上界允许每步换路线，"
        "不能证明代码来源、完整动作一致或采用了某个具体 router。",
        "- 24 步开局数：不同单位指令前缀数量，合并三个日期与两个席位；"
        "不同版本或席位分支也会增加这个数。",
        "- 对外胜率：排除同显示名互打，以终局现金比较，平局记为非胜；"
        "各队遇到的对手和商店分布并不相同。",
        "",
        "## 全队伍结果",
        "",
        *_table(teams),
        "",
        "## 各日概览",
        "",
        "| 日期 | 对局 | 显示名 | 终局现金中位数 | 对局平均 rating 中位数 | "
        "席位0胜 / 席位1胜 / 平 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for day in report["dates"]:
        lines.append(
            f"| {day['date']} | {day['episodes']} | {day['teams']} | "
            f"{day['cash_median']:,.0f} | {day['match_rating_median']:.1f} | "
            f"{day['seat0_wins']} / {day['seat1_wins']} / {day['ties']} |"
        )
    lines += ["", "## 同可见历史的动作分歧", ""]
    for team in teams:
        conflict = team["histories"]
        if not conflict["conflicting_history_groups"]:
            continue
        lines.append(
            f"- **{team['name']}**：{conflict['replicated_history_groups']} 个重复历史组中，"
            f"{conflict['conflicting_history_groups']} 组完整动作不同，"
            f"{conflict['conflicting_unit_history_groups']} 组单位动作不同。"
        )
        for witness in conflict["witnesses"][:2]:
            lines.append(
                f"  - {witness['date']}、席位 {witness['seat']}、决策步 "
                f"{witness['decision_step']}：episode "
                f"{' / '.join(witness['episode_ids'])}。"
            )
    lines += [
        "",
        "重复历史比较首个游戏日完整可见观测与此前自身动作；保留席位，"
        "仅去除 remainingOverageTime。发现分歧排除了这些可见历史字段的变化作为唯一解释，"
        "但同日更新提交、随机脚本、运行时间或隐藏内部状态仍可解释差异。"
        "确定性的神经网络也可能高度重复；高变化不是 RL 训练的证明。",
        "",
        "## 行为分组阈值",
        "",
        "自动分组按顺序执行：不足 10 条轨迹或不足 5 个可比较对 → 样本不足；"
        "单位动作重复率 ≥97% → 近固定路线；公开路线覆盖中位数 ≥95% → 公开路线族；"
        "单位动作重复率 ≥80% → 稳定骨架；24 步主开局占比 ≥80% → 固定开局；"
        "其余 → 高变化、机制未定。阈值用于筛查，不是经标注校准的分类器。",
        "",
        "## 文件与复现",
        "",
        "- [可搜索交互表格](dashboard.html)",
        "- [机器可读完整结果](report.json)",
        "- [队伍 CSV](teams.csv)、[逐日 CSV](teams-by-date.csv)、[对阵 CSV](matchups.csv)",
        "- [行为图](behavior.png)、[源文件与哈希](sources.json)",
        "- `trajectories.json` 保存逐场摘要；`fingerprints.npz` 保存按步骤对齐的动作哈希。",
        "",
        "```bash",
        ".venv/bin/python -m kagg_revue.datasets.behavior.cli",
        "```",
        "",
        "原始 ZIP 永久保存在 data/external，旧日包按来源清单复用；分析产物在 outputs/analysis。",
    ]
    return "\n".join(lines) + "\n"


def _csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _figure(report: dict[str, Any], output: Path) -> None:
    plt = importlib.import_module("matplotlib.pyplot")
    teams = [team for team in report["teams"] if team["category"] != "insufficient"]
    fig, axes = plt.subplots(1, 2, figsize=(15, max(7, len(teams) * 0.25)), layout="constrained")
    colors = {key: f"C{i}" for i, key in enumerate(LABELS)}
    for index, team in enumerate(teams, start=1):
        x = team["pair_agreement"]["units"] * 100
        y = team["reference_union_median"] * 100
        axes[0].scatter(
            x, y, s=25 + team["trajectories"], alpha=0.6, color=colors[team["category"]]
        )
        axes[0].annotate(str(index), (x, y), fontsize=8)
    axes[0].set(
        xlabel="Within-day, same-seat unit agreement (%)",
        ylabel="Public-route union coverage (%)",
        xlim=(-3, 104),
        ylim=(-3, 104),
    )
    axes[0].grid(alpha=0.2)
    axes[0].set_title("Behavior fingerprints (numbered in dashboard)")
    matrix = np.asarray([team["stage_unit_agreement"] for team in teams])
    plot = axes[1].imshow(matrix, vmin=0, vmax=1, aspect="auto", cmap="viridis")
    axes[1].set_yticks(range(len(teams)), [str(i) for i in range(1, len(teams) + 1)])
    axes[1].set_xticks(
        range(len(report["stages"])), [f"{a}-{b - 1}" for a, b in report["stages"]], rotation=45
    )
    axes[1].set(xlabel="Decision steps", ylabel="Team number", title="Unit agreement by game stage")
    fig.colorbar(plot, ax=axes[1], label="Agreement")
    fig.savefig(output / "behavior.png", dpi=180)
    plt.close(fig)


def _dashboard(report: dict[str, Any], output: Path) -> None:
    rows = []
    numbered = 0
    for team in report["teams"]:
        if team["category"] != "insufficient":
            numbered += 1
        value = _flat(team)
        name = html.escape(value["name"])
        detail = html.escape(
            orjson.dumps(
                {"daily": team["daily"], "references": team["best_references"]},
                option=orjson.OPT_INDENT_2,
            ).decode()
        )
        rows.append(
            f"<tr data-n='{value['trajectories']}'><td>"
            f"{numbered if team['category'] != 'insufficient' else '—'}</td>"
            f"<td><details><summary>{name}</summary><pre>{detail}</pre></details></td>"
            f"<td>{value['category']}</td><td>{value['trajectories']}</td>"
            f"<td>{_percent(value['unit_agreement'])}</td>"
            f"<td>{_percent(value['reference_union_median'])}</td>"
            f"<td>{value['opening24_distinct']}</td>"
            f"<td>{_percent(value['win_fraction'])}</td>"
            f"<td>{value['cash_median']:,.0f}</td></tr>"
        )
    document = Path(__file__).with_name("dashboard.html").read_text()
    replacements = {
        "DATE_RANGE": f"{report['dates'][0]['date']} — {report['dates'][-1]['date']}",
        "EPISODE_COUNT": f"{report['episodes']:,}",
        "MINIMUM_GAMES": str(report["minimum_games"]),
        "TABLE_ROWS": "".join(rows),
    }
    for key, replacement in replacements.items():
        document = document.replace(key, replacement)
    (output / "dashboard.html").write_text(document)


def render(
    report: dict[str, Any], rows: list[dict[str, Any]], hashes: Hashes, output: Path
) -> None:
    """Write human-readable and machine-readable views of the same diagnostics."""
    del hashes
    (output / "report.md").write_text(_markdown(report))
    _csv(output / "teams.csv", [_flat(team) for team in report["teams"]])
    _csv(
        output / "teams-by-date.csv",
        [
            {"date": date, **_flat({**daily, "name": team["name"], "category": team["category"]})}
            for team in report["teams"]
            for date, daily in team["daily"].items()
        ],
    )
    matchups: dict[tuple[str, str], Counter[int]] = {}
    for row in rows:
        if row["complete"] and row["name"] != row["opponent"]:
            key = (row["name"], row["opponent"])
            matchups.setdefault(key, Counter())[row["result"]] += 1
    _csv(
        output / "matchups.csv",
        [
            {
                "name": a,
                "opponent": b,
                "wins": count[1],
                "draws": count[0],
                "losses": count[-1],
                "n": sum(count.values()),
            }
            for (a, b), count in sorted(matchups.items())
        ],
    )
    (output / "route-overlap.json").write_bytes(
        orjson.dumps(
            [
                {
                    "episode_id": row["episode_id"],
                    "seat": row["seat"],
                    "name": row["name"],
                    **row["reference_overlap"],
                }
                for row in rows
            ]
        )
    )
    _figure(report, output)
    _dashboard(report, output)
