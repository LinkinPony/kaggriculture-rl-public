"""Export standalone checkpoint curves, matchup matrices and a concise study report."""

import json
from pathlib import Path
from typing import Any

import numpy as np


def publish(directory: Path) -> None:
    """Render completed evidence without changing candidate selection or game records."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    report = json.loads((directory / "report.json").read_text())
    manifest, selection = report["manifest"], report["selection"]
    confirmation, robin = report["confirmation"], report["round_robin"]
    updates = {row["name"]: row["update"] for row in manifest["candidates"]}
    names = list(updates)
    figures = directory / "figures"
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": 0.2})
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)
    selected = {row["candidate"]: row for row in selection["results"]}
    for group in manifest["group_weights"]:
        axes[0].plot(
            [updates[name] for name in names],
            [100 * selected[name]["family_scores"][group] for name in names],
            marker=".",
            label=group,
            alpha=0.75,
        )
    axes[0].plot(
        [updates[name] for name in names],
        [100 * selected[name]["composite_score"] for name in names],
        color="black",
        linewidth=2.5,
        marker="o",
        label="Equal-family composite",
    )
    axes[0].set(
        xlabel="PPO update", ylabel="WDL score (%)", title="All retained checkpoints: screening"
    )
    axes[0].legend(fontsize=8)
    rows = list(reversed(confirmation["results"]))
    for i, row in enumerate(rows):
        mean = row["composite_score"] * 100
        interval = np.asarray(row["score_ci95"]) * 100
        axes[1].errorbar(
            mean,
            i,
            xerr=[[mean - interval[0]], [interval[1] - mean]],
            fmt="o",
            color="tab:blue",
            capsize=4,
        )
    axes[1].set_yticks(range(len(rows)), [row["candidate"].upper() for row in rows])
    axes[1].set(
        xlabel="Equal-family WDL score (%)", title="Independent confirmation: 95% seed intervals"
    )
    fig.savefig(figures / "checkpoint-comparison.png", dpi=180)
    fig.savefig(figures / "checkpoint-comparison.svg")
    plt.close(fig)
    matrix = np.full((len(names), len(names)), np.nan)
    for i, left in enumerate(names):
        for j, right in enumerate(names):
            if left != right:
                matrix[i, j] = robin["scores"][left][right]
    fig, axis = plt.subplots(figsize=(11, 10), constrained_layout=True)
    shown = axis.imshow(matrix, vmin=0, vmax=1, cmap="RdYlGn")
    for i in range(len(names)):
        for j in range(len(names)):
            if i != j:
                axis.text(j, i, f"{100 * matrix[i, j]:.0f}", ha="center", va="center", fontsize=7)
    axis.set_xticks(range(len(names)), [name.upper() for name in names], rotation=60)
    axis.set_yticks(range(len(names)), [name.upper() for name in names])
    axis.set(
        title="Candidate round robin: row policy WDL score (%)",
        xlabel="Opponent",
        ylabel="Candidate",
    )
    axis.grid(False)
    fig.colorbar(shown, ax=axis, label="Row candidate score")
    fig.savefig(figures / "round-robin.png", dpi=180)
    fig.savefig(figures / "round-robin.svg")
    plt.close(fig)
    _markdown(directory, report)


def _markdown(directory: Path, report: dict[str, Any]) -> None:
    """Keep the selected metric, uncertainty and frozen-cutoff limitations explicit."""
    confirmation = report["confirmation"]
    rows = confirmation["results"]
    leader = rows[0]
    unresolved = [
        row["candidate"].upper()
        for row in rows[1:]
        if row["leader_difference_simultaneous_ci95"][0] <= 0
    ]
    comparison = (
        f"其余 {len(unresolved)} 个复核候选"
        if len(unresolved) == len(rows) - 1
        else "、".join(unresolved)
    )
    status = (
        f"与{comparison}的差距在同时 95% 区间下尚未分辨。"
        if unresolved
        else "相对其余入围候选的配对差，在同时 95% 区间下均高于 0。"
    )
    games = sum(report[phase]["total_games"] for phase in ("selection", "confirmation")) + sum(
        report[phase]["physical_games"] for phase in ("round_robin", "final_duels")
    )
    actor = next(
        row for row in report["manifest"]["candidates"] if row["name"] == leader["candidate"]
    )
    actor_path = Path(actor["path"]).resolve().relative_to(directory.resolve())
    health_lines = []
    verification = directory / "completion-verification.json"
    if verification.exists():
        training = json.loads(verification.read_text())["training"]
        health_lines = [
            f"训练由冻结时 U{training['frozen_update']} 持续推进到 "
            f"U{training['current_health']['training_update']}，"
            f"最新已保存 U{training['latest_completed_update']}。"
            "训练 PID、运行身份、协议、源码和原生引擎身份均保持一致；"
            f"正式评测期间最低显存余量 {training['minimum_free_mib'] / 1024:.2f} GiB。",
            "[逐批与训练连续性核验](completion-verification.json)。",
            "",
        ]
    lines = [
        "# s99001 保留权重综合胜率比较",
        "",
        f"独立确认面板点估计最高：**{leader['candidate'].upper()}，"
        f"家族等权 WDL 得分 {leader['composite_score']:.2%}**。",
        f"按环境种子聚类的 95% 区间为 [{leader['score_ci95'][0]:.2%}, "
        f"{leader['score_ci95'][1]:.2%}]。{status}",
        "",
        f"正式完成 **{games:,} 场**，技术资格比赛单独保存、不计入排名。",
        "范围固定为 2026-09-28 15:11 UTC 时 U0–U616 的 "
        f"{len(report['manifest']['candidates'])} 个可恢复权重，"
        "包含已提交 U588；不包含之后新训练的权重或已删除的中间检查点。",
        "",
        "指标为四代神经策略家族及原生脚本家族各占 20%；胜 1、平 0.5、负 0，"
        "现金不参与排名。对手为历史可运行策略，不等于当前 Kaggle 私有强手总体胜率。",
        "",
        f"[最高点估计候选的冻结 Actor 权重]({actor_path})；"
        f"原检查点 SHA256：`{actor['checkpoint_sha256']}`。",
        "",
        *health_lines,
        "## 独立确认",
        "",
        "| 权重 | 综合得分 | 95% 种子区间 | 胜 / 平 / 负 | 实际场数 |",
        "| --- | ---: | --- | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['candidate'].upper()} | {row['composite_score']:.2%} | "
            f"{row['score_ci95'][0]:.2%}–{row['score_ci95'][1]:.2%} | "
            f"{row['wins']} / {row['draws']} / {row['losses']} | {row['games']:,} |"
        )
    lines += [
        "",
        "原始场次含较多脚本，因此直接胜场比例与家族等权得分不同。",
        "筛选、确认与最终交手使用互不重叠的种子。两席位和全部对手作为环境种子簇重采样；"
        "不把每场对局视为独立样本。候选差异的同时区间见 report.json。",
        "",
        "## 全部候选筛选",
        "",
        "| 权重 | 综合得分 | s82001 | s91001 | s95001 | s97001 | 原生脚本 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in report["selection"]["results"]:
        scores = " | ".join(
            f"{row['family_scores'][g]:.2%}" for g in report["manifest"]["group_weights"]
        )
        lines.append(f"| {row['candidate'].upper()} | {row['composite_score']:.2%} | {scores} |")
    lines += [
        "",
        f"全候选循环赛第一名：**{report['round_robin']['ranking'][0]['candidate'].upper()}，"
        f"{report['round_robin']['ranking'][0]['score']:.2%}**（每对候选 32 场）。",
        f"最终前四名交手第一名：**{report['final_duels']['ranking'][0]['candidate'].upper()}，"
        f"{report['final_duels']['ranking'][0]['score']:.2%}**（每对候选 256 场）。",
        "不同面板的名次允许不同，主结论以预声明的综合得分为准。",
        "",
        "![筛选曲线与独立确认](figures/checkpoint-comparison.png)",
        "",
        "![候选交手矩阵](figures/round-robin.png)",
        "",
        "[完整报告](report.json)、[预声明协议](protocol.json)、[冻结权重](manifest.json)、"
        "[技术资格](qualification.json)。每阶段 batches/ 保存全部实际对局。",
        "",
    ]
    (directory / "summary.md").write_text("\n".join(lines))
