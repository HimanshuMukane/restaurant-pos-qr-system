(function () {
  'use strict';

  // Namespace
  window.POS = window.POS || {};
  const POS = window.POS;

  // ---------- helpers (single source of truth) ----------
  function minutesUntil(tsISO){
    if (!tsISO) return Infinity;
    const now = new Date();
    const at  = new Date(tsISO);
    return Math.floor((at - now) / 60000);
  }

  function clearResClasses(el){
    el.classList.remove(
      'reserved','reserved-lockout','reserved-active',
      'reserved-split','reserved-far','conflict-pulsate'
    );
  }

  function dataMinutes(el){
    const raw = el.getAttribute('data-res-minutes');
    const n   = raw == null ? NaN : Number(raw);
    return Number.isFinite(n) ? n : null;
  }

  function setOccupied(tableNumber, occupied=true, billing=false){
    document.querySelectorAll(`.table-box[data-table="${CSS.escape(String(tableNumber))}"]`).forEach(el => {
      el.classList.toggle('occupied',  occupied);
      el.classList.toggle('available', !occupied);
      el.classList.toggle('billing',   !!billing);
    });
  }

  function findVisibleFloor() {
    const list = document.querySelectorAll(".floor-container");
    for (const ctn of list) {
      const style = getComputedStyle(ctn);
      if (style.display !== "none" && style.visibility !== "hidden") {
        return ctn.dataset.floor;
      }
    }
    return null;
  }

  function currentFloor() {
    if (window.currentFloor) {
      const f = window.currentFloor();
      if (f) return f;
    }
    const stored = localStorage.getItem("lastFloor");
    if (stored) return stored;
    return window.DEFAULT_FLOOR || findVisibleFloor() || "1";
  }

  // ---------- reservation overlays ----------
  function applyReservationHint(evt){
    // evt = { table_number, ts_iso? }
    const tn = String(evt?.table_number || '');
    if (!tn) return;

    const el = document.querySelector(`.table-box[data-table="${CSS.escape(tn)}"]`);
    if (!el) return;

    clearResClasses(el);

    // If server didn't send ts_iso, fall back gracefully:
    if (!evt.ts_iso) {
      // 1) If the server inlined minutes, use them for proper lockout coloring
      const mins = dataMinutes(el);
      const hasSession = el.classList.contains('occupied');
      if (mins != null) {
        if (!hasSession) {
          el.classList.add('reserved');
          if (mins <= 120) el.classList.add('reserved-lockout');
        } else {
          if (mins <= 120) el.classList.add('reserved-active','conflict-pulsate');
          else el.classList.add('reserved-split');
        }
        return;
      }
      // 2) No minutes either? At least mark base pink so the user sees it instantly
      el.classList.add('reserved');
      return;
    }

    // Normal path: we have ts_iso
    const ts = new Date(evt.ts_iso);
    if (isNaN(ts.getTime())) return; // invalid ts

    const mins = minutesUntil(evt.ts_iso);
    if (mins < 0) return; // past → nothing

    const hasSession = el.classList.contains('occupied');

    if (!hasSession) {
      el.classList.add('reserved');
      if (mins <= 120) el.classList.add('reserved-lockout'); // pink lockout
    } else {
      if (mins <= 120) el.classList.add('reserved-active','conflict-pulsate'); // orange + pulse
      else el.classList.add('reserved-split');                                  // half orange/half pink
    }
  }

  function applyReservationOverlayFromDataset(tableNumber){
    const el = document.querySelector(`.table-box[data-table="${CSS.escape(String(tableNumber))}"]`);
    if (!el) return;
    clearResClasses(el);

    const hasSession = el.classList.contains('occupied');
    const mins = dataMinutes(el);
    if (mins == null) return; // no known reservation

    if (!hasSession) {
      el.classList.add('reserved');
      if (mins <= 120) el.classList.add('reserved-lockout');
    } else {
      if (mins <= 120) el.classList.add('reserved-active','conflict-pulsate');
      else el.classList.add('reserved-split');
    }
  }

  POS.applyReservationHint = applyReservationHint;
  POS.applyReservationOverlayFromDataset = applyReservationOverlayFromDataset;

  // ---------- list utils ----------
  function normalizeSplitLabels(j) {
    const fromSplit   = Array.isArray(j.split_labels) ? j.split_labels : null;
    const fromPresent = Array.isArray(j.present_groups) ? j.present_groups : null;
    const src = (fromSplit && fromSplit.length) ? fromSplit : (fromPresent || []);
    return src
      .map((v) => {
        if (v && typeof v === 'object') {
          return v.key || v.label || v.id || v.group || '';
        }
        return String(v);
      })
      .map(String)
      .filter(Boolean)
      .sort((a,b) => {
        const na = +a, nb = +b;
        if (Number.isFinite(na) && Number.isFinite(nb)) return na - nb;
        return String(a).localeCompare(String(b), undefined, { numeric:true });
      });
  }

  function normalizeSplitMeta(j) {
    const raw = Array.isArray(j.split_meta)
      ? j.split_meta
      : (Array.isArray(j.split_labels) && j.split_labels.length && typeof j.split_labels[0] === 'object'
        ? j.split_labels
        : []);
    const out = [];
    (raw || []).forEach((entry) => {
      if (!entry) return;
      if (typeof entry === 'object') {
        const key = String(entry.key || entry.label || entry.id || entry.group || '').trim();
        if (!key || !/^\d+$/.test(key)) return;
        out.push({ key, name: String(entry.name || entry.title || '').trim() });
      } else {
        const key = String(entry).trim();
        if (!key || !/^\d+$/.test(key)) return;
        out.push({ key, name: '' });
      }
    });
    out.sort((a,b) => Number(a.key) - Number(b.key));
    return out;
  }

  // ---------- socket binding (bind once) ----------
  function bindRealtimeReservation(sock){
    if (!sock || sock.__resvBound) return;
    sock.__resvBound = true;

    // Reservation changed → recolor one tile (with fallback if ts_iso missing)
    const onChanged = (evt) => { try { POS.applyReservationHint(evt); } catch(_){} };

    // Auto-seated in background → mark occupied & clear overlay
    const onAutoseated = (evt) => {
      try {
        const tn = String(evt.table_number || '');
        if (!tn) return;
        setOccupied(tn, true, false);
        POS.applyReservationHint({ table_number: tn, ts_iso: null });
      } catch(_) {}
    };

    sock.on('reservations.changed', onChanged);
    sock.on('reservation_changed',  onChanged); // legacy alias

    sock.on('reservations.autoseated', onAutoseated);
    sock.on('reservation_autoseated',  onAutoseated); // legacy alias

    // Session lifecycle → re-evaluate reservation overlay from dataset minutes
    sock.on('session_created', ({ table_number }) => {
      setOccupied(table_number, true, false);
      POS.applyReservationOverlayFromDataset(table_number);
    });
    sock.on('session_billing', ({ table_number }) => {
      setOccupied(table_number, true, true);
      POS.applyReservationOverlayFromDataset(table_number);
    });
    sock.on('session_closed', ({ table_number }) => {
      setOccupied(table_number, false, false);
      POS.applyReservationOverlayFromDataset(table_number);
    });
  }

  // ---------- ensure socket (single creator) ----------
  function ensureSocket(){
    if (POS.socket) return POS.socket;

    if (typeof window.io !== 'function') {
      console.error('[WS] socket.io not loaded yet; will retry after DOMContentLoaded');
      return null;
    }

    const socket = io('/pos', { transports: ['websocket', 'polling'] });
    POS.socket = socket;

    socket.on('connect', () => {
      socket.emit('hello', { outlet: 'DEMO', floor: currentFloor() });

      const sid = document.body?.dataset?.sessionId;
      if (sid) socket.emit('watch.session', { session_id: sid });

      const tn = document.body?.dataset?.tableNumber;
      if (tn) socket.emit('watch.table', { table: tn });

      bindRealtimeReservation(socket);
    });

    // live refresh for the open session view
    socket.on('session.state.changed', (evt) => {
      const sid = document.body?.dataset?.sessionId;
      if (sid && evt?.session_id === sid) POS.requestSessionState?.();
    });
    socket.on('session_items_changed', (evt) => {
      const sid = document.body?.dataset?.sessionId;
      if (sid && evt?.session_id === sid) POS.requestSessionState?.();
    });

    return socket;
  }

  // ---------- state pull for session pages ----------
  let stateBusy = false;
  let pendingStateOpts = null;

  POS.requestSessionState = async function requestSessionState(opts = {}) {
    if (document.visibilityState === "hidden") {
      pendingStateOpts = opts;
      return;
    }
    if (stateBusy) {
      pendingStateOpts = opts;
      return;
    }
    stateBusy = true;
    const sid = document.body?.dataset?.sessionId;
    try {
      if (sid) {
        try {
          const r = await fetch(`/api/session_state/${encodeURIComponent(sid)}`, {
            headers: { 'Accept': 'application/json' }
          });
          const j = await r.json();

          if (!opts.skipRows) {
            const shape = String(j.rows_shape || '').toLowerCase();
            if (shape.startsWith('raw')) {
              window.ORDER_ROWS = Array.isArray(j.rows) ? j.rows : [];
            } else {
              console.warn('[WS] Ignoring non-raw rows to avoid merge/flicker');
            }
          }

          window.SPLIT_LABELS    = normalizeSplitLabels(j);
          window.SPLIT_META      = normalizeSplitMeta(j);
          window.GROUP_SUBTOTALS = j.group_subtotals || {};
          window.GROUP_STATUS    = j.group_status || {};
          window.DP_REMAINING    = Number(j.dp_remaining || 0);

          const savedKey  = (localStorage.getItem('table_group_key') || 'all');
          const targetKey = opts.forceAll ? 'all' : savedKey;
          if (opts.forceAll) {
            try { localStorage.setItem('table_group_key', 'all'); } catch(_){}
          }

          if (POS.__pagedOrders?.setGroup) {
            POS.__pagedOrders.setGroup(targetKey);
          } else if (POS.__pagedOrders?.setFilter) {
            POS.__pagedOrders.setFilter({ group: targetKey });
          }
          if (POS.__pagedOrders?.render) POS.__pagedOrders.render();

          if (typeof POS.rerenderTable === 'function') POS.rerenderTable();
          if (typeof POS._onGroupChanged === 'function') POS._onGroupChanged(targetKey);
          if (typeof window.refreshDpButton === 'function') window.refreshDpButton();
          if (typeof window.updatePriceBreakdown === 'function') window.updatePriceBreakdown();
        } catch (e) {
          console.debug('[WS] requestSessionState failed', e);
        }
      }

      ensureSocket();
    } finally {
      stateBusy = false;
      if (pendingStateOpts) {
        const next = pendingStateOpts;
        pendingStateOpts = null;
        POS.requestSessionState(next);
      }
    }
  };

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible") return;
    if (pendingStateOpts) {
      const next = pendingStateOpts;
      pendingStateOpts = null;
      POS.requestSessionState(next);
    }
  });

  // ---------- boot ----------
  document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.io === 'function') {
      const sock = ensureSocket();
      if (sock && sock.connected) bindRealtimeReservation(sock);
    } else {
      const iv = setInterval(() => {
        if (typeof window.io === 'function') {
          clearInterval(iv);
          const sock = ensureSocket();
          if (sock && sock.connected) bindRealtimeReservation(sock);
        }
      }, 300);
      setTimeout(() => clearInterval(iv), 10000);
    }

    if (document.body?.dataset?.sessionId) {
      POS.requestSessionState({ forceAll: false, skipRows: true });
    }
  });
})();
