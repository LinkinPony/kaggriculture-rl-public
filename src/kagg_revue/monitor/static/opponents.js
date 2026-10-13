const version = new URL(import.meta.url).search;
const { renderPlot } = await import(`./plot.js${version}`);
const { PAGE_SIZE, PLOTS, filteredEntries, summaryTable, detailHtml, number } = await import(`./opponent-view.js${version}`);

export function createOpponentExplorer({ fetchJson }) {
  const section = document.getElementById("opponent-history-section");
  const status = section.querySelector(".opponent-history-status");
  const table = section.querySelector(".opponent-history-table");
  const detailPanel = section.querySelector(".opponent-history-detail");
  const pager = section.querySelector(".opponent-summary-pagination");
  const dialog = document.getElementById("opponent-plot-dialog");
  let context = null; let data = null; let run = null; let selected = null;
  let page = 0; let cursors = [null]; let rangeKey = ""; let raw = false;
  let ticket = 0; let pending = ""; let received = ""; let expanded = null;
  let hoverCallbacks = []; let dialogHover = null;
  const filters = { search: "", kind: "all", membership: "all", sort: "last_update", direction: -1 };

  function reset() {
    ticket += 1; pending = ""; received = ""; data = null; selected = null;
    page = 0; cursors = [null]; rangeKey = ""; expanded = null;
    if (dialog.open) dialog.close();
    table.innerHTML = ""; detailPanel.innerHTML = "";
    section.setAttribute("aria-busy", "false");
    document.body.classList.remove("opponent-history-ready");
  }

  function renderTable() {
    if (!data) return;
    const entries = filteredEntries(data.entries, filters);
    page = Math.min(page, Math.max(0, Math.ceil(entries.length / PAGE_SIZE) - 1));
    table.innerHTML = summaryTable(entries.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE), filters, selected, data.saved_update);
    pager.querySelector("span").textContent = `${number(entries.length)} 个对手 · 第 ${page + 1} / ${Math.max(1, Math.ceil(entries.length / PAGE_SIZE))} 页`;
    pager.querySelector("[data-summary-prev]").disabled = page === 0;
    pager.querySelector("[data-summary-next]").disabled = (page + 1) * PAGE_SIZE >= entries.length;
  }

  const hover = (step) => { hoverCallbacks.forEach((callback) => callback(step)); dialogHover?.(step); };
  const plotOptions = (large = false) => ({
    raw, expanded: large, hover, select: () => {},
    zoom: (start, end) => context?.zoom(start, end),
    expand: (config) => { expanded = config; if (!dialog.open) dialog.showModal(); renderDialog(); },
  });
  function renderDialog() {
    if (dialog.open && expanded && data?.selected) dialogHover = renderPlot(dialog.querySelector("article"), expanded, data.selected.curves, plotOptions(true));
  }
  function renderDetail() {
    hoverCallbacks = [];
    detailPanel.hidden = !selected;
    if (!selected) { detailPanel.innerHTML = ""; return; }
    if (!data?.selected || data.selected.key !== selected) {
      detailPanel.textContent = pending ? "正在读取交手明细…" : "该对手暂无可归属的明细";
      return;
    }
    detailPanel.innerHTML = detailHtml(data.selected, data.range);
    detailPanel.querySelector("[data-batches-prev]").disabled = cursors.length === 1;
    const grid = detailPanel.querySelector(".opponent-history-plots");
    for (const config of PLOTS) {
      const card = document.createElement("article"); card.className = "chart-card"; grid.appendChild(card);
      hoverCallbacks.push(renderPlot(card, config, data.selected.curves, plotOptions()));
    }
    renderDialog();
  }

  function showStatus() {
    if (!data) return;
    const warnings = [];
    if (data.unassigned_games) warnings.push(`${number(data.unassigned_games)} 场缺少对手身份，未归入明细`);
    if (data.invalid_panels) warnings.push(`${number(data.invalid_panels)} 个批次结果不完整`);
    if (data.unidentified_pool) warnings.push(`${number(data.unidentified_pool)} 个池成员身份不完整，保留原池表`);
    status.textContent = `战绩已保存至 U${number(data.saved_update)} · 区间 U${data.range.start}–U${data.range.end} · 实时 U${number(data.live_update)} · 当前 PFSP 估计：U${number(data.pfsp_update)} 后${warnings.length ? "。" + warnings.join("；") : ""}`;
    status.dataset.error = "false";
    document.body.classList.toggle("opponent-history-ready", data.entries.length > 0 && !data.unidentified_pool && !data.unassigned_games);
  }

  function render() {
    if (!data) return;
    showStatus(); renderTable(); renderDetail();
  }

  async function load() {
    if (!context || context.settings.view !== "opponents") return;
    const { detail, settings } = context;
    const query = new URLSearchParams({ window: settings.window, smoothing: settings.smoothing });
    for (const field of ["start", "end"]) if (settings[field] != null) query.set(field, settings[field]);
    if (selected) query.set("opponent", selected);
    if (cursors.at(-1) != null) query.set("before", cursors.at(-1));
    const key = JSON.stringify([run, detail.metrics?.last_modified, detail.run.learning?.pfsp?.update, detail.run.learning?.updated_at, query.toString()]);
    if (pending === key) return;
    if (received === key && data) {
      if (pending) { ticket += 1; pending = ""; }
      showStatus(); section.setAttribute("aria-busy", "false");
      return;
    }
    pending = key; const current = ++ticket;
    status.textContent = "正在读取对手战绩…"; section.setAttribute("aria-busy", "true");
    try {
      const encoded = run.split("/").map(encodeURIComponent).join("/");
      const result = await fetchJson(`/api/opponents/${encoded}?${query}`);
      if (current !== ticket) return;
      data = result; received = key; pending = ""; render();
    } catch (error) {
      if (current !== ticket) return;
      pending = ""; status.dataset.error = "true";
      status.textContent = `战绩读取失败：${error.message}。下次刷新重试。`;
    } finally {
      if (current === ticket) section.setAttribute("aria-busy", "false");
    }
  }

  section.addEventListener("input", (event) => {
    const field = event.target.dataset.filter;
    if (!field) return;
    filters[field] = event.target.value; page = 0; renderTable();
  });
  section.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.sort) {
      const field = button.dataset.sort;
      filters.direction = filters.sort === field ? -filters.direction : field === "label" ? 1 : -1;
      filters.sort = field; page = 0; renderTable();
    } else if (button.dataset.opponent || button.hasAttribute("data-close-opponent")) {
      const key = button.dataset.opponent;
      selected = key && key !== selected ? key : null; cursors = [null];
      if (dialog.open) dialog.close();
      load(); renderTable(); renderDetail();
      if (selected) detailPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    } else if (button.hasAttribute("data-summary-prev") || button.hasAttribute("data-summary-next")) {
      page += button.hasAttribute("data-summary-next") ? 1 : -1; renderTable();
    } else if (button.hasAttribute("data-batches-next") && data?.selected?.batches.next_before != null) {
      cursors.push(data.selected.batches.next_before); load();
    } else if (button.hasAttribute("data-batches-prev") && cursors.length > 1) {
      cursors.pop(); load();
    }
  });
  dialog.querySelector("button").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => { expanded = null; dialogHover = null; });
  let resizeTimer;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { if (context?.settings.view === "opponents") renderDetail(); }, 150);
  });

  return {
    update(next) {
      const active = next && next.detail.run.family === "learning" && next.detail.run.kind !== "bc" && !next.detail.run.learning?.league;
      section.classList.toggle("hidden", !active);
      if (!active) { reset(); context = null; run = null; return; }
      const changedRun = run !== next.detail.run.id;
      if (changedRun) reset();
      run = next.detail.run.id; context = next;
      const nextRange = JSON.stringify([next.settings.window, next.settings.start, next.settings.end]);
      if (rangeKey !== nextRange) { cursors = [null]; rangeKey = nextRange; }
      const changedRaw = raw !== next.settings.raw; raw = next.settings.raw;
      if (next.settings.view !== "opponents") {
        ticket += 1; pending = "";
        section.setAttribute("aria-busy", "false");
        if (dialog.open) dialog.close();
        return;
      }
      if (changedRaw) renderDetail();
      load();
    },
  };
}
