let MOVE_SELECTED = null;
let MOVE_FLOOR = "ALL";
let _rowPickerContext = null;
let MERGE_SELECTED = null;
let MERGE_FLOOR = "ALL";
const ORDER_LIST_MODE = localStorage.getItem("ol_mode") || "scroll"; // 'scroll' | 'paged'
const IS_SCROLL_MODE = ORDER_LIST_MODE === "scroll";

function openMergeModal() {
  document.getElementById("merge-modal").style.display = "flex";
  document.getElementById("merge-error").textContent = "";
  const sel = document.getElementById("merge-selection");
  sel.textContent = "Belum memilih meja tujuan.";
  sel.classList.add("muted");
  document.getElementById("merge-confirm").disabled = true;
  MERGE_SELECTED = null;

  // default to current table floor (keeps grid readable), fallback to ALL
  const curFloor = (window.CURRENT_TABLE_FLOOR ?? null);
  const floorVal = (curFloor === null || typeof curFloor === "undefined") ? "ALL" : String(curFloor);
  MERGE_FLOOR = floorVal;
  filterMergeFloor(floorVal);
}

function closeMergeModal() {
  document.getElementById("merge-modal").style.display = "none";
}

function filterMergeFloor(floor) {
  MERGE_FLOOR = floor;
  document.querySelectorAll("#merge-floor-row .floor-btn").forEach((btn) => {
    btn.classList.toggle(
      "active",
      btn.dataset.floor === floor ||
        (floor === "ALL" && btn.dataset.floor === undefined)
    );
  });
  document.querySelectorAll("#mergeGrid .table-box").forEach((box) => {
    const f = box.dataset.floor;
    box.style.display =
      floor === "ALL" || String(f) === String(floor) ? "" : "none";
  });
}

function selectMergeTarget(el) {
  const num = el.dataset.number;
  // clear previous
  document
    .querySelectorAll("#mergeGrid .table-box.selected")
    .forEach((b) => b.classList.remove("selected"));
  el.classList.add("selected");
  MERGE_SELECTED = num;

  const sel = document.getElementById("merge-selection");
  sel.classList.remove("muted");
  sel.textContent = `Gabung ke meja ${num}.`;
  document.getElementById("merge-error").textContent = "";
  document.getElementById("merge-confirm").disabled = false;
}

async function confirmMerge() {
  if (!MERGE_SELECTED) return;
  const sessionId = document.body.dataset.sessionId;
  try {
    const res = await fetch("/merge_table", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, to_table: MERGE_SELECTED }),
    });
    const j = await res.json();
    if (j.status === "success") {
      window.location.href = j.redirect; // go to target session
    } else {
      document.getElementById("merge-error").textContent =
        j.message || "Gagal gabung meja";
    }
  } catch (e) {
    document.getElementById("merge-error").textContent =
      "Jaringan bermasalah, coba lagi.";
  }
}

function openRowGroupPicker(btn) {
  if (btn.disabled) return;
  const ids = JSON.parse(btn.dataset.ids || "[]");
  const current = btn.dataset.currentGroup || "main";
  _rowPickerContext = { ids, btnEl: btn, current };

  const body = document.getElementById("row-group-picker-body");
  const err = document.getElementById("row-group-picker-error");
  body.innerHTML = "";
  err.textContent = "";

  body.appendChild(
    makeRowGroupBtn("main", "Main (gabung)", current === "main")
  );
  (SPLIT_LABELS || []).forEach((lbl) => {
    body.appendChild(makeRowGroupBtn(lbl, `Group ${lbl}`, current === lbl));
  });

  document.getElementById("row-group-picker-modal").style.display = "flex";
}

function closeRowGroupPicker() {
  document.getElementById("row-group-picker-modal").style.display = "none";
  _rowPickerContext = null;
}

function makeRowGroupBtn(value, text, isActive) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "action-button";
  if (isActive) b.classList.add("selected");
  b.textContent = text;
  b.onclick = () => applyRowGroup(value, text);
  return b;
}

