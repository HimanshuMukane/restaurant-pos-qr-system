const Layout = (() => {
  "use strict";

  let editing = false;
  let selected = null;
  let startMouse = null;
  let startBox = null;
  let layoutSnapshot = null;

  function visibleFloorContainer() {
    const list = document.querySelectorAll(".floor-container");
    for (const ctn of list) {
      const style = getComputedStyle(ctn);
      if (style.display !== "none" && style.visibility !== "hidden") return ctn;
    }
    return null;
  }

  function visibleGrid() {
    const ctn = visibleFloorContainer();
    return ctn?.querySelector(".grid") || null;
  }

  function setDefaultGap(px = 6) {
    document.querySelectorAll(".grid").forEach((g) => {
      const cur = getComputedStyle(g).getPropertyValue("--gap").trim();
      if (!cur) g.style.setProperty("--gap", `${px}px`);
    });
  }
  setDefaultGap(6);

  function setCoordText(txt) {
    document
      .querySelectorAll("#coordReadout")
      .forEach((el) => (el.textContent = txt));
  }

  function parseGridTrack(track) {
    if (!track) return { start: 1, span: 1 };
    const parts = String(track).split("/");
    const start = parseInt(parts[0], 10) || 1;
    const spanPart = (parts[1] || "").trim();
    const span = spanPart.startsWith("span")
      ? parseInt(spanPart.replace("span", ""), 10) || 1
      : parseInt(spanPart, 10) || 1;
    return { start, span };
  }

  function seedBoxDataFromInline(grid) {
    grid.querySelectorAll(".table-box").forEach((el) => {
      if (el.dataset.c && el.dataset.r && el.dataset.w && el.dataset.h) return;
      const col = parseGridTrack(el.style.gridColumn);
      const row = parseGridTrack(el.style.gridRow);
      el.dataset.c = String(col.start);
      el.dataset.w = String(col.span);
      el.dataset.r = String(row.start);
      el.dataset.h = String(row.span);
    });
  }

  function boxPos(el) {
    const d = el.dataset;
    if (d && d.c && d.r && d.w && d.h) {
      return { c: +d.c, r: +d.r, w: +d.w, h: +d.h };
    }
    const col = parseGridTrack(el.style.gridColumn);
    const row = parseGridTrack(el.style.gridRow);
    return { c: col.start, r: row.start, w: col.span, h: row.span };
  }

  function gridExtents(grid) {
    let maxCol = 1,
      maxRow = 1;
    grid.querySelectorAll(".table-box").forEach((el) => {
      const { c, r, w, h } = boxPos(el);
      maxCol = Math.max(maxCol, c + w - 1);
      maxRow = Math.max(maxRow, r + h - 1);
    });
    return { maxCol, maxRow };
  }

  function captureLayoutSnapshot() {
    const grid = visibleGrid();
    if (!grid) return null;
    seedBoxDataFromInline(grid);
    const cs = getComputedStyle(grid);
    const snap = {
      vars: {
        cols: parseFloat(cs.getPropertyValue("--cols") || "18"),
        rowh: parseFloat(cs.getPropertyValue("--rowh") || "90"),
        cellw: parseFloat(cs.getPropertyValue("--cellw") || "90"),
        gap: parseFloat(cs.getPropertyValue("--gap") || "6"),
      },
      boxes: {},
    };
    grid.querySelectorAll(".table-box").forEach((el) => {
      const key = String(el.dataset.table || "");
      if (!key) return;
      snap.boxes[key] = {
        c: String(el.dataset.c || ""),
        r: String(el.dataset.r || ""),
        w: String(el.dataset.w || ""),
        h: String(el.dataset.h || ""),
        shape: String(el.dataset.shape || ""),
      };
    });
    return snap;
  }

  function restoreLayoutSnapshot(snap) {
    const grid = visibleGrid();
    if (!grid || !snap) return;
    const vars = snap.vars || {};
    if (vars.cols) grid.style.setProperty("--cols", String(vars.cols));
    if (vars.rowh) grid.style.setProperty("--rowh", `${vars.rowh}px`);
    if (vars.cellw) grid.style.setProperty("--cellw", `${vars.cellw}px`);
    if (vars.gap != null) grid.style.setProperty("--gap", `${vars.gap}px`);

    grid.querySelectorAll(".table-box").forEach((el) => {
      const key = String(el.dataset.table || "");
      const box = snap.boxes ? snap.boxes[key] : null;
      if (!box) return;
      el.dataset.c = box.c;
      el.dataset.r = box.r;
      el.dataset.w = box.w;
      el.dataset.h = box.h;
      if (box.shape) el.dataset.shape = box.shape;
      applyStyle(el);
    });
    initGridInputsFromComputed();
  }

  function fitGridToViewport(opts = {}) {
    const grid = visibleFloorContainer()?.querySelector(".grid");
    if (!grid) return;

    seedBoxDataFromInline(grid);

    const scroller = grid.closest(".left-panel") || grid.parentElement;
    const padX = 40,
      padY = 40;

    const csGrid = getComputedStyle(grid);
    const gap = parseInt(csGrid.getPropertyValue("--gap") || "6", 10);

    const availW = scroller.clientWidth - padX;
    const availH = scroller.clientHeight - padY;

    const { maxCol, maxRow } = gridExtents(grid);

    const curRowh = parseInt(csGrid.getPropertyValue("--rowh") || "90", 10);
    const curCellw = parseInt(
      csGrid.getPropertyValue("--cellw") || String(curRowh),
      10
    );

    const curW = maxCol * curCellw + (maxCol - 1) * gap;
    const curH = maxRow * curRowh + (maxRow - 1) * gap;

    const minCell = opts.minCell ?? 36;
    const maxCell = opts.maxCell ?? 140;
    const allowGrow = opts.allowGrow ?? false;
    const force = opts.force ?? false;

    const fitCellW = Math.floor((availW - gap * (maxCol - 1)) / maxCol);
    const fitCellH = Math.floor((availH - gap * (maxRow - 1)) / maxRow);
    const cell = Math.max(
      minCell,
      Math.min(maxCell, Math.min(fitCellW, fitCellH))
    );

    const curCell = Math.min(curCellw, curRowh);
    if (!force) {
      if (!allowGrow && curW <= availW && curH <= availH) return;
      if (!allowGrow && cell >= curCell) return;
      if (allowGrow && Math.abs(cell - curCell) < 1) return;
    }

    grid.style.setProperty("--cellw", `${cell}px`);
    grid.style.setProperty("--rowh", `${cell}px`);

    scroller.scrollLeft = 0;
    scroller.scrollTop = 0;

    const cellEl = document.getElementById("gridCell");
    if (cellEl) cellEl.value = String(cell);
  }

  function initGridInputsFromComputed() {
    const grid = visibleGrid();
    if (!grid) return;
    const cs = getComputedStyle(grid);
    const cols = Number((cs.getPropertyValue("--cols") || "12").trim());
    const rowh = parseInt(cs.getPropertyValue("--rowh") || "90", 10);
    const gap = parseInt(cs.getPropertyValue("--gap") || "6", 10);

    const colsEl = document.getElementById("gridCols");
    const cellEl = document.getElementById("gridCell");
    const gapEl = document.getElementById("gridGap");

    if (colsEl) colsEl.value = String(cols);
    if (cellEl) cellEl.value = String(rowh);
    if (gapEl) gapEl.value = String(gap);
  }

  function readGridInputs() {
    const colsEl = document.getElementById("gridCols");
    const cellEl = document.getElementById("gridCell");
    const gapEl = document.getElementById("gridGap");

    const cols = parseInt(colsEl?.value || "", 10);
    const cell = parseInt(cellEl?.value || "", 10);
    const gap = parseInt(gapEl?.value || "", 10);

    return {
      cols: Number.isFinite(cols) ? cols : null,
      cell: Number.isFinite(cell) ? cell : null,
      gap: Number.isFinite(gap) ? gap : null,
      colsEl,
      cellEl,
      gapEl,
    };
  }

  function applyGridInputs() {
    const grid = visibleGrid();
    if (!grid) return;

    const {
      colsEl,
      cellEl,
      gapEl,
      cols: colsRaw,
      cell: cellRaw,
      gap: gapRaw,
    } = readGridInputs();
    const cols = Math.max(1, colsRaw ?? 12);
    const cell = Math.max(10, cellRaw ?? 90);
    const gap = Math.max(0, gapRaw ?? 6);

    if (colsEl) colsEl.value = String(cols);
    if (cellEl) cellEl.value = String(cell);
    if (gapEl) gapEl.value = String(gap);

    grid.style.setProperty("--cols", String(cols));
    grid.style.setProperty("--rowh", `${cell}px`);
    grid.style.setProperty("--cellw", `${cell}px`);
    grid.style.setProperty("--gap", `${gap}px`);

    grid.querySelectorAll(".table-box").forEach((el) => {
      clampBox(el, grid);
      applyStyle(el);
    });

    return { cols, cell, gap };
  }

  function gridVars(grid) {
    const cs = getComputedStyle(grid);
    const cols = Number(cs.getPropertyValue("--cols") || 18);
    const rowh = parseFloat(cs.getPropertyValue("--rowh") || 90);
    const cellw = parseFloat(cs.getPropertyValue("--cellw") || rowh);
    return { cols, rowh, cellw };
  }

  function applyStyle(el) {
    let c = el.dataset.c,
      r = el.dataset.r,
      w = el.dataset.w,
      h = el.dataset.h;
    if (!(c && r && w && h)) {
      const col = parseGridTrack(el.style.gridColumn);
      const row = parseGridTrack(el.style.gridRow);
      c = c || String(col.start);
      w = w || String(col.span);
      r = r || String(row.start);
      h = h || String(row.span);
      el.dataset.c = c;
      el.dataset.r = r;
      el.dataset.w = w;
      el.dataset.h = h;
    }
    el.style.gridColumn = `${c} / span ${w}`;
    el.style.gridRow = `${r} / span ${h}`;
    el.querySelector(".coord-badge")?.replaceChildren(
      document.createTextNode(`c${c},r${r} • ${w}×${h}`)
    );
    setCoordText(`c:${c} r:${r} w:${w} h:${h}`);
  }

  function clampBox(el, grid) {
    const { cols } = gridVars(grid);
    const c = Math.max(1, Math.min(cols, Number(el.dataset.c || 1)));
    const w = Math.max(1, Number(el.dataset.w || 1));
    const r = Math.max(1, Number(el.dataset.r || 1));
    const h = Math.max(1, Number(el.dataset.h || 1));
    el.dataset.c = String(Math.min(c, Math.max(1, cols - w + 1)));
    el.dataset.w = String(w);
    el.dataset.r = String(r);
    el.dataset.h = String(h);
  }

  function select(el) {
    if (!editing) return;
    document
      .querySelectorAll(".table-box.is-selected")
      .forEach((e) => e.classList.remove("is-selected"));
    selected = el;
    if (el) {
      if (!(el.dataset.c && el.dataset.r && el.dataset.w && el.dataset.h)) {
        const col = parseGridTrack(el.style.gridColumn);
        const row = parseGridTrack(el.style.gridRow);
        el.dataset.c = String(col.start);
        el.dataset.w = String(col.span);
        el.dataset.r = String(row.start);
        el.dataset.h = String(row.span);
      }
      el.classList.add("is-selected");
      applyStyle(el);
    } else {
      setCoordText("c:– r:– w:– h:–");
    }
  }

  function onKey(e) {
    if (editing && e.key === "Escape") {
      toggleEdit();
      return;
    }
    if (!editing || !selected) return;
    const grid = selected.closest(".grid");
    const step = e.ctrlKey || e.metaKey ? 5 : 1;

    let c = Number(selected.dataset.c || 1);
    let r = Number(selected.dataset.r || 1);
    let w = Number(selected.dataset.w || 1);
    let h = Number(selected.dataset.h || 1);

    const resize = e.shiftKey;

    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
      e.preventDefault();
      if (!resize) {
        if (e.key === "ArrowLeft") c -= step;
        if (e.key === "ArrowRight") c += step;
        if (e.key === "ArrowUp") r -= step;
        if (e.key === "ArrowDown") r += step;
      } else {
        if (e.key === "ArrowLeft") w = Math.max(1, w - step);
        if (e.key === "ArrowRight") w += step;
        if (e.key === "ArrowUp") h = Math.max(1, h - step);
        if (e.key === "ArrowDown") h += step;
      }
      selected.dataset.c = String(c);
      selected.dataset.r = String(r);
      selected.dataset.w = String(w);
      selected.dataset.h = String(h);
      clampBox(selected, grid);
      applyStyle(selected);
    }

    if (e.key.toLowerCase() === "o") {
      const isCircle = selected.classList.toggle("circle");
      selected.dataset.shape = isCircle ? "circle" : "";
      if (isCircle) {
        const wnow = Number(selected.dataset.w || 1);
        selected.dataset.h = String(wnow);
        applyStyle(selected);
      }
    }
  }

  function onMouseDown(e) {
    if (!editing) return;
    const handle = e.target.closest(".resize-handle");
    const el = e.target.closest(".table-box");
    if (!el) return;

    select(el);
    const grid = el.closest(".grid");
    const { cellw, rowh } = gridVars(grid);

    startMouse = {
      x: e.clientX,
      y: e.clientY,
      mode: handle ? "resize" : "move",
    };
    startBox = {
      c: Number(el.dataset.c || 1),
      r: Number(el.dataset.r || 1),
      w: Number(el.dataset.w || 1),
      h: Number(el.dataset.h || 1),
      cellw,
      rowh,
      grid,
    };
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp, { once: true });
  }

  function onMouseMove(e) {
    if (!editing || !selected || !startMouse || !startBox) return;
    const dx = e.clientX - startMouse.x;
    const dy = e.clientY - startMouse.y;
    const dc = Math.round(dx / startBox.cellw);
    const dr = Math.round(dy / startBox.rowh);

    if (startMouse.mode === "move") {
      selected.dataset.c = String(startBox.c + dc);
      selected.dataset.r = String(startBox.r + dr);
    } else {
      selected.dataset.w = String(Math.max(1, startBox.w + dc));
      selected.dataset.h = String(Math.max(1, startBox.h + dr));
    }
    clampBox(selected, startBox.grid);
    applyStyle(selected);
  }

  function onMouseUp() {
    document.removeEventListener("mousemove", onMouseMove);
    startMouse = null;
    startBox = null;
  }

  function toggleEdit() {
    editing = !editing;
    document.body.classList.toggle("layout-edit", editing);
    syncEditUi();

    const visible = visibleFloorContainer();
    const tables = document.querySelectorAll(".table-box");

    if (editing) {
      const grid = visible?.querySelector(".grid");
      if (grid) seedBoxDataFromInline(grid);
      layoutSnapshot = captureLayoutSnapshot();
      tables.forEach((el) => {
        el.setAttribute("tabindex", "0");
        el.__layoutClick = (e) => {
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          select(el);
        };
        el.addEventListener("click", el.__layoutClick);
      });

      const wantBadges = document.getElementById("chkBadges")?.checked ?? true;
      toggleBadges(wantBadges);

      document.addEventListener("keydown", onKey);
      document.addEventListener("mousedown", onMouseDown);

      initGridInputsFromComputed();
      const colsEl = document.getElementById("gridCols");
      const cellEl = document.getElementById("gridCell");
      const gapEl = document.getElementById("gridGap");
      colsEl && colsEl.addEventListener("input", applyGridInputs);
      cellEl && cellEl.addEventListener("input", applyGridInputs);
      gapEl && gapEl.addEventListener("input", applyGridInputs);

      requestAnimationFrame(() =>
        fitGridToViewport({ minCell: 36, maxCell: 140, allowGrow: false })
      );
    } else {
      tables.forEach((el) => {
        el.removeAttribute("tabindex");
        if (el.__layoutClick) {
          el.removeEventListener("click", el.__layoutClick);
          delete el.__layoutClick;
        }
      });

      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onMouseDown);

      const colsEl = document.getElementById("gridCols");
      const cellEl = document.getElementById("gridCell");
      const gapEl = document.getElementById("gridGap");
      colsEl && colsEl.removeEventListener("input", applyGridInputs);
      cellEl && cellEl.removeEventListener("input", applyGridInputs);
      gapEl && gapEl.removeEventListener("input", applyGridInputs);

      document
        .querySelectorAll(".table-box.is-selected")
        .forEach((e) => e.classList.remove("is-selected"));
      selected = null;
    }
  }

  function syncEditUi() {
    const panel = document.getElementById("layoutPanel");
    if (panel) panel.setAttribute("aria-hidden", editing ? "false" : "true");
    const btn = document.getElementById("layoutToggleBtn");
    if (btn) btn.textContent = editing ? "Exit Layout" : "Edit Layout";
  }

  function toggleGrid(on) {
    document.body.classList.toggle("layout-debug", !!on);
  }

  function toggleBadges(on) {
    document.body.classList.toggle("layout-badges", !!on);
    document.querySelectorAll(".table-box").forEach(applyStyle);
  }

  function currentFloor() {
    const ctn = visibleFloorContainer();
    return ctn?.dataset.floor ?? null;
  }

  function scaleGranularity(f) {
    if (!f || f === 1) return;
    const grid = visibleGrid();
    if (!grid) return;

    const cs = getComputedStyle(grid);
    const cols = parseInt(cs.getPropertyValue("--cols") || "12", 10);
    const rowh = parseInt(cs.getPropertyValue("--rowh") || "90", 10);
    const cellw = parseInt(cs.getPropertyValue("--cellw") || String(rowh), 10);

    const newCols = Math.max(1, Math.round(cols * f));
    const newRowh = Math.max(10, Math.round(rowh / f));
    const newCellw = Math.max(10, Math.round(cellw / f));
    grid.style.setProperty("--cols", String(newCols));
    grid.style.setProperty("--rowh", `${newRowh}px`);
    grid.style.setProperty("--cellw", `${newCellw}px`);

    grid.querySelectorAll(".table-box").forEach((el) => {
      ["c", "r", "w", "h"].forEach((k) => {
        const v = Math.max(1, Math.round(Number(el.dataset[k] || 1) * f));
        el.dataset[k] = String(v);
      });
      clampBox(el, grid);
      applyStyle(el);
    });

    initGridInputsFromComputed();
    requestAnimationFrame(() =>
      fitGridToViewport({
        minCell: 36,
        maxCell: 140,
        allowGrow: false,
        force: true,
      })
    );
  }

  async function save() {
    const floor = currentFloor();
    if (!floor) return alert("No floor visible.");

    const grid = document.querySelector(
      `.floor-container[data-floor="${floor}"] .grid`
    );
    if (!grid) return alert("Grid not found.");

    const applied = applyGridInputs() || {};
    const cs = getComputedStyle(grid);
    const colsFallback = Number((cs.getPropertyValue("--cols") || "12").trim());
    const cellFallback = parseInt(cs.getPropertyValue("--rowh") || "90", 10);
    const gapFallback = parseInt(cs.getPropertyValue("--gap") || "6", 10);

    const gridCols = Number.isFinite(applied.cols)
      ? applied.cols
      : colsFallback;
    const gridCell = Number.isFinite(applied.cell)
      ? applied.cell
      : cellFallback;
    const gridGap = Number.isFinite(applied.gap) ? applied.gap : gapFallback;

    const payload = {
      grid_cols: gridCols,
      grid_row_px: gridCell,
      grid_gap_px: gridGap,
      boxes: {},
    };

    grid.querySelectorAll(".table-box").forEach((el) => {
      const c = Number(el.dataset.c || 0);
      const r = Number(el.dataset.r || 0);
      const w = Number(el.dataset.w || 0);
      const h = Number(el.dataset.h || 0);
      const shape = (el.dataset.shape || "").trim();
      if (c && r && w && h) {
        payload.boxes[el.dataset.table] = {
          c,
          r,
          w,
          h,
          ...(shape ? { shape } : {}),
        };
      }
    });

    const res = await fetch(`/api/layouts/${encodeURIComponent(floor)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const j = await res.json().catch(() => ({}));
    if (j.status === "ok") {
      alert("Layout saved.");
      layoutSnapshot = null;
      if (editing) toggleEdit();
    } else {
      alert("Save failed: " + (j.message || res.status));
    }
  }

  function cancel() {
    if (layoutSnapshot) restoreLayoutSnapshot(layoutSnapshot);
    layoutSnapshot = null;
    if (editing) toggleEdit();
  }

  window.setFloor = (function (orig) {
    return function (floor) {
      orig(floor);
      if (document.body.classList.contains("layout-edit")) {
        initGridInputsFromComputed();
        requestAnimationFrame(() =>
          fitGridToViewport({ minCell: 36, maxCell: 140, allowGrow: false })
        );
      }
    };
  })(window.setFloor);

  function hookFit() {
    const doFit = () => {
      const grid = visibleFloorContainer()?.querySelector(".grid");
      if (grid) seedBoxDataFromInline(grid);
      if (document.body.classList.contains("layout-edit")) {
        fitGridToViewport({ minCell: 36, maxCell: 140, allowGrow: false });
      }
    };
    window.addEventListener("resize", doFit);
    const left = document.querySelector(".left-panel");
    if (left && "ResizeObserver" in window) {
      new ResizeObserver(doFit).observe(left);
    }
    requestAnimationFrame(doFit);
  }

  hookFit();

  return {
    toggleEdit,
    toggleGrid,
    toggleBadges,
    save,
    cancel,
    scaleGranularity,
    fitGridToViewport,
    hookFit,
  };
})();
