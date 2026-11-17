(() => {
  const fmtRp = (n) => `Rp ${Number(n || 0).toLocaleString('id-ID')}`;
  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
  const getEl = (id) => document.getElementById(id);
  const POS = (window.POS = window.POS || {});
  const isDemoMode = () =>
    typeof POS.isDemoMode === 'function' ? POS.isDemoMode() : window.POS_DEMO_MODE === true;
  const notify = (message, type = 'info', duration = 2400) => {
    if (POS && typeof POS.notify === 'function') {
      POS.notify(message, type, duration);
      return;
    }
    if (POS && typeof POS.toast === 'function') {
      POS.toast(message, { type, duration });
      return;
    }
    alert(String(message || ''));
  };
  const showDemoPrintModal = (config) => {
    if (POS && typeof POS.showDemoPrintModal === 'function') {
      POS.showDemoPrintModal(config);
      return;
    }
    notify('Print preview staged locally.', 'info', 2200);
  };
  const withBusy = async (btn, text, fn) => {
    if (POS && typeof POS.withButtonBusy === 'function') {
      return POS.withButtonBusy(btn, text, fn);
    }
    return Promise.resolve(fn());
  };
  const normalizeGroup = (g) => (g === 'all' || g == null || g === 'main') ? 'main' : String(g);
  const splitMetaName = (label) => {
    const meta = Array.isArray(window.SPLIT_META) ? window.SPLIT_META : [];
    const key = String(label ?? '').trim();
    if (!key) return '';
    const hit = meta.find(m => String(m.key ?? m.label ?? m.id ?? m.group ?? '').trim() === key);
    const name = (hit?.name ?? hit?.title ?? '').toString().trim();
    return name || '';
  };
  const displayGroupLabel = (label) => {
    if (label === 'main') return 'Bill 1';
    const name = splitMetaName(label);
    return name || `Bill ${label}`;
  };

  let selectedDiscount = 0;

  // Default Payment Status = False
  let closingBill = false;

  const bool = (v) => (typeof v === 'boolean' ? v : (typeof v === 'string' ? (v.toLowerCase() === 'true' || v === '1') : !!v));
  const BILLING_CFG = (window.POS_CONFIG && window.POS_CONFIG.billing) ? window.POS_CONFIG.billing : {};
  const TAX_PERCENT = Number(BILLING_CFG.tax_percent ?? window.TAX_PERCENT ?? 10);
  const SERVICE_PERCENT = Number(BILLING_CFG.service_percent ?? window.SERVICE_PCT ?? 5);
  const TAX_ON_SERVICE = bool(BILLING_CFG.tax_on_service ?? window.TAX_ON_SERVICE);
  const TAKEAWAY_FEE_IDR = Number(BILLING_CFG.takeaway_fee_idr ?? window.TAKEAWAY_FEE_IDR ?? 10000);
  const ROUNDING_STEP_IDR = Number(BILLING_CFG.rounding_step_idr ?? window.ROUNDING_STEP_IDR ?? 100);
  const isTakeaway = () => bool(window && window.IS_TAKEAWAY);
  const isDineIn   = () => !isTakeaway();
  const svcPercent = () => (isTakeaway() ? 0 : SERVICE_PERCENT);
  async function softSessionRefresh() {
    if (window.POS && typeof window.POS.softSessionRefresh === 'function') {
      return window.POS.softSessionRefresh();
    }
    if (window.POS && typeof window.POS.requestSessionState === 'function') {
      try {
        await window.POS.requestSessionState({ skipRows: false });
        return true;
      } catch (_) {}
    }
    return false;
  }

  const DEFAULT_PAYMENT_KEYS = ['cash', 'debit', 'mastercard', 'visa'];
  const PAYMENT_METHOD_DEFS = {
    cash: { key: 'cash', method: 'cash', label: 'Cash', needsCash: true },
    debit: { key: 'debit', method: 'debit', label: 'Debit' },
    mastercard: { key: 'mastercard', method: 'card', label: 'Mastercard', cardType: 'mastercard' },
    visa: { key: 'visa', method: 'card', label: 'Visa', cardType: 'visa' },
    card: { key: 'card', method: 'card', label: 'Card', askCardType: true },
    credit: { key: 'credit', method: 'credit', label: 'Credit', askCardType: true },
    qris: { key: 'qris', method: 'qris', label: 'QRIS' },
    transfer: { key: 'transfer', method: 'transfer', label: 'Transfer' },
  };
  const rawPaymentKeys = Array.isArray(BILLING_CFG.payment_methods)
    ? BILLING_CFG.payment_methods
    : DEFAULT_PAYMENT_KEYS;
  const paymentKeys = rawPaymentKeys
    .map((m) => String(m || '').trim().toLowerCase())
    .filter(Boolean);
  const PAYMENT_OPTIONS = [];
  const PAYMENT_OPTION_MAP = {};
  const seenPaymentKeys = new Set();
  for (const key of paymentKeys) {
    if (seenPaymentKeys.has(key)) continue;
    const def = PAYMENT_METHOD_DEFS[key];
    if (def) {
      PAYMENT_OPTIONS.push(def);
      PAYMENT_OPTION_MAP[def.key] = def;
      seenPaymentKeys.add(key);
    }
  }
  if (!PAYMENT_OPTIONS.length) {
    DEFAULT_PAYMENT_KEYS.forEach((key) => {
      const def = PAYMENT_METHOD_DEFS[key];
      if (!def) return;
      PAYMENT_OPTIONS.push(def);
      PAYMENT_OPTION_MAP[def.key] = def;
    });
  }
  const defaultPaymentKey = () => {
    if (PAYMENT_OPTION_MAP.debit) return 'debit';
    return PAYMENT_OPTIONS[0]?.key || 'cash';
  };

  // Default payment = debit (or first configured option)
  let selectedPayment = defaultPaymentKey();

  const HAS_SPLIT = Array.isArray(window.SPLIT_LABELS) && window.SPLIT_LABELS.length > 0;

  // DP amount per group (for split bills)
  const DP_PREFS_AMOUNT = window.DP_PREFS_AMOUNT || (window.DP_PREFS_AMOUNT = {});
  const dpRemaining = () => Math.max(0, Number(window.DP_REMAINING || 0));
  function currentGroupKey() {
    return normalizeGroup(window.CURRENT_GROUP || 'main');
  }
  function readDpAmountInput() {
    const el = getEl('dp-amount');
    if (!el) return { value: 0, empty: true };
    const raw = String(el.value ?? '').trim();
    if (raw === '') return { value: 0, empty: true };
    return { value: Math.max(parseIntSafe(raw), 0), empty: false };
  }
  function getDpRequestInfo(gross) {
    const remaining = dpRemaining();
    const cap = Math.min(remaining, Math.max(0, Number(gross || 0)));
    const { value, empty } = readDpAmountInput();
    let want = empty ? cap : value;
    if (want < 0) want = 0;
    if (want > cap) want = cap;
    return { remaining, cap, want, empty };
  }
  function storeDpAmountForGroup(val) {
    if (!HAS_SPLIT) return;
    const g = currentGroupKey();
    if (!g) return;
    if (val == null || val === '') {
      delete DP_PREFS_AMOUNT[g];
    } else {
      DP_PREFS_AMOUNT[g] = val;
    }
  }
  function loadDpAmountForGroup() {
    const el = getEl('dp-amount');
    if (!el) return;
    const g = currentGroupKey();
    const saved = DP_PREFS_AMOUNT[g];
    el.value = (saved == null) ? '' : String(saved);
  }

  // --- Persist packaging per-session so Batal doesn't reset it ---
  const PKG_KEY = `pkg:${window.SESSION_ID}`;
  let pkgState = (sessionStorage.getItem(PKG_KEY) === '1');  // true if previously ON
  window.__pkgOn = pkgState; // exposed for other scripts if needed

  function packagingOn() {
    // driven by checkbox when present, but fall back to persisted state
    const chk = getEl('apply-packaging');
    const uiOn = !!chk?.checked;
    return uiOn || (!chk && pkgState);
  }

  function getSelectedOption() {
    if (selectedPayment && PAYMENT_OPTION_MAP[selectedPayment]) {
      return PAYMENT_OPTION_MAP[selectedPayment];
    }
    return PAYMENT_OPTIONS[0] || null;
  }

  function renderPaymentButtons() {
    const wrap = getEl('payment_buttons');
    if (!wrap) return;
    wrap.innerHTML = '';
    PAYMENT_OPTIONS.forEach((opt) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.id = `payment_${opt.key}`;
      btn.textContent = opt.label;
      btn.addEventListener('click', () => selectPayment(opt.key));
      wrap.appendChild(btn);
    });
  }

  function currentSubtotal() {
    const g = normalizeGroup(window.CURRENT_GROUP || 'main');
    // 1) Prefer authoritative server value
    const fromServer = window.GROUP_SUBTOTALS?.[g];
    if (Number.isFinite(fromServer)) return (fromServer | 0);

    // 2) Fall back to rows (group-aware)
    const normGroup = (v) => {
      const s = (v ?? '').toString().trim();
      return s === '' ? 'main' : s;
    };

    if (Array.isArray(window.ORDER_ROWS) && window.ORDER_ROWS.length) {
      let total = 0;
      for (const r of window.ORDER_ROWS) {
        const st = (r.status ?? '').toString().trim().toLowerCase();
        if (st === 'cancelled') continue;

        const grp = normGroup(r.bill_group ?? r.group ?? r.group_label);
        if (g === 'main' ? grp !== 'main' : String(grp) !== String(g)) continue;

        const qty  = Number(r.qty ?? r.quantity ?? r.amount ?? r.count ?? 0) - Number(r.void_qty ?? 0);
        if (qty <= 0) continue;

        if (r.total_price != null && r.total_price !== '') {
          total += (parseInt(String(r.total_price), 10) || 0);
        } else {
          const unit = Number(r.unit_price ?? r.price ?? r.unit ?? r.rate ?? 0);
          total += Math.round(Math.max(qty, 0) * unit);
        }
      }
      return total;
    }

    // 3) Nothing else available
    return 0;
  }

  function floor100(n) {
    const x = Number(n || 0);
    const step = Number(ROUNDING_STEP_IDR || 0);
    if (step <= 0) return Math.floor(x);
    return Math.floor(x / step) * step;
  }

  function ceil100(n) {
    const x = Number(n || 0);
    const step = Number(ROUNDING_STEP_IDR || 0);
    if (step <= 0) return Math.ceil(x);
    return Math.ceil(x / step) * step;
  }

  let cashAuto = true;

  function roundUpTo(n, step) {
    if (step <= 0) return n;
    return Math.ceil(n / step) * step;
  }

  function suggestCash() {
    const active = getSelectedOption();
    if ((active?.method || selectedPayment) !== 'cash') return;
    const el = getEl('cash_received');
    if (!el || el.getAttribute('data-auto-cash') === '0') return;

    const { remaining } = computeAmountDue();
    const suggested = roundUpTo(remaining, 50000);
    if (String(el.value || '') !== String(suggested)) {
      el.value = String(suggested);
    }
  }

  function getDiscountFromUI(subtotal){
    const pctEl = getEl('discount_percent');
    const valEl = getEl('discount_value');

    const rawPct = clamp(parseFloat(pctEl?.value ?? '0') || 0, 0, 100);
    const rawVal = Math.max(parseIntSafe(valEl?.value ?? '0'), 0);

    if (subtotal <= 0) {
      return { percent: 0, amount: 0, mode: 'none' };
    }

    const active = document.activeElement;
    const editingPct = active === pctEl;
    const editingVal = active === valEl;

    // ⬇️ If user is typing in the % field → force "percent mode"
    if (editingPct) {
      const percent = rawPct;
      const amount  = Math.min(Math.round(subtotal * (percent / 100)), subtotal);
      return { percent, amount, mode: 'percent' };
    }

    // If user is editing nominal, or nominal has value → "value mode"
    if (rawVal > 0) {
      const amount  = Math.min(rawVal, subtotal);
      const percent = clamp(Math.round((amount / subtotal) * 100), 0, 100);
      return { percent, amount, mode: 'value' };
    }

    // Default → percent mode
    const amount = Math.round(subtotal * (rawPct / 100));
    return { percent: rawPct, amount, mode: 'percent' };
  }



  function syncDiscountInputs(subtotal){
    const pctEl = getEl('discount_percent');
    const valEl = getEl('discount_value');
    if (!pctEl || !valEl) return;

    const d = getDiscountFromUI(subtotal);
    const wantVal = String(d.amount);
    const wantPct = String(d.percent);

    const active = document.activeElement;
    const editingPct = active === pctEl;
    const editingVal = active === valEl;

    // If the user is editing percent, only sync the nominal field, and vice versa.
    if (!editingVal && valEl.value !== wantVal) valEl.value = wantVal;
    if (!editingPct && pctEl.value !== wantPct) pctEl.value = wantPct;
  }


  function computeAmountDue() {
    const subtotal = currentSubtotal();

    const d = getDiscountFromUI(subtotal);
    const discountPercent = d.percent;
    const discountAmount  = d.amount;

    const afterDiscount = subtotal - discountAmount;

    const packaging = packagingOn() ? TAKEAWAY_FEE_IDR : 0;
    const base = afterDiscount + packaging;

    const service = Math.round(base * (svcPercent() / 100));
    const taxBase = TAX_ON_SERVICE ? (base + service) : base;
    const tax = Math.round(taxBase * (TAX_PERCENT / 100));
    const gross = base + service + tax;

    const applyDP = !!getEl('apply-dp')?.checked;
    const dpInfo = getDpRequestInfo(gross);
    const dpShown = applyDP ? dpInfo.want : 0;

    const remainingRaw = Math.max(gross - dpShown, 0);
    // ⬆️ ROUND UP to nearest Rp 100
    const remainingRounded = ceil100(remainingRaw);

    return {
      subtotal,
      discountPercent,
      discountAmount,
      packaging,
      base,
      service,
      tax,
      gross,
      dpShown,
      dpCap: dpInfo.cap,
      dpRemaining: dpInfo.remaining,
      remaining: remainingRounded,
      // positive: how much we added because of pembulatan
      rounding_down: (remainingRounded - remainingRaw),
    };
  }

  async function updatePriceBreakdown() {
    const breakdownEl = getEl('finalPriceBreakdown');
    const changeEl = getEl('changeAmount');
    if (!breakdownEl) return;

    let amounts = null;
    try {
      amounts = await fetchFreshAmounts();
    } catch (_) {}
    if (!amounts) amounts = computeAmountDue();

    const {
      subtotal,
      discountPercent,
      discountAmount,
      packaging,
      service,
      tax,
      gross,
      dpShown = 0,
      dpCap: dpCapRaw = 0,
      dpRemaining: dpRemainingRaw = 0,
    } = amounts;
    const dpRemainingVal = dpRemainingRaw || dpRemaining();
    const dpCapVal = dpCapRaw || Math.min(dpRemainingVal, gross | 0);

    // Recompute normalized remaining in case `amounts` came from the server
    const remainingRaw = Math.max((gross | 0) - (dpShown | 0), 0);
    const remaining = ceil100(remainingRaw);
    const roundingDown = remaining - remainingRaw;  // positive

    // Packaging indicator
    const badge = getEl('pkg-indicator');
    if (badge) {
      const on = packaging > 0;
      badge.style.display = on ? 'block' : 'none';
      if (on) badge.textContent = `TAKE AWAY (+${fmtRp(packaging)})`;
    }

    const pkgLine = (packaging > 0)
      ? `Biaya Take Away: ${fmtRp(packaging)}`
      : null;

    syncDiscountInputs(subtotal);

    // Pembulatan line (now correctly labeled + sign & "ke atas")
    const pembulatanLine = roundingDown > 0
      ? `Pembulatan ke atas: +${fmtRp(roundingDown)}`
      : null;

    const dpHint = getEl('dp-hint');
    if (dpHint) {
      if (dpRemainingVal > 0) {
        dpHint.textContent = `Sisa DP: ${fmtRp(dpRemainingVal)} • Max bill ini: ${fmtRp(dpCapVal)}`;
      } else {
        dpHint.textContent = 'DP tidak tersedia';
      }
    }
    const dpInput = getEl('dp-amount');
    if (dpInput) {
      dpInput.setAttribute('max', String(dpCapVal));
      dpInput.disabled = dpRemainingVal <= 0;
    }

    breakdownEl.innerHTML = [
      `Subtotal: ${fmtRp(subtotal)}`,
      `Diskon (${discountPercent}%): -${fmtRp(discountAmount)}`,
      ...(pkgLine ? [pkgLine] : []),
      `Service (${svcPercent()}%): ${fmtRp(service)}`,
      `Pajak (${TAX_PERCENT}%): ${fmtRp(tax)}`,
      `<strong>Total: ${fmtRp(gross)}</strong>`,
      `<em>DP: -${fmtRp(dpShown)}</em>`,
      ...(pembulatanLine ? [pembulatanLine] : []),
      `<strong>Sisa Dibayar: ${fmtRp(remaining)}</strong>`,
    ].join('<br>');

    // Cash change / shortage uses the rounded remaining
    const active = getSelectedOption();
    if ((active?.method || selectedPayment) === 'cash') {
      const el = getEl('cash_received');
      if (el && el.getAttribute('data-auto-cash') !== '0') {
        suggestCash();
      }
      const raw = el?.value ?? '';
      const cashReceived = Number.parseInt(raw || '0', 10);
      if (!isNaN(cashReceived) && raw !== '') {
        const delta = cashReceived - remaining;
        changeEl.textContent = delta >= 0
          ? `Kembalian: ${fmtRp(delta)}`
          : `Kurang: ${fmtRp(-delta)}`;
      } else {
        changeEl.textContent = '';
      }
    } else {
      if (changeEl) changeEl.textContent = '';
    }
  }
  /* ---------- helpers (tiny, safe) ---------- */

  // Detect full Take Away session (prefer explicit flag if you already set one)
  function isFullTakeaway() {
    if (typeof window.IS_TAKEAWAY === 'boolean') return window.IS_TAKEAWAY;
    const tn = (window.TABLE_NUMBER || document.body?.dataset?.tableNumber || '').toUpperCase();
    if (tn === 'TA') return true;
    try { if (typeof svcPercent === 'function' && svcPercent() === 0) return true; } catch(_) {}
    return (document.title || '').toLowerCase().includes('take away');
  }

  // Sum from actual line rows, not from any displayed subtotal text
  function deriveFreshSubtotal(fallback = 0) {
    // Prefer rows with data-qty & data-unit-price (accurate and fast)
    const rows = Array.from(document.querySelectorAll('[data-qty][data-unit-price]'));
    let sum = 0;
    if (rows.length) {
      sum = rows.reduce((acc, tr) => {
        const qty  = parseFloat(tr.getAttribute('data-qty')) || 0;
        const unit = parseInt(tr.getAttribute('data-unit-price'), 10) || 0;
        return acc + Math.round(qty * unit);
      }, 0);
    }
    // Fallback: elements carrying precomputed line totals
    if (!sum) {
      const lt = Array.from(document.querySelectorAll('[data-line-total]'));
      if (lt.length) {
        sum = lt.reduce((a, el) => a + (parseInt(el.getAttribute('data-line-total'), 10) || 0), 0);
      }
    }
    return sum || fallback;
  }

  // If you expose an API for live totals, set window.URLS.amounts = "/your/json/endpoint"
  // Response can be either your computeAmountDue() shape or a payment/totals shape — we normalize it.
  async function fetchFreshAmounts() {
    if (!window.URLS || !window.URLS.amounts) return null;
    const r = await fetch(window.URLS.amounts, { cache: 'no-store' });
    if (!r.ok) return null;
    const j = await r.json();

    if ('subtotal' in j && 'gross' in j) return j; // already in expected shape

    // Normalize common server-side names
    const subtotal = (j.total_before_discount ?? j.subtotal ?? 0) | 0;
    const discountAmount = (j.discount_amount ?? 0) | 0;
    const discountPercent = (j.discount_percent ?? 0) | 0;
    const packaging = (j.packaging_fee ?? j.takeaway_fee ?? 0) | 0;
    const service = (j.service ?? 0) | 0;
    const tax = (j.tax ?? 0) | 0;

    const gross = ('gross' in j)
      ? (j.gross | 0)
      : (subtotal - discountAmount + packaging + service + tax);

    const dpShown = (j.dp_applied ?? j.dp_used ?? 0) | 0;
    const remaining = ('remaining' in j) ? (j.remaining | 0) : Math.max(0, gross - dpShown);

    return { subtotal, discountPercent, discountAmount, packaging, service, tax, gross, dpShown, remaining };
  }


  function setPackagingUI(on) {
    const chk = getEl('apply-packaging');
    const btn = getEl('btn-packaging-toggle');
    if (!chk || !btn) return;

    const effective = !!on;
    chk.checked = effective;
    btn.classList.toggle('on', effective);
    btn.setAttribute('aria-checked', String(!!effective));
    btn.textContent = effective
      ? `Biaya take away: ON (klik untuk matikan) +${fmtRp(TAKEAWAY_FEE_IDR)}`
      : `Tambahkan biaya take away (${fmtRp(TAKEAWAY_FEE_IDR)})`;

    // persist state
    pkgState = effective;
    window.__pkgOn = pkgState;
    try { sessionStorage.setItem(PKG_KEY, pkgState ? '1' : '0'); } catch(e){}

    updatePriceBreakdown();
  }

  function togglePackaging() {
    const chk = getEl('apply-packaging');
    setPackagingUI(!(chk?.checked));
  }

  function setDPUI(on) {
    const btn = getEl('btn-dp-toggle');
    const chk = getEl('apply-dp');
    if (!btn || !chk) return;
    const remaining = dpRemaining();
    if (remaining <= 0) {
      chk.checked = false;
      btn.classList.remove('on');
      btn.setAttribute('aria-checked', 'false');
      btn.textContent = 'DP tidak tersedia';
      btn.disabled = true;
      updatePriceBreakdown();
      return;
    }
    btn.disabled = false;
    chk.checked = !!on;
    btn.classList.toggle('on', !!on);
    btn.textContent = on ? 'DP Digunakan (klik untuk matikan)' : 'Gunakan DP untuk bill ini';
    btn.setAttribute('aria-checked', String(!!on));
    updatePriceBreakdown();
  }
  function toggleDP() {
    const chk = getEl('apply-dp');
    setDPUI(!(chk?.checked));
  }

  function selectPayment(key) {
    const normKey = String(key || '').trim().toLowerCase();
    selectedPayment = PAYMENT_OPTION_MAP[normKey] ? normKey : defaultPaymentKey();

    const active = getSelectedOption();
    PAYMENT_OPTIONS.forEach((opt) => {
      getEl('payment_' + opt.key)?.classList.toggle('selected', opt.key === selectedPayment);
    });

    const method = active?.method || selectedPayment;
    getEl('cash_section')?.style && (getEl('cash_section').style.display = method === 'cash' ? 'block' : 'none');
    getEl('card_section')?.style && (getEl('card_section').style.display = active?.askCardType ? 'block' : 'none');

    const cardEl = getEl('card_type');
    if (cardEl && active?.cardType) {
      cardEl.value = active.cardType;
    }

    if (method === 'cash') {
      const el = getEl('cash_received');
      if (el) el.setAttribute('data-auto-cash', '1'); // re-enable auto if switching back to cash
      suggestCash();
    }

    updatePriceBreakdown();
  }

  function selectDiscount(percent) {
    selectedDiscount = clamp(Number(percent) || 0, 0, 100);
    if (getEl('discount_percent')) getEl('discount_percent').value = String(selectedDiscount);

    // also reflect into nominal field based on current subtotal
    const subtotal = currentSubtotal();
    const valEl = getEl('discount_value');
    if (valEl && subtotal > 0) {
      valEl.value = String(Math.round(subtotal * (selectedDiscount / 100)));
    } else if (valEl) {
      valEl.value = '0';
    }
    updatePriceBreakdown();
  }


  function groupLabels() {
    return (window.SPLIT_LABELS || []).map(String).filter(Boolean);
  }

  function itemsForGroup(label) {
    const gkey = (!label || label === 'main') ? 'main' : String(label);
    const rows = (window.ORDER_ROWS || []).filter(r => {
      const grp = r.bill_group ?? r.group ?? r.group_label ?? 'main';
      return (gkey === 'main') ? (String(grp) === 'main' || !grp) : String(grp) === gkey;
    });

    const map = new Map();
    let total = 0;
    for (const r of rows) {
      const qty  = Number(r.qty ?? r.quantity ?? r.amount ?? 0) - Number(r.void_qty ?? 0);
      const unit = Number(r.unit_price ?? r.price ?? r.unit ?? r.rate ?? 0);
      if (qty > 0) {
        total += Math.round(qty * unit);
        const name = (r.item_name ?? r.name ?? r.title ?? '').trim() || 'Item';
        map.set(name, (map.get(name) || 0) + qty);
      }
    }
    return { items: Array.from(map.entries()), total };
  }

  function renderGroupOverview() {
    const wrap = getEl('group-overview');
    if (!wrap) return;
    wrap.innerHTML = '';

    const labels = groupLabels();
    const all = labels.length ? labels : ['main'];

    for (const lbl of all) {
      const pretty = displayGroupLabel(lbl);
      const key = (lbl === 'main' ? 'main' : String(lbl));
      const status = window.GROUP_STATUS || {};
      const paid = !!(status[key] && status[key].all_paid);
      const card = document.createElement('div');
      card.className = 'group-card';
      const head = document.createElement('button');
      head.type = 'button';
      head.className = 'action-button group-head';
      const titleSpan = document.createElement('span');
      titleSpan.className = 'group-title';
      titleSpan.textContent = pretty;
      head.appendChild(titleSpan);
      if (paid) {
        const badge = document.createElement('span');
        badge.className = 'group-paid';
        badge.textContent = 'LUNAS';
        head.appendChild(badge);
      }
      head.onclick = () => {
        window.CURRENT_GROUP = (lbl === 'main' ? 'main' : lbl);
        showPaymentStep(true);
      };
      card.appendChild(head);

      const { items, total } = itemsForGroup(lbl);
      const table = document.createElement('table');
      table.className = 'mini';
      const tbody = document.createElement('tbody');
      for (const [name, qty] of items.slice(0, 6)) {
        const tr = document.createElement('tr');
        const tdq = document.createElement('td'); tdq.textContent = String(qty);
        const tdn = document.createElement('td'); tdn.textContent = name;
        tr.appendChild(tdq); tr.appendChild(tdn);
        tbody.appendChild(tr);
      }
      table.appendChild(tbody);
      card.appendChild(table);

      const totalEl = document.createElement('div');
      totalEl.className = 'group-total';
      totalEl.textContent = `Total: ${fmtRp(total)}`;
      card.appendChild(totalEl);

      wrap.appendChild(card);
    }
  }

  function showOverview() {
    getEl('bill-step-overview').style.display = 'block';
    getEl('bill-step-payment').style.display = 'none';
    getEl('step-back').style.display = 'none';
    getEl('dp-row').style.display = 'none';
  }

  function showPaymentStep(fromOverview=false) {
    getEl('bill-step-overview').style.display = 'none';
    getEl('bill-step-payment').style.display = 'block';
    getEl('step-back').style.display = HAS_SPLIT ? 'inline-block' : 'none';
    getEl('dp-row').style.display = 'block';

    // DP default ON for both split and no-split
    setDPUI(true);

    // Load DP amount per group (split only)
    loadDpAmountForGroup();

    // Init payment default (debit or first configured)
    selectPayment(selectedPayment || defaultPaymentKey());

    // Packaging initial state (persisted)
    setPackagingUI(pkgState);

    updatePriceBreakdown();

    const active = getSelectedOption();
    if (fromOverview && active?.method === 'cash') {
      suggestCash();
    }
  }


  function toggleDP() {
    const chk = getEl('apply-dp');
    setDPUI(!(chk?.checked));
  }

  function openBillPopup() {
    const btn = getEl('btn-group-picker'); // legacy button text still okay to update
    const group = normalizeGroup(window.CURRENT_GROUP || 'main');
    if (btn) btn.textContent = (group !== 'main') ? `Group ${group}` : 'Pilih Group';

    const popup = getEl('bill-popup');
    if (!popup) return;

    popup.classList.remove('hidden');

    if (HAS_SPLIT) {
      renderGroupOverview();
      showOverview();
    } else {
      showPaymentStep(false);
    }
  }

  function openBillChooser() {
    const companion = (window.COMPANION_SESSION_ID || '').trim();
    const hasCompanion = !!companion;
    const splitLabels = Array.isArray(window.SPLIT_LABELS) ? window.SPLIT_LABELS : [];
    const sid = window.SESSION_ID;

    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.45);display:flex;align-items:center;justify-content:center;z-index:120000;';

    const card = document.createElement('div');
    card.style.cssText = 'background:#fff;border-radius:10px;padding:16px;min-width:260px;max-height:80vh;overflow:hidden;box-shadow:0 10px 32px rgba(0,0,0,0.22);font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;';
    const title = document.createElement('h3');
    title.textContent = 'Pilih Bill';
    title.style.margin = '0 0 10px';
    card.appendChild(title);

    const wrap = document.createElement('div');
    wrap.style.display = 'grid';
    wrap.style.gap = '8px';
    wrap.style.maxHeight = '60vh';
    wrap.style.overflowY = 'auto';
    wrap.style.paddingRight = '4px';

    function close() { overlay.remove(); }
    function addBtn(label, sub, fn) {
      const b = document.createElement('button');
      b.type = 'button';
      b.innerHTML = `<div style="font-weight:700;">${label}</div><div style="font-size:12px;color:#444;">${sub}</div>`;
      b.style.cssText = 'padding:10px 12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;cursor:pointer;text-align:left;';
      b.onclick = () => { close(); fn(); };
      wrap.appendChild(b);
    }

    // Totals
    (async () => {
      let summary = null;
      try {
        const qs = companion ? `?companion=${encodeURIComponent(companion)}` : '';
        const res = await fetch(`/api/session/summary/${encodeURIComponent(sid)}${qs}`, { headers: { 'Accept':'application/json' }});
        summary = await res.json();
      } catch (_) {}

      const priceLabel = (tot) => tot ? `Rp ${Number(tot.total || 0).toLocaleString('id-ID')}` : 'Rp --';

      const groups = (summary && summary.groups) || [];

      if (splitLabels.length > 0) {
        const groups = (summary && summary.groups) || [];
        splitLabels.forEach(lbl => {
          const g = groups.find(x => (x.label||'') === lbl);
          addBtn(displayGroupLabel(lbl), priceLabel(g), () => {
            window.CURRENT_GROUP = lbl;
            close(); openBillPopup();
          });
        });
      } else {
        const g = (groups && groups[0]) || null;
        const lblTxt = (g && g.service_type === 'takeaway') ? 'Take Away' : 'Dine In';
        addBtn(lblTxt, priceLabel(g), () => { close(); openBillPopup(); });
      }

      if (hasCompanion) {
        const taTot = (summary && summary.companion_total) || null;
        const compLabel = (taTot && taTot.service_type === 'takeaway') ? 'Take Away' : 'Dine In';
        addBtn(compLabel, priceLabel(taTot), () => {
          const tn = document.body?.dataset?.tableNumber || '';
          // navigate to companion session and auto-open bill popup
          window.location.href = `/table/${encodeURIComponent(tn)}/${encodeURIComponent(companion)}?bill=1`;
        });
        const combinedTotal = (() => {
          const dine = (groups && groups[0]) ? Number(groups[0].total || 0) : 0;
          const ta = Number(taTot?.total || 0);
          return dine + ta;
        })();
        addBtn(`Gabung`, `Rp ${combinedTotal.toLocaleString('id-ID')}`, () => {
          const tn = document.body?.dataset?.tableNumber || '';
          // go to companion with a flag to combine, and auto-open bill popup
          window.location.href = `/table/${encodeURIComponent(tn)}/${encodeURIComponent(companion)}?bill=1&combine=1`;
        });
      }

      const bCancel = document.createElement('button');
      bCancel.type = 'button';
      bCancel.textContent = 'Batal';
      bCancel.style.cssText = 'padding:10px 12px;border-radius:8px;border:1px solid #ddd;background:#fafafa;font-weight:600;cursor:pointer;text-align:center;';
      bCancel.onclick = close;
      wrap.appendChild(bCancel);
      card.appendChild(wrap);
      overlay.appendChild(card);
      document.body.appendChild(overlay);
    })();
  }
  window.openBillChooser = openBillChooser;

  function closeBillPopup() {
    getEl('bill-popup')?.classList.add('hidden');
  }

  // --- Print Bill button outside the popup should honor packaging & params ---
  async function printPreBill() {
    if (isDemoMode()) {
      const _sid = window.SESSION_ID;
      const _grp = normalizeGroup(window.CURRENT_GROUP || 'main');
      showDemoPrintModal({
        title: 'Bill printed (demo)',
        url: _sid ? new URL(`/print/preview/${encodeURIComponent(_sid)}?group=${_grp}`, location.origin).toString() : '',
      });
      return;
    }
    const sid = window.SESSION_ID;
    const group = normalizeGroup(window.CURRENT_GROUP || 'main');
    const u = new URL(`/print/preview/${encodeURIComponent(sid)}`, location.origin);
    u.searchParams.set('group', group);

    // include discount if present (value takes precedence)
    const discPct = clamp(parseInt(getEl('discount_percent')?.value || '0', 10) || 0, 0, 100);
    const discVal = parseIntSafe(getEl('discount_value')?.value || '0');
    if (discVal > 0) {
      u.searchParams.set('discount_amount', String(discVal));
    } else if (discPct > 0) {
      u.searchParams.set('discount_percent', String(discPct));
    }


    // include DP (supports split with dp_amount)
    const applyDP = !!getEl('apply-dp')?.checked;
    const dpShown = computeAmountDue().dpShown || 0;
    if (applyDP && dpShown > 0) {
      u.searchParams.set('apply_dp', '1');
      u.searchParams.set('dp_amount', String(dpShown));
    }

    // include packaging only when toggled ON
    if (packagingOn()) {
      u.searchParams.set('packaging', '1');
    }

    const hx = new URL(`/api/print/get-hex/${encodeURIComponent(sid)}`, location.origin);
    hx.search = u.search;

    if (typeof window.openPrintPreviewOptions === 'function') {
      const previewFilename = (POS && typeof POS.buildPreviewFilename === 'function')
        ? POS.buildPreviewFilename('bill', sid, group)
        : `bill-${String(sid || 'preview')}-${group}.html`;
      await window.openPrintPreviewOptions({
        title: displayGroupLabel(group),
        message: 'Choose whether to print this pre-bill now or inspect the preview first.',
        meta: 'The preview already includes the current discount, DP, and packaging selections.',
        url: u.toString(),
        hexUrl: hx.toString(),
        filename: previewFilename,
      });
      return;
    }

    if (window.printBridgeHex) {
      try {
        await window.printBridgeHex(hx.toString(), u.toString());
        return;
      } catch (e) {
        console.warn("bridge prebill failed", e);
      }
    }

    if (typeof window.printClient === "function") {
      window.printClient(u.toString());
    } else {
      window.open(u.toString(), '_blank');
    }
  }

  async function printFinalReceipt(printUrl, paymentId) {
    if (!printUrl) return;
    if (isDemoMode()) {
      showDemoPrintModal({
        title: 'Receipt printed (demo)',
        url: new URL(printUrl, location.origin).toString(),
      });
      return;
    }
    const previewUrl = new URL(printUrl, location.origin);
    const u = new URL(previewUrl.toString());
    u.searchParams.set('autoprint', '1');

    if (typeof window.openPrintPreviewOptions === 'function') {
      const previewFilename = (POS && typeof POS.buildPreviewFilename === 'function')
        ? POS.buildPreviewFilename('receipt', paymentId || 'paid', 'final')
        : `receipt-${paymentId || 'paid'}.html`;
      await window.openPrintPreviewOptions({
        title: 'Final receipt',
        message: 'Choose whether to print the final receipt now, open it in a tab, or download a copy.',
        meta: 'The receipt preview will use the same paid receipt data tied to this payment.',
        url: previewUrl.toString(),
        hexUrl: paymentId ? `/api/print/paid_hex/${encodeURIComponent(paymentId)}` : '',
        filename: previewFilename,
      });
      return;
    }

    if (window.printBridgeHex) {
      const pid = paymentId || u.searchParams.get('payment_id');
      if (pid) {
        try {
          await window.printBridgeHex(`/api/print/paid_hex/${encodeURIComponent(pid)}`, u.toString());
          return;
        } catch (err) {
          console.warn('bridge print failed, falling back to HTML', err);
        }
      }
    }

    if (typeof window.printClient === 'function') {
      try {
        await Promise.race([
          window.printClient(u.toString()),
          new Promise((resolve) => setTimeout(resolve, 4000)),
        ]);
        return;
      } catch (err) {
        console.warn('printClient failed, falling back to window.open', err);
      }
    }

    window.open(u.toString(), '_blank');
    await new Promise((resolve) => setTimeout(resolve, 1200));
  }

  async function submitBillNow(sessionId) {
    if (closingBill){
      return;
    }
    closingBill = true;
    try {
      const discountPercent = clamp(parseInt(getEl('discount_percent')?.value || '0', 10) || 0, 0, 100);
      const discountValue   = Math.max(parseIntSafe(getEl('discount_value')?.value || '0'), 0);
      const activePayment   = getSelectedOption();
      const paymentMethod   = activePayment?.method || selectedPayment;
      let cardType = null;
      if (activePayment?.cardType) {
        cardType = activePayment.cardType;
      } else if (activePayment?.askCardType) {
        cardType = getEl('card_type')?.value || null;
      }

      const cashRaw      = getEl('cash_received')?.value ?? '';
      const cashReceived = cashRaw !== '' ? (parseInt(cashRaw, 10) || 0) : null;

      const applyDP = !!getEl('apply-dp')?.checked;
      const pkgOn  = packagingOn();
      const { remaining, dpShown } = computeAmountDue();
      const group = normalizeGroup(window.CURRENT_GROUP || 'main');

      const payload = {
        group,
        apply_dp: applyDP,
        dp_amount: applyDP ? (dpShown || 0) : 0,
        apply_packaging_fee: pkgOn,
        discount_percent: (discountValue > 0 ? 0 : discountPercent),
        discount_amount:  (discountValue > 0 ? discountValue : 0),
        payment_method: paymentMethod,
        card_type: cardType,
        cash_received: paymentMethod === 'cash' ? cashReceived : null,
        change_given: (paymentMethod === 'cash' && cashReceived != null) ? (cashReceived - remaining) : null
      };

      const r = await fetch(`/close_bill/${encodeURIComponent(sessionId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await r.json();
  
      if (data.status !== 'success') {
        notify('Failed to close bill: ' + (data.message || ''), 'error', 3600);
        return;
      }
  
      closeBillPopup();
      await printFinalReceipt(data.print_url, data.payment_id);
      notify('Bill ditutup.', 'success', 1500);

      if (data.fully_paid) {
        location.href = '/';
      } else {
        const ok = await softSessionRefresh();
        if (!ok) window.location.replace(window.location.href);
      }
  
    } catch (err) {
      console.error(err);
      notify('Something went wrong submitting the bill.', 'error', 3600);
    } finally {
      closingBill = false;
    }
  }
  
  // Minimal fallback for group picker (split.js overrides this with a richer UI)
  function openGroupPicker() {
    const body = getEl('group-picker-body');
    const modal = getEl('group-picker-modal');
    if (!body || !modal) return;

    body.innerHTML = '';
    const addBtn = (value, text) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'action-button';
      if ((window.CURRENT_GROUP || 'main') === (value || 'main')) b.classList.add('selected');

      const key = value || 'main';
      const st = (window.GROUP_STATUS && window.GROUP_STATUS[key]) || null;
      const isPaid = !!(st && st.all_paid);

      b.textContent = text + (isPaid ? ' ✓' : '');
      b.onclick = () => {
        window.CURRENT_GROUP = value || 'main';
        getEl('btn-group-picker').textContent = (value && value !== 'main') ? text : 'Pilih Group';
        loadDpAmountForGroup();
        updatePriceBreakdown();
        openGroupPicker(); // refresh selection state
      };
      body.appendChild(b);
    };

    addBtn('main', 'Main (gabung)');
    (window.SPLIT_LABELS || []).forEach(lbl => addBtn(lbl, `Group ${lbl}`));

    modal.style.display = 'flex';
  }

  function closeGroupPicker() {
    getEl('group-picker-modal')?.style && (getEl('group-picker-modal').style.display = 'none');
  }

  function parseIntSafe(v){ 
    const n = parseInt(String(v||'').replace(/[^\d\-]/g,''), 10);
    return isNaN(n) ? 0 : n;
  }

  // Wire listeners
  document.addEventListener('DOMContentLoaded', () => {
    renderPaymentButtons();
    selectPayment(selectedPayment || defaultPaymentKey());
    setPackagingUI(pkgState);

    // packaging controls are available for takeaway now

    // Always wipe discount fields when tapped/clicked to avoid stuck selections
    const hookClearOnFocus = (el) => {
      if (!el) return;
      const clear = () => {
        if (el.value === '') return;
        el.value = '';
        updatePriceBreakdown();
      };
      el.addEventListener('pointerdown', clear);
      el.addEventListener('focus', clear);
      el.addEventListener('click', clear);
    };
    hookClearOnFocus(getEl('discount_percent'));
    hookClearOnFocus(getEl('discount_value'));

    // step back
    getEl('step-back')?.addEventListener('click', showOverview);

    // inputs that should refresh breakdown
    getEl('discount_percent')?.addEventListener('input', updatePriceBreakdown);
    getEl('discount_percent')?.addEventListener('keyup', updatePriceBreakdown);
    getEl('apply-dp')?.addEventListener('change', updatePriceBreakdown);
    getEl('discount_value')?.addEventListener('input', updatePriceBreakdown);
    getEl('discount_value')?.addEventListener('keyup', updatePriceBreakdown);
    const dpAmountEl = getEl('dp-amount');
    if (dpAmountEl) {
      dpAmountEl.addEventListener('input', () => {
        const raw = String(dpAmountEl.value || '').trim();
        const val = raw === '' ? '' : String(Math.max(parseIntSafe(raw), 0));
        storeDpAmountForGroup(val);
        updatePriceBreakdown();
      });
      dpAmountEl.addEventListener('blur', () => {
        const gross = computeAmountDue().gross;
        const info = getDpRequestInfo(gross);
        if (!info.empty) {
          dpAmountEl.value = String(info.want);
          storeDpAmountForGroup(String(info.want));
        }
        updatePriceBreakdown();
      });
    }

    // cash field: user typing disables auto-cash
    getEl('cash_received')?.addEventListener('input', () => {
      const el = getEl('cash_received');
      if (el) el.setAttribute('data-auto-cash', '0');
      updatePriceBreakdown();
    });

    const popupPrintBtn = getEl('btn-print-bill-popup');
    if (popupPrintBtn) {
      popupPrintBtn.addEventListener('click', () =>
        withBusy(popupPrintBtn, 'Mencetak...', () => printPreBill())
      );
    }
    
    // Keyboard switches for toggles
    const dpBtn  = getEl('btn-dp-toggle');
    dpBtn?.setAttribute('role', 'switch');
    dpBtn?.setAttribute('aria-checked', String(!!getEl('apply-dp')?.checked));
    dpBtn?.addEventListener('keydown', (e) => {
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); toggleDP(); }
    });

    const pkgBtn = getEl('btn-packaging-toggle');
    if (pkgBtn) {
      pkgBtn.setAttribute('role', 'switch');
      pkgBtn.setAttribute('aria-checked', String(!!getEl('apply-packaging')?.checked));
      pkgBtn.addEventListener('keydown', (e) => {
        if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); togglePackaging(); }
      });
    }
    updatePriceBreakdown();
  });

  // expose
  window.openBillPopup = openBillPopup;
  window.closeBillPopup = closeBillPopup;
  window.selectPayment = selectPayment;
  window.selectDiscount = selectDiscount;
  window.toggleDP = toggleDP;
  window.togglePackaging = togglePackaging;
  window.submitBill = function(sessionId) {
    return withBusy(getEl('btn-bill-submit'), 'Memproses...', () => submitBillNow(sessionId));
  };
  window.printPreBill = printPreBill;

  if (!('openGroupPicker' in window)) window.openGroupPicker = function(){};
  if (!('closeGroupPicker' in window)) window.closeGroupPicker = function(){};
})();
