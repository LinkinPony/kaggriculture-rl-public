const version = new URL(import.meta.url).search;
const { renderPlot, escapeHtml, formatValue } = await import(`./plot.js${version}`);
const { learningChartConfigurations, opponentLabel } = await import(`./learning.js${version}`);
const { leagueEvaluationSummary, leaguePairs } = await import(`./league.js${version}`);

export function readPreference(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}

export function savePreference(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* Storage can be disabled. */ }
}

const OPPONENT_COLORS = {
  router_95: "#3398c5", farming_v4: "#209f80", kaito_v58: "#9172c5", shop_router_0908: "#c48a24", shop_router_0909: "#bc617d",
  a_vs_bc: "#3398c5", a_vs_spataro: "#209f80", bc_vs_spataro: "#9172c5",
  a_vs_a: "#209f80", bc_vs_bc: "#3398c5", spataro_vs_spataro: "#c48a24",
  "a_vs_bc/right": "#c48a24", "a_vs_spataro/right": "#c16866", "bc_vs_spataro/right": "#2e6475",
};
const FALLBACK_COLORS = ["#209f80", "#3398c5", "#c48a24", "#9172c5", "#c16866"];
function opponentColor(name) {
  return OPPONENT_COLORS[name] || FALLBACK_COLORS[[...name].reduce((sum, char) => sum + char.charCodeAt(0), 0) % FALLBACK_COLORS.length];
}

export function explorerConfigurations(configurations, settings) {
  const selected = configurations.filter((config) => settings.view === "overview"
    ? config.overview || ["脚本对手胜率", "终局现金", "Update 阶段耗时"].includes(config.title)
    : config.group === settings.view);
  return selected.flatMap((config) => {
    if (config.group !== "opponents") return [config];
    const lines = config.lines.filter(([tag]) => settings.opponent === "all" || tag.split("/")[3] === settings.opponent)
      .map(([tag, label]) => [tag, label, opponentColor(tag.split("/")[3] + (tag.endsWith("/mean_cash_right") ? "/right" : ""))]);
    if (!lines.length) return [];
    if (settings.layout === "overlay") return [{ ...config, lines }];
    return lines.map((line) => ({ ...config, title: `${line[1]} · ${config.title.replace("脚本对手", "").replace("对脚本", "")}`, lines: [line] }));
  });
}