async function applyRowGroup(groupValue, labelText) {
  if (!_rowPickerContext) return;
  const { ids, btnEl } = _rowPickerContext;
  const modal = document.getElementById("row-group-picker-modal");
  const modalBtns = modal ? Array.from(modal.querySelectorAll("button")) : [];
  modalBtns.forEach((b) => (b.disabled = true));

  // Normalize and short-circuit if nothing changes
  const newGroup = groupValue && groupValue !== "main" ? groupValue : "main";
  const current = btnEl.dataset.currentGroup || "main";
  if (newGroup === current) {
    closeRowGroupPicker();
    modalBtns.forEach((b) => (b.disabled = false));
    return;
  }

  try {
    const res = await fetch("/split/set_bill_group", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_ids: ids, group: newGroup }),
    });
    const j = await res.json();
    if (j.status !== "success") {
      document.getElementById("row-group-picker-error").textContent =
        j.message || "Gagal set group";
      return;
    }

    // Optional: brief visual feedback before reload
    btnEl.dataset.currentGroup = newGroup;
    btnEl.textContent = newGroup !== "main" ? labelText : "Pilih Group";

    closeRowGroupPicker();

    // Refresh rows/subtotals without a full reload
    if (window.POS && typeof window.POS.requestSessionState === "function") {
      await window.POS.requestSessionState({ skipRows: false });
    } else if (window.POS && typeof window.POS.rerenderTable === "function") {
      window.POS.rerenderTable();
    }
    if (window.POS && typeof window.POS.toast === "function") {
      window.POS.toast("Group diperbarui", { type: "success", duration: 1600 });
    }
  } catch (err) {
    document.getElementById("row-group-picker-error").textContent =
      "Jaringan bermasalah, coba lagi.";
  } finally {
    modalBtns.forEach((b) => (b.disabled = false));
  }
}

function openMoveModal() {
  document.getElementById("move-modal").style.display = "flex";
  document.getElementById("move-error").textContent = "";
  document.getElementById("move-selection").textContent =
    "Belum memilih meja tujuan.";
  document.getElementById("move-selection").classList.add("muted");
  document.getElementById("move-confirm").disabled = true;
  MOVE_SELECTED = null;

  // derive floor from the current table box, fallback ALL
  const currentBox = document.querySelector("#moveGrid .table-box.current");
  const curFloor = currentBox?.dataset.floor || "1";

  MOVE_FLOOR = curFloor;
  filterMoveFloor(curFloor);
}

function closeMoveModal() {
  document.getElementById("move-modal").style.display = "none";
}

function filterMoveFloor(floor) {
  MOVE_FLOOR = floor;
  // toggle active btn
  document.querySelectorAll("#move-floor-row .floor-btn").forEach((btn) => {
    btn.classList.toggle(
      "active",
      btn.dataset.floor === floor ||
        (floor === "ALL" && btn.dataset.floor === undefined)
    );
  });
  // filter tiles
  document.querySelectorAll("#moveGrid .table-box").forEach((box) => {
    const f = box.dataset.floor;
    box.style.display =
      floor === "ALL" || String(f) === String(floor) ? "" : "none";
  });
}

function selectMoveTarget(el) {
  const isCurrent = el.dataset.current === "1";
  const num = el.dataset.number;

  // allow selecting occupied tables (as you requested), just warn at confirm step
  // (server will still block if not allowed)
  if (isCurrent) {
    // selecting the current table doesn't make sense; ignore
    return;
  }

  // clear previous selection
  document
    .querySelectorAll("#moveGrid .table-box.selected")
    .forEach((b) => b.classList.remove("selected"));
  el.classList.add("selected");

  MOVE_SELECTED = num;

  const occ = el.dataset.occupied === "1";
  const sel = document.getElementById("move-selection");
  sel.classList.remove("muted");
  sel.textContent = `Pindah ke meja ${num}${
    occ ? " (ada orang)" : " (kosong)"
  }.`;
  document.getElementById("move-error").textContent = "";
  document.getElementById("move-confirm").disabled = false;
}

async function confirmMove() {
  if (!MOVE_SELECTED) return;
  const sessionId = document.body.dataset.sessionId;

  const res = await fetch("/move_table", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, to_table: MOVE_SELECTED }),
  });

  const j = await res.json();
  if (j.status === "success") {
    window.location.href = j.redirect;
  } else {
    // show error (e.g., occupied)
    document.getElementById("move-error").textContent =
      j.message || "Gagal memindahkan meja";
  }
}

