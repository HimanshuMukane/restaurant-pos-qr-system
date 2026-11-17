(() => {
  if (window.SPLIT_BOARD_MODE) return;
  // --- helpers ---------------------------------------------------------------
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, m => (
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]
  ));
  const fmtRp = (n) => `Rp ${Number(n || 0).toLocaleString('id-ID')}`;
  const isPaged = () => !!(window.POS && window.POS.__pagedOrders);
  const qfmt  = (q) => {
    const n = Number(q || 0);
    return (Math.round(n * 10) % 10 === 0) ? String(Math.round(n)) : n.toFixed(1);
  };
  const isMain = (v) => v == null || String(v).trim() === '' || String(v).toLowerCase() === 'main';
  const gkey   = (row) => isMain(row.bill_group) ? 'main' : String(row.bill_group);
  const bool = (v) => (typeof v === 'boolean' ? v : (typeof v === 'string' ? (v.toLowerCase() === 'true' || v === '1') : !!v));
  const splitMetaName = (label) => {
    const meta = Array.isArray(window.SPLIT_META) ? window.SPLIT_META : [];
    const key = String(label ?? '').trim();
    if (!key) return '';
    const hit = meta.find(m => String(m.key ?? m.label ?? m.id ?? m.group ?? '').trim() === key);
    const name = (hit?.name ?? hit?.title ?? '').toString().trim();
    return name || '';
  };
  const BILLING_CFG = (window.POS_CONFIG && window.POS_CONFIG.billing) ? window.POS_CONFIG.billing : {};
  const SERVICE_PERCENT = Number(BILLING_CFG.service_percent ?? window.SERVICE_PCT ?? 5);
  const TAX_PERCENT = Number(BILLING_CFG.tax_percent ?? window.TAX_PERCENT ?? 10);
  const TAX_ON_SERVICE = bool(BILLING_CFG.tax_on_service ?? window.TAX_ON_SERVICE);

  const getRowIds = (r) => {
    if (Array.isArray(r?.ids) && r.ids.length) {
      return r.ids.map(n => Number(n)).filter(Number.isFinite);
    }
    if (r && r.id != null) {
      const n = Number(r.id);
      return Number.isFinite(n) ? [n] : [];
    }
    return [];
  };

  function deriveLabels() {
    const SL = window.SPLIT_LABELS;

    if (Array.isArray(SL)) {
      const arr = SL.map(String).filter(Boolean)
        .sort((a,b) => {
          const na = +a, nb = +b;
          if (Number.isFinite(na) && Number.isFinite(nb)) return na - nb;
          return String(a).localeCompare(String(b), undefined, { numeric: true });
        });
      if (arr.length) return arr;
    }

    // If server supplies an object: { "1": true, "2": true } or similar
    if (SL && typeof SL === 'object') {
      const keys = Object.keys(SL).filter(Boolean)
        .sort((a,b) => String(a).localeCompare(String(b), undefined, { numeric: true }));
      if (keys.length) return keys;
    }

    // Fallback: infer from subtotal map, ignore 'main'
    const subs = window.GROUP_SUBTOTALS || {};
    return Object.keys(subs)
      .filter(k => k !== 'main')
      .sort((a,b) => String(a).localeCompare(String(b), undefined, { numeric: true }));
  }

  // ---- compat getters (support old & new shapes) ---------------------------
  const getName = (r) => r.item_name ?? r.name ?? "";
  const getEffQty = (r) => {
    if (r.qty_effective != null) return Number(r.qty_effective) || 0;
    const printed = Number(r.printed_effective || 0);
    const pending = Number(r.pending_qty || 0);
    const combo = printed + pending;
    if (combo > 0) return combo;
    return Number(r.qty || 0); // last resort
  };
  // raw DB qty – use this for split moves so it matches backend checks
  const getRawQty = (r) => Number(r.qty || r.qty_effective || 0) || 0;

  const getSubtotal = (r) => (
    r.subtotal ?? r.total_price ?? Math.round(getEffQty(r) * (r.price || 0))
  );

  const wasPrinted = (r) =>
    !!(r.wasPrinted || r.print_state === 'printed_all' || r.print_state === 'printed');
  const hasPending = (r) =>
    !!(r.hasPending || r.print_state === 'printed_partial' || r.print_state === 'partial');

  function changeGroup(delta) {
    if (!GROUPS.length) return;
    idx = (idx + delta + GROUPS.length) % GROUPS.length;
    try { localStorage.setItem('table_group_key', currentGroup()); } catch(_){}
    render(); // in paged mode, render() calls applyGroupToHostRenderer() then returns
  }

  // --- state -----------------------------------------------------------------
  let ROWS = Array.isArray(window.ORDER_ROWS) ? window.ORDER_ROWS : [];
  let LABELS = deriveLabels();
  let GROUPS = ['all', ...LABELS];   // 'all' means ALL rows (main + all split groups)
  let idx = 0;

  // --- dom refs --------------------------------------------------------------
  const $ = (id) => document.getElementById(id);
  let __lastHostGroup = null;

  // --- bridge to host paged orders renderer ----------------------------------
  function applyGroupToHostRenderer(g) {
    if (!isPaged() || !window.POS || !window.POS.__pagedOrders) return;

    const host = window.POS.__pagedOrders;
    if (__lastHostGroup === g) return;
    __lastHostGroup = g;

    if (typeof host.setGroup === 'function') {
      host.setGroup(g);                // preferred: host owns rendering
    } else if (typeof host.setFilter === 'function') {
      host.setFilter({ group: g });    // alt API
    } else {
      // Fallback: set prop and try to force a render if host exposes it
      host.group = g;
      if (typeof host.render === 'function') host.render();
    }
  }

  // Re-apply the current group after any realtime refresh
  (function wrapRequestSessionState(){
    const POS = (window.POS = window.POS || {});
    const orig = POS.requestSessionState;
    if (typeof orig === 'function' && !orig.__wrappedForSplit) {
      POS.requestSessionState = async function(...args){
        const out = await orig.apply(this, args);
        try { ensureOrderBodyOwnership(); } catch(_) {}
        try { applyGroupToHostRenderer(currentGroup()); } catch(_) {}
        return out;
      };
      POS.requestSessionState.__wrappedForSplit = true;
    }
  })();

  const friendly = (g) => {
    if (g === 'all') return 'Semua';
    const name = splitMetaName(g);
    return name || `Bill ${g}`;
  };
  const currentGroup = () => GROUPS[idx] || 'all';

  // ====== RIGHT-PANEL MODE (ALL vs Split) ====================================
  function hasSplits() {
    const SL = window.SPLIT_LABELS;
    if (!SL) return false;
    const keys = Array.isArray(SL) ? SL : Object.keys(SL || {});
    return keys.filter(Boolean).length > 0;
  }
  function isAllView() {
    const g = currentGroup();
    return g === 'all';
  }
  function buildSplitChips() {
    const cont = $('split-chip-row');
    if (!cont) return;
    cont.innerHTML = '';

    const SL = window.SPLIT_LABELS;
    const keys = Array.isArray(SL) ? SL : Object.keys(SL || {});
    const cur = currentGroup();

    keys.forEach((k) => {
      const label = String(k).trim();
      if (!label) return;

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'chip';
      const name = splitMetaName(label);
      btn.textContent = name || ('Split ' + label);
      btn.dataset.group = label;
      if (cur === label) btn.classList.add('active');

      btn.addEventListener('click', () => {
        const newIdx = GROUPS.indexOf(label);
        if (newIdx >= 0) idx = newIdx;
        try { localStorage.setItem('table_group_key', currentGroup()); } catch(_){}
        const gname = $('grp-name');
        if (gname) gname.textContent = friendly(label);
        render();
        if (typeof window.refreshDpButton === 'function') window.refreshDpButton();
      });

      cont.appendChild(btn);
    });
  }

  function updateRightPanelMode() {
    // try several common containers for the menu side
    const menuWrap =
        document.getElementById('menu-rail') ||
        document.querySelector('.menu-rail, [data-role="menu-rail"]') ||
        document.querySelector('#menu-grid')?.closest('.menu, .menu-pane, .right-col, [data-role="menu"]') ||
        document.querySelector('#menu-grid')?.parentElement;

    // try several common containers for the split side
    const splitSide =
        document.getElementById('split-side') ||
        document.querySelector('.split-side, [data-role="split-side"]');

    if (!menuWrap || !splitSide) return;

    const split = hasSplits() && !isAllView();

    document.body.classList.toggle('is-split-view', split);
    splitSide.classList.toggle('hidden', !split);
    menuWrap.classList.toggle('hidden',  split);
    splitSide.style.display = split ? '' : 'none';
    menuWrap.style.display  = split ? 'none' : '';
  }

  // ---------- Generic qty modal (reusable) ----------
  let __qtyCtx = null;

  function ensureQtyModal(){
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
          <button type="button" class="modal-close" onclick="closeQtyModal()">×</button>
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
    try { inp.focus(); inp.select && inp.select(); } catch (_){}
  };

  window.closeQtyModal = function (){
    const modal = document.getElementById('qty-modal');
    if (modal) modal.style.display = 'none';
    __qtyCtx = null;
  };

  window.__qtyModalOk = function (){
    if (!__qtyCtx) return closeQtyModal();
    const err = document.getElementById('qty-err');
    const raw = (document.getElementById('qty-input').value || '').replace(',', '.');
    const val = parseFloat(raw);
    if (!(val > 0)) { err.textContent = 'Jumlah tidak valid'; return; }
    if (val > __qtyCtx.maxQty) { err.textContent = `Maks ${qfmt(__qtyCtx.maxQty)}`; return; }
    if (Math.round(val*2) !== val*2) { err.textContent = 'Gunakan kelipatan 0.5'; return; }
    const cb = __qtyCtx.onConfirm;
    closeQtyModal();
    try { cb && cb(val); } catch(_){}
  };

  let __spl_painting = false;
  let __spl_observer = null;

  function ensureOrderBodyOwnership() {
    const tbody = document.getElementById('order-body');
    if (!tbody) return;
    if (__spl_observer) __spl_observer.disconnect();

    if (isPaged()) return;
    __spl_observer = new MutationObserver(() => {
      if (__spl_painting) return;           // ignore our own writes
      const g = currentGroup();
      if (tbody.__splitRenderedFor !== g) render();
    });

    __spl_observer.observe(tbody, { childList: true });
  }

  // --- rendering -------------------------------------------------------------
  function render() {
    const $ = (id) => document.getElementById(id);
    ROWS   = Array.isArray(window.ORDER_ROWS) ? window.ORDER_ROWS : [];
    LABELS = deriveLabels();
    GROUPS = ['all', ...LABELS];
    if (!GROUPS.length) GROUPS = ['all'];
    if (idx >= GROUPS.length) idx = 0;

    const grpNameEl     = $('grp-name');
    const destNameEl    = $('dest-group-name');
    const bodyEl        = $('order-body');
    const ungroupedWrap = $('ungrouped-section');
    const ungroupedBody = $('ungrouped-body');
    const subtotalCell  = $('subtotal-cell');
    const grandCell     = $('grandtotal-cell');

    const g = currentGroup();

    window.VISIBLE_GROUP = g;
    window.CURRENT_GROUP = g;
    window.CURRENT_GROUP_FOR_BILL = (g === 'all') ? 'main' : g;
    window.BILL_GROUP = window.CURRENT_GROUP_FOR_BILL;

    if (grpNameEl) grpNameEl.textContent = friendly(g);

    applyGroupToHostRenderer(g);
    updateRightPanelMode();

    const useHost = isPaged() && window.POS && window.POS.__pagedOrders;
    if (useHost) {
      if (bodyEl) bodyEl.__splitRenderedFor = g;
      const subs = window.GROUP_SUBTOTALS || {};
      let subtotal = 0;
      if (g === 'all') {
        const keys = Object.keys(subs);
        subtotal = keys.length ? keys.reduce((a,k)=> a + (Number(subs[k]||0)), 0) : 0;
      } else {
        subtotal = Number(subs[g] || 0);
      }
      const service = Math.round(subtotal * (SERVICE_PERCENT / 100));
      const taxBase = TAX_ON_SERVICE ? (subtotal + service) : subtotal;
      const tax     = Math.round(taxBase * (TAX_PERCENT / 100));
      const grand   = subtotal + service + tax;
      if (subtotalCell) subtotalCell.textContent = fmtRp(subtotal);
      if (grandCell)    grandCell.textContent    = fmtRp(grand);

      if (g !== 'all') {
        if (destNameEl) destNameEl.textContent = friendly(g);
        if (ungroupedBody) {
          const frag = document.createDocumentFragment();
          ungroupedBody.innerHTML = '';
          const mainRows = ROWS.filter(r => gkey(r) === 'main');
          if (!mainRows.length) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 3;
            td.innerHTML = '<em>Tidak ada item ungrouped</em>';
            tr.appendChild(td);
            frag.appendChild(tr);
          } else {
            mainRows.forEach(r => {
              const tr = document.createElement('tr');
              tr.innerHTML = `
                <td>
                  ${esc(getName(r))}
                  ${r.sauce ? `<br><small>${esc(r.sauce)}</small>` : ''}
                  ${r.note  ? `<br><small><em>${esc(r.note)}</em></small>` : ''}
                </td>
                <td>${qfmt(getEffQty(r))}</td>
                <td><button class="move-btn" type="button">Masuk</button></td>
              `;
              tr.querySelector('.move-btn')?.addEventListener('click', () => moveFromMainPrompt(r));
              frag.appendChild(tr);
            });
          }
          ungroupedBody.appendChild(frag);
        }
        if (ungroupedWrap) ungroupedWrap.classList.remove('hidden');
      } else {
        if (ungroupedWrap) ungroupedWrap.classList.add('hidden');
      }

      if (typeof window.refreshDpButton === 'function') window.refreshDpButton();
      if (typeof window.updatePriceBreakdown === 'function') window.updatePriceBreakdown();

      return; // host owns tbody
    }

    // non-paged: Filter rows for current view
    const rows = (g === 'all') ? ROWS.slice() : ROWS.filter(r => gkey(r) === g);

    const scrollHost = document.querySelector('.order-table-wrap');
    const prevTop = scrollHost ? scrollHost.scrollTop : 0;

    // Build table body
    if (bodyEl) {
      const frag = document.createDocumentFragment();
      __spl_painting = true;
      try {
        bodyEl.innerHTML = '';

        if (!rows.length) {
          const tr = document.createElement('tr');
          const td = document.createElement('td');
          td.colSpan = 3;
          td.innerHTML = '<em>Belum ada pesanan</em>';
          tr.appendChild(td);
          frag.appendChild(tr);
        } else {
          rows.forEach(r => {
            const tr = document.createElement('tr');
            if (wasPrinted(r)) tr.classList.add('row-print-printed');
            if (hasPending(r)) tr.classList.add('row-print-partial');
            if (r.all_paid)    tr.classList.add('is-paid');

            const actionsHtml = (g !== 'all')
              ? `<div class="row-actions" style="margin-top:6px;">
                  <button type="button" class="mini-btn ungroup-btn">Keluarkan</button>
                </div>`
              : '';

            tr.innerHTML = `
              <td>
                ${esc(getName(r))}
                ${r.sauce ? `<br><small>${esc(r.sauce)}</small>` : ''}
                ${r.note  ? `<br><small><em>${esc(r.note)}</em></small>` : ''}
                ${r.all_paid ? `<div style="margin-top:4px;"><span class="badge on">PAID</span></div>` : ''}
                ${actionsHtml}
              </td>
              <td>${qfmt(getEffQty(r))}</td>
              <td>${fmtRp(getSubtotal(r))}</td>
            `;
            tr.dataset.ids     = JSON.stringify(r.ids || (r.id ? [r.id] : []));
            tr.dataset.name    = getName(r) || '';
            tr.dataset.note    = r.note || '';
            tr.dataset.station = (r.station || r.dept || r.category || '').toString().toLowerCase();

            if (g !== 'all') {
              tr.querySelector('.ungroup-btn')?.addEventListener('click', () => unassignFromGroupPrompt(r));
            }
            frag.appendChild(tr);
          });
        }

        bodyEl.appendChild(frag);
        bodyEl.__splitRenderedFor = g;
      } finally {
        __spl_painting = false;
      }
      if (scrollHost) scrollHost.scrollTop = prevTop;
    }

    // Totals (prefer server GROUP_SUBTOTALS, else compute from visible rows)
    const subs = window.GROUP_SUBTOTALS || {};
    let subtotal;
    if (g === 'all') {
      const keys = Object.keys(subs);
      subtotal = keys.length
        ? keys.reduce((a,k)=> a + (Number(subs[k]||0)), 0)
        : rows.reduce((a, r) => a + getSubtotal(r), 0);
    } else {
      subtotal = (subs[g] ?? rows.reduce((a, r) => a + getSubtotal(r), 0));
    }
    const afterDisc = subtotal;
    const service   = Math.round(afterDisc * (SERVICE_PERCENT / 100));
    const taxBase   = TAX_ON_SERVICE ? (afterDisc + service) : afterDisc;
    const tax       = Math.round(taxBase * (TAX_PERCENT / 100));
    const grand     = afterDisc + service + tax;

    if (subtotalCell) subtotalCell.textContent = fmtRp(subtotal);
    if (grandCell)    grandCell.textContent    = fmtRp(grand);

    // Ungrouped list (only when viewing a specific split)
    if (g !== 'all') {
      if (destNameEl) destNameEl.textContent = friendly(g);
      if (ungroupedBody) {
        const frag = document.createDocumentFragment();
        ungroupedBody.innerHTML = '';
        const mainRows = ROWS.filter(r => gkey(r) === 'main');

        if (!mainRows.length) {
          const tr = document.createElement('tr');
          const td = document.createElement('td');
          td.colSpan = 3;
          td.innerHTML = '<em>Tidak ada item ungrouped</em>';
          tr.appendChild(td);
          frag.appendChild(tr);
        } else {
          mainRows.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>
                ${esc(getName(r))}
                ${r.sauce ? `<br><small>${esc(r.sauce)}</small>` : ''}
                ${r.note  ? `<br><small><em>${esc(r.note)}</em></small>` : ''}
              </td>
              <td>${qfmt(getEffQty(r))}</td>
              <td><button class="move-btn" type="button">Masuk</button></td>
            `;
            tr.querySelector('.move-btn')?.addEventListener('click', () => moveFromMainPrompt(r));
            frag.appendChild(tr);
          });
        }

        ungroupedBody.appendChild(frag);
      }
      if (ungroupedWrap) ungroupedWrap.classList.remove('hidden');
    } else {
      if (ungroupedWrap) ungroupedWrap.classList.add('hidden');
    }

    if (typeof window.refreshDpButton === 'function') window.refreshDpButton();
    if (typeof window.updatePriceBreakdown === 'function') window.updatePriceBreakdown();
  }

  window.POS = window.POS || {};
  if (typeof window.POS._onGroupChanged !== 'function') {
    window.POS._onGroupChanged = function(key){
      const k = String(key || 'all');
      const i = GROUPS.indexOf(k);
      idx = (i >= 0 ? i : 0);
      __lastHostGroup = k;
      render();
    };
  }

  // --- fetch helper ----------------------------------------------------------
  async function postJSON(url, payload) {
    const res = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload),
      redirect: 'follow'
    });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); }
    catch (e) {
      console.error('Non-JSON response from', url, {
        status: res.status,
        headers: Object.fromEntries(res.headers.entries()),
        body: text
      });
      throw new Error(`Non-JSON (${res.status}) from ${url}`);
    }
    return data;
  }

  async function reloadPreservingGroup(){
    try { localStorage.setItem('table_group_key', currentGroup()); } catch(_){}
    await window.POS.requestSessionState();
  }

  // --- actions ---------------------------------------------------------------
  async function moveFromMainPrompt(row) {
    const dest = currentGroup();
    if (dest === 'all') return;

    const maxQty = getRawQty(row);
    if (!(maxQty > 0)) return;

    window.openQtyModal({
      title: `Pindahkan ke ${friendly(dest)}`,
      label: `Berapa dari “${getName(row)}”? (maks ${qfmt(maxQty)})`,
      initial: qfmt(maxQty),
      maxQty: maxQty,
      onConfirm: async (moveQty) => {
        try {
          const j = await postJSON('/split/move', {
            session_id: window.SESSION_ID,
            to_group: dest,
            qty: moveQty,
            source_ids: getRowIds(row)
          });
          if (j.status !== 'ok') throw new Error(j.message || 'Gagal memindahkan item');
          reloadPreservingGroup();
        } catch (e) {
          alert(e.message || 'Gagal memindahkan item');
        }
      }
    });
  }

  function unassignFromGroupPrompt(row){
    const maxQty = getRawQty(row);
    if (!(maxQty > 0)) return;

    window.openQtyModal({
      title: 'Keluarkan ke Main',
      label: `Keluarkan berapa dari “${getName(row)}”? (maks ${qfmt(maxQty)})`,
      initial: qfmt(maxQty),
      maxQty: maxQty,
      onConfirm: async (qtyOut) => {
        try {
          const j = await postJSON('/split/move', {
            session_id: window.SESSION_ID,
            to_group: 'main',
            qty: qtyOut,
            source_ids: getRowIds(row)
          });
          if (j.status !== 'ok') throw new Error(j.message || 'Gagal mengeluarkan item');
          reloadPreservingGroup();
        } catch (e) {
          alert(e.message || 'Gagal mengeluarkan item');
        }
      }
    });
  }

  if (typeof window.POS._splitUnassign !== 'function') {
    window.POS._splitUnassign = function(ids, itemName, maxQty){
      window.openQtyModal({
        title: 'Keluarkan ke Main',
        label: `Keluarkan berapa dari “${itemName}”? (maks ${qfmt(maxQty)})`,
        initial: qfmt(maxQty),
        maxQty: Number(maxQty || 0),
        onConfirm: async (qtyOut) => {
          try {
            const res = await fetch('/split/move', {
              method:'POST', headers:{'Content-Type':'application/json'},
              body: JSON.stringify({
                session_id: window.SESSION_ID,
                to_group: 'main',
                qty: qtyOut,
                source_ids: (Array.isArray(ids) ? ids : [])
              })
            });
            const j = await res.json();
            if (j.status !== 'ok') throw new Error(j.message || 'Gagal mengeluarkan item');
            try { await window.POS.requestSessionState({ forceAll:true }); } catch(_){}
          } catch(e) { alert(e.message || 'Gagal mengeluarkan item'); }
        }
      });
    };
  }

  document.addEventListener('DOMContentLoaded', () => {
    ensureOrderBodyOwnership();
    ROWS   = Array.isArray(window.ORDER_ROWS) ? window.ORDER_ROWS : [];
    LABELS = deriveLabels();
    GROUPS = ['all', ...LABELS];

    const savedKey = localStorage.getItem('table_group_key');
    if (savedKey) {
      const i = GROUPS.indexOf(savedKey);
      if (i >= 0) idx = i;
    }

    const prevBtn = document.getElementById('grp-prev');
    const nextBtn = document.getElementById('grp-next');

    if (!isPaged()) {
      prevBtn?.addEventListener('click', () => changeGroup(-1));
      nextBtn?.addEventListener('click', () => changeGroup(+1));
    }

    if (isPaged()) {
      if (hasSplits()) buildSplitChips();
      applyGroupToHostRenderer(currentGroup());
      const gname = document.getElementById('grp-name');
      if (gname) gname.textContent = friendly(currentGroup());
      updateRightPanelMode();
      if (typeof window.refreshDpButton === 'function') window.refreshDpButton();
      if (typeof window.updatePriceBreakdown === 'function') window.updatePriceBreakdown();

      const _watch = setInterval(() => {
        try {
          const host = window.POS && window.POS.__pagedOrders;
          if (!host) return;
          const k = String(host.group || 'all');
          if (k !== __lastHostGroup) {
            const i = GROUPS.indexOf(k);
            idx = (i >= 0 ? i : 0);
            __lastHostGroup = k;
            render();
          }
        } catch (_) {}
      }, 300);

      return;
    }

    if (hasSplits()) buildSplitChips();
    render();
  });

})();

// --- split setup modal (open/close/apply/reset) ------------------------------
(() => {
  let splitShowCol = false;

  const okStatus = (s) => s === 'success' || s === 'ok';

  function updateSplitToggleUI() {
    const btn = document.getElementById('split-col-toggle');
    const hidden = document.getElementById('split-show-col');
    if (!btn || !hidden) return;
    btn.classList.toggle('is-on', splitShowCol);
    btn.setAttribute('aria-pressed', splitShowCol ? 'true' : 'false');
    btn.textContent = splitShowCol
      ? 'Sembunyikan kolom "Group Bill"'
      : 'Tampilkan kolom "Group Bill"';
    hidden.value = splitShowCol ? '1' : '0';
  }

  function renderSplitPreview() {
    const input = document.getElementById('split-count');
    const prev  = document.getElementById('split-preview');
    if (!input || !prev) return;
    const n = parseInt(input.value || '0', 10);
    prev.innerHTML = '';
    if (!(n >= 1 && n <= 20)) return;
    for (let i = 1; i <= n; i++) {
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.style.padding = '4px 8px';
      chip.style.border = '1px solid #ccc';
      chip.style.borderRadius = '6px';
      chip.textContent = String(i);
      prev.appendChild(chip);
    }
  }

  window.openSplitModal = function () {
    const countEl = document.getElementById('split-count');
    const modal   = document.getElementById('split-modal');
    if (!countEl || !modal) return;

    if (!window.SESSION_ID) {
      alert('Session belum siap, reload dulu halaman ini.');
      return;
    }

    const labels = (window.SPLIT_LABELS || []);
    countEl.value = labels.length > 0 ? labels.length : 2;

    const pref = localStorage.getItem('splitVisible');
    splitShowCol = (pref === 'true') || (pref === null && (labels.length || 0) > 0);
    updateSplitToggleUI();

    countEl.removeEventListener?.('input', renderSplitPreview);
    countEl.addEventListener('input', renderSplitPreview);
    renderSplitPreview();

    modal.style.display = 'flex';
    const err = document.getElementById('split-err');
    if (err) err.textContent = '';
  };

  window.closeSplitModal = function () {
    const m = document.getElementById('split-modal');
    if (m) m.style.display = 'none';
  };

  window.toggleSplitColumn = function () {
    splitShowCol = !splitShowCol;
    updateSplitToggleUI();
  };

  window.presetSplit = function (btn) {
    const n = parseInt(btn.dataset.preset, 10);
    const input = document.getElementById('split-count');
    if (input) { input.value = n; renderSplitPreview(); }
  };

  window.applySplit = async function () {
    const err = document.getElementById('split-err');
    if (err) err.textContent = '';
    const input = document.getElementById('split-count');
    const n = parseInt(input?.value || '0', 10);
    if (!(n >= 1 && n <= 20)) { if (err) err.textContent = 'Jumlah split harus 1–20'; return; }

    if (!window.SESSION_ID) {
      if (err) err.textContent = 'Session belum siap, reload dulu.';
      return;
    }

    try {
      const res = await fetch(`/split/config/${window.SESSION_ID}`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ count: n })
      });
      const j = await res.json();
      if (!okStatus(j.status)) {
        if (err) err.textContent = j.message || 'Gagal menyimpan split';
        return;
      }

      window.SPLIT_LABELS = j.labels || [];
      window.SPLIT_META = j.meta || [];
      document.querySelectorAll('.col-bill-group')
        .forEach(el => el.style.display = splitShowCol ? '' : 'none');
      localStorage.setItem('splitVisible', String(splitShowCol));

      window.closeSplitModal();
      await window.POS.requestSessionState({ forceAll: true });

    } catch {
      if (err) err.textContent = 'Jaringan bermasalah, coba lagi.';
    }
  };

  window.resetSplit = async function () {
    if (!confirm('Hapus pengaturan split dan kembalikan semua item ke Main?')) return;
    const err = document.getElementById('split-err');
    if (err) err.textContent = '';
    try {
      const res = await fetch(`/split/config/${window.SESSION_ID}`, { method: 'DELETE' });
      const j = await res.json();
      if (!okStatus(j.status)) {
        if (err) err.textContent = j.message || 'Gagal reset split';
        return;
      }
      window.SPLIT_LABELS = [];
      window.SPLIT_META = [];
      document.querySelectorAll('.col-bill-group').forEach(el => el.style.display = 'none');
      window.closeSplitModal();
      await window.POS.requestSessionState({ forceAll: true });
    } catch {
      if (err) err.textContent = 'Jaringan bermasalah, coba lagi.';
    }
  };

  document.getElementById('split-count')?.addEventListener('input', renderSplitPreview);
})();
