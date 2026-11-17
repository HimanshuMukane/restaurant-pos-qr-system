const qs = id => document.getElementById(id);
const debounce = (fn, ms = 120) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };


// --- dd/mm/yyyy helper ---
const toDDMMYYYY = (s) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s||''));
  return m ? `${m[3]}/${m[2]}/${m[1]}` : s;
};

// Kiosk fallbacks (no Canvas)
function renderDailyFallback(ts) {
  const box = qs('chartSalesEmpty'); if (!box) return;
  if (!ts || !ts.length) { box.hidden = false; box.textContent = 'Tidak ada data.'; return; }
  const max = Math.max(1, ...ts.map(x => x.gross || 0));
  const rows = ts.map(x => {
    const w = Math.round(((x.gross||0) / max) * 100);
    return `<tr>
      <td>${toDDMMYYYY(x.date)}</td>
      <td style="width:70%"><div style="height:10px;width:${w}%;background:#93c5fd"></div></td>
      <td style="text-align:right">${fmtIDR(x.gross||0)}</td>
    </tr>`;
  }).join('');
  box.innerHTML = `<table style="width:100%"><thead><tr><th>Tanggal</th><th>Bar</th><th>Gross</th></tr></thead><tbody>${rows}</tbody></table>`;
  box.hidden = false;
}

function renderHourFallback(hours) {
  const box = qs('chartHourEmpty'); if (!box) return;
  if (!hours || !hours.length) { box.hidden = false; box.textContent = 'Tidak ada data.'; return; }
  const max = Math.max(1, ...hours.map(h => h.gross || 0));
  const rows = hours.map(h => {
    const w = Math.round(((h.gross||0)/max)*100);
    return `<tr>
      <td>${h.hh}:00</td>
      <td style="width:70%"><div style="height:10px;width:${w}%;background:#93c5fd"></div></td>
      <td style="text-align:right">${fmtIDR(h.gross||0)}</td>
    </tr>`;
  }).join('');
  box.innerHTML = `<table style="width:100%"><thead><tr><th>Jam</th><th>Bar</th><th>Gross</th></tr></thead><tbody>${rows}</tbody></table>`;
  box.hidden = false;
}

// --- Number formatting ---
const fmtIDR = n => 'Rp ' + (Math.round(n || 0)).toLocaleString('id-ID');
let nfCompact;
try { nfCompact = new Intl.NumberFormat('id-ID', { notation: 'compact', maximumFractionDigits: 1 }); } catch {}
const fmtIDRCompact = n => nfCompact ? 'Rp ' + nfCompact.format(Math.round(n || 0)) : fmtIDR(n);
const fmtQty = (n, max=1) => Number(n || 0).toLocaleString('id-ID', { maximumFractionDigits: max });
const fmtQtyFixed1 = (n) => Number(n || 0).toLocaleString('id-ID', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

// --- Chart refs ---
let chartSales, chartHour, chartQrHour;
const hasChart = () => typeof window.Chart !== 'undefined';

let chartTrendMoney, chartTrendTx, chartTrendArrivals;
let currentTrendGroup = 'hour';

function fmtClockFromSeconds(sec) {
  const totalMinutes = Math.round((sec || 0) / 60);
  const hh = (Math.floor(totalMinutes / 60)) % 24;
  const mm = totalMinutes % 60;
  return String(hh).padStart(2, '0') + ':' + String(mm).padStart(2, '0');
}

// Keep payment/discount charts numeric-only (tables only)
const USE_PAYMIX_CHART = false;
const USE_DISCOUNT_CHART = false;

// Keep the latest overview in memory for insights
let __lastOverview = null;

// Race-safety token
let __loadSeq = 0;
let __itemSelectedCategory = null;
let __itemSelectedSubcategory = null;
let __staffVoidSelectedUserId = null;
let __itemDishRows = [];
let __itemDishPage = 0;
let __itemDishDays = 0;
const DISH_PAGE_SIZE = 15;

// --- utils ---
const show = (id, yes) => { const el = qs(id); if (el) el.hidden = !yes; };
const sum = (arr) => arr.reduce((a,b)=>a+(+b||0),0);
const setTableEmpty = (tb, cols, msg) => {
  if (!tb) return;
  tb.innerHTML = `<tr><td colspan="${cols}" class="muted">${msg}</td></tr>`;
};
const renderModifierTable = (tableId, rows, emptyMsg) => {
  const tb = qs(tableId)?.querySelector('tbody');
  if (!tb) return;
  tb.innerHTML = '';
  (rows || []).forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.name || '-'}</td>
      <td>${fmtQty(r.qty || 0, 1)}</td>
      <td>${(r.lines || 0).toLocaleString('id-ID')}</td>
    `;
    tb.appendChild(tr);
  });
  if (!tb.children.length) setTableEmpty(tb, 3, emptyMsg || 'Tidak ada data.');
};
const getDaysCount = (fr, to) => {
  try {
    const start = new Date(`${fr}T00:00:00`);
    const end = new Date(`${to}T00:00:00`);
    const diff = Math.round((end - start) / 86400000) + 1;
    return diff > 0 ? diff : 1;
  } catch (_) {
    return 1;
  }
};

function updateDishPager(totalRows) {
  const pager = qs('itemDishesPager');
  if (!pager) return;
  const totalPages = Math.max(1, Math.ceil((totalRows || 0) / DISH_PAGE_SIZE));
  pager.hidden = (totalRows || 0) <= DISH_PAGE_SIZE;
  const hud = qs('itemDishesHud');
  if (hud) hud.textContent = `${Math.min(__itemDishPage + 1, totalPages)}/${totalPages}`;
  const prev = pager.querySelector('[data-dir="prev"]');
  const next = pager.querySelector('[data-dir="next"]');
  if (prev) prev.disabled = __itemDishPage <= 0;
  if (next) next.disabled = __itemDishPage >= totalPages - 1;
}

function resetDishTable(msg) {
  const dishTb = qs('tableItemDishes')?.querySelector('tbody');
  if (dishTb) setTableEmpty(dishTb, 7, msg || 'Tidak ada data.');
  __itemDishRows = [];
  __itemDishPage = 0;
  __itemDishDays = 0;
  updateDishPager(0);
}

function renderDishPage() {
  const tb = qs('tableItemDishes')?.querySelector('tbody');
  if (!tb) return;
  tb.innerHTML = '';
  const rows = Array.isArray(__itemDishRows) ? __itemDishRows : [];
  if (!rows.length) {
    setTableEmpty(tb, 7, 'Tidak ada data.');
    updateDishPager(0);
    return;
  }
  const totalPages = Math.max(1, Math.ceil(rows.length / DISH_PAGE_SIZE));
  if (__itemDishPage >= totalPages) __itemDishPage = totalPages - 1;
  if (__itemDishPage < 0) __itemDishPage = 0;
  const start = __itemDishPage * DISH_PAGE_SIZE;
  const pageRows = rows.slice(start, start + DISH_PAGE_SIZE);
  const days = __itemDishDays || 0;
  pageRows.forEach(r => {
    const avg = (r && typeof r.avg_per_day === 'number')
      ? r.avg_per_day
      : (days ? (Number(r.qty_sold || 0) / days) : 0);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.dish || '-'}</td>
      <td>${r.unit || '-'}</td>
      <td>${fmtQty(r.qty_sold, 1)}</td>
      <td>${fmtQtyFixed1(avg)}</td>
      <td>${fmtQty(r.qty_void, 1)}</td>
      <td>${fmtQty(r.qty_cancelled, 1)}</td>
      <td>${fmtIDR(r.revenue || 0)}</td>
    `;
    tb.appendChild(tr);
  });
  if (!tb.children.length) setTableEmpty(tb, 7, 'Tidak ada data.');
  updateDishPager(rows.length);
}

