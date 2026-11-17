(function () {
  const body = document.getElementById("cx_body");
  const fromEl = document.getElementById("cx_from");
  const toEl = document.getElementById("cx_to");
  const applyBtn = document.getElementById("cx_apply");
  const countEl = document.getElementById("cx_count");
  const ranges = document.getElementById("cx_ranges");

  const fmtRp = (n) => `Rp ${Number(n || 0).toLocaleString("id-ID")}`;
  const esc = (s) =>
    String(s ?? "").replace(/[&<>"']/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[m]);

  function todayStr(offsetDays = 0) {
    const d = new Date();
    d.setDate(d.getDate() + offsetDays);
    return d.toISOString().slice(0, 10);
  }

  function setRange(key) {
    const now = new Date();
    const y = now.getFullYear();
    const m = now.getMonth();
    if (key === "today") {
      fromEl.value = todayStr(0);
      toEl.value = todayStr(0);
    } else if (key === "yesterday") {
      fromEl.value = todayStr(-1);
      toEl.value = todayStr(-1);
    } else if (key === "7d") {
      fromEl.value = todayStr(-6);
      toEl.value = todayStr(0);
    } else if (key === "30d") {
      fromEl.value = todayStr(-29);
      toEl.value = todayStr(0);
    } else if (key === "mtd") {
      const first = new Date(y, m, 1);
      fromEl.value = first.toISOString().slice(0, 10);
      toEl.value = todayStr(0);
    }
  }

  async function fetchItems(sessionId, targetRow) {
    targetRow.innerHTML = `<td colspan="8" class="row-details"><div class="details-wrap muted">Memuat...</div></td>`;
    try {
      const r = await fetch(`/admin/api/cancelled_sessions/${encodeURIComponent(sessionId)}/items`);
      const j = await r.json();
      if (!r.ok || !j || j.status !== "ok") throw new Error(j.message || `HTTP ${r.status}`);

      const items = j.items || [];
      if (!items.length) {
        targetRow.innerHTML = `<td colspan="8" class="row-details"><div class="details-wrap muted">Tidak ada item.</div></td>`;
        return;
      }

      const rows = items.map((it) => {
        const qtyCancelled = Number(it.qty_cancelled || 0);
        const qtyVoid = Number(it.qty_void || 0);
        const totalQty = qtyCancelled + qtyVoid;
        const total = Number(it.total_value || 0);
        return `
          <tr>
            <td>${esc(it.item_name)}</td>
            <td>${qtyCancelled ? qtyCancelled : "-"}</td>
            <td>${qtyVoid ? qtyVoid : "-"}</td>
            <td>${totalQty ? totalQty : "-"}</td>
            <td>${fmtRp(it.price)}</td>
            <td>${fmtRp(total)}</td>
          </tr>
        `;
      }).join("");

      targetRow.innerHTML = `
        <td colspan="8" class="row-details">
          <div class="details-wrap">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Qty Cancel</th>
                  <th>Qty Void</th>
                  <th>Qty Total</th>
                  <th>Harga</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </td>
      `;
    } catch (e) {
      targetRow.innerHTML = `<td colspan="8" class="row-details"><div class="details-wrap muted">Gagal: ${esc(e.message || e)}</div></td>`;
    }
  }

  function renderRows(rows) {
    if (!rows.length) {
      body.innerHTML = `<tr><td colspan="8" class="muted">Tidak ada data.</td></tr>`;
      countEl.textContent = "0 sesi";
      return;
    }
    countEl.textContent = `${rows.length} sesi`;
    body.innerHTML = rows.map((r, idx) => {
      const est = Number(r.estimate || 0);
      return `
        <tr data-session-id="${esc(r.session_id)}">
          <td>${esc(r.table_number || "-")}</td>
          <td>${esc(r.session_id)}</td>
          <td>${esc(r.opened_at_wib || "-")}</td>
          <td>${esc(r.closed_at_wib || "-")}</td>
          <td>${esc(r.opened_by || "-")}</td>
          <td>${esc(r.closed_by || "-")}</td>
          <td>${fmtRp(est)}</td>
          <td><button class="btn" data-action="toggle" data-idx="${idx}">Detail</button></td>
        </tr>
        <tr class="detail-row" data-detail-for="${esc(r.session_id)}" style="display:none;">
          <td colspan="8" class="row-details"><div class="details-wrap muted">Klik Detail untuk memuat item.</div></td>
        </tr>
      `;
    }).join("");

    body.querySelectorAll("button[data-action='toggle']").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const tr = btn.closest("tr");
        const sid = tr?.dataset?.sessionId;
        if (!sid) return;
        const detailRow = body.querySelector(`tr.detail-row[data-detail-for="${sid}"]`);
        if (!detailRow) return;
        const isOpen = detailRow.style.display !== "none";
        detailRow.style.display = isOpen ? "none" : "table-row";
        if (!isOpen && !detailRow.dataset.loaded) {
          detailRow.dataset.loaded = "1";
          await fetchItems(sid, detailRow);
        }
      });
    });
  }

  async function load() {
    const params = new URLSearchParams();
    if (fromEl.value) params.set("from", fromEl.value);
    if (toEl.value) params.set("to", toEl.value);
    body.innerHTML = `<tr><td colspan="8" class="muted">Memuat...</td></tr>`;
    try {
      const r = await fetch(`/admin/api/cancelled_sessions?${params.toString()}`);
      const j = await r.json();
      if (!r.ok || !j || j.status !== "ok") throw new Error(j.message || `HTTP ${r.status}`);
      renderRows(j.rows || []);
    } catch (e) {
      body.innerHTML = `<tr><td colspan="8" class="muted">Gagal: ${esc(e.message || e)}</td></tr>`;
      countEl.textContent = "-";
    }
  }

  applyBtn?.addEventListener("click", load);
  ranges?.addEventListener("click", (e) => {
    const btn = e.target.closest(".chip");
    if (!btn) return;
    ranges.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
    btn.classList.add("active");
    setRange(btn.dataset.range);
    load();
  });

  setRange("7d");
  load();
})();
