"""Render frozen temperature results with paired uncertainty and replay evidence."""

import json
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from matplotlib import pyplot as plt
from omegaconf import DictConfig, OmegaConf

from kagg_revue.evaluation.temperature.cli import Comparison


def render(config: Comparison) -> None:
    """Write a shareable figure and a concise report after every declared panel completes."""
    root = config.output_dir
    report = json.loads((root / "report.json").read_text())
    sensitivity = json.loads((root / "sampling-sensitivity.json").read_text())
    duels = json.loads((root / "duels-report.json").read_text())
    replay = json.loads((root / "replay-audit.json").read_text())
    names = list(report["opponents"])
    figure, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    x = np.arange(len(names))
    for offset, mode, color in ((-0.18, "t1", "#3979a8"), (0.18, "t0", "#df8532")):
        values = [report["opponents"][n][mode]["win_rate"] * 100 for n in names]
        bars = axes[0].bar(x + offset, values, width=0.36, label=mode.upper(), color=color)
        axes[0].bar_label(
            bars,
            labels=["100" if v == 100 else f"{v:.1f}" for v in values],
            padding=3,
            fontsize=8,
        )
    axes[0].set(
        xticks=x,
        xticklabels=names,
        ylim=(0, 110),
        ylabel="Win rate (%)",
        title="Win rate against native scripts",
    )
    axes[0].tick_params(axis="x", labelrotation=35)
    axes[0].legend(frameon=False)
    delta = [report["opponents"][n]["t0_minus_t1"] for n in names]
    means = np.array([v["mean_score_change"] * 100 for v in delta])
    intervals = np.array([v["seed_cluster_bootstrap_95_interval"] for v in delta]) * 100
    axes[1].errorbar(
        means,
        x,
        xerr=np.stack((means - intervals[:, 0], intervals[:, 1] - means)),
        fmt="o",
        capsize=4,
        color="#7f4b1f",
    )
    axes[1].axvline(0, color="grey", linewidth=1)
    axes[1].set(
        yticks=x,
        yticklabels=names,
        xlabel="T0 minus T1 score (percentage points)",
        title="Paired change with 95% intervals",
    )
    axes[1].invert_yaxis()
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
    figure.supxlabel(
        "CPU FP32, batch one; native scripts; 32 common seeds and both seats. "
        "Intervals describe this fixed panel only.",
        fontsize=8,
    )
    figure.savefig(root / "temperature-comparison.png", dpi=180)
    figure.savefig(root / "temperature-comparison.pdf")
    plt.close(figure)

    def line(label: str, row: dict[str, Any]) -> str:
        return (
            f"| {label} | {row['t1']['wins']}/{row['t1']['games']} "
            f"({row['t1']['win_rate']:.2%}) | {row['t0']['wins']}/{row['t0']['games']} "
            f"({row['t0']['win_rate']:.2%}) | "
            f"{row['t0_minus_t1']['mean_score_change'] * 100:+.2f} |"
        )

    change = report["t0_minus_t1"]
    low, high = np.asarray(change["seed_cluster_bootstrap_95_interval"]) * 100
    cash = report["cash_t0_minus_t1"]
    duel = duels["t0"]
    first_action = sensitivity["opening_distributions"][0]
    text = [
        "# U2748：T=0 / T=1 本地对照（2026-09-11）",
        "",
        "固定提交 56161366 / 56161402 的 U2748 权重。T=1 直接加载提交包中的 actor.pt；"
        "T=0 使用同一权重逐条件 argmax。CPU FP32、单局推理、719 次状态转移；"
        "复用原生 C++ 脚本对手。没有更改训练、推理部署配置或提交新的包。",
        "",
        "## 640 场脚本面板",
        "",
        "每个温度 320 场：5 个固定脚本 × 32 个共同环境种子 × 双席位。"
        "T=1 每局按提交方式重置为 1210000000 + 席位。两个温度使用完全匹配的"
        "种子、席位和对手；不确定性按环境种子聚类，保留双席位及全部对手。",
        "",
        "| 对手 | T=1 胜场 / 胜率 | T=0 胜场 / 胜率 | T0−T1（百分点） |",
        "|---|---:|---:|---:|",
        *[line(n, report["opponents"][n]) for n in names],
        line("合计", report),
        "",
        f"总体 T0−T1 为 {change['mean_score_change'] * 100:+.2f} 个百分点，"
        f"配对 95% bootstrap 区间 [{low:+.2f}, {high:+.2f}]。"
        f"平均现金 T1={report['t1']['mean_cash']:,.0f}，"
        f"T0={report['t0']['mean_cash']:,.0f}，配对变化 {cash['mean_cash_change']:+,.0f}。",
        "脚本面板接近饱和，且四个脚本参与过训练；这些数字不是 Kaggle 整体胜率。",
        "",
        "![温度对照](temperature-comparison.png)",
        "",
        "## 同权重直接互打",
        "",
        f"使用另行固定的 16 个新环境种子、双席位，共 {duel['games']} 场。"
        f"从 T=0 视角：{duel['wins']} 胜 / {duel['draws']} 平 / {duel['losses']} 负，"
        f"胜率 {duel['win_rate']:.2%}。这是脚本面板接近饱和后补充的探索性验证。",
        "",
        "## 采样种子敏感性",
        "",
        "固定环境种子 1511000000 和 shop_router_0909，使用 16 组新采样种子，"
        "每组覆盖双席位，共 32 场。未从结果中挑选有利的部署种子。",
        f"T=1：{sensitivity['summary']['wins']} 胜 / "
        f"{sensitivity['summary']['draws']} 平 / {sensitivity['summary']['losses']} 负；"
        f"终局现金范围 {sensitivity['cash_min']:,.0f}–{sensitivity['cash_max']:,.0f}，"
        f"标准差 {sensitivity['cash_std']:,.0f}。"
        f"前 72 步动作程序有 {sensitivity['unique_openings']} 个不同哈希。",
        f"固定初始观测、另抽 {first_action['draws']} 个采样种子时，"
        f"{first_action['counts'][0]['count']} 次仍选相同的首回合动作。"
        "因此开局固化也来自策略分布本身的集中，不只是固定种子。"
        "少羊后的第五步，第四个帮手的动作分布变得分散；对照局同一帮手的"
        "128 次采样则全部为领取一只羊。",
        "",
        "固定种子适合调试和配对评估。若部署的目的是真正执行 T=1 混合策略，"
        "每局新建采样种子并在局内连续使用更符合这一目标；本地固定、记录种子以便复现。"
        "固定种子 + 席位使同一观测历史重复相同随机序列，可能反复进入同一不利分支。"
        "不过随机化不能保证改善胜率，也不能自动修复采购预算不足。",
        "",
        "## 两场开局差异",
        "",
        "用户指定的 107807755、107806761 均为第二席对 ymg_aq，前 72 步动作一致。"
        "额外取得的同对手 107810794 与第一场前 145 步一致。对其他对手的对照局，"
        "前四步我方指令一致，第五步开始分叉。",
        "",
        "前两步交易逐项复算与官方回放完全一致。异常局买羊前只有 988，"
        "两只羊需要 1000，因此只成交一只并剩余 488。对照局买到两只并剩余 54。"
        "固定初始状态及我方前两步动作，只换入对照对手的前两步动作，便可复现"
        "买到两只羊的结果。这是资金阈值引起的分叉；T=0 在这些开局观测上的前两步"
        "指令与 T=1 相同，切温度本身不会消除这个触发点。",
        "进一步的局部反事实只删除对手首回合买入/卖出小麦两笔交易，"
        "其余动作全部不变，也恢复为买到两只羊、剩余 54。",
        "",
        "## 验证与边界",
        "",
        "五场回放各取前 96 步，提交 actor 与重建 eager T=1、"
        "T=0 导出与 eager argmax 共 480 组状态检查均一致。"
        "原生批量观测和包内观测扩展另有双席位 192 次逐位比较。",
        "本机无法完整复现线上采样轨迹：各场前 96 步的不一致数为 "
        + ", ".join(f"{r['episode']}: {r['mismatched_turns']}" for r in replay["episodes"])
        + "。"
        "Python 3.12 / Torch 2.12 和 AVX2 重查仍出现同样的早期不一致；"
        "具体差异来源尚未确定。107807755 的 719 步运行日志无 stderr，"
        "首步 12.276 秒、后续最大 0.573 秒。因此上述本地数字不能视为线上逐局复现。",
        "",
        "## 可复现入口与原始结果",
        "",
        "```bash",
        "CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "
        "PYTHONPATH=src .venv/bin/python -m kagg_revue.evaluation.temperature.cli",
        "```",
        "",
        "Hydra 配置：configs/evaluation_temperature.yaml。"
        "附加入口：同包下 replays、sensitivity、duels、reporting 模块。",
        "",
        "- [逐局结果](games.jsonl)与[配对统计](report.json)",
        "- [直接互打](duels-report.json)与[种子敏感性](sampling-sensitivity.json)",
        "- [开局交易复算](opening-settlement.json)与[回放审计](replay-audit.json)",
        "- [原生观测核验](native-feature-qualification.json)与[源码身份](provenance.json)",
        "- 外部回放、元数据、日志及来源清单保存在 data/external/kaggle-submission-56161402/。",
        "",
    ]
    (root / "REPORT.md").write_text("\n".join(text))


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="evaluation_temperature",
)
def main(configuration: DictConfig) -> None:
    """Render already-completed evidence without running additional games."""
    render(
        Comparison.model_validate(OmegaConf.to_container(configuration.comparison, resolve=True))
    )


if __name__ == "__main__":
    main()