// --- Hidden-tab chart sizing ---
function forceChartResize() {
  if (!hasChart()) return;
  [chartSales, chartHour, chartQrHour].forEach(c => c && typeof c.resize === 'function' && c.resize());
  window.dispatchEvent(new Event('resize'));
}

function tabbind() {
  const container = document.getElementById('analytics-tabs');
  if (!container) return;
  const panels = document.querySelectorAll('.tab-panel');
  container.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const panel = document.getElementById('tab-' + btn.dataset.tab);
      if (panel) panel.classList.add('active');
      setTimeout(forceChartResize, 30);
    });
  });
  window.addEventListener('resize', debounce(forceChartResize, 120));
}

async function loadItemCategories(fr, to, seq) {
  try {
    const data = await fetchJSON('/api/analytics/items_rollup', { from: fr, to, level: 'category', attr: 'printed' });
    if (seq !== __loadSeq) return;
    const tb = qs('tableItemCategories')?.querySelector('tbody');
    if (!tb) return;
    tb.innerHTML = '';
    const rows = data.rows || [];
    rows.forEach(r => {
      const tr = document.createElement('tr');
      const cat = r.category || '-';
      tr.dataset.category = cat;
      if (__itemSelectedCategory && cat.toLowerCase() === __itemSelectedCategory.toLowerCase()) {
        tr.classList.add('active');
      }
      tr.innerHTML = `
        <td>${cat}</td>
        <td>${r.unit || '-'}</td>
        <td>${fmtQty(r.qty_sold, 1)}</td>
        <td>${fmtQty(r.qty_void, 1)}</td>
        <td>${fmtQty(r.qty_cancelled, 1)}</td>
        <td>${fmtIDR(r.revenue || 0)}</td>
      `;
      tb.appendChild(tr);
    });
    if (!tb.children.length) setTableEmpty(tb, 6, 'Tidak ada data.');
    const catKeys = new Set(rows.map(r => (r.category || '').toLowerCase()));
    if (__itemSelectedCategory && !catKeys.has(__itemSelectedCategory.toLowerCase())) {
      __itemSelectedCategory = null;
      __itemSelectedSubcategory = null;
      show('itemDetailCard', false);
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('items_rollup category failed', e);
    const tb = qs('tableItemCategories')?.querySelector('tbody');
    if (tb) setTableEmpty(tb, 6, 'Gagal memuat.');
  }

  if (!__itemSelectedCategory) {
    show('itemDetailCard', false);
    return;
  }
  await loadItemSubcategories(fr, to, seq);
}

async function loadItemSubcategories(fr, to, seq) {
  if (!__itemSelectedCategory) {
    show('itemDetailCard', false);
    resetDishTable('Pilih subkategori.');
    return;
  }
  try {
    const data = await fetchJSON('/api/analytics/items_rollup', {
      from: fr,
      to,
      level: 'subcategory',
      category: __itemSelectedCategory,
      attr: 'printed'
    });
    if (seq !== __loadSeq) return;
    show('itemDetailCard', true);
    const title = qs('itemDetailTitle');
    if (title) title.textContent = `Detail Kategori: ${__itemSelectedCategory}`;
    const tb = qs('tableItemSubcategories')?.querySelector('tbody');
    if (!tb) return;
    tb.innerHTML = '';
    const rows = data.rows || [];
    rows.forEach(r => {
      const tr = document.createElement('tr');
      const sub = r.subcategory || '-';
      tr.dataset.subcategory = sub;
      if (__itemSelectedSubcategory && sub.toLowerCase() === __itemSelectedSubcategory.toLowerCase()) {
        tr.classList.add('active');
      }
      tr.innerHTML = `
        <td>${sub}</td>
        <td>${r.unit || '-'}</td>
        <td>${fmtQty(r.qty_sold, 1)}</td>
        <td>${fmtQty(r.qty_void, 1)}</td>
        <td>${fmtQty(r.qty_cancelled, 1)}</td>
        <td>${fmtIDR(r.revenue || 0)}</td>
      `;
      tb.appendChild(tr);
    });
    if (!tb.children.length) setTableEmpty(tb, 6, 'Tidak ada data.');

    const subKeys = new Set(rows.map(r => (r.subcategory || '').toLowerCase()));
    if (!__itemSelectedSubcategory || !subKeys.has(__itemSelectedSubcategory.toLowerCase())) {
      __itemSelectedSubcategory = null;
      resetDishTable('Pilih subkategori.');
      return;
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('items_rollup subcategory failed', e);
    const tb = qs('tableItemSubcategories')?.querySelector('tbody');
    if (tb) setTableEmpty(tb, 6, 'Gagal memuat.');
    return;
  }

  await loadItemDishes(fr, to, seq);
}

async function loadItemDishes(fr, to, seq) {
  if (!__itemSelectedCategory || !__itemSelectedSubcategory) {
    resetDishTable('Pilih subkategori.');
    return;
  }
  try {
    const data = await fetchJSON('/api/analytics/items_rollup', {
      from: fr,
      to,
      level: 'dish',
      category: __itemSelectedCategory,
      subcategory: __itemSelectedSubcategory,
      attr: 'printed'
    });
    if (seq !== __loadSeq) return;
    __itemDishRows = data.rows || [];
    __itemDishPage = 0;
    __itemDishDays = Number(data.days || 0) || getDaysCount(fr, to);
    renderDishPage();
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('items_rollup dish failed', e);
    resetDishTable('Gagal memuat.');
  }
}

async function loadModifierUsage(fr, to, seq) {
  try {
    const data = await fetchJSON('/api/analytics/modifiers', { from: fr, to, limit: 25 });
    if (seq !== __loadSeq) return;

    renderModifierTable('tableModifiersPreset', data.preset || [], 'Tidak ada data.');
    renderModifierTable('tableModifiersCustom', data.custom || [], 'Tidak ada data.');

    const unused = Array.isArray(data.unused_presets) ? data.unused_presets : [];
    const wrap = qs('modifiersUnusedWrap');
    const summary = qs('modifiersUnusedSummary');
    const box = qs('modifiersUnused');
    if (wrap && summary && box) {
      if (unused.length) {
        wrap.hidden = false;
        summary.textContent = `Preset tidak terpakai (${unused.length})`;
        box.textContent = unused.join(', ');
      } else {
        wrap.hidden = true;
        summary.textContent = 'Preset tidak terpakai (0)';
        box.textContent = '';
      }
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('modifiers failed', e);
    renderModifierTable('tableModifiersPreset', [], 'Gagal memuat.');
    renderModifierTable('tableModifiersCustom', [], 'Gagal memuat.');
    const wrap = qs('modifiersUnusedWrap');
    if (wrap) wrap.hidden = true;
  }
}

async function loadStaffVoids(fr, to, seq) {
  const excludeSeafood = qs('staffVoidExcludeSeafood')?.checked ? '1' : '0';
  try {
    const data = await fetchJSON('/api/analytics/staff_voids', {
      from: fr,
      to,
      exclude_seafood: excludeSeafood
    });
    if (seq !== __loadSeq) return;
    const tb = qs('tableStaffVoids')?.querySelector('tbody');
    if (!tb) return;
    tb.innerHTML = '';
    const rows = data.staff || [];
    rows.forEach(r => {
      const tr = document.createElement('tr');
      tr.dataset.userId = r.user_id;
      if (__staffVoidSelectedUserId && Number(r.user_id) === Number(__staffVoidSelectedUserId)) {
        tr.classList.add('active');
      }
      tr.innerHTML = `
        <td>${r.name || '-'}</td>
        <td>${fmtQty(r.qty_void, 1)}</td>
        <td>${fmtIDR(r.value_void || 0)}</td>
        <td>${fmtQty(r.qty_cancelled, 1)}</td>
        <td>${fmtIDR(r.value_cancelled || 0)}</td>
        <td>${fmtIDR(r.total_value || 0)}</td>
      `;
      tb.appendChild(tr);
    });
    if (!tb.children.length) setTableEmpty(tb, 6, 'Tidak ada data.');
    const userIds = new Set(rows.map(r => String(r.user_id)));
    if (__staffVoidSelectedUserId && !userIds.has(String(__staffVoidSelectedUserId))) {
      __staffVoidSelectedUserId = null;
      show('staffVoidDetailCard', false);
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('staff_voids failed', e);
    const tb = qs('tableStaffVoids')?.querySelector('tbody');
    if (tb) setTableEmpty(tb, 6, 'Gagal memuat.');
    return;
  }

  if (!__staffVoidSelectedUserId) {
    show('staffVoidDetailCard', false);
    return;
  }
  await loadStaffVoidItems(fr, to, seq);
}

async function loadStaffVoidItems(fr, to, seq) {
  if (!__staffVoidSelectedUserId) {
    show('staffVoidDetailCard', false);
    return;
  }
  const excludeSeafood = qs('staffVoidExcludeSeafood')?.checked ? '1' : '0';
  try {
    const data = await fetchJSON('/api/analytics/staff_voids', {
      from: fr,
      to,
      exclude_seafood: excludeSeafood,
      user_id: __staffVoidSelectedUserId,
      limit: 60
    });
    if (seq !== __loadSeq) return;
    show('staffVoidDetailCard', true);
    const title = qs('staffVoidDetailTitle');
    if (title) title.textContent = `Detail Void: ${data.name || '-'}`;
    const tb = qs('tableStaffVoidItems')?.querySelector('tbody');
    if (!tb) return;
    tb.innerHTML = '';
    (data.items || []).forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${r.item_name || '-'}</td>
        <td>${fmtQty(r.qty_void, 1)}</td>
        <td>${fmtIDR(r.value_void || 0)}</td>
        <td>${fmtQty(r.qty_cancelled, 1)}</td>
        <td>${fmtIDR(r.value_cancelled || 0)}</td>
        <td>${fmtIDR(r.total_value || 0)}</td>
      `;
      tb.appendChild(tr);
    });
    if (!tb.children.length) setTableEmpty(tb, 6, 'Tidak ada data.');
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('staff_voids detail failed', e);
    const tb = qs('tableStaffVoidItems')?.querySelector('tbody');
    if (tb) setTableEmpty(tb, 6, 'Gagal memuat.');
  }
}

async function fetchJSON(url, params) {
  const u = new URL(url, window.location.origin);
  if (params) Object.entries(params).forEach(([k, v]) => u.searchParams.set(k, v));
  const r = await fetch(u, { credentials: 'same-origin' });
  if (!r.ok) throw new Error('Gagal memuat ' + url);
  return r.json();
}

// Quick-range helpers (Asia/Jakarta assumed on the server)
function dateISO(d){
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function setRange(kind){
  const now = new Date();
  const ymd = (d)=>dateISO(d);
  let from = ymd(now), to = ymd(now);
  if (kind === 'yesterday') {
    const y = new Date(now); y.setDate(y.getDate()-1); from = to = ymd(y);
  } else if (kind === '7d') {
    const s = new Date(now); s.setDate(s.getDate()-6); from = ymd(s); to = ymd(now);
  } else if (kind === '30d') {
    const s = new Date(now); s.setDate(s.getDate()-29); from = ymd(s); to = ymd(now);
  } else if (kind === 'mtd') {
    const s = new Date(now.getFullYear(), now.getMonth(), 1); from = ymd(s); to = ymd(now);
  } else if (kind === 'ytd') {
    const s = new Date(now.getFullYear(), 0, 1); from = ymd(s); to = ymd(now);
  }
  if (qs('fromDate')) qs('fromDate').value = from;
  if (qs('toDate'))   qs('toDate').value   = to;

  document.querySelectorAll('#quickRanges .chip').forEach(c => c.classList.remove('active'));
  const active = document.querySelector(`#quickRanges .chip[data-range="${kind}"]`);
  if (active) active.classList.add('active');
}

async function loadAll() {
  const seq = ++__loadSeq;

  const fr = qs('fromDate').value;
  const to = qs('toDate').value;

  // ---- OVERVIEW ----
  try {
    const ov = await fetchJSON('/api/analytics/overview', { from: fr, to });
    if (seq !== __loadSeq) return;
    __lastOverview = ov;

    // KPIs
    qs('kpiGross').textContent   = fmtIDR(ov.kpi.gross);         // ← NEW: gross after refunds & reversal
    qs('kpiNet').textContent     = fmtIDR(ov.kpi.kas_masuk);     // Kas Masuk (before refunds/reversal)

    // show negatives with "- Rp …" style
    qs('kpiRefunds').textContent = '- ' + fmtIDR(Math.abs(ov.kpi.refunds_net || 0));
    if (qs('kpiReopen')) qs('kpiReopen').textContent = '- ' + fmtIDR(Math.abs(ov.kpi.reopen_net || 0));


    // NEW: Transaksi (jumlah pembayaran non-refund di periode ini)
    const txCount = ov.kpi.payments_count || 0;
    if (qs('kpiPay')) {
      qs('kpiPay').textContent = txCount.toLocaleString('id-ID');
    }

    // NEW: AOV / Sesi = Kas Masuk (Net) dibagi jumlah sesi yang punya pembayaran
    const aov = ov.kpi.aov_per_session || 0;
    if (qs('kpiAov')) {
      qs('kpiAov').textContent = fmtIDR(aov);
    }


    // Ringkasan Komponen
    qs('sumSubtotal').textContent = fmtIDR(ov.kpi.subtotal_total);

    // Diskon as "- Rp …"
    qs('sumDiscount').textContent = '- ' + fmtIDR(Math.abs(ov.kpi.discount_total || 0));

    qs('sumService').textContent  = fmtIDR(ov.kpi.service_total);
    qs('sumTax').textContent      = fmtIDR(ov.kpi.tax_total);

    // Setelah service & pajak (BOOK, sebelum refunds/buka ulang)
    const bookGross =
      (ov.kpi.subtotal_total || 0)
      - (ov.kpi.discount_total || 0)
      + (ov.kpi.service_total  || 0)
      + (ov.kpi.tax_total      || 0);

    qs('sumNetCollected').textContent = fmtIDR(bookGross);

    // (optional) DP row – only if the cell exists in the HTML
    if (qs('sumDP')) {
      qs('sumDP').textContent = fmtIDR(ov.kpi.dp_used_total);
    }

    // Refunds & Reversal as negative numbers
    qs('sumRefunds').textContent = '- ' + fmtIDR(Math.abs(ov.kpi.refunds_net || 0));
    if (qs('sumReopen')) {
      qs('sumReopen').textContent = '- ' + fmtIDR(Math.abs(ov.kpi.reopen_net || 0));
    }

    // Final gross (sesuai KPI atas) = Kas Masuk - Refunds - Reversal
    qs('sumGross').textContent = fmtIDR(ov.kpi.gross);

    // Daily trend data source (labels unchanged)
    const labels    = (ov.timeseries || []).map(x => toDDMMYYYY(x.date));
    const dataGross = (ov.timeseries || []).map(x => x.gross || 0);  // already (kas_masuk_day + refunds_day)

    const hasGross  = dataGross.some(v => v > 0);

    if (!hasChart()) {
      renderDailyFallback(ov.timeseries || []);
    } else {
      show('chartSalesEmpty', !hasGross);
      if (chartSales) chartSales.destroy();
      const elSales = qs('chartSales');
      if (elSales && hasGross) {
        const maxGross  = Math.max(0, ...dataGross);
        const suggestedMax = maxGross > 0 ? Math.round(maxGross * 1.1) : undefined;
        chartSales = new Chart(elSales, {
          type: 'line',
          data: { labels, datasets: [{ label: 'Gross Sales', data: dataGross, tension: 0.35 }] },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => fmtIDR(ctx.parsed.y) } } },
            scales: {
              x: { ticks: { maxRotation: 0, autoSkip: true }, grid: { display: false } },
              y: { beginAtZero: true, suggestedMax, ticks: { callback: v => fmtIDRCompact(v) }, grid: { drawBorder: false } }
            }
          }
        });
      }
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('overview failed', e);
    show('chartSalesEmpty', true);
  }

  // ---- OUTSTANDING (current open sessions) ----
  try {
    const out = await fetchJSON('/api/analytics/outstanding');
    if (seq !== __loadSeq) return;
  
    if (qs('kpiOutstanding')) qs('kpiOutstanding').textContent = fmtIDR(out.outstanding_pre_tax_service || 0);
    if (qs('sumOutstanding')) qs('sumOutstanding').textContent = fmtIDR(out.outstanding_pre_tax_service || 0);
  
    if (qs('insOpenSessions')) qs('insOpenSessions').textContent = (out.open_sessions || 0).toLocaleString('id-ID');
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('outstanding failed', e);
  }
  
  // ---- SALES: payment mix & discounts ----
  try {
    const mix = await fetchJSON('/api/analytics/payments_mix', { from: fr, to });
    if (seq !== __loadSeq) return;

    // Payment mix numeric table
    {
      const methods = (mix.methods || []).map(m => ({...m, method: (m.method || 'unknown')}));
      const tb = qs('tablePayMix')?.querySelector('tbody');
      const totalAmt = methods.reduce((s, m) => s + (m.amt || 0), 0);
      if (tb) {
        tb.innerHTML = '';
        methods
          .sort((a,b) => (b.amt||0) - (a.amt||0))
          .forEach(m => {
            const share = totalAmt > 0 ? (m.amt / totalAmt) * 100 : 0;
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${String(m.method).toUpperCase()}</td>
              <td>${fmtIDR(m.amt || 0)}</td>
              <td>${share.toFixed(1)}%</td>
            `;
            tb.appendChild(tr);
          });
        if (!tb.children.length) tb.innerHTML = `<tr><td colspan="3" class="muted">Tidak ada data.</td></tr>`;
      }
      if (qs('paymixTotal')) qs('paymixTotal').textContent = fmtIDR(totalAmt);

      // Insight: cash vs non-cash
      const cashAmt = methods.filter(x => (x.method||'').toLowerCase()==='cash').reduce((s,m)=>s+(m.amt||0),0);
      const shareCash = totalAmt ? (cashAmt/totalAmt*100) : 0;
      if (qs('insCashShare')) qs('insCashShare').textContent =
        `${shareCash.toFixed(1)}% cash • ${(100 - shareCash).toFixed(1)}% non-cash`;

      show('chartPayMixEmpty', totalAmt === 0);
    }

    // Discounts numeric table
    {
      const discounts = (mix.discounts || []).filter(x => (x.pct || 0) > 0);
      const tb = qs('tableDisc')?.querySelector('tbody');
      const discTxTotal = discounts.reduce((s, d) => s + (d.cnt || 0), 0);
      if (tb) {
        tb.innerHTML = '';
        discounts
          .sort((a,b) => (b.pct||0) - (a.pct||0))
          .forEach(d => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${(d.pct || 0)}%</td>
              <td>${(d.cnt || 0).toLocaleString('id-ID')}</td>
              <td></td>
            `;
            tb.appendChild(tr);
          });
        if (!tb.children.length) tb.innerHTML = `<tr><td colspan="3" class="muted">Tidak ada data.</td></tr>`;
      }
      if (qs('discTxTotal')) qs('discTxTotal').textContent = (discTxTotal || 0).toLocaleString('id-ID');

      const totalTx = __lastOverview?.kpi?.payments_count || 0;
      const rate = totalTx ? (discTxTotal / totalTx * 100) : 0;
      if (qs('discTxRate')) qs('discTxRate').textContent = `${rate.toFixed(1)}%`;
      if (qs('insDiscRate')) qs('insDiscRate').textContent = `${rate.toFixed(1)}% dari ${totalTx.toLocaleString('id-ID')} transaksi`;

      show('chartDiscEmpty', discTxTotal === 0);
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('payments_mix failed', e);
    const tb = qs('tablePayMix')?.querySelector('tbody');
    if (tb) tb.innerHTML = `<tr><td colspan="3" class="muted">Gagal memuat.</td></tr>`;
    const td = qs('tableDisc')?.querySelector('tbody');
    if (td) td.innerHTML = `<tr><td colspan="3" class="muted">Gagal memuat.</td></tr>`;
    show('chartPayMixEmpty', true);
    show('chartDiscEmpty', true);
  }

  // ---- SALES: by hour ----
  try {
    const byh = await fetchJSON('/api/analytics/by_hour', { from: fr, to });
    if (seq !== __loadSeq) return;

    const hours = byh.hours || [];
    const hourVals = hours.map(x => x.gross || 0);
    const hasHour  = hourVals.some(v => v > 0);

    // Insight: peak hour
    if (Array.isArray(hours) && hours.length) {
      const best = hours.reduce((best, h) => (h.gross||0) > (best.gross||0) ? h : best, { gross:0 });
      if (qs('insPeakHour')) qs('insPeakHour').textContent = best.gross > 0
        ? `${best.hh}:00 — ${fmtIDR(best.gross)}`
        : '-';
    }

    if (!hasChart()) {
      renderHourFallback(hours);
    } else {
      show('chartHourEmpty', !hasHour);
      if (chartHour) chartHour.destroy();
      const elHour = qs('chartHour');
      if (elHour && hasHour) {
        const hourMax = Math.max(0, ...hourVals);
        chartHour = new Chart(elHour, {
          type: 'bar',
          data: { labels: hours.map(x => x.hh), datasets: [{ label: 'Gross', data: hourVals }] },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => fmtIDR(ctx.parsed.y) } } },
            scales: {
              x: { grid: { display: false } },
              y: { beginAtZero: true, suggestedMax: Math.round(hourMax * 1.1), ticks: { callback: v => fmtIDRCompact(v) } }
            }
          }
        });
      }
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('by_hour failed', e);
    show('chartHourEmpty', true);
  }

  // ---- ITEMS: category rollup + drilldown ----
  await loadItemCategories(fr, to, seq);
  await loadModifierUsage(fr, to, seq);

  // ---- OPS ----
  try {
    const ops = await fetchJSON('/api/analytics/ops', { from: fr, to });
    if (seq !== __loadSeq) return;

    const tb2 = qs('tableTurns')?.querySelector('tbody');
    if (tb2) {
      tb2.innerHTML = '';
      (ops.tables || []).forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.table_number}</td><td>${r.sessions}</td><td>${(Number(r.avg_minutes) || 0).toFixed(1)}</td>`;
        tb2.appendChild(tr);
      });
      if (!tb2.children.length) {
        tb2.innerHTML = `<tr><td colspan="3" class="muted">Tidak ada data.</td></tr>`;
      }
    }
    const split = qs('splitCount');
    if (split) split.textContent = ops.split_sessions ?? 0;
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('ops failed', e);
    const tb2 = qs('tableTurns')?.querySelector('tbody');
    if (tb2) tb2.innerHTML = `<tr><td colspan="3" class="muted">Gagal memuat.</td></tr>`;
  }

  // ---- RESERVATIONS ----
  try {
    const rv = await fetchJSON('/api/analytics/reservations', { from: fr, to });
    if (seq !== __loadSeq) return;

    const tb3 = qs('tableRes')?.querySelector('tbody');
    if (tb3) {
      tb3.innerHTML = '';
      (rv.by_status || []).forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.status}</td><td>${r.cnt}</td>`;
        tb3.appendChild(tr);
      });
      if (!tb3.children.length) {
        tb3.innerHTML = `<tr><td colspan="2" class="muted">Tidak ada data.</td></tr>`;
      }
    }
    const noshow = qs('noShow');
    if (noshow) noshow.textContent = rv.no_show ?? 0;
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('reservations failed', e);
    const tb3 = qs('tableRes')?.querySelector('tbody');
    if (tb3) tb3.innerHTML = `<tr><td colspan="2" class="muted">Gagal memuat.</td></tr>`;
  }

  // ---- STAFF ----
  try {
    const st = await fetchJSON('/api/analytics/staff', { from: fr, to });
    if (seq !== __loadSeq) return;

    const tbC = qs('tableCashiers')?.querySelector('tbody');
    if (tbC) {
      tbC.innerHTML = '';
      (st.cashiers || []).forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.name || '-'}</td><td>${(r.payments_cnt || 0).toLocaleString('id-ID')}</td><td>${fmtIDR(r.gross_handled || 0)}</td>`;
        tbC.appendChild(tr);
      });
      if (!tbC.children.length) tbC.innerHTML = `<tr><td colspan="3" class="muted">Tidak ada data.</td></tr>`;
    }

    const tbW = qs('tableWaiters')?.querySelector('tbody');
    if (tbW) {
      tbW.innerHTML = '';
      (st.waiters || []).forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.name || '-'}</td><td>${(r.items_added || 0).toLocaleString('id-ID')}</td><td>${fmtIDR(r.items_value || 0)}</td>`;
        tbW.appendChild(tr);
      });
      if (!tbW.children.length) tbW.innerHTML = `<tr><td colspan="3" class="muted">Tidak ada data.</td></tr>`;
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('staff failed', e);
    const tbC = qs('tableCashiers')?.querySelector('tbody');
    if (tbC) tbC.innerHTML = `<tr><td colspan="3" class="muted">Gagal memuat.</td></tr>`;
    const tbW = qs('tableWaiters')?.querySelector('tbody');
    if (tbW) tbW.innerHTML = `<tr><td colspan="3" class="muted">Gagal memuat.</td></tr>`;
  }

  // ---- STAFF: void/cancel audit ----
  await loadStaffVoids(fr, to, seq);

  // ---- SERVICE TYPE MIX ----
  try {
    const svc = await fetchJSON('/api/analytics/service_mix', { from: fr, to });
    if (seq !== __loadSeq) return;

    const tb = qs('tableServiceMix')?.querySelector('tbody');
    if (tb) {
      tb.innerHTML = '';
      const rows = (svc.service_mix || []);
      rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${(r.service_type || '').toUpperCase()}</td><td>${fmtIDR(r.revenue || 0)}</td><td>${(r.lines || 0).toLocaleString('id-ID')}</td>`;
        tb.appendChild(tr);
      });
      if (!tb.children.length) tb.innerHTML = `<tr><td colspan="3" class="muted">Tidak ada data.</td></tr>`;
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('service_mix failed', e);
    const tb = qs('tableServiceMix')?.querySelector('tbody');
    if (tb) tb.innerHTML = `<tr><td colspan="3" class="muted">Gagal memuat.</td></tr>`;
  }

  // ---- QR PERFORMANCE ----
  try {
    const qr = await fetchJSON('/api/analytics/qr', { from: fr, to });
    if (seq !== __loadSeq) return;

    const k = qr.kpi || {};
    if (qs('kpiQrGross')) qs('kpiQrGross').textContent = fmtIDR(k.gross);
    if (qs('kpiQrLines')) qs('kpiQrLines').textContent = (k.lines || 0).toLocaleString('id-ID');
    if (qs('kpiQrQty')) qs('kpiQrQty').textContent = fmtQty(k.qty || 0, 1);
    if (qs('kpiQrSessions')) qs('kpiQrSessions').textContent = (k.sessions || 0).toLocaleString('id-ID');
    if (qs('kpiQrTables')) qs('kpiQrTables').textContent = (k.tables || 0).toLocaleString('id-ID');
    if (qs('kpiQrAov')) qs('kpiQrAov').textContent = fmtIDR(k.aov_per_session || 0);

    if (qs('kpiQrOutstanding')) qs('kpiQrOutstanding').textContent = fmtIDR(k.outstanding_gross || 0);
    if (qs('kpiQrOutstandingQty')) qs('kpiQrOutstandingQty').textContent = `${fmtQty(k.outstanding_qty || 0, 1)} qty`;

    const sharePct = ((k.share_of_revenue || 0) * 100);
    if (qs('kpiQrShare')) qs('kpiQrShare').textContent = `${sharePct.toFixed(1)}%`;

    // Status table
    const stRows = qr.statuses || [];
    const tbSt = qs('tableQrStatuses')?.querySelector('tbody');
    if (tbSt) {
      tbSt.innerHTML = '';
      stRows.forEach(r => {
        const label = (r.status || '').toUpperCase();
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${label || '-'}</td><td>${(r.lines || 0).toLocaleString('id-ID')}</td><td>${fmtQty(r.qty || 0, 1)}</td><td>${fmtIDR(r.gross || 0)}</td>`;
        tbSt.appendChild(tr);
      });
      if (!tbSt.children.length) tbSt.innerHTML = `<tr><td colspan="4" class="muted">Tidak ada data.</td></tr>`;
    }

    // Top tables
    const tbl = qs('tableQrTables')?.querySelector('tbody');
    if (tbl) {
      tbl.innerHTML = '';
      (qr.tables || []).forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.table_number || '-'}</td><td>${(r.sessions || 0).toLocaleString('id-ID')}</td><td>${(r.lines || 0).toLocaleString('id-ID')}</td><td>${fmtQty(r.qty || 0, 1)}</td><td>${fmtIDR(r.gross || 0)}</td>`;
        tbl.appendChild(tr);
      });
      if (!tbl.children.length) tbl.innerHTML = `<tr><td colspan="5" class="muted">Tidak ada data.</td></tr>`;
    }

    // Hourly chart
    const hours = qr.hours || [];
    const hasHour = hours.some(h => (h.gross || 0) > 0);
    if (!hasChart()) {
      const box = qs('chartQrHourEmpty');
      if (box) { box.hidden = false; box.textContent = 'Chart membutuhkan Chart.js.'; }
    } else {
      show('chartQrHourEmpty', !hasHour);
      if (chartQrHour) chartQrHour.destroy();

      const el = qs('chartQrHour');
      if (el && hasHour) {
        const labels = hours.map(h => `${h.hh}:00`);
        const gross = hours.map(h => h.gross || 0);
        chartQrHour = new Chart(el, {
          type: 'bar',
          data: {
            labels,
            datasets: [{ label: 'Gross QR per Jam', data: gross }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: { callbacks: { label: (ctx) => fmtIDR(ctx.parsed.y || 0) } }
            },
            scales: {
              x: { grid: { display: false } },
              y: { beginAtZero: true, ticks: { callback: v => fmtIDRCompact(v) } }
            }
          }
        });
      }
    }

    // Legacy queue (qr.qr_orders)
    const qTable = qs('tableQrQueue')?.querySelector('tbody');
    if (qTable) {
      qTable.innerHTML = '';
      (qr.queue || []).forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${(r.status || '-').toUpperCase()}</td><td>${(r.count || 0).toLocaleString('id-ID')}</td>`;
        qTable.appendChild(tr);
      });
      if (!qTable.children.length) qTable.innerHTML = `<tr><td colspan="2" class="muted">Tidak ada data.</td></tr>`;
    }
  } catch (e) {
    if (seq !== __loadSeq) return;
    console.warn('qr analytics failed', e);
    const tbSt = qs('tableQrStatuses')?.querySelector('tbody');
    if (tbSt) tbSt.innerHTML = `<tr><td colspan="4" class="muted">Gagal memuat.</td></tr>`;
    const tbl = qs('tableQrTables')?.querySelector('tbody');
    if (tbl) tbl.innerHTML = `<tr><td colspan="5" class="muted">Gagal memuat.</td></tr>`;
    const qTable = qs('tableQrQueue')?.querySelector('tbody');
    if (qTable) qTable.innerHTML = `<tr><td colspan="2" class="muted">Gagal memuat.</td></tr>`;
    show('chartQrHourEmpty', true);
  }

  await loadTrends();
  
  forceChartResize();
}