function toggleSplit() {
  const shown =
    document.querySelector(".col-bill-group")?.style.display !== "none";
  document
    .querySelectorAll(".col-bill-group")
    .forEach((el) => (el.style.display = shown ? "none" : ""));
  const newState = !shown;
  document.getElementById("toggle-split")?.classList.toggle("active", newState);
  localStorage.setItem("splitVisible", String(newState));
}

// table.js
function openRefundModal(paymentId, maxAmount) {
  document.getElementById("refund-modal").style.display = "flex";
  document.getElementById("refund-payment-id").value = paymentId;
  const amt = document.getElementById("refund-amount");
  amt.value = maxAmount;
  amt.setAttribute("max", maxAmount);
  document.getElementById("refund-error").textContent = "";
}

function closeRefundModal() {
  document.getElementById("refund-modal").style.display = "none";
}

async function submitRefund() {
  const id = parseInt(document.getElementById("refund-payment-id").value, 10);
  const amount = parseInt(document.getElementById("refund-amount").value, 10);
  const reason = document.getElementById("refund-reason").value.trim();
  const err = document.getElementById("refund-error");
  err.textContent = "";
  try {
    const r = await fetch("/refund_payment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payment_id: id, amount, reason }),
    });
    const j = await r.json();
    if (j.status === "success") {
      let refreshed = false;
      if (window.POS && typeof window.POS.softSessionRefresh === "function") {
        refreshed = await window.POS.softSessionRefresh();
      } else if (window.POS && typeof window.POS.requestSessionState === "function") {
        try {
          await window.POS.requestSessionState({ skipRows: false });
          refreshed = true;
        } catch (_) {}
      }
      if (window.POS && typeof window.POS.toast === "function") {
        window.POS.toast("Refund berhasil", { type: "success", duration: 1800 });
      }
      if (!refreshed) window.location.replace(window.location.href);
    } else {
      err.textContent = j.message || "Gagal refund";
    }
  } catch {
    err.textContent = "Jaringan bermasalah";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const pref = localStorage.getItem("splitVisible");
  const wantShown =
    pref === "true" ||
    (pref === null && Array.isArray(SPLIT_LABELS) && SPLIT_LABELS.length > 0);
  if (wantShown) {
    document
      .querySelectorAll(".col-bill-group")
      .forEach((el) => (el.style.display = ""));
    document.getElementById("toggle-split")?.classList.add("active");
  }
});

