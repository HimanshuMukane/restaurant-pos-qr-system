(() => {
  'use strict';

  // ---------- utils ----------
  const qs = (id) => document.getElementById(id);
  const fmtIDR = n => 'Rp ' + (Math.round(n || 0)).toLocaleString('id-ID');
  const POS = (window.POS = window.POS || {});
  const isDemoMode = () =>
    typeof POS.isDemoMode === 'function' ? POS.isDemoMode() : window.POS_DEMO_MODE === true;
  const showDemoPrintModal = (config) => {
    if (POS && typeof POS.showDemoPrintModal === 'function') {
      POS.showDemoPrintModal(config);
      return;
    }
  };

  let SORT = { key: 'time', dir: 'desc' }; // newest first

  function isoDateOnly(d){
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
  function setDefaultDates() {
    const t = new Date();
    const today = isoDateOnly(t);
    qs('tx_from').value = today;
    qs('tx_to').value   = today;
    markChip('today');
  }
  function markChip(kind){
    document.querySelectorAll('#tx_ranges .chip')
      .forEach(c => c.classList.toggle('active', c.dataset.range===kind));
  }
  function setRange(kind){
    const now = new Date();
    let from = isoDateOnly(now), to = isoDateOnly(now);
    if (kind==='yesterday'){ const y=new Date(now); y.setDate(y.getDate()-1); from=to=isoDateOnly(y); }
    if (kind==='7d'){ const s=new Date(now); s.setDate(s.getDate()-6); from=isoDateOnly(s); }
    if (kind==='30d'){ const s=new Date(now); s.setDate(s.getDate()-29); from=isoDateOnly(s); }
    if (kind==='mtd'){ const s=new Date(now.getFullYear(), now.getMonth(), 1); from=isoDateOnly(s); }
    qs('tx_from').value = from; qs('tx_to').value = to;
    markChip(kind);
  }

  function fmtDateCell(isoLike) {
    if (!isoLike) return '';
    try {
      const d = new Date(isoLike);
      if (isNaN(d.getTime())) return isoLike;
      const pad = (x) => String(x).padStart(2,'0');
      const dd = pad(d.getDate());
      const mm = pad(d.getMonth()+1);
      const yyyy = d.getFullYear();
      const hh = pad(d.getHours());
      const mi = pad(d.getMinutes());
      return `<div class="date"><div class="d">${dd}/${mm}/${yyyy}</div><div class="t">${hh}:${mi}</div></div>`;
    } catch { return isoLike; }
  }

  // ---------- fetch & render ----------
  let txLoadController = null;
  async function loadTx() {
    if (txLoadController) {
      try { txLoadController.abort(); } catch (_) {}
    }
    const controller = (typeof AbortController !== 'undefined') ? new AbortController() : null;
    txLoadController = controller;
    const params = new URLSearchParams();
    params.set('from', qs('tx_from').value);
    params.set('to', qs('tx_to').value);
    const m = qs('tx_method').value; if (m) params.set('method', m);
    const c = qs('tx_cashier').value; if (c) params.set('cashier', c);
    const id = qs('tx_id').value; if (id) params.set('id', id);
    const nm = (qs('tx_name').value || '').trim(); if (nm) params.set('name', nm);
    if (qs('tx_show_refunds').checked) params.set('show_refunds', '1');
    if (qs('tx_show_dp').checked) params.set('show_dp', '1');
    params.set('sort', SORT.key);
    params.set('dir', SORT.dir);
    params.set('limit', '500');

    let r = null;
    try {
      r = await fetch('/admin/api/transactions?' + params.toString(), {
        credentials:'same-origin',
        signal: controller ? controller.signal : undefined
      });
    } catch (err) {
      if (err && err.name === 'AbortError') return;
      throw err;
    } finally {
      if (txLoadController === controller) txLoadController = null;
    }
    if (!r.ok) { alert('Gagal memuat data'); return; }
    const j = await r.json();
    renderTx(j.rows || []);
  }

  // =========================
  // REOPEN HANDLERS (FIX)
  // =========================
  window.closeReopen = function closeReopen() {
    const m = document.getElementById('reopen-modal');
    if (m) m.style.display = 'none';
  };

  window.confirmReopen = async function confirmReopen() {
    const sid  = document.getElementById('reopen-modal').dataset.sessionId;
    const tbl  = document.getElementById('reopen-modal').dataset.tableNum;

    const reason = (document.getElementById('reopen-reason').value || '').trim();
    const note   = (document.getElementById('reopen-note').value || '').trim();
    const errEl  = document.getElementById('reopen-err');

    errEl.textContent = '';

    if (!sid) {
      errEl.textContent = "Sesi tidak valid.";
      return;
    }
    if (!reason) {
      errEl.textContent = "Isi alasan buka ulang.";
      return;
    }

    try {
      const r = await fetch(`/admin/transactions/reopen_copy/${sid}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({
          reason,
          refund_note: note
        })
      });

      const j = await r.json().catch(() => null);
      if (r.ok && j && j.status === "success") {
        // OK → close modal and refresh
        closeReopen();
        loadTx();
      } else {
        errEl.textContent = (j && j.message) || "Gagal buka ulang.";
      }

    } catch (e) {
      errEl.textContent = "Jaringan bermasalah.";
    }
  };


  function renderTx(rows) {
    const tb = qs('tx_body');
    const frag = document.createDocumentFragment();
    if (!rows.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = 11;
      td.className = 'muted';
      td.textContent = 'Tidak ada data.';
      tr.appendChild(td);
      frag.appendChild(tr);
      if (typeof tb.replaceChildren === 'function') tb.replaceChildren(frag);
      else { tb.innerHTML = ''; tb.appendChild(frag); }
      return;
    }

    rows.forEach(p => {
      const tr = document.createElement('tr');
      const isBackfill = !!p.is_backfill;
      if (p.is_refund) tr.classList.add('refund');
      if (isBackfill) tr.classList.add('backfill');

      // Amounts
      const amountDisp = p.is_refund ? -Math.abs(p.amount) : (p.amount || 0);
      const refunded   = Math.max(0, Math.abs(p.refunded_amount || 0));
      const origBase   = Math.abs((p.original_amount ?? p.amount) || 0);
      const remain     = p.is_refund ? 0 : Math.max(origBase - refunded, 0);

      // DP from backend (both possible names)
      const dpApplied = Math.max(0, Math.abs(p.dp_applied ?? p.dp_applied_amount ?? 0));

      // Date (prefer server-local string if provided)
      const paidAtText = p.paid_at_wib || p.paid_at;
      const paidAtHtml = fmtDateCell(paidAtText);

      const billGroup = isBackfill ? 'backfill' : (p.bill_group || 'main');
      const methodLabel = (() => {
        const base = (p.method || '').toUpperCase();
        if (['DEBIT','CREDIT','CARD'].includes(base) && p.card_type) return `${base} (${p.card_type})`;
        return base || '-';
      })();
      const methodText = isBackfill ? 'BACKFILL' : methodLabel;
      const tableLabel = isBackfill ? '—' : (p.table_number || '-');
      const nameHtml = isBackfill
        ? `<div class="backfill-title">Backfill</div><div class="muted backfill-note">Tidak menambah penjualan item</div>`
        : (p.guest_name || '-');

      tr.innerHTML = `
        <td>${paidAtHtml}</td>
        <td>#${p.id} / ${billGroup}</td>
        <td>${tableLabel}</td>
        <td>${nameHtml}</td>
        <td>${methodText}</td>
        <td class="${amountDisp < 0 ? 'neg':''}">${fmtIDR(amountDisp)}</td>
        <td>${dpApplied ? fmtIDR(dpApplied) : '—'}</td>
        <td>${refunded ? fmtIDR(refunded) : '—'}</td>
        <td>${p.is_refund ? '—' : (remain > 0 ? fmtIDR(remain) : '—')}</td>
        <td>${p.cashier_name || '-'}</td>
      `;

      // Actions cell -> only the "Aksi" button
      const tdActions = document.createElement('td');
      tdActions.className = 'actions';
      const widget = window.renderTxActions({
        session_id:        p.session_id || '',
        table_number:      p.table_number || '',
        payment_id:        p.id,
        bill_group:        billGroup,
        guest_name:        p.guest_name || '',
        method_label:      methodText,
        paid_at_text:      paidAtText || '',
        amount_number:     Number(amountDisp || 0),
        dp_number:         Number(dpApplied || 0),
        refundable_left:   remain,
        can_reopen:        !!(p.can_reopen || p.is_closed),
        is_refund:         !!p.is_refund,
        is_backfill:       isBackfill
      });
      tdActions.appendChild(widget);
      tr.appendChild(tdActions);

      frag.appendChild(tr);
    });
    if (typeof tb.replaceChildren === 'function') tb.replaceChildren(frag);
    else { tb.innerHTML = ''; tb.appendChild(frag); }
  }

  // ---------- refund modal ----------
  function openRefundModal(paymentId, maxAmount) {
    qs('refund-payment-id').value = paymentId;
    const amt = qs('refund-amount');
    amt.value = maxAmount; amt.setAttribute('max', maxAmount);
    qs('refund-reason').value = '';
    qs('refund-error').textContent = '';
    qs('refund-modal').style.display = 'flex';
  }
  function closeRefundModal() { qs('refund-modal').style.display = 'none'; }

  async function submitRefund() {
    const id   = parseInt(qs('refund-payment-id').value, 10);
    const amount = parseInt(qs('refund-amount').value, 10);
    const max  = parseInt(qs('refund-amount').getAttribute('max') || '0', 10);
    const reason = (qs('refund-reason').value || '').trim();
    const err = qs('refund-error');
    err.textContent = '';
    if (!id || !amount || amount <= 0) { err.textContent = 'Jumlah refund tidak valid.'; return; }
    if (max && amount > max) { err.textContent = `Maksimal bisa refund Rp ${max.toLocaleString('id-ID')}`; return; }

    try {
      const r = await fetch('/admin/api/refund', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        credentials: 'same-origin',
        body: JSON.stringify({ payment_id:id, amount, reason })
      });
      const j = await r.json().catch(()=>null);
      if (r.ok && j && j.status === 'ok') {
        closeRefundModal();
        loadTx();
      } else {
        err.textContent = (j && j.message) || 'Gagal refund';
      }
    } catch {
      err.textContent = 'Jaringan bermasalah';
    }
  }

  // ---------- backfill modal ----------
  function openBackfillModal() {
    const dateEl = qs('backfill-date');
    const timeEl = qs('backfill-time');
    const amtEl = qs('backfill-amount');
    const errEl = qs('backfill-error');

    if (dateEl && !dateEl.value) {
      dateEl.value = qs('tx_from')?.value || isoDateOnly(new Date());
    }
    if (timeEl) timeEl.value = '';
    if (amtEl) amtEl.value = '';
    if (errEl) errEl.textContent = '';

    const modal = qs('backfill-modal');
    if (modal) modal.style.display = 'flex';
    if (amtEl) amtEl.focus();
  }

  function closeBackfillModal() {
    const modal = qs('backfill-modal');
    if (modal) modal.style.display = 'none';
  }

  async function submitBackfill() {
    const dateVal = (qs('backfill-date')?.value || '').trim();
    const timeVal = (qs('backfill-time')?.value || '').trim();
    const amount = parseInt(qs('backfill-amount')?.value || '0', 10);
    const errEl = qs('backfill-error');
    if (errEl) errEl.textContent = '';

    if (!dateVal) {
      if (errEl) errEl.textContent = 'Tanggal wajib diisi.';
      return;
    }
    if (!amount || amount <= 0) {
      if (errEl) errEl.textContent = 'Jumlah tidak valid.';
      return;
    }

    try {
      const r = await fetch('/admin/api/transactions/backfill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          date: dateVal,
          time: timeVal,
          amount
        })
      });
      const j = await r.json().catch(() => null);
      if (r.ok && j && j.status === 'ok') {
        closeBackfillModal();
        loadTx();
      } else if (errEl) {
        errEl.textContent = (j && j.message) || 'Gagal simpan backfill.';
      }
    } catch {
      if (errEl) errEl.textContent = 'Jaringan bermasalah.';
    }
  }

  // ---------- open/print helpers ----------
  function openSession(sessionId, tableNumber) {
    const patternIn = (window.SESSION_OPEN_URL || '/table/<table_number>/<session_id>');
    const s = encodeURIComponent(String(sessionId || ''));
    const t = encodeURIComponent(String(tableNumber || ''));
    let url = patternIn
      .replace('{table}', t).replace('{session}', s)
      .replace('<table_number>', t).replace('<session_id>', s);
    if (!url.includes(s)) url = `/table/${t}/${s}`;
    const sep = url.includes('?') ? '&' : '?';
    window.location.href = `${url}${sep}exact=1`;
  }
  function viewReceipt(paymentId) { window.location.href = `/receipt/reprint/${paymentId}`; }
  async function printReceipt(paymentId) {
    if (isDemoMode()) {
      showDemoPrintModal({
        title: 'Receipt printed (demo)',
        url: `/receipt/reprint/${paymentId}`,
      });
      return;
    }
    const bridgeUrl = window.POS_BRIDGE_URL || "http://127.0.0.1:5000/print-raw";
    const hexUrl = `/api/print/paid_hex/${encodeURIComponent(paymentId)}`;
    const url = `/receipt/reprint/${paymentId}`;

    async function fallbackHtml() {
      const ifr = document.createElement('iframe');
      Object.assign(ifr.style, {position:'fixed',right:'0',bottom:'0',width:'0',height:'0',border:'0',opacity:'0'});
      document.body.appendChild(ifr);
      const cleanup = () => { try { document.body.removeChild(ifr); } catch {} };
      let loaded = false;
      ifr.onload = () => {
        loaded = true;
        try { ifr.contentWindow.focus(); ifr.contentWindow.print(); } catch {}
        setTimeout(cleanup, 1500);
      };
      const fallbackInject = async () => {
        if (loaded) return;
        try {
          const r = await fetch(url, { credentials: 'same-origin' });
          const html = await r.text();
          const doc = ifr.contentDocument || ifr.contentWindow.document;
          const withBase = html.replace('<head>', '<head><base href="/">');
          doc.open(); doc.write(withBase); doc.close();
          try { ifr.contentWindow.focus(); ifr.contentWindow.print(); } catch {}
          setTimeout(cleanup, 1500);
        } catch {
          const w = window.open(url + '?autoprint=1', 'receiptPopup', 'width=480,height=700,noopener,noreferrer');
          if (!w) return;
          const start = Date.now();
          const timer = setInterval(() => {
            try {
              if (w.document && w.document.readyState === 'complete') {
                try { w.print(); } catch {}
                clearInterval(timer);
                setTimeout(() => { try { w.close(); } catch {} }, 1200);
              } else if (Date.now() - start > 15000) clearInterval(timer);
            } catch {}
          }, 250);
        }
      };
      ifr.src = url;
      setTimeout(fallbackInject, 1000);
    }

    try {
      const r = await fetch(hexUrl, { headers: { "Accept": "application/json" }, credentials: "same-origin" });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || !j.hex) throw new Error(j.message || `HTTP ${r.status}`);
      const p = await fetch(bridgeUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ data: j.hex })
      });
      if (!p.ok) throw new Error(`Bridge HTTP ${p.status}`);
    } catch (e) {
      console.warn("bridge print failed, fallback to HTML", e);
      fallbackHtml();
    }
  }

  // ---------- sorting & ranges ----------
  function setSort(key){
    if (SORT.key === key) { SORT.dir = (SORT.dir === 'asc' ? 'desc' : 'asc'); }
    else { SORT.key = key; SORT.dir = (key==='time' || key==='id') ? 'desc' : 'asc'; }
    loadTx();
  }
  function bindSortHeaders(){
    document.querySelectorAll('.tx-table th.sortable').forEach(th=>{
      th.addEventListener('click', ()=> setSort(th.dataset.sort));
    });
  }
  function bindQuickRanges(){
    const box = document.getElementById('tx_ranges');
    if (!box) return;
    box.addEventListener('click', ev=>{
      const b = ev.target.closest('.chip[data-range]'); if (!b) return;
      setRange(b.dataset.range); loadTx();
    });
  }

  // ---------- Aksi modal (bigger + summary) ----------
  let __aksiCtx = null;
  let __aksiBound = false;

  function ensureAksiStyles(){
    if (document.getElementById('aksi-inline-styles')) return;
    const st = document.createElement('style');
    st.id = 'aksi-inline-styles';
    st.textContent = `
      #aksi-modal.modal-overlay { display:none; align-items:center; justify-content:center; }
      #aksi-modal .modal-card { width:min(96vw, 560px); border-radius:14px; overflow:hidden; }
      #aksi-modal .modal-header { padding:14px 16px; border-bottom:1px solid #eef2f7; }
      #aksi-modal .modal-body { padding:14px 16px; }
      #aksi-modal .aksi-summary {
        border:1px solid #e5e7eb; background:#f8fafc; border-radius:10px; padding:10px 12px; margin-bottom:12px;
        font-size:14px; line-height:1.35;
      }
      #aksi-modal .aksi-summary .title { font-weight:600; margin-bottom:6px; }
      #aksi-modal .aksi-row { display:flex; justify-content:space-between; gap:12px; margin:4px 0; }
      #aksi-modal .aksi-row .k { color:#64748b; }
      #aksi-modal .aksi-row .v { font-variant-numeric: tabular-nums; }
      #aksi-modal .aksi-actions { display:flex; flex-direction:column; gap:10px; margin-top:4px; }
      #aksi-modal .aksi-btn {
        width:100%; height:48px; font-size:16px; line-height:1; border-radius:10px; cursor:pointer;
        border:1px solid #e5e7eb; background:#fff;
      }
      #aksi-modal .aksi-btn:hover { background:#f8fafc; }
      #aksi-modal .aksi-btn.primary { background:#0ea5e9; border-color:#0ea5e9; color:#fff; }
      #aksi-modal .aksi-btn.danger  { color:#b91c1c; border-color:#fecaca; }
      #aksi-modal .aksi-footer { margin-top:12px; }
      #aksi-modal .btn-tutup {
        width:100%; height:44px; font-size:14px; border-radius:10px; cursor:pointer;
        background:#df4747; border:1px solid #e5e7eb;
      }
      #aksi-modal .btn-tutup:hover { background:#e5e7eb; }
    `;
    document.head.appendChild(st);
  }

  
  function initOrBindAksiModal() {
    ensureAksiStyles();

    let modal = document.getElementById('aksi-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'aksi-modal';
      modal.className = 'modal-overlay';
      modal.innerHTML = `
        <div class="modal-card">
          <div class="modal-header"><h3>Aksi</h3></div>
          <div class="modal-body">
            <div class="aksi-summary" id="aksi-summary">
              <div class="title" id="aksi-title">—</div>
              <div class="aksi-row"><div class="k">Tanggal</div><div class="v" id="aksi-date">—</div></div>
              <div class="aksi-row"><div class="k">Metode</div><div class="v" id="aksi-method">—</div></div>
              <div class="aksi-row"><div class="k">Amount</div><div class="v" id="aksi-amount">—</div></div>
              <div class="aksi-row" id="aksi-dp-row" style="display:none;"><div class="k">DP</div><div class="v" id="aksi-dp">—</div></div>
              <div class="aksi-row" id="aksi-rem-row" style="display:none;"><div class="k">Sisa refund</div><div class="v" id="aksi-rem">—</div></div>
            </div>
            <div class="aksi-actions">
              <button type="button" class="aksi-btn primary" id="aksi-open">Buka</button>
              <button type="button" class="aksi-btn"        id="aksi-print">Cetak Ulang</button>
              <button type="button" class="aksi-btn"        id="aksi-refund">Refund</button>
              <button type="button" class="aksi-btn danger" id="aksi-reopen">Buka Ulang</button>
            </div>
            <div class="aksi-footer">
              <button type="button" class="btn-tutup" id="aksi-close">Tutup</button>
            </div>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    } else {
      // ensure structure (summary + big buttons + Tutup)
      const body = modal.querySelector('.modal-body') || modal;
      if (!modal.querySelector('#aksi-summary')) {
        const sum = document.createElement('div');
        sum.className = 'aksi-summary';
        sum.id = 'aksi-summary';
        sum.innerHTML = `
          <div class="title" id="aksi-title">—</div>
          <div class="aksi-row"><div class="k">Tanggal</div><div class="v" id="aksi-date">—</div></div>
          <div class="aksi-row"><div class="k">Metode</div><div class="v" id="aksi-method">—</div></div>
          <div class="aksi-row"><div class="k">Amount</div><div class="v" id="aksi-amount">—</div></div>
          <div class="aksi-row" id="aksi-dp-row" style="display:none;"><div class="k">DP</div><div class="v" id="aksi-dp">—</div></div>
          <div class="aksi-row" id="aksi-rem-row" style="display:none;"><div class="k">Sisa refund</div><div class="v" id="aksi-rem">—</div></div>
        `;
        body.prepend(sum);
      }
      if (!modal.querySelector('#aksi-open')) {
        const actions = document.createElement('div');
        actions.className = 'aksi-actions';
        actions.innerHTML = `
          <button type="button" class="aksi-btn primary" id="aksi-open">Buka</button>
          <button type="button" class="aksi-btn"        id="aksi-print">Cetak Ulang</button>
          <button type="button" class="aksi-btn"        id="aksi-refund">Refund</button>
          <button type="button" class="aksi-btn danger" id="aksi-reopen">Buka Ulang</button>
        `;
        body.appendChild(actions);
      }
      if (!modal.querySelector('#aksi-close')) {
        const foot = document.createElement('div');
        foot.className = 'aksi-footer';
        foot.innerHTML = `<button type="button" class="btn-tutup" id="aksi-close">Tutup</button>`;
        body.appendChild(foot);
      }
      // hide any header "×"
      modal.querySelectorAll('.modal-close').forEach(x => x.style.display = 'none');
    }

    if (__aksiBound) return;
    __aksiBound = true;

    // close by overlay / ESC / Tutup
    modal.addEventListener('click', (e)=>{ if (e.target === modal) closeAksi(); });
    document.addEventListener('keydown', (e)=>{ if (e.key === 'Escape') closeAksi(); });
    modal.querySelector('#aksi-close').addEventListener('click', closeAksi);

    // buttons
    modal.querySelector('#aksi-open').addEventListener('click', ()=>{
      if (!__aksiCtx) return;
      const { session_id, table_number, payment_id } = __aksiCtx;
      if (session_id && table_number) openSession(session_id, table_number);
      else if (payment_id) viewReceipt(payment_id);
      closeAksi();
    });
    modal.querySelector('#aksi-print').addEventListener('click', ()=>{
      if (!__aksiCtx) return;
      if (__aksiCtx.payment_id) printReceipt(__aksiCtx.payment_id);
      closeAksi();
    });
    modal.querySelector('#aksi-refund').addEventListener('click', ()=>{
      if (!__aksiCtx) return;
      const { payment_id, refundable_left } = __aksiCtx;
      if (refundable_left > 0) openRefundModal(payment_id, refundable_left);
      closeAksi();
    });
    modal.querySelector('#aksi-reopen').addEventListener('click', ()=>{
      if (!__aksiCtx) return;
      const { session_id, table_number } = __aksiCtx;
      if (typeof window.openReopenDialog === 'function') {
        window.openReopenDialog(session_id, table_number);
      } else {
        const title = document.querySelector('#reopen-title');
        if (title) title.textContent = `Sesi ${session_id} – Meja ${table_number}`;
        document.querySelector('#reopen-reason').value = 'Salah tutup';
        document.querySelector('#reopen-note').value = '';
        document.querySelector('#reopen-err').textContent = '';

        // STORE IDs INSIDE THE MODAL
        const rm = document.getElementById('reopen-modal');
        rm.dataset.sessionId = session_id;
        rm.dataset.tableNum  = table_number;

        rm.style.display = 'flex';
      }
      closeAksi();
    });

  }

  function openAksi(ctx){
    __aksiCtx = ctx || null;
    const m = document.getElementById('aksi-modal'); if (!m) return;

    // Summary content
    const title = ctx.is_backfill
      ? `Backfill • #${ctx.payment_id}${ctx.bill_group ? ' / '+ctx.bill_group : ''}`
      : `Meja ${ctx.table_number || '-'} • #${ctx.payment_id}${ctx.bill_group ? ' / '+ctx.bill_group : ''}` +
        (ctx.guest_name ? ` — ${ctx.guest_name}` : '');
    m.querySelector('#aksi-title').textContent  = title;
    m.querySelector('#aksi-date').textContent   = ctx.paid_at_text || '—';
    m.querySelector('#aksi-method').textContent = ctx.method_label || '—';
    m.querySelector('#aksi-amount').textContent = fmtIDR(ctx.amount_number || 0);

    const dpRow = m.querySelector('#aksi-dp-row');
    const dpVal = m.querySelector('#aksi-dp');
    if ((ctx.dp_number || 0) > 0) {
      dpRow.style.display = '';
      dpVal.textContent = fmtIDR(ctx.dp_number);
    } else {
      dpRow.style.display = 'none';
    }

    const remRow = m.querySelector('#aksi-rem-row');
    const remVal = m.querySelector('#aksi-rem');
    const canRefund = !ctx.is_refund && (ctx.refundable_left > 0);
    if (canRefund) {
      remRow.style.display = '';
      remVal.textContent = fmtIDR(ctx.refundable_left);
    } else {
      remRow.style.display = 'none';
    }

    // Button visibility
    m.querySelector('#aksi-refund').classList.toggle('hidden', !canRefund);
    m.querySelector('#aksi-reopen').classList.toggle('hidden', !ctx.can_reopen);
    const hasSession = !!ctx.session_id;
    m.querySelector('#aksi-open').classList.toggle('hidden', !hasSession);
    m.querySelector('#aksi-print').classList.toggle('hidden', !hasSession);

    // show
    m.style.display = 'flex';
  }
  function closeAksi(){
    const m = document.getElementById('aksi-modal');
    if (m) m.style.display = 'none';
    __aksiCtx = null;
  }

  // ---------- actions widget & table delegation ----------
  window.renderTxActions = function renderTxActions(payload) {
    const {
      session_id, table_number, payment_id, bill_group, guest_name,
      method_label, paid_at_text, amount_number, dp_number,
      refundable_left=0, can_reopen=true, is_refund=false, is_backfill=false
    } = payload;

    const tpl = document.querySelector('#tx-actions-tpl');
    const root = tpl.content.firstElementChild.cloneNode(true);

    // remove any leftover inline dropdowns
    root.querySelectorAll('.menu, .aksi-menu').forEach(n => n.remove());

    // ensure trigger
    let btn = root.querySelector('.btn-aksi');
    if (!btn) {
      btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'btn btn-aksi';
      btn.textContent = 'Aksi ▾';
      root.appendChild(btn);
    }

    // datasets for the modal
    root.dataset.sessionId      = session_id || '';
    root.dataset.tableNumber    = table_number || '';
    root.dataset.paymentId      = payment_id || '';
    root.dataset.billGroup      = bill_group || '';
    root.dataset.guestName      = guest_name || '';
    root.dataset.methodLabel    = method_label || '';
    root.dataset.paidAt         = paid_at_text || '';
    root.dataset.amountNumber   = String(Number(amount_number || 0));
    root.dataset.dpNumber       = String(Number(dp_number || 0));
    root.dataset.refundableLeft = String(Number(refundable_left || 0));
    root.dataset.canReopen      = can_reopen ? '1' : '';
    root.dataset.isRefund       = is_refund ? '1' : '';
    root.dataset.isBackfill     = is_backfill ? '1' : '';
    return root;
  };

  // open modal on Aksi click
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.btn-aksi'); if (!btn) return;
    const split = btn.closest('.actions-split'); if (!split) return;

    openAksi({
      session_id:      split.dataset.sessionId || '',
      table_number:    split.dataset.tableNumber || '',
      payment_id:      split.dataset.paymentId || '',
      bill_group:      split.dataset.billGroup || '',
      guest_name:      split.dataset.guestName || '',
      method_label:    split.dataset.methodLabel || '',
      paid_at_text:    split.dataset.paidAt || '',
      amount_number:   Number(split.dataset.amountNumber || 0),
      dp_number:       Number(split.dataset.dpNumber || 0),
      refundable_left: Number(split.dataset.refundableLeft || 0),
      can_reopen:      !!Number(split.dataset.canReopen || '0'),
      is_refund:       !!Number(split.dataset.isRefund || '0'),
      is_backfill:     !!Number(split.dataset.isBackfill || '0'),
    });
  });

  // ---------- expose helpers ----------
  window.openSession = openSession;
  window.viewReceipt = viewReceipt;
  window.printReceipt = printReceipt;
  window.openRefundModal = openRefundModal;
  window.closeRefundModal = closeRefundModal;
  window.submitRefund = submitRefund;
  window.openBackfillModal = openBackfillModal;
  window.closeBackfillModal = closeBackfillModal;
  window.submitBackfill = submitBackfill;

  // ---------- boot ----------
  document.addEventListener('DOMContentLoaded', () => {
    initOrBindAksiModal();
    setDefaultDates();
    bindQuickRanges();
    bindSortHeaders();

    const nameInp = document.getElementById('tx_name');
    if (nameInp) nameInp.addEventListener('keydown', (e) => { if (e.key === 'Enter') loadTx(); });

    document.getElementById('tx_apply')?.addEventListener('click', loadTx);
    document.getElementById('tx_backfill')?.addEventListener('click', openBackfillModal);
    loadTx();
  });

})();