async function loadTrends() {
  const fr = qs('fromDate')?.value;
  const to = qs('toDate')?.value;
  const group = currentTrendGroup;

  try {
    const data = await fetchJSON('/api/analytics/trends', { from: fr, to, group });
    if (!data || data.group !== group) return;

    const moneySlots = data.money_tx || [];
    const arrSlots   = data.arrivals || [];

    // ----- Trend Pendapatan (avg) -----
    const labelsMoney = moneySlots.map(s => s.label);
    const avgMoney    = moneySlots.map(s => s.avg_amount || 0);
    const hasMoney    = avgMoney.some(v => v > 0);

    if (!hasChart()) {
      const box = qs('chartTrendMoneyEmpty');
      if (box) {
        box.hidden = false;
        box.textContent = 'Chart membutuhkan Chart.js.';
      }
    } else {
      show('chartTrendMoneyEmpty', !hasMoney);
      if (chartTrendMoney) chartTrendMoney.destroy();

      const el = qs('chartTrendMoney');
      if (el && hasMoney) {
        const maxVal = Math.max(0, ...avgMoney);
        chartTrendMoney = new Chart(el, {
          type: 'line',
          data: {
            labels: labelsMoney,
            datasets: [{
              label: 'Pendapatan rata-rata',
              data: avgMoney,
              tension: 0.35
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: (ctx) => {
                    const slot = moneySlots[ctx.dataIndex] || {};
                    const avg = fmtIDR(ctx.parsed.y);
                    const total = fmtIDR(slot.total_amount || 0);
                    const samples = slot.sample_cnt || 0;
                    return `${avg} (avg) • ${total} total (${samples} sample)`;
                  }
                }
              }
            },
            scales: {
              x: { grid: { display: false } },
              y: {
                beginAtZero: true,
                ticks: { callback: v => fmtIDRCompact(v) },
                grid: { drawBorder: false }
              }
            }
          }
        });
      }
    }

    // ----- Trend Jumlah Transaksi -----
    const labelsTx = moneySlots.map(s => s.label);
    const avgTx    = moneySlots.map(s => s.avg_tx || 0);
    const hasTx    = avgTx.some(v => v > 0);

    if (!hasChart()) {
      const box = qs('chartTrendTxEmpty');
      if (box) {
        box.hidden = false;
        box.textContent = 'Chart membutuhkan Chart.js.';
      }
    } else {
      show('chartTrendTxEmpty', !hasTx);
      if (chartTrendTx) chartTrendTx.destroy();

      const elTx = qs('chartTrendTx');
      if (elTx && hasTx) {
        const maxTx = Math.max(0, ...avgTx);
        chartTrendTx = new Chart(elTx, {
          type: 'bar',
          data: {
            labels: labelsTx,
            datasets: [{
              label: 'Transaksi rata-rata',
              data: avgTx
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: (ctx) => {
                    const slot = moneySlots[ctx.dataIndex] || {};
                    const avg = (ctx.parsed.y || 0).toFixed(2);
                    const total = slot.total_tx || 0;
                    const samples = slot.sample_cnt || 0;
                    return `${avg} trx/hari • ${total} total (${samples} sample)`;
                  }
                }
              }
            },
            scales: {
              x: { grid: { display: false } },
              y: {
                beginAtZero: true,
                suggestedMax: Math.round(maxTx * 1.2),
                ticks: { callback: v => v.toLocaleString('id-ID') }
              }
            }
          }
        });
      }
    }

    // ----- Trend Waktu Masuk -----
    const groupType = data.group || group;

    if (!hasChart()) {
      const box = qs('chartTrendArrivalsEmpty');
      if (box) {
        box.hidden = false;
        box.textContent = 'Chart membutuhkan Chart.js.';
      }
      return;
    }

    if (chartTrendArrivals) chartTrendArrivals.destroy();

    if (!arrSlots.length) {
      show('chartTrendArrivalsEmpty', true);
      return;
    } else {
      show('chartTrendArrivalsEmpty', false);
    }

    const labelsArr = arrSlots.map(s => s.label);

    if (groupType === 'hour') {
      // avg sessions per jam
      const avgSess = arrSlots.map(s => s.avg_sessions || 0);
      const maxSess = Math.max(0, ...avgSess);
      const elA = qs('chartTrendArrivals');
      if (elA) {
        chartTrendArrivals = new Chart(elA, {
          type: 'bar',
          data: {
            labels: labelsArr,
            datasets: [{
              label: 'Sesi rata-rata per jam',
              data: avgSess
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: (ctx) => {
                    const slot = arrSlots[ctx.dataIndex] || {};
                    const avg = (ctx.parsed.y || 0).toFixed(2);
                    const total = slot.total_sessions || 0;
                    const samples = slot.sample_cnt || 0;
                    return `${avg} sesi/jam • ${total} total (${samples} hari)`;
                  }
                }
              }
            },
            scales: {
              x: { grid: { display: false } },
              y: {
                beginAtZero: true,
                suggestedMax: Math.round(maxSess * 1.2),
                ticks: { callback: v => v.toLocaleString('id-ID') }
              }
            }
          }
        });
      }
    } else {
      // avg jam masuk (time-of-day) per dow / month / year
      const avgSec = arrSlots.map(s => s.avg_seconds || 0);
      const elA = qs('chartTrendArrivals');
      if (elA) {
        chartTrendArrivals = new Chart(elA, {
          type: 'line',
          data: {
            labels: labelsArr,
            datasets: [{
              label: 'Rata-rata jam masuk',
              data: avgSec,
              tension: 0.35
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: (ctx) => {
                    const slot = arrSlots[ctx.dataIndex] || {};
                    const jam = fmtClockFromSeconds(ctx.parsed.y);
                    const cnt = slot.sessions_cnt || 0;
                    return `${jam} • ${cnt.toLocaleString('id-ID')} sesi`;
                  }
                }
              }
            },
            scales: {
              x: { grid: { display: false } },
              y: {
                beginAtZero: false,
                ticks: {
                  callback: v => fmtClockFromSeconds(v)
                }
              }
            }
          }
        });
      }
    }

  } catch (e) {
    console.warn('trends failed', e);
    show('chartTrendMoneyEmpty', true);
    show('chartTrendTxEmpty', true);
    show('chartTrendArrivalsEmpty', true);
  }
}