export function createExplorer({ fetchJson, onContext = () => {} }) {
  const $ = (id) => document.getElementById(id);
  const toolbar = $("explorer-toolbar"); const grid = $("chart-grid");
  const dialog = $("plot-dialog");
  const preferenceKey = "revue.monitor.explorer.v1";
  const stored = readPreference(preferenceKey, {});
  const settings = { window: 500, smoothing: 32, raw: false, view: "overview", layout: "separate", opponent: "all", ...stored };
  let detail = null; let data = null; let configs = []; let requested = ""; let received = "";
  let requestVersion = 0; let hoverCallbacks = []; let expanded = null;
  let dialogHover = null; let editingRange = false;
  let defaultsLoaded = false;
  const save = () => savePreference(preferenceKey, settings);

  const hover = (step) => { hoverCallbacks.forEach((callback) => callback(step)); dialogHover?.(step); };
  const options = (large = false) => ({
    raw: settings.raw, expanded: large, hover, zoom,
    select: (tag) => {
      if (!["rl/rollout/opponents/", "rl/league/pairs/"].some((prefix) => tag.startsWith(prefix))) return;
      const opponent = tag.split("/")[3];
      settings.opponent = settings.opponent === opponent ? "all" : opponent;
      settings.view = "opponents"; save(); syncControls(); render();
    },
    expand: (config) => { expanded = config; if (!dialog.open) dialog.showModal(); renderDialog(); },
  });

  function renderDialog() {
    if (!dialog.open || !expanded || !data) return;
    const current = configs.find((config) => config.title === expanded.title);
    if (current) expanded = current;
    dialogHover = renderPlot(dialog.querySelector("article"), expanded, data, options(true));
  }

  function syncControls() {
    for (const [id, number] of [["curve-window", settings.window], ["curve-smoothing", settings.smoothing]]) {
      if (![...$(id).options].some((option) => option.value === String(number))) $(id).add(new Option(`${number} 轮`, String(number)));
    }
    $("curve-window").value = settings.start != null || editingRange ? "custom" : String(settings.window);
    $("curve-smoothing").value = String(settings.smoothing);
    $("curve-raw").checked = Boolean(settings.raw);
    $("curve-layout").value = settings.layout;
    $("curve-opponent").value = settings.opponent;
    $("curve-follow").textContent = settings.end == null ? "暂停跟随" : "继续跟随";
    $("curve-follow").setAttribute("aria-pressed", String(settings.end == null));
    toolbar.querySelectorAll("[data-view]").forEach((button) => {
      button.setAttribute("aria-selected", String(button.dataset.view === settings.view));
    });
    $("curve-custom").classList.toggle("hidden", settings.start == null && !editingRange);
    if (settings.start != null && !editingRange) {
      $("curve-start").value = settings.start; $("curve-end").value = settings.end;
    }
  }

  function applyLayout() {
    onContext({ detail, settings: { ...settings }, zoom });
    document.querySelectorAll("[data-views]").forEach((element) => {
      element.classList.toggle("view-hidden", !element.dataset.views.split(" ").includes(settings.view));
    });
    const titles = { overview: "近期训练趋势", opponents: "逐对手趋势", diagnostics: "优化与稳定性", resources: "耗时、吞吐与显存" };
    $("training-charts-section").querySelector("h2").textContent = titles[settings.view];
    $("metric-grid").querySelectorAll(".metric-card").forEach((card) => {
      const label = card.querySelector(".metric-label span")?.textContent;
      card.classList.toggle("view-hidden", ["Actor 学习率", "价值损失", "GPU 内存峰值"].includes(label));
    });
  }

  function evaluationSummary() {
    const panel = $("overview-evaluation");
    const points = detail.evaluation_history?.points || [];
    panel.classList.remove("hidden");
    if (!points.length) {
      panel.innerHTML = "<div><h3>固定评估</h3><p>尚无完整评估记录，训练采样趋势见下方。</p></div>";
      return;
    }
    const point = [...points].sort((a, b) => b.step - a.step || a.mode.localeCompare(b.mode))[0];
    if (point.pairs) {
      panel.innerHTML = leagueEvaluationSummary(point, {
        escapeHtml, integer: (value) => value.toLocaleString("zh-CN"),
        percent: (value) => formatValue(value, { percent: true }),
      });
      return;
    }
    const overall = point.overall;
    const mode = point.mode.startsWith("confirmation") ? "confirmation" : point.mode.startsWith("selection") ? "selection" : point.mode;
    panel.innerHTML = `<div><h3>最近固定评估 · U${point.step.toLocaleString("zh-CN")} · ${escapeHtml(mode)}</h3>
      <p>${overall.games} 场 · ${overall.wins} 胜 / ${overall.ties} 平 / ${overall.losses} 负 · 胜率 ${formatValue(overall.wins / overall.games, { percent: true })}
      · 现金差 ${formatValue(overall.mean_cash_difference)}</p><p>${escapeHtml(point.mode.endsWith("_sampled") ? "自身初始化与随机锚点的固定种子对照" : point.scope || "固定对手完整比赛")}</p></div>
      <button type="button">查看评估明细 →</button>`;
    panel.querySelector("button").addEventListener("click", () => {
      settings.view = "opponents"; save(); syncControls(); render();
      $("evaluation-panel").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  function renderEvents() {
    const events = data.events || [];
    const visible = events.filter((event) => event.step >= data.range.start && event.step <= data.range.end);
    $("curve-events").querySelector("summary").textContent = `配置事件 ${visible.length} / ${events.length} · 点击展开`;
    $("curve-event-list").innerHTML = events.map((event, index) => `<div class="curve-event">
      <button data-event="${index}">U${event.step} · ${escapeHtml(event.title)}</button>
      <p><strong>${escapeHtml(event.before)}</strong><br>→ ${escapeHtml(event.after)}<br>来源：${escapeHtml(event.source)}</p></div>`).join("") || "尚未记录到配置切换。";
    $("curve-event-list").querySelectorAll("[data-event]").forEach((button) => {
      button.addEventListener("click", () => {
        const step = events[Number(button.dataset.event)].step;
        zoom(Math.max(0, step - 100), Math.min(data.extent.end, step + 100));
      });
    });
  }

  function render() {
    if (!detail) return;
    applyLayout(); evaluationSummary();
    if (!data) return;
    if (data.extent.end == null) {
      const pretraining = ["initializing", "demonstrations"].includes(detail.run.learning?.phase);
      grid.innerHTML = `<div class="chart-card"><div class="chart-empty">${pretraining ? "示范预训练进行中；进度与 NLL 见上方。" : "等待首个 PPO 指标提交。"}</div></div>`;
      return;
    }
    configs = explorerConfigurations(learningChartConfigurations(detail.run, detail.metrics), settings);
    grid.innerHTML = ""; hoverCallbacks = [];
    for (const config of configs) {
      const card = document.createElement("article"); card.className = "chart-card";
      grid.appendChild(card); hoverCallbacks.push(renderPlot(card, config, data, options()));
    }
    if (!configs.length) grid.innerHTML = '<div class="chart-card"><div class="chart-empty">当前视图暂无可用曲线</div></div>';
    renderDialog();
  }

  function showStatus() {
    if (!data || !detail || requested) return;
    const live = detail.run.learning?.update ?? data.extent.end;
    $("curve-status").textContent = `U${data.range.start.toLocaleString("zh-CN")}–${data.range.end.toLocaleString("zh-CN")} · ${data.resolution === "full" ? "完整点" : "保留极值的分桶视图"} · 曲线提交 U${data.extent.end ?? "—"} / 实时 U${live ?? "—"}${settings.end != null ? " · 已暂停跟随" : ""}`;
  }

  async function load() {
    if (!detail) return;
    onContext({ detail, settings: { ...settings }, zoom });
    const tags = [...new Set(learningChartConfigurations(detail.run, detail.metrics).flatMap((config) => config.lines.map(([tag]) => tag)))];
    const query = new URLSearchParams({ window: settings.window, smoothing: settings.smoothing, tags: tags.join(",") });
    if (settings.start != null) query.set("start", settings.start);
    if (settings.end != null) query.set("end", settings.end);
    const key = `${detail.run.id}:${detail.metrics.last_modified}:${query}`;
    if (key === requested) return;
    if (key === received && data) {
      if (requested) { requestVersion += 1; requested = ""; render(); }
      return;
    }
    requested = key; const ticket = ++requestVersion;
    $("curve-status").textContent = "正在读取所选区间…";
    $("curve-status").dataset.error = "false";
    grid.setAttribute("aria-busy", "true");
    try {
      const encoded = detail.run.id.split("/").map(encodeURIComponent).join("/");
      const result = await fetchJson(`/api/curves/${encoded}?${query}`);
      if (ticket !== requestVersion) return;
      data = result; received = key; requested = "";
      showStatus();
      renderEvents(); render();
    } catch (error) {
      if (ticket !== requestVersion) return;
      requested = ""; $("curve-status").dataset.error = "true";
      $("curve-status").textContent = `趋势读取失败：${error.message}。下次刷新重试。`;
    } finally {
      if (ticket === requestVersion) grid.setAttribute("aria-busy", "false");
    }
  }

  function zoom(start, end) {
    editingRange = false; settings.start = start; settings.end = end;
    savePreference(`revue.monitor.range:${detail.run.id}`, { start, end });
    syncControls(); load();
  }

  toolbar.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => {
    settings.view = button.dataset.view; save(); syncControls(); render();
  }));
  $("curve-window").addEventListener("change", (event) => {
    const custom = event.target.value === "custom"; editingRange = custom;
    $("curve-custom").classList.toggle("hidden", !custom);
    if (custom) {
      $("curve-start").value = data?.range.start ?? 0; $("curve-end").value = data?.range.end ?? 0;
      $("curve-start").focus(); return;
    }
    settings.window = Number(event.target.value); delete settings.start; delete settings.end;
    savePreference(`revue.monitor.range:${detail.run.id}`, {}); save(); syncControls(); load();
  });
  $("curve-custom").addEventListener("submit", (event) => {
    event.preventDefault();
    const start = Number($("curve-start").value); const end = Number($("curve-end").value);
    $("curve-end").setCustomValidity(start > end ? "结束轮次必须大于或等于起始轮次" : "");
    if (event.target.reportValidity()) zoom(start, end);
  });
  for (const id of ["curve-start", "curve-end"]) $(id).addEventListener("input", () => {
    editingRange = true; $("curve-end").setCustomValidity("");
  });
  $("curve-smoothing").addEventListener("change", (event) => { settings.smoothing = Number(event.target.value); save(); load(); });
  $("curve-raw").addEventListener("change", (event) => { settings.raw = event.target.checked; save(); render(); });
  $("curve-layout").addEventListener("change", (event) => { settings.layout = event.target.value; save(); render(); });
  $("curve-opponent").addEventListener("change", (event) => { settings.opponent = event.target.value; save(); render(); });
  $("curve-follow").addEventListener("click", () => {
    if (settings.end == null) settings.end = data?.range.end ?? detail.run.learning?.update ?? 0;
    else { editingRange = false; delete settings.start; delete settings.end; $("curve-custom").classList.add("hidden"); }
    savePreference(`revue.monitor.range:${detail.run.id}`, { start: settings.start, end: settings.end });
    syncControls(); load();
  });
  $("curve-latest").addEventListener("click", () => {
    editingRange = false; delete settings.start; delete settings.end; settings.window = settings.window || 500;
    savePreference(`revue.monitor.range:${detail.run.id}`, {}); save();
    $("curve-custom").classList.add("hidden"); syncControls(); load();
  });
  $("plot-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => { expanded = null; dialogHover = null; });
  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer); resizeTimer = setTimeout(() => { if (detail) render(); }, 150);
  });

  return {
    update(next, defaults = {}) {
      const active = next.run.family === "learning" && next.run.kind !== "bc";
      toolbar.classList.toggle("hidden", !active); document.body.classList.toggle("explorer-active", active);
      if (!active) {
        onContext(null);
        detail = null; data = null; requested = ""; received = ""; requestVersion += 1;
        if (dialog.open) dialog.close();
        $("overview-evaluation").classList.add("hidden");
        document.querySelectorAll(".view-hidden").forEach((element) => element.classList.remove("view-hidden"));
        $("training-charts-section").querySelector("h2").textContent = "训练走势";
        return;
      }
      if (!defaultsLoaded) {
        for (const key of ["window", "smoothing", "raw"]) if (!(key in stored) && key in defaults) settings[key] = defaults[key];
        defaultsLoaded = true;
      }
      if (detail?.run.id !== next.run.id) {
        data = null; requested = ""; received = ""; requestVersion += 1;
        if (dialog.open) dialog.close();
        editingRange = false; delete settings.start; delete settings.end;
        Object.assign(settings, readPreference(`revue.monitor.range:${next.run.id}`, {}));
        grid.innerHTML = '<div class="chart-card"><div class="chart-empty">读取训练趋势…</div></div>';
      }
      detail = next;
      const league = next.run.learning?.league;
      const names = league ? Object.keys(leaguePairs(next.metrics?.latest, next.run.learning?.members ? Object.keys(next.run.learning.members) : null)) : Object.keys(next.run.learning?.population_games || {}).filter((name) => !["self_play", "historical_self_play"].includes(name));
      if (!names.includes(settings.opponent)) settings.opponent = "all";
      $("curve-opponent").innerHTML = `<option value="all">${league ? "全部模型配对" : "全部当前脚本"}</option>` + names.map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(opponentLabel(name))}</option>`).join("");
      syncControls(); applyLayout(); evaluationSummary(); showStatus(); load();
    },
  };
}
