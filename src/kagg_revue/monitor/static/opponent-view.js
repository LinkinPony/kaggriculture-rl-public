const version = new URL(import.meta.url).search;
const { escapeHtml, formatValue } = await import(`./plot.js${version}`);
const { opponentLabel } = await import(`./learning.js${version}`);

export const PAGE_SIZE = 50;
export const number = (value) => formatValue(value);
export const percent = (value) => formatValue(value, { percent: true });
const probability = (value) => Number.isFinite(value) ? `${(value * 100).toFixed(3)}%` : "—";
export const wdl = (stats) => `${number(stats.wins)} · ${number(stats.ties)} · ${number(stats.losses)}`;

export function label(entry) {
  if (entry.kind === "script") return opponentLabel(entry.name || entry.key);
  const source = entry.source_run?.split("/").pop() || entry.path?.match(/^historical\/([^/]+)\//)?.[1] || "本次运行";
  const step = entry.update ?? Number(entry.path?.match(/update-(\d+)/)?.[1]);
  const checkpoint = Number.isFinite(step) ? step === 0 ? "初始策略" : `U${step}` : entry.path?.split("/").pop() || "冻结模型";
  return `${source} · ${checkpoint}`;
}

const sortValue = (entry, key) => key === "label" ? label(entry) : key.split(".").reduce((value, part) => value?.[part], entry);

export function filteredEntries(entries, filters) {
  const search = filters.search.trim().toLowerCase();
  return entries.filter((entry) => (filters.kind === "all" || entry.kind === filters.kind)
    && (filters.membership === "all" || entry.in_pool === (filters.membership === "active"))
    && (!search || [label(entry), entry.name, entry.path, entry.key].join(" ").toLowerCase().includes(search)))
    .sort((a, b) => {
      const left = sortValue(a, filters.sort); const right = sortValue(b, filters.sort);
      if (left == null || right == null) return left == null && right == null ? a.key.localeCompare(b.key) : left == null ? 1 : -1;
      const difference = typeof left === "string" ? left.localeCompare(right, "zh-CN") : left - right;
      return difference * filters.direction || a.key.localeCompare(b.key);
    });
}

const COLUMNS = [
  ["label", "对手 / 来源"], ["lifetime.games", "累计场数"], ["lifetime.wins", "累计胜 · 平 · 负"],
  ["lifetime.win_rate", "累计胜率"], ["interval.games", "区间场数"], ["interval.win_rate", "区间胜率"],
  ["score", "当前预估比分"], ["probability", "抽样概率"], ["last_update", "最后交手"],
];

export function summaryTable(entries, filters, selected, savedUpdate) {
  const headers = COLUMNS.map(([key, name]) => `<th aria-sort="${filters.sort === key ? filters.direction === 1 ? "ascending" : "descending" : "none"}"><button data-sort="${key}">${name}${filters.sort === key ? filters.direction === 1 ? " ↑" : " ↓" : ""}</button></th>`).join("");
  const rows = entries.map((entry) => `<tr class="${entry.key === selected ? "opponent-selected" : ""}">
    <td><button class="opponent-open" data-opponent="${escapeHtml(entry.key)}" aria-expanded="${entry.key === selected}">${escapeHtml(label(entry))}</button>
      <small>${entry.kind === "script" ? "脚本" : "历史模型"} · ${entry.in_pool == null ? "池状态未知" : entry.in_pool ? "当前在池" : "已退出池"}</small></td>
    <td>${number(entry.lifetime.games)}</td><td class="opponent-wdl">${wdl(entry.lifetime)}</td><td>${percent(entry.lifetime.win_rate)}</td>
    <td>${entry.interval.games ? number(entry.interval.games) : "无交手"}</td><td>${percent(entry.interval.win_rate)}</td>
    <td>${percent(entry.score)}</td><td>${probability(entry.probability)}</td>
    <td>${entry.last_update == null ? "尚未交手" : `U${number(entry.last_update)}<small>距保存点 ${number(savedUpdate - entry.last_update)} 轮</small>`}</td></tr>`).join("");
  return `<table class="opponent-table"><thead><tr>${headers}</tr></thead><tbody>${rows || '<tr><td colspan="9">没有匹配的对手</td></tr>'}</tbody></table>`;
}

export function detailHtml(entry, range) {
  const stats = [["全程累计", entry.lifetime], [`区间 U${range.start}–U${range.end}`, entry.interval]];
  const rows = stats.map(([title, value]) => `<tr><td>${title}</td><td>${number(value.games)}</td><td>${wdl(value)}</td><td>${percent(value.win_rate)}</td><td>${percent(value.observed_score)}</td><td>${number(value.mean_terminal_cash)}</td><td>${number(value.mean_cash_difference)}</td></tr>`).join("");
  const batches = entry.batches.rows.map((row) => `<tr><td>U${number(row.update)}</td><td>${number(row.games)}</td><td>${wdl(row)}</td><td>${percent(row.win_rate)}</td><td>${number(row.mean_terminal_cash)}</td><td>${number(row.mean_cash_difference)}</td><td>${percent(row.sampling_score)}</td><td>${probability(row.sampling_probability)}</td></tr>`).join("");
  return `<div class="section-heading"><h3>${escapeHtml(label(entry))}</h3><button data-close-opponent>收起明细</button></div>
    <p class="opponent-identity">来源：${escapeHtml(entry.source_run || (entry.kind === "script" ? "冻结脚本池" : "本次运行"))}<br>
      ${entry.path ? `Checkpoint：${escapeHtml(entry.path)}<br>` : ""}身份：${escapeHtml(entry.key)}</p>
    <div class="opponent-table-wrap"><table class="opponent-table"><thead><tr><th>范围</th><th>场数</th><th>胜 · 平 · 负</th><th>实际胜率</th><th>实测比分</th><th>平均终局现金</th><th>平均现金差</th></tr></thead><tbody>${rows}</tbody></table></div>
    <p class="opponent-footnote">学习方视角；胜率 = 胜 / 场数，实测比分 = (胜 + 0.5 × 平) / 场数，现金按场数加权。</p>
    <div class="opponent-history-plots"></div>
    <h4>逐轮交手记录 · 所选区间 ${number(entry.batches.total)} 个批次</h4>
    <p class="opponent-footnote">每行是一个训练轮次的完整比赛汇总。抽样前预估比分与概率取自当轮记录。</p>
    <div class="opponent-table-wrap"><table class="opponent-table"><thead><tr><th>学习方轮次</th><th>场数</th><th>胜 · 平 · 负</th><th>实际胜率</th><th>终局现金</th><th>现金差</th><th>抽样前预估比分</th><th>抽样概率</th></tr></thead><tbody>${batches || '<tr><td colspan="8">所选区间没有交手记录</td></tr>'}</tbody></table></div>
    <div class="opponent-pagination"><button data-batches-prev>较新一页</button><button data-batches-next ${entry.batches.next_before == null ? "disabled" : ""}>较早一页</button></div>`;
}

export const PLOTS = [
  { title: "实际胜率与实测比分", percent: true, note: "仅统计与此对手真实发生的对局；趋势按场数加权", lines: [["win_rate", "实际胜率", "#3398c5"], ["observed_score", "实测比分", "#209f80"]] },
  { title: "对该对手的现金差", zero: true, note: "学习方终局现金减对手终局现金；趋势按场数加权", lines: [["mean_cash_difference", "平均现金差", "#9172c5"]] },
];