function quickRangeBind(){
  const box = qs('quickRanges');
  if (!box) return;
  box.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.chip[data-range]');
    if (!btn) return;
    setRange(btn.dataset.range);
    loadAll();
  });
}

function bindTrendControls() {
  const box = document.getElementById('trendGroupChips');
  if (!box) return;
  box.addEventListener('click', (ev) => {
    const btn = ev.target.closest('.chip[data-group]');
    if (!btn) return;
    const grp = btn.dataset.group;
    if (!grp) return;

    currentTrendGroup = grp;

    box.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');

    loadTrends();   // reload charts with new grouping
  });
}

function bindItemRollupControls() {
  const catTable = qs('tableItemCategories');
  if (catTable) {
    catTable.addEventListener('click', (ev) => {
      const tr = ev.target.closest('tr[data-category]');
      if (!tr) return;
      __itemSelectedCategory = tr.dataset.category || null;
      __itemSelectedSubcategory = null;
      catTable.querySelectorAll('tbody tr').forEach(row => row.classList.toggle('active', row === tr));
      const fr = qs('fromDate')?.value;
      const to = qs('toDate')?.value;
      loadItemSubcategories(fr, to, __loadSeq);
    });
  }

  const subTable = qs('tableItemSubcategories');
  if (subTable) {
    subTable.addEventListener('click', (ev) => {
      const tr = ev.target.closest('tr[data-subcategory]');
      if (!tr) return;
      __itemSelectedSubcategory = tr.dataset.subcategory || null;
      subTable.querySelectorAll('tbody tr').forEach(row => row.classList.toggle('active', row === tr));
      const fr = qs('fromDate')?.value;
      const to = qs('toDate')?.value;
      loadItemDishes(fr, to, __loadSeq);
    });
  }

  const pager = qs('itemDishesPager');
  if (pager) {
    pager.addEventListener('click', (ev) => {
      const btn = ev.target.closest('button[data-dir]');
      if (!btn) return;
      const totalPages = Math.max(1, Math.ceil(__itemDishRows.length / DISH_PAGE_SIZE));
      if (btn.dataset.dir === 'prev') {
        __itemDishPage = Math.max(0, __itemDishPage - 1);
      } else if (btn.dataset.dir === 'next') {
        __itemDishPage = Math.min(totalPages - 1, __itemDishPage + 1);
      }
      renderDishPage();
    });
  }

  const clearBtn = qs('itemDetailClear');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      __itemSelectedCategory = null;
      __itemSelectedSubcategory = null;
      resetDishTable('Pilih subkategori.');
      show('itemDetailCard', false);
      catTable?.querySelectorAll('tbody tr').forEach(row => row.classList.remove('active'));
      subTable?.querySelectorAll('tbody tr').forEach(row => row.classList.remove('active'));
    });
  }
}