// ---- Compact, paged order list (host renderer; split-aware) ----
(() => {
  const table = document.querySelector(".order-table");
  const tbody = document.getElementById("order-body");
  const thead = table?.querySelector("thead");
  const tfoot = table?.querySelector("tfoot");
  const wrap = document.querySelector(".order-table-wrap");

  const hud = document.getElementById("page-hud");
  const btnPrev = document.getElementById("page-prev");
  const btnNext = document.getElementById("page-next");

  const subtotalCell = document.getElementById("subtotal-cell");
  const grandCell = document.getElementById("grandtotal-cell");

  const grpNameEl = document.getElementById("grp-name");
  const grpPrev = document.getElementById("grp-prev");
  const grpNext = document.getElementById("grp-next");

  // conservative first-pass cap to avoid overflow "flash"
  const FIRST_PASS_CAP = 12;
  let firstPaint = true;
  let currentKey = "all";

  function getSplitLabels() {
    const SL = window.SPLIT_LABELS;

    // 1) Primary: labels from server (array or object)
    if (Array.isArray(SL)) {
      return SL.map(String)
        .filter(Boolean)
        .sort((a, b) => {
          const na = +a,
            nb = +b;
          if (Number.isFinite(na) && Number.isFinite(nb)) return na - nb;
          return String(a).localeCompare(String(b), undefined, {
            numeric: true,
          });
        });
    }

    if (SL && typeof SL === "object") {
      return Object.keys(SL)
        .filter(Boolean)
        .sort((a, b) =>
          String(a).localeCompare(String(b), undefined, { numeric: true })
        );
    }

    // 2) Fallback: derive from server-subtotals (ignore 'main')
    const subs = window.GROUP_SUBTOTALS || {};
    const fromSubs = Object.keys(subs || {}).filter((k) => k && k !== "main");
    if (fromSubs.length) {
      return fromSubs.sort((a, b) =>
        String(a).localeCompare(String(b), undefined, { numeric: true })
      );
    }

    // 3) Last resort: infer from current ORDER_ROWS (ignore empty/main)
    const rows = Array.isArray(window.ORDER_ROWS) ? window.ORDER_ROWS : [];
    const fromRows = [
      ...new Set(
        rows
          .map((r) =>
            String(r.bill_group ?? r.group ?? r.group_label ?? "").trim()
          )
          .filter((s) => s && s.toLowerCase() !== "main")
      ),
    ];
    return fromRows.sort((a, b) =>
      String(a).localeCompare(String(b), undefined, { numeric: true })
    );
  }

  // dynamic group keys: 'all' + numeric split labels (no separate 'main' tab here)
  let GROUP_KEYS = ["all", ...getSplitLabels()];

  const splitMetaName = (label) => {
    const meta = Array.isArray(window.SPLIT_META) ? window.SPLIT_META : [];
    const key = String(label ?? '').trim();
    if (!key) return '';
    const hit = meta.find(m => String(m.key ?? m.label ?? m.id ?? m.group ?? '').trim() === key);
    const name = (hit?.name ?? hit?.title ?? '').toString().trim();
    return name || '';
  };

  const friendly = (k) => {
    if (k === "all") return "Semua";
    const name = splitMetaName(k);
    return name || `Bill ${k}`;
  };

  // Restore last chosen group/page
  let groupIdx = Number(localStorage.getItem("ol_groupIdx") || 0);
  if (
    !Number.isFinite(groupIdx) ||
    groupIdx < 0 ||
    groupIdx >= GROUP_KEYS.length
  )
    groupIdx = 0;

  let page = Number(localStorage.getItem("ol_page") || 1);
  let pageCount = 1;
  let rowsPerPage = 8; // sensible default before we measure
  const state = { rowsFiltered: [] };

  // ===== helpers (with robust field fallbacks) =====
  const qfmt = (q) => {
    const n = Number(q || 0);
    return Math.round(n * 10) % 10 === 0 ? String(Math.round(n)) : n.toFixed(1);
  };
  const fmtRp = (n) => `Rp ${Number(n || 0).toLocaleString("id-ID")}`;
  const esc = (s) =>
    String(s ?? "").replace(
      /[&<>"']/g,
      (m) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        }[m])
    );

  function getName(row) {
    const base =
      row.name ??
      row.item_name ??
      row.title ??
      row.product_name ??
      row.menu_name ??
      row.item ??
      "";
    const mod =
      row.modifier ?? row.modifier_note ?? row.note ?? row.options ?? "";
    const full = mod ? `${base} — ${mod}` : base;
    return String(full || "");
  }

  function getBaseName(row) {
    return (
      row.item_name ??
      row.name ??
      row.title ??
      row.product_name ??
      row.menu_name ??
      row.item ??
      ""
    );
  }

  function getQty(row) {
    const hasNet = row.net_qty != null;
    if (hasNet) return Number(row.net_qty);

    const base = Number(
      row.qty ?? row.quantity ?? row.amount ?? row.count ?? 0
    );
    const vq = Number(row.void_qty ?? 0);
    return Math.max(0, base - vq);
  }

  function getUnitPrice(row) {
    return Number(row.unit_price ?? row.price ?? row.unit ?? row.rate ?? 0);
  }

  function getPrintClass(row) {
    const status =
      row.print_status ??
      row.kitchen_status ??
      row.status ??
      (row.sent ? "printed" : null) ??
      (row.is_printed ? "printed" : null);

    return String(status || "").toLowerCase() === "printed"
      ? "row-print-printed"
      : "";
  }

  function getRowIds(row) {
    if (Array.isArray(row?.ids) && row.ids.length) return row.ids;
    if (row && row.id != null) return [row.id];
    return [];
  }

  function isMergeable(row) {
    const st = String(row.status ?? "").toLowerCase();

    // Anything that looks like "already fired" / printed should NEVER be merged
    const printState = String(row.print_state ?? "").toLowerCase();
    const printedFlag = _printedFlag(row); // from _printedFlag()
    const printedQty = _printedQty(row); // from _printedQty()
    const wasPrinted = Boolean(
      row.wasPrinted ||
        row.was_printed ||
        row.kitchen_printed ||
        row.kitchen_sent ||
        row.sent ||
        row.is_sent
    );

    const looksPrinted =
      printedFlag ||
      printedQty > 0 ||
      wasPrinted ||
      printState === "printed" ||
      printState === "printed_partial";

    // Merge only if:
    // - NOT paid
    // - and doesn't look printed in ANY way
    return st !== "paid" && !looksPrinted;
  }

  function mergeRowsForDisplay(rows) {
    // Key on group + base name + normalized note + unit + station
    const keyOf = (r) => {
      const group = String(r.bill_group ?? r.group ?? "main");
      const base = getBaseName(r).trim().toLowerCase();
      const note = getRawNote(r).trim().toLowerCase();
      const unit = getUnitPrice(r);
      const station = String(r.station ?? r.dept ?? r.category ?? "")
        .trim()
        .toLowerCase();
      return [group, base, note, unit, station].join("¦");
    };

    const buckets = new Map(); // insertion order preserves first-seen order
    const keep = []; // non-mergeable rows

    for (const r of rows) {
      if (!isMergeable(r)) {
        keep.push(r);
        continue;
      }

      const k = keyOf(r);
      const qty = getQty(r);
      const ids = getRowIds(r);

      if (!buckets.has(k)) {
        // seed with this row’s data
        buckets.set(k, { ...r, qty, net_qty: qty, ids: ids.slice() });
      } else {
        const acc = buckets.get(k);
        acc.qty = Number(acc.qty || 0) + qty;
        acc.net_qty = acc.qty;
        acc.ids = acc.ids.concat(ids);

        // keep freshest timestamp/status for display flavoring
        const ta = new Date(acc.timestamp || 0);
        const tb = new Date(r.timestamp || 0);
        if (tb > ta) {
          acc.timestamp = r.timestamp;
          acc.status = r.status;
        }
      }
    }

    // merged (in first-seen order) + untouched non-mergeables
    return [...buckets.values(), ...keep];
  }

  function getRawNote(row) {
    return String(
      row.note ?? row.modifier ?? row.modifier_note ?? row.options ?? ""
    );
  }

  function noteTokens(note) {
    const raw = String(note || "").trim();
    if (!raw) return [];
    return raw
      .split(/[;,|•/]+/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  function nameHTML(base, note) {
    const toks = noteTokens(note);
    const lines = toks
      .map((t) => `<div class="nm-note">${esc(t)}</div>`)
      .join("");
    return `<div class="nm"><div class="nm-base">${esc(
      base
    )}</div>${lines}</div>`;
  }

  // --- PATCH: robust sent/paid coloring + keep separate rows ---

  function _printedFlag(row) {
    const s = String(
      row.print_status ??
        row.kitchen_status ??
        row.status ??
        (row.sent ? "printed" : "") ??
        (row.is_printed ? "printed" : "") ??
        (row.was_printed ? "printed" : "") ??
        (row.kitchen_printed ? "printed" : "") ??
        (row.kitchen_sent ? "printed" : "") ??
        (row.is_sent ? "printed" : "")
    ).toLowerCase();
    return s === "printed";
  }

  function _printedQty(row) {
    const v = Number(
      row.printed_qty ??
        row.sent_qty ??
        row.qty_printed ??
        row.qty_sent ??
        row.kitchen_qty ??
        0
    );
    return Number.isFinite(v) ? v : 0;
  }

  function expandRowForPrint(row) {
    const total = getQty(row);
    const unit = Number(
      row.unit_price ?? row.price ?? row.unit ?? row.rate ?? 0
    );
    const base =
      row.item_name ??
      row.name ??
      row.title ??
      row.product_name ??
      row.menu_name ??
      row.item ??
      "";
    const note = String(
      row.note ?? row.modifier ?? row.modifier_note ?? row.options ?? ""
    );
    const ids = row.ids || (row.id ? [row.id] : []);
    const station = String(
      row.station ?? row.dept ?? row.category ?? ""
    ).toLowerCase();
    const st = String(row.status ?? "").toLowerCase();

    // PAID takes precedence -> single blue row
    if (st === "paid" && total > 0) {
      return [
        {
          base,
          note,
          qty: total,
          unit,
          ids,
          station,
          className: "row-paid",
          sentState: "paid",
        },
      ];
    }

    // Use printed quantity if provided to split partials
    const printed = Math.max(0, Math.min(_printedQty(row), total));
    const pending = Math.max(0, total - printed);

    // Fully printed -> green
    if (printed >= total && total > 0) {
      return [
        {
          base,
          note,
          qty: total,
          unit,
          ids,
          station,
          className: "row-print-printed",
          sentState: "printed",
        },
      ];
    }

    // Partial -> green printed part + yellow pending part
    if (printed > 0 && pending > 0) {
      return [
        {
          base,
          note,
          qty: printed,
          unit,
          ids: Array.isArray(row.printed_ids) ? row.printed_ids : ids,
          station,
          className: "row-print-printed",
          sentState: "printed",
        },
        {
          base,
          note,
          qty: pending,
          unit,
          ids: Array.isArray(row.pending_ids) ? row.pending_ids : ids,
          station,
          className: "row-print-pending",
          sentState: "pending",
        },
      ];
    }

    // No printed qty → trust flags
    if (_printedFlag(row) && total > 0) {
      return [
        {
          base,
          note,
          qty: total,
          unit,
          ids,
          station,
          className: "row-print-printed",
          sentState: "printed",
        },
      ];
    }

    // Default: unsent/new → yellow
    return [
      {
        base,
        note,
        qty: total,
        unit,
        ids,
        station,
        className: "row-print-pending",
        sentState: "pending",
      },
    ];
  }
  // --- END PATCH

  function matchesGroup(row, key) {
    if (key === "all") return true;
    const grp = row.bill_group ?? row.group ?? row.group_label ?? "";
    return String(grp) === String(key);
  }

  function fixTableStylesOnce() {
    if (!table || !thead || !tfoot || !tbody) return;
    table.style.tableLayout = "fixed";
    table.style.borderCollapse = "collapse";
    thead.style.display = "table-header-group";
    tfoot.style.display = "table-footer-group";
    tbody.style.display = "table-row-group";
  }

  // pin wrapper so footer stays at bottom
  function lockWrapperHeight() {
    if (!wrap) return;
    const top = wrap.getBoundingClientRect().top || 0;
    const targetH = Math.max(0, window.innerHeight - top - 12);
    if (
      !wrap.style.height ||
      Math.abs(parseFloat(wrap.style.height) - targetH) > 1
    ) {
      wrap.style.height = targetH + "px";
    }
  }

  // offscreen ghost to get stable row height
  let cachedRowHeight = null;
  function measureRowHeight() {
    if (!table) return 24;
    if (cachedRowHeight) return cachedRowHeight;
    const ghost = document.createElement("table");
    ghost.className = "order-table";
    ghost.style.cssText = `position:absolute;left:-99999px;top:0;visibility:hidden;table-layout:fixed;width:${
      table.getBoundingClientRect().width || 600
    }px`;
    ghost.innerHTML = `
      <colgroup>
        <col id="col-name"><col id="col-qty" style="width:72px"><col id="col-price" style="width:120px">
      </colgroup>
      <tbody>
        <tr>
          <td class="name-cell">
            <div class="nm">
              <div class="nm-base">Nama item yang cukup panjang</div>
              <div class="nm-note">catatan</div>
            </div>
          </td>
          <td class="num">1</td>
          <td class="price-cell">Rp 0</td>
        </tr>
      </tbody>
    `;
    table.parentElement.appendChild(ghost);
    const h = Math.max(
      1,
      Math.ceil(ghost.querySelector("tr").getBoundingClientRect().height || 24)
    );
    ghost.remove();
    cachedRowHeight = h;
    return h;
  }

  function computeRowsPerPage() {
    if (!wrap || !thead || !tfoot || !tbody) {
      rowsPerPage = 6;
      return;
    }
    lockWrapperHeight(); // we still want a fixed-height wrap for scrolling

    if (IS_SCROLL_MODE) {
      // Render ALL rows → body taller than wrap → wrap scrolls
      rowsPerPage = Number.POSITIVE_INFINITY;
      return;
    }

    // original paged math
    const headH = Math.max(0, thead.getBoundingClientRect().height || 36);
    const footH = Math.max(0, tfoot.getBoundingClientRect().height || 84);
    const avail = Math.max(
      0,
      (parseFloat(wrap.style.height) || wrap.getBoundingClientRect().height) -
        headH -
        footH
    );
    const rowH = measureRowHeight();
    const next = Math.floor(avail / rowH);
    const cap = firstPaint ? FIRST_PASS_CAP : 999;
    rowsPerPage = Math.max(3, Math.min(Number.isFinite(next) ? next : 6, cap));
  }

  function notifyGroupChanged(key) {
    try {
      if (window.POS && typeof window.POS._onGroupChanged === "function") {
        window.POS._onGroupChanged(String(key));
      }
    } catch (_) {}
  }

  function setGroupByKey(key) {
    GROUP_KEYS = ["all", ...getSplitLabels()]; // keep fresh
    let idx = GROUP_KEYS.indexOf(String(key));
    if (idx < 0) idx = 0;
    groupIdx = idx;
    localStorage.setItem("ol_groupIdx", String(groupIdx));
    page = 1;
    stableRender();
    notifyGroupChanged(GROUP_KEYS[groupIdx]);
  }

  function setGroupByIndex(newIdx) {
    GROUP_KEYS = ["all", ...getSplitLabels()];
    if (GROUP_KEYS.length === 0) GROUP_KEYS = ["all"];
    groupIdx = (newIdx + GROUP_KEYS.length) % GROUP_KEYS.length;
    localStorage.setItem("ol_groupIdx", String(groupIdx));
    page = 1;
    stableRender();
    notifyGroupChanged(GROUP_KEYS[groupIdx]);
  }

  // expose a host API that split.js can talk to
  window.POS = window.POS || {};
  window.POS.__pagedOrders = {
    setGroup: (key) => setGroupByKey(key),
    setFilter: (obj) => {
      if (obj && obj.group != null) setGroupByKey(obj.group);
    },
    get group() {
      return GROUP_KEYS[groupIdx];
    },
    set group(v) {
      setGroupByKey(v);
    },
    render: () => stableRender(),
  };

  function render() {
    fixTableStylesOnce();
    computeRowsPerPage();

    // refresh keys on every render (splits can change)
    GROUP_KEYS = ["all", ...getSplitLabels()];
    if (groupIdx >= GROUP_KEYS.length) groupIdx = 0;

    currentKey = GROUP_KEYS[groupIdx];
    if (grpNameEl) grpNameEl.textContent = friendly(currentKey);

    const all = Array.isArray(window.ORDER_ROWS) ? window.ORDER_ROWS : [];
    const filtered = all.filter((r) => matchesGroup(r, currentKey));
    state.rowsFiltered = filtered;

    // totals (service 0% for takeaway; else 5%)
    const baseRows = mergeRowsForDisplay(filtered);
    const subtotal = baseRows.reduce(
      (s, r) => s + getUnitPrice(r) * getQty(r),
      0
    );
    const billingCfg = (window.POS_CONFIG && window.POS_CONFIG.billing) ? window.POS_CONFIG.billing : {};
    const svcPct =
      typeof window.SERVICE_PCT === "number" ? window.SERVICE_PCT : Number(billingCfg.service_percent ?? 5);
    const taxPct = Number(billingCfg.tax_percent ?? window.TAX_PERCENT ?? 10);
    const taxOnService = (billingCfg.tax_on_service === true || billingCfg.tax_on_service === "true" || billingCfg.tax_on_service === 1 || window.TAX_ON_SERVICE === true);
    const service = Math.round(subtotal * (svcPct / 100));
    const taxBase = taxOnService ? (subtotal + service) : subtotal;
    const tax = Math.round(taxBase * (taxPct / 100));
    const grand = subtotal + service + tax;

    if (subtotalCell) subtotalCell.textContent = fmtRp(subtotal);
    if (grandCell) grandCell.textContent = fmtRp(grand);

    state.rowsDisplay = filtered.flatMap(expandRowForPrint);

    pageCount = Math.max(1, Math.ceil(state.rowsDisplay.length / rowsPerPage));
    const pagerEls = [hud, btnPrev, btnNext].filter(Boolean);
    pagerEls.forEach((el) => (el.style.display = IS_SCROLL_MODE ? "none" : ""));

    if (page > pageCount) page = pageCount;

    renderPageOnly();
  }

  function renderPageOnly() {
    const rows = state.rowsDisplay;

    // In scroll mode, show everything
    let start = 0,
      end = rows.length;
    if (!IS_SCROLL_MODE) {
      start = (page - 1) * rowsPerPage;
      end = Math.min(rows.length, start + rowsPerPage);
    }

    tbody.style.visibility = "hidden";
    const frag = document.createDocumentFragment();

    if (rows.length === 0) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 3;
      td.innerHTML = "<em>Belum ada pesanan</em>";
      tr.appendChild(td);
      frag.appendChild(tr);
    } else {
      for (let i = start; i < end; i++) {
        const r = rows[i];
        const tr = document.createElement("tr");
        if (r.className) tr.className = r.className;
        if (r.sentState) tr.dataset.sent = r.sentState;
        else delete tr.dataset.sent;

        const baseName = r.base;
        const qty = r.qty;
        const unit = r.unit;
        const line = unit * qty;

        // multiline name cell (base + indented notes)
        tr.innerHTML = `
          <td class="name-cell">${nameHTML(baseName, r.note)}</td>
          <td class="num">${qfmt(qty)}</td>
          <td class="price-cell">${fmtRp(line)}</td>
        `;

        const nameTd = tr.querySelector(".name-cell");

        if (!window.SPLIT_BOARD_MODE && currentKey !== "all" && nameTd) {
          const actions = document.createElement("div");
          actions.className = "row-actions";
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "mini-btn ungroup-btn";
          btn.textContent = "Keluarkan";
          btn.addEventListener("click", () => {
            if (
              Array.isArray(r.ids) &&
              r.ids.length &&
              window.POS &&
              typeof window.POS._splitUnassign === "function"
            ) {
              window.POS._splitUnassign(
                r.ids,
                String(baseName || ""),
                Number(qty || 0)
              );
            }
          });
          actions.appendChild(btn);
          nameTd.appendChild(actions);
        }

        const idsArr = r.ids || [];
        tr.dataset.ids = JSON.stringify(idsArr);
        tr.dataset.name = String(baseName || "");
        tr.dataset.note = String(r.note || "");
        tr.dataset.station = String(r.station || "").toLowerCase();

        frag.appendChild(tr);
      }
    }

    if (typeof tbody.replaceChildren === "function") {
      tbody.replaceChildren(frag);
    } else {
      tbody.innerHTML = "";
      tbody.appendChild(frag);
    }

    requestAnimationFrame(() => {
      tbody.style.visibility = "";
    });

    hud.textContent = `${page}/${pageCount}`;
    btnPrev.disabled = page <= 1;
    btnNext.disabled = page >= pageCount;
    localStorage.setItem("ol_page", String(page));
  }

  // render safely: conservative first frame, accurate second/third
  function stableRender() {
    firstPaint = true;
    render(); // conservative cap -> no overflow
    requestAnimationFrame(() => {
      // layout settled
      firstPaint = false;
      render(); // exact fill based on real sizes
      setTimeout(render, 60); // tiny settle after fonts/images
    });
  }

  // controls
  grpPrev?.addEventListener("click", () => setGroupByIndex(groupIdx - 1));
  grpNext?.addEventListener("click", () => setGroupByIndex(groupIdx + 1));
  btnPrev?.addEventListener("click", () => {
    if (page > 1) {
      page--;
      renderPageOnly();
    }
  });
  btnNext?.addEventListener("click", () => {
    if (page < pageCount) {
      page++;
      renderPageOnly();
    }
  });

  // resize
  let _rz;
  window.addEventListener("resize", () => {
    clearTimeout(_rz);
    cachedRowHeight = null;
    _rz = setTimeout(() => stableRender(), 80);
  });

  // init
  grpNameEl && (grpNameEl.textContent = friendly(GROUP_KEYS[groupIdx]));
  stableRender();
  notifyGroupChanged(GROUP_KEYS[groupIdx]);

  // debug handle
  window._ol = {
    get rowsPerPage() {
      return rowsPerPage;
    },
    get page() {
      return page;
    },
    get pageCount() {
      return pageCount;
    },
    get group() {
      return GROUP_KEYS[groupIdx];
    },
    state,
    render,
    renderPageOnly,
  };

  // realtime hook
  window.POS = window.POS || {};
  window.POS.refreshOrders = function (newRows) {
    if (Array.isArray(newRows)) window.ORDER_ROWS = newRows;
    stableRender();
  };
  window.POS.rerenderTable = () => window.POS.refreshOrders();
})();
