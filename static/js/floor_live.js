// static/js/floor_live.js
(() => {
  const POS = (window.POS = window.POS || {});
  POS.floorTableState = POS.floorTableState || {};

  // ---------- element helpers ----------
  const selTiles = (tn) =>
    document.querySelectorAll(`.table-box[data-table="${CSS.escape(String(tn))}"]`);

  const hasReservationOverlay = (el) =>
    el.classList.contains('reserved') ||
    el.classList.contains('reserved-lockout') ||
    el.classList.contains('reserved-active') ||
    el.classList.contains('reserved-split') ||
    el.classList.contains('reserved-far') ||
    el.classList.contains('conflict-pulsate');

  const minutesUntil = (tsISO) => {
    if (!tsISO) return Infinity;
    const now = new Date();
    const at  = new Date(tsISO);
    return Math.floor((at - now) / 60000);
  };

  const clearResClasses = (el) => {
    el.classList.remove(
      'reserved','reserved-lockout','reserved-active',
      'reserved-split','reserved-far','conflict-pulsate'
    );
  };

  const dataMinutes = (el) => {
    const raw = el.getAttribute('data-res-minutes');
    const n = raw == null ? NaN : Number(raw);
    return Number.isFinite(n) ? n : null;
  };

  const setOccupied = (tableNumber, occupied=true, billing=false) => {
    selTiles(tableNumber).forEach((el) => {
      el.classList.toggle('occupied',  !!occupied);
      el.classList.toggle('available', !occupied);
      el.classList.toggle('billing',   !!billing);
    });
  };

  const formatIDR = (value) => {
    const num = Number(value);
    if (!Number.isFinite(num)) return 'Rp --';
    return `Rp ${Math.round(num).toLocaleString('id-ID')}`;
  };

  function refreshFloorButtonIndicators() {
    const qrByFloor = {};
    Object.values(POS.floorTableState || {}).forEach((state) => {
      const floor = String(state.floor || '');
      if (!floor) return;
      qrByFloor[floor] = qrByFloor[floor] || !!state.has_qr_unsent;
      if (state.has_qr_unsent) qrByFloor[floor] = true;
    });

    document.querySelectorAll('.floor-btn[data-floor]').forEach((btn) => {
      const floor = String(btn.dataset.floor || '');
      btn.classList.toggle('has-qr-unsent', !!qrByFloor[floor]);
    });
  }

  function setGuestLine(el, guestName) {
    const body = el.querySelector('.table-body');
    if (!body) return;

    let line = body.querySelector('.guest-line');
    const text = String(guestName || '').trim();
    if (text) {
      if (!line) {
        line = document.createElement('div');
        line.className = 'guest-line';
        body.insertBefore(line, body.firstChild);
      }
      line.textContent = text;
    } else if (line) {
      line.remove();
    }
  }

  function setTableSub(el, state) {
    const sub = el.querySelector('.table-sub');
    if (!sub) return;

    const occupied = !!state.occupied;
    const amount = state.total_amount;
    const maxPax = el.getAttribute('data-max-pax') || '';

    sub.innerHTML = '';
    if (occupied) {
      const amountEl = document.createElement('span');
      amountEl.className = 'table-amount';
      if (amount == null) {
        amountEl.classList.add('muted');
        amountEl.textContent = 'Rp --';
      } else {
        amountEl.textContent = formatIDR(amount);
      }
      sub.appendChild(amountEl);
      return;
    }

    if (maxPax) {
      const paxEl = document.createElement('span');
      paxEl.className = 'table-pax';
      paxEl.textContent = `Max: ${maxPax}`;
      sub.appendChild(paxEl);
    }
  }

  function applyTableStateSnapshot(state) {
    if (!state || !state.table_number) return;
    const tableNumber = String(state.table_number);
    const floor = String(state.floor || '');
    POS.floorTableState[tableNumber] = {
      floor,
      has_unsent: !!state.has_unsent,
      has_qr_unsent: !!state.has_qr_unsent,
    };

    selTiles(tableNumber).forEach((el) => {
      const occupied = !!state.occupied;
      const billing = !!state.billing;
      const empty = !!state.empty_session && occupied;

      el.classList.toggle('occupied', occupied);
      el.classList.toggle('available', !occupied);
      el.classList.toggle('billing', billing);
      el.classList.toggle('empty-session', empty);
      el.setAttribute('data-billing', billing ? '1' : '0');
      el.setAttribute('data-empty', empty ? '1' : '0');

      if (floor) {
        el.dataset.floor = floor;
      }

      if (occupied && state.session_id) {
        el.setAttribute('href', `/table/${encodeURIComponent(tableNumber)}/${encodeURIComponent(String(state.session_id))}`);
      } else {
        el.setAttribute('href', `/table/${encodeURIComponent(tableNumber)}`);
      }

      setGuestLine(el, state.guest_name);
      setTableSub(el, state);
    });

    toggleUnsentClass(tableNumber, !!state.has_unsent, !!state.has_qr_unsent);
    refreshFloorButtonIndicators();
  }

  // ---------- reservation overlays ----------
  function applyReservationHint(evt) {
    // evt = { table_number, ts_iso (may be null) }
    const tn = String(evt && evt.table_number || '');
    if (!tn) return;
    selTiles(tn).forEach((el) => {
      // always start by clearing
      clearResClasses(el);

      // if ts_iso is null/undefined -> reservation removed/consumed -> leave clear
      const ts = evt.ts_iso ? new Date(evt.ts_iso) : null;
      if (!ts || isNaN(ts.getTime())) return;

      const mins = minutesUntil(evt.ts_iso);
      if (mins < 0) return;

      const hasSession = el.classList.contains('occupied');
      if (!hasSession) {
        el.classList.add('reserved');
        if (mins <= 120) el.classList.add('reserved-lockout');
      } else {
        if (mins <= 120) el.classList.add('reserved-active','conflict-pulsate');
        else el.classList.add('reserved-split');
      }
    });
  }

  function applyReservationOverlayFromDataset(tableNumber) {
    selTiles(String(tableNumber)).forEach((el) => {
      clearResClasses(el);
      const hasSession = el.classList.contains('occupied');
      const mins = dataMinutes(el);
      if (mins == null) return; // no known reservation in the DOM
      if (!hasSession) {
        el.classList.add('reserved');
        if (mins <= 120) el.classList.add('reserved-lockout');
      } else {
        if (mins <= 120) el.classList.add('reserved-active','conflict-pulsate');
        else el.classList.add('reserved-split');
      }
    });
  }

  // expose so other scripts can reuse
  POS.applyReservationHint = applyReservationHint;
  POS.applyReservationOverlayFromDataset = applyReservationOverlayFromDataset;
  POS.applyTableStateSnapshot = applyTableStateSnapshot;
  POS.refreshFloorButtonIndicators = refreshFloorButtonIndicators;

  function toggleUnsentClass(tableNumber, hasUnsent, hasQrUnsent) {
    selTiles(String(tableNumber)).forEach((el) => {
      const hasRes = hasReservationOverlay(el);
      // Always toggle .unsent if there are unsent items
      el.classList.toggle('unsent', !!hasUnsent);
      el.classList.toggle('qr-unsent', !!hasQrUnsent);
  
      // When BOTH unsent and reservation overlay are present, add a hint class
      // We'll style this to be half red / half pink.
      el.classList.toggle('unsent-split', !!hasUnsent && hasRes);
    });
  }
  

  async function refreshUnsentForTable(tableNumber) {
    try {
      const r = await fetch(`/api/table/${encodeURIComponent(String(tableNumber))}/unsent_flag`, { credentials: 'same-origin' });
      if (!r.ok) return;
      const j = await r.json();
      const firstTile = selTiles(String(tableNumber))[0];
      const prev = POS.floorTableState[String(tableNumber)] || {};
      POS.floorTableState[String(tableNumber)] = {
        ...prev,
        floor: prev.floor || firstTile?.dataset?.floor || '',
        has_unsent: !!j.has_unsent,
        has_qr_unsent: !!j.has_qr_unsent,
      };
      toggleUnsentClass(tableNumber, !!j.has_unsent, !!j.has_qr_unsent);
      refreshFloorButtonIndicators();
    } catch (_) {}
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

  function getCurrentFloor() {
    return (
      (window.currentFloor && window.currentFloor()) ||
      findVisibleFloor() ||
      window.DEFAULT_FLOOR ||
      "1"
    );
  }

  async function applyUnsentFlagsForCurrentFloor() {
    return applyUnsentFlagsForFloor(getCurrentFloor());
  }

  async function applyUnsentFlagsForFloor(floor) {
    const floorKey = String(floor || '').trim();
    if (!floorKey) return;
    try {
      const r = await fetch(`/api/floor/${encodeURIComponent(floorKey)}/unsent_flags`, { credentials: 'same-origin' });
      if (!r.ok) return;
      const j = await r.json();
      const flags = (j && j.flags) || {};
      const qrFlags = (j && j.qr_flags) || {};

      document.querySelectorAll(`.table-box[data-floor="${CSS.escape(floorKey)}"]`).forEach((el) => {
        const tn = String(el.dataset.table || '').trim();
        if (!tn) return;
        const prev = POS.floorTableState[tn] || {};
        POS.floorTableState[tn] = {
          ...prev,
          floor: floorKey,
          has_unsent: !!flags[tn],
          has_qr_unsent: !!qrFlags[tn],
        };
        toggleUnsentClass(tn, !!flags[tn], !!qrFlags[tn]);
      });

      refreshFloorButtonIndicators();
    } catch (_) {}
  }

  async function applyUnsentFlagsForAllFloors() {
    const floors = [...document.querySelectorAll('.floor-btn[data-floor]')].map((btn) => btn.dataset.floor).filter(Boolean);
    await Promise.all(floors.map((floor) => applyUnsentFlagsForFloor(floor)));
  }

  // initial one-shot paint
  document.addEventListener('DOMContentLoaded', () => {
    applyUnsentFlagsForAllFloors();
  });
  window.applyUnsentFlagsForCurrentFloor = applyUnsentFlagsForCurrentFloor;
  window.applyUnsentFlagsForAllFloors = applyUnsentFlagsForAllFloors;

  // ---------- sockets ----------
  function bindFloorLive(socket) {
    if (!socket || socket.__floorLiveBound) return;
    socket.__floorLiveBound = true;

    const maybeRefresh = (tn) => tn && refreshUnsentForTable(String(tn));

    socket.on('connect', () => {
      try {
        socket.emit('hello', { outlet: 'DEMO', floor: getCurrentFloor() });
      } catch (_) {}
    });

    // Orders/sessions affect unsent flags
    socket.on('table.state.changed', (state) => {
      if (!state || !state.table_number) return;
      applyTableStateSnapshot(state);
    });
    socket.on('session.state.changed', (state) => {
      if (!state || !state.table_number) return;
      applyTableStateSnapshot(state);
    });

    socket.on('session_items_changed', (e) => maybeRefresh(e && e.table_number));
    socket.on('session_created',       (e) => {
      if (e && e.table_number) {
        setOccupied(String(e.table_number), true, false);
        applyReservationOverlayFromDataset(String(e.table_number));
        maybeRefresh(e.table_number);
      }
    });
    socket.on('session_billing',       (e) => {
      if (e && e.table_number) {
        setOccupied(String(e.table_number), true, true);
        applyReservationOverlayFromDataset(String(e.table_number));
        maybeRefresh(e.table_number);
      }
    });
    socket.on('session_closed',        (e) => {
      if (e && e.table_number) {
        setOccupied(String(e.table_number), false, false);
        applyReservationOverlayFromDataset(String(e.table_number));
        maybeRefresh(e.table_number);
      }
    });

    // Reservations drive overlays + unsent
    socket.on('reservations.changed', (e) => {
      if (!e || !e.table_number) return;
      applyReservationHint(e);             // paint pink / clear to green
      maybeRefresh(e.table_number);        // keep unsent in sync
    });

    socket.on('reservations.autoseated', (e) => {
      if (!e || !e.table_number) return;
      const tn = String(e.table_number);
      // Mark occupied and clear reservation overlay
      setOccupied(tn, true, false);
      applyReservationHint({ table_number: tn, ts_iso: null });
      maybeRefresh(tn);
    });

    // Table moves
    socket.on('table_moved', (e) => {
      if (!e) return;
      if (e.from_table) maybeRefresh(e.from_table);
      if (e.to_table)   maybeRefresh(e.to_table);
    });
  }

  if (typeof window.io === 'function') {
    const socket = POS.socket || (POS.socket = io('/pos', { transports: ['websocket', 'polling'] }));
    bindFloorLive(socket);
  } else {
    console.warn('[WS] Socket.IO client not loaded; live paints disabled.');
  }
})();