function bindStaffVoidControls() {
  const table = qs('tableStaffVoids');
  if (table) {
    table.addEventListener('click', (ev) => {
      const tr = ev.target.closest('tr[data-user-id]');
      if (!tr) return;
      const uid = tr.dataset.userId;
      if (!uid) return;
      __staffVoidSelectedUserId = uid;
      table.querySelectorAll('tbody tr').forEach(row => row.classList.toggle('active', row === tr));
      const fr = qs('fromDate')?.value;
      const to = qs('toDate')?.value;
      loadStaffVoidItems(fr, to, __loadSeq);
    });
  }

  const clearBtn = qs('staffVoidDetailClear');
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      __staffVoidSelectedUserId = null;
      show('staffVoidDetailCard', false);
      table?.querySelectorAll('tbody tr').forEach(row => row.classList.remove('active'));
    });
  }

  const toggle = qs('staffVoidExcludeSeafood');
  if (toggle) {
    toggle.addEventListener('change', () => {
      __staffVoidSelectedUserId = null;
      show('staffVoidDetailCard', false);
      table?.querySelectorAll('tbody tr').forEach(row => row.classList.remove('active'));
      const fr = qs('fromDate')?.value;
      const to = qs('toDate')?.value;
      loadStaffVoids(fr, to, __loadSeq);
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const today = new Date();
  if (qs('fromDate')) qs('fromDate').value = dateISO(today);
  if (qs('toDate'))   qs('toDate').value   = dateISO(today);

  quickRangeBind();
  setRange('today');
  tabbind();
  bindTrendControls();
  bindItemRollupControls();
  bindStaffVoidControls();

  const applyBtn = qs('applyFilters');
  if (applyBtn) applyBtn.addEventListener('click', loadAll);

  loadAll();

  window.addEventListener('chartjs:ready', () => { loadAll(); });
});
