(() => {
  const board = document.getElementById('split-board');
  if (!board) return;

  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, m => (
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]
  ));
  const fmtRp = (n) => `Rp ${Number(n || 0).toLocaleString('id-ID')}`;
  const qfmt  = (q) => {
    const n = Number(q || 0);
    return (Math.round(n * 10) % 10 === 0) ? String(Math.round(n)) : n.toFixed(1);
  };
  const isMain = (v) => v == null || String(v).trim() === '' || String(v).toLowerCase() === 'main';
  const rowGroup = (row) => isMain(row.bill_group) ? 'main' : String(row.bill_group || '').trim();
  const bool = (v) => (typeof v === 'boolean' ? v : (typeof v === 'string' ? (v.toLowerCase() === 'true' || v === '1') : !!v));
  const BILLING_CFG = (window.POS_CONFIG && window.POS_CONFIG.billing) ? window.POS_CONFIG.billing : {};
  const SERVICE_PERCENT = Number(BILLING_CFG.service_percent ?? window.SERVICE_PCT ?? 5);
  const TAX_PERCENT = Number(BILLING_CFG.tax_percent ?? window.TAX_PERCENT ?? 10);
  const TAX_ON_SERVICE = bool(BILLING_CFG.tax_on_service ?? window.TAX_ON_SERVICE);

  let activeGroup = null;
  let selected = null; // { groupKey, row, el }
  let boardCollapsed = false;
  let renameKey = null;
  let showPaidSplits = false;

  // ---- Split -> table move modal state ----
  let splitMoveGroup = null;
  let splitMoveName = '';
  let splitMoveSelected = null;
  let splitMoveFloor = 'ALL';

  function openSplitMoveModal(groupKey, groupName) {
    const modal = document.getElementById('split-move-modal');
    if (!modal) return;
    splitMoveGroup = String(groupKey || '').trim();
    splitMoveName = String(groupName || '').trim();
    splitMoveSelected = null;
    const defaultFloor = (window.CURRENT_TABLE_FLOOR ?? null);
    splitMoveFloor = (defaultFloor === null || typeof defaultFloor === 'undefined') ? 'ALL' : String(defaultFloor);

    const title = document.getElementById('split-move-title');
    const sel = document.getElementById('split-move-selection');
    const err = document.getElementById('split-move-error');
    const btn = document.getElementById('split-move-confirm');
    if (title) title.textContent = `Pindah ${splitMoveName || `Split ${splitMoveGroup}`}`;
    if (sel) {
      sel.textContent = 'Belum memilih meja tujuan.';
      sel.classList.add('muted');
    }
    if (err) err.textContent = '';
    if (btn) btn.disabled = true;

    filterSplitMoveFloor(splitMoveFloor);
    modal.style.display = 'flex';
  }

  function closeSplitMoveModal() {
    const modal = document.getElementById('split-move-modal');
    if (modal) modal.style.display = 'none';
    splitMoveSelected = null;
  }

  function filterSplitMoveFloor(floor) {
    splitMoveFloor = floor;
    document.querySelectorAll('#split-move-floor-row .floor-btn').forEach((btn) => {
      btn.classList.toggle(
        'active',
        btn.dataset.floor === floor || (floor === 'ALL' && btn.dataset.floor === undefined)
      );
    });
    document.querySelectorAll('#splitMoveGrid .table-box').forEach((box) => {
      const f = box.dataset.floor;
      box.style.display = floor === 'ALL' || String(f) === String(floor) ? '' : 'none';
    });
  }

  function selectSplitMoveTarget(el) {
    if (!el || el.dataset.current === '1') return;
    const num = el.dataset.number;
    document.querySelectorAll('#splitMoveGrid .table-box.selected').forEach((b) => b.classList.remove('selected'));
    el.classList.add('selected');
    splitMoveSelected = num;

    const sel = document.getElementById('split-move-selection');
    const occ = el.dataset.occupied === '1';
    if (sel) {
      sel.classList.remove('muted');
      sel.textContent = occ
        ? `Gabung ke meja ${num} (akan masuk split baru: "baru").`
        : `Pindah ke meja ${num} (meja kosong).`;
    }
    const err = document.getElementById('split-move-error');
    if (err) err.textContent = '';
    const btn = document.getElementById('split-move-confirm');
    if (btn) btn.disabled = false;
  }

  async function confirmSplitMove() {
    if (!splitMoveSelected || !splitMoveGroup) return;
    const sessionId = window.SESSION_ID || document.body?.dataset?.sessionId;
    const err = document.getElementById('split-move-error');
    try {
      const res = await fetch('/split/move_group_to_table', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          group: splitMoveGroup,
          to_table: splitMoveSelected,
        }),
      });
      const j = await res.json();
      if (j.status !== 'success') {
        if (err) err.textContent = j.message || 'Gagal pindah split';
        return;
      }
      closeSplitMoveModal();
      if (j.redirect) {
        window.location.href = j.redirect;
        return;
      }
      await window.POS.requestSessionState();
    } catch (e) {
      if (err) err.textContent = 'Jaringan bermasalah, coba lagi.';
    }
  }

  window.openSplitMoveModal = openSplitMoveModal;
  window.closeSplitMoveModal = closeSplitMoveModal;
  window.filterSplitMoveFloor = filterSplitMoveFloor;
  window.selectSplitMoveTarget = selectSplitMoveTarget;
  window.confirmSplitMove = confirmSplitMove;

  function normalizeMeta() {
    let meta = Array.isArray(window.SPLIT_META) ? window.SPLIT_META.slice() : [];
    if (!meta.length) {
      const labels = Array.isArray(window.SPLIT_LABELS) ? window.SPLIT_LABELS : [];
      meta = labels.map((k) => ({ key: String(k).trim(), name: '' }));
    }
    meta = meta
      .map((m) => {
        if (!m) return null;
        const key = String(m.key || m.label || m.id || m.group || '').trim();
        if (!key || !/^\d+$/.test(key)) return null;
        return { key, name: String(m.name || m.title || '').trim() };
      })
      .filter(Boolean)
      .sort((a, b) => Number(a.key) - Number(b.key));
    return meta;
  }

  function hasSplits(meta) {
    return Array.isArray(meta) && meta.length > 0;
  }

  function friendlyName(metaEntry) {
    const name = (metaEntry?.name || '').trim();
    if (name) return name;
    return `Bill ${metaEntry?.key || ''}`.trim();
  }

  function updateActiveGlobals(key, labelName) {
    activeGroup = key;
    window.ACTIVE_BILL_GROUP = key;
    window.CURRENT_GROUP = key;
    window.CURRENT_GROUP_FOR_BILL = key;
    window.BILL_GROUP = key;
    try { localStorage.setItem('table_group_key', key); } catch (_) {}

    const label = document.getElementById('grp-name');
    if (label) label.textContent = labelName || friendlyName({ key });
  }

  function setSplitBarVisible(show) {
    const bar = document.getElementById('split-view-bar');
    if (bar) bar.style.display = show ? 'flex' : 'none';
  }

  function setPaidToggleVisible(hasPaid) {
    const toolbar = document.getElementById('split-board-toolbar');
    const btn = document.getElementById('btn-show-paid');
    if (toolbar) toolbar.style.display = hasPaid ? 'flex' : 'none';
    if (btn) {
      btn.textContent = showPaidSplits ? 'Sembunyikan Bill Lunas' : 'Tampilkan Bill Lunas';
    }
  }

  window.getActiveBillGroup = function () { return activeGroup; };

  function setHostGroup(groupKey) {
    const host = window.POS && window.POS.__pagedOrders;
    if (!host) return;
    if (typeof host.setGroup === 'function') {
      host.setGroup(groupKey);
      return;
    }
    if (typeof host.setFilter === 'function') {
      host.setFilter({ group: groupKey });
      return;
    }
    if (typeof host.render === 'function') {
      host.group = groupKey;
      host.render();
    }
  }

  function enterSingleView(groupKey, labelName) {
    boardCollapsed = true;
    clearSelection();
    updateActiveGlobals(groupKey, labelName);
    document.body.classList.remove('split-board-active');
    document.body.classList.add('split-board-collapsed');
    board.style.display = 'none';
    setSplitBarVisible(true);
    setHostGroup(groupKey);
  }

  function exitSingleView() {
    boardCollapsed = false;
    document.body.classList.remove('split-board-collapsed');
    render();
  }

  function isPaidGroup(key) {
    const status = window.GROUP_STATUS || {};
    const info = status ? status[key] : null;
    return !!(info && info.all_paid);
  }

  function openSplitRenameModal(metaEntry) {
    const modal = document.getElementById('split-rename-modal');
    const input = document.getElementById('split-rename-input');
    const err = document.getElementById('split-rename-err');
    if (!modal || !input) return;
    renameKey = metaEntry?.key || '';
    input.value = metaEntry?.name || '';
    if (err) err.textContent = '';
    modal.style.display = 'flex';
    try { input.focus(); input.select && input.select(); } catch (_) {}
  }

  window.closeSplitRenameModal = function () {
    const modal = document.getElementById('split-rename-modal');
    if (modal) modal.style.display = 'none';
    renameKey = null;
  };

  window.saveSplitRename = async function () {
    const err = document.getElementById('split-rename-err');
    if (err) err.textContent = '';
    if (!renameKey) return;
    const input = document.getElementById('split-rename-input');
    const next = (input?.value || '').trim();
    try {
      const sid = window.SESSION_ID || document.body?.dataset?.sessionId;
      const j = await postJSON(`/split/meta/${encodeURIComponent(sid)}`, {
        key: renameKey,
        name: next
      });
      if (j.meta) window.SPLIT_META = j.meta;
      if (j.labels) window.SPLIT_LABELS = j.labels;
      window.closeSplitRenameModal();
      render();
    } catch (err2) {
      if (err) err.textContent = err2.message || 'Gagal menyimpan nama split';
    }
  };

  function ensureActive(meta) {
    const saved = (() => {
      try { return localStorage.getItem('table_group_key'); } catch (_) { return null; }
    })();
    const keys = meta.map(m => m.key);
    let target = saved && keys.includes(saved) ? saved : activeGroup;
    if (!target || !keys.includes(target)) target = keys[0];
    const entry = meta.find(m => m.key === target) || { key: target };
    updateActiveGlobals(target, friendlyName(entry));
  }

  function ensureQtyModal() {
    let m = document.getElementById('qty-modal');
    if (m) return m;
    m = document.createElement('div');
    m.id = 'qty-modal';
    m.className = 'modal-overlay';
    m.style.display = 'none';
    m.innerHTML = `
      <div class="modal-card" style="max-width:420px;">
        <div class="modal-header">
          <h3 id="qty-title">Jumlah</h3>
          <button type="button" class="modal-close" onclick="closeQtyModal()">x</button>
        </div>
        <div class="modal-body" style="text-align:center;">
          <label id="qty-label" for="qty-input">Masukkan jumlah</label>
          <input id="qty-input" type="text" inputmode="decimal" data-numpad="true"
                 style="width:140px; height:48px; font-size:20px; text-align:center; display:block; margin:8px auto;">
          <div id="qty-err" style="color:#c00; text-align:center; margin-top:6px;"></div>
        </div>
        <div class="modal-footer" style="justify-content:center;">
          <button type="button" class="action-button" onclick="__qtyModalOk()">Konfirmasi</button>
          <button type="button" class="action-button outline" onclick="closeQtyModal()">Batal</button>
        </div>
      </div>`;
    document.body.appendChild(m);
    return m;
  }

  let __qtyCtx = null;

  window.openQtyModal = function ({ title, label, initial, maxQty, onConfirm }) {
    ensureQtyModal();
    __qtyCtx = { maxQty: Number(maxQty ?? Infinity), onConfirm };
    document.getElementById('qty-title').textContent = title || 'Jumlah';
    document.getElementById('qty-label').textContent = label || 'Masukkan jumlah';
    const inp = document.getElementById('qty-input');
    inp.value = (initial != null) ? String(initial) : '';
    document.getElementById('qty-err').textContent = '';
    const modal = document.getElementById('qty-modal');
    modal.style.display = 'flex';
    try { inp.focus(); inp.select && inp.select(); } catch (_) {}
  };

  window.closeQtyModal = function () {
    const modal = document.getElementById('qty-modal');
    if (modal) modal.style.display = 'none';
    __qtyCtx = null;
  };

  window.__qtyModalOk = function () {
    if (!__qtyCtx) return window.closeQtyModal();
    const err = document.getElementById('qty-err');
    const raw = (document.getElementById('qty-input').value || '').replace(',', '.');
    const val = parseFloat(raw);
    if (!(val > 0)) { err.textContent = 'Jumlah tidak valid'; return; }
    if (val > __qtyCtx.maxQty) { err.textContent = `Maks ${qfmt(__qtyCtx.maxQty)}`; return; }
    if (Math.round(val * 2) !== val * 2) { err.textContent = 'Gunakan kelipatan 0.5'; return; }
    const cb = __qtyCtx.onConfirm;
    window.closeQtyModal();
    try { cb && cb(val); } catch (_) {}
  };

  async function postJSON(url, payload) {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      redirect: 'follow'
    });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); } catch (e) {
      console.error('Non-JSON response from', url, { status: res.status, body: text });
      throw new Error(`Non-JSON (${res.status}) from ${url}`);
    }
    if (!res.ok) {
      const msg = data?.message || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return data;
  }

  function getRows() {
    return Array.isArray(window.ORDER_ROWS) ? window.ORDER_ROWS : [];
  }

  function getQty(r) {
    if (r.qty_effective != null) return Number(r.qty_effective) || 0;
    if (r.net_qty != null) return Number(r.net_qty) || 0;
    return Number(r.qty || 0) || 0;
  }

  function getSubtotal(r) {
    if (r.subtotal != null) return Number(r.subtotal) || 0;
    if (r.total_price != null) return Number(r.total_price) || 0;
    const unit = Number(r.price || r.unit_price || 0);
    return Math.round(getQty(r) * unit);
  }

  function resolveGroupKey(row, meta) {
    const g = rowGroup(row);
    if (g !== 'main') return g;
    return meta[0]?.key || 'main';
  }

  function selectRow(row, groupKey, rowEl) {
    if (selected && selected.el) selected.el.classList.remove('is-selected');
    selected = { row, groupKey, el: rowEl };
    if (rowEl) rowEl.classList.add('is-selected');
    updateActiveGlobals(groupKey);
  }

  function clearSelection() {
    if (selected && selected.el) selected.el.classList.remove('is-selected');
    selected = null;
  }

  async function moveSelectedTo(destGroup) {
    if (!selected || !destGroup || selected.groupKey === destGroup) {
      updateActiveGlobals(destGroup || activeGroup);
      return;
    }

    const row = selected.row;
    const maxQty = getQty(row);
    if (!(maxQty > 0)) return;

    window.openQtyModal({
      title: `Pindahkan ke ${friendlyName({ key: destGroup })}`,
      label: `Berapa dari "${row.item_name || row.name || ''}"? (maks ${qfmt(maxQty)})`,
      initial: qfmt(maxQty),
      maxQty,
      onConfirm: async (moveQty) => {
        try {
          const ids = Array.isArray(row.ids) && row.ids.length ? row.ids : (row.id != null ? [row.id] : []);
          const j = await postJSON('/split/move', {
            session_id: window.SESSION_ID || document.body?.dataset?.sessionId,
            to_group: destGroup,
            qty: moveQty,
            source_ids: ids
          });
          if (j.status !== 'ok') throw new Error(j.message || 'Gagal memindahkan item');
          clearSelection();
          const currentMeta = normalizeMeta();
          const entry = currentMeta.find(m => m.key === destGroup) || { key: destGroup };
          updateActiveGlobals(destGroup, friendlyName(entry));
          await window.POS.requestSessionState();
        } catch (e) {
          alert(e.message || 'Gagal memindahkan item');
        }
      }
    });
  }

  function buildColumn(metaEntry, meta, rows, groupSubtotals) {
    const groupKey = metaEntry.key;
    const name = friendlyName(metaEntry);
    const readOnly = window.READ_ONLY === true;
    const paid = isPaidGroup(groupKey);

    const col = document.createElement('div');
    col.className = 'split-col' + (groupKey === activeGroup ? ' is-active' : '');
    col.dataset.group = groupKey;

    const head = document.createElement('div');
    head.className = 'split-col-head';
    head.innerHTML = `
      <div class="split-col-title">
        <span class="split-col-name">${esc(name)}</span>
        <button type="button" class="split-rename" title="Ubah nama">Edit</button>
        <button type="button" class="split-move" title="Pindah split ke meja lain">Pindah</button>
      </div>
      <div class="split-col-tags">
        <span class="split-col-key">#${esc(groupKey)}</span>
        <span class="split-col-active" style="display:${groupKey === activeGroup ? 'inline-flex' : 'none'};">AKTIF</span>
      </div>
    `;

    const renameBtn = head.querySelector('.split-rename');
    const moveBtn = head.querySelector('.split-move');
    if (readOnly || paid) {
      renameBtn.disabled = true;
      renameBtn.style.opacity = '0.5';
      renameBtn.style.cursor = 'not-allowed';
      if (moveBtn) {
        moveBtn.disabled = true;
        moveBtn.style.opacity = '0.5';
        moveBtn.style.cursor = 'not-allowed';
      }
    } else {
      renameBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        openSplitRenameModal(metaEntry);
      });
      moveBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        openSplitMoveModal(groupKey, name);
      });
    }
    if (paid) {
      col.classList.add('is-paid');
    }

    head.addEventListener('click', (e) => {
      if (e.target.closest('.split-rename')) return;
      e.stopPropagation();
      enterSingleView(groupKey, name);
    });

    const body = document.createElement('div');
    body.className = 'split-col-body';

    const table = document.createElement('table');
    table.className = 'order-table split-table';
    table.innerHTML = `
      <thead>
        <tr>
          <th>Item</th>
          <th>Qty</th>
          <th>Harga</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;

    const tbody = table.querySelector('tbody');
    const groupRows = rows.filter((r) => resolveGroupKey(r, meta) === groupKey);

    if (!groupRows.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 3;
      td.innerHTML = '<em>Belum ada pesanan</em>';
      tr.appendChild(td);
      tbody.appendChild(tr);
    } else {
      groupRows.forEach((r) => {
        const tr = document.createElement('tr');
        tr.className = 'split-row';
        if (r.wasPrinted || r.print_state === 'printed' || r.print_state === 'printed_all') {
          tr.classList.add('row-print-printed');
        }
        if (r.hasPending || r.print_state === 'printed_partial' || r.print_state === 'partial') {
          tr.classList.add('row-print-partial');
        }

        const name = r.item_name || r.name || '';
        const note = (r.note || '').trim();
        const sauce = (r.sauce || '').trim();
        tr.innerHTML = `
          <td>
            <div class="name-cell">
              <div class="nm">${esc(name)}</div>
              ${sauce ? `<div class="nm-note">${esc(sauce)}</div>` : ''}
              ${note ? `<div class="nm-note"><em>${esc(note)}</em></div>` : ''}
            </div>
          </td>
          <td class="num">${esc(qfmt(getQty(r)))}</td>
          <td class="num">${esc(fmtRp(getSubtotal(r)))}</td>
        `;
        if (!readOnly && !paid) {
          tr.addEventListener('click', (e) => {
            e.stopPropagation();
            if (selected && selected.groupKey !== groupKey) {
              moveSelectedTo(groupKey);
              return;
            }
            selectRow(r, groupKey, tr);
          });
        }
        tbody.appendChild(tr);
      });
    }

    body.appendChild(table);

    let subtotal = (groupSubtotals && groupSubtotals[groupKey] != null)
      ? Number(groupSubtotals[groupKey] || 0)
      : groupRows.reduce((a, r) => a + getSubtotal(r), 0);
    if (groupKey === meta[0]?.key && groupSubtotals && groupSubtotals.main) {
      subtotal += Number(groupSubtotals.main || 0);
    }
    const servicePct = Number(SERVICE_PERCENT || 0) / 100;
    const service = Math.round(subtotal * servicePct);
    const taxBase = TAX_ON_SERVICE ? (subtotal + service) : subtotal;
    const tax = Math.round(taxBase * (TAX_PERCENT / 100));
    const total = subtotal + service + tax;

    const foot = document.createElement('div');
    foot.className = 'split-col-foot';
    foot.innerHTML = `
      <div class="split-foot-row"><span>Subtotal</span><strong>${esc(fmtRp(subtotal))}</strong></div>
      ${service ? `<div class="split-foot-row"><span>Service</span><strong>${esc(fmtRp(service))}</strong></div>` : ''}
      <div class="split-foot-row"><span>Pajak</span><strong>${esc(fmtRp(tax))}</strong></div>
      <div class="split-foot-row split-foot-total"><span>Total</span><strong>${esc(fmtRp(total))}</strong></div>
    `;

    if (paid) {
      const badge = document.createElement('span');
      badge.className = 'split-col-paid';
      badge.textContent = 'PAID';
      head.querySelector('.split-col-tags')?.appendChild(badge);
    }

    col.appendChild(head);
    col.appendChild(body);
    col.appendChild(foot);

    col.addEventListener('click', (e) => {
      if (e.target.closest('.split-rename')) return;
      if (e.target.closest('.split-col-head')) return;
      if (e.target.closest('tbody tr')) return;
      if (!readOnly && !paid && selected && selected.groupKey !== groupKey) {
        moveSelectedTo(groupKey);
        return;
      }
      if (!paid) {
        updateActiveGlobals(groupKey);
        render();
      }
    });

    return col;
  }

  function render() {
    const metaAll = normalizeMeta();
    if (!hasSplits(metaAll)) {
      boardCollapsed = false;
      board.innerHTML = '';
      board.style.display = 'none';
      document.body.classList.remove('split-board-active');
      document.body.classList.remove('split-board-collapsed');
      setSplitBarVisible(false);
      setPaidToggleVisible(false);
      return;
    }

    const paidGroups = metaAll.filter(m => isPaidGroup(m.key));
    const shouldShowPaid = showPaidSplits || paidGroups.length === 0;
    let metaVisible = shouldShowPaid ? metaAll : metaAll.filter(m => !isPaidGroup(m.key));
    if (!metaVisible.length) metaVisible = metaAll;
    const metaForActive = boardCollapsed ? metaAll : (metaVisible.length ? metaVisible : metaAll);
    ensureActive(metaForActive);
    clearSelection();

    const rows = getRows();
    const groupSubtotals = window.GROUP_SUBTOTALS || {};

    board.innerHTML = '';
    const frag = document.createDocumentFragment();
    const renderMeta = metaVisible.length ? metaVisible : metaAll;
    renderMeta.forEach((m) => {
      frag.appendChild(buildColumn(m, metaAll, rows, groupSubtotals));
    });
    board.appendChild(frag);

    if (boardCollapsed) {
      board.style.display = 'none';
      document.body.classList.remove('split-board-active');
      setSplitBarVisible(true);
      setPaidToggleVisible(false);
      return;
    }

    setSplitBarVisible(false);
    setPaidToggleVisible(paidGroups.length > 0);
    document.body.classList.remove('split-board-collapsed');
    document.body.classList.add('split-board-active');
    board.style.display = 'grid';
    board.style.setProperty('--split-cols', String(renderMeta.length));
  }

  function hookSessionUpdates() {
    const POS = (window.POS = window.POS || {});
    const orig = POS.requestSessionState;
    if (typeof orig === 'function' && !orig.__wrappedForSplitBoard) {
      POS.requestSessionState = async function (...args) {
        const out = await orig.apply(this, args);
        try { render(); } catch (_) {}
        return out;
      };
      POS.requestSessionState.__wrappedForSplitBoard = true;
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    hookSessionUpdates();
    const backBtn = document.getElementById('btn-back-split');
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        exitSingleView();
      });
    }
    const paidBtn = document.getElementById('btn-show-paid');
    if (paidBtn) {
      paidBtn.addEventListener('click', () => {
        showPaidSplits = !showPaidSplits;
        render();
      });
    }
    render();
  });
})();
