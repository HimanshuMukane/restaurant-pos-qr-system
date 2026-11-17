function openOverlay(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('hidden');
  el.style.display = 'flex';
  document.body.classList.add('modal-open');
}

function setFloor(floor) {
  // Remember this floor
  localStorage.setItem('lastFloor', String(floor));

  document.querySelectorAll('.floor-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.floor === String(floor));
  });
  document.querySelectorAll('.floor-container').forEach(ctn => {
    ctn.style.display = (ctn.dataset.floor === String(floor)) ? 'block' : 'none';
  });

  // If realtime.js is loaded, tell the server we’re now on this floor (join room)
  if (window.POS && POS.socket && POS.socket.connected) {
    POS.socket.emit('hello', { outlet: 'DEMO', floor: String(floor) });
  }
}
window.setFloor = setFloor;

document.addEventListener('DOMContentLoaded', () => {
  const stored = localStorage.getItem('lastFloor');
  const DEFAULT_FLOOR =
    stored ||
    window.DEFAULT_FLOOR ||
    document.querySelector('.floor-btn.active')?.dataset.floor ||
    document.querySelector('.floor-container')?.dataset.floor ||
    null;

  if (DEFAULT_FLOOR) setFloor(DEFAULT_FLOOR);
  bindInstantTableNavigation();
});

function closeOverlay(id) {
  const el = document.getElementById(id);
  if (!el) return;

  if (el.classList.contains('popup')) {
    el.classList.add('hidden');
  } else {
    el.style.display = 'none';
  }

  const anyOpen = Array.from(document.querySelectorAll('.modal-overlay, .popup'))
    .some(node => {
      const style = getComputedStyle(node);
      const hasHidden = node.classList.contains('hidden');
      return !hasHidden && style.display !== 'none';
    });
  if (!anyOpen) document.body.classList.remove('modal-open');
}

function attachBackdropClose(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('click', (e) => {
    if (e.target === el) closeOverlay(id);
  });
}

function refreshReservationHints() {
  return fetch('/api/reservations/hints')
    .then(r => r.ok ? r.json() : Promise.reject())
    .then(j => {
      (j.items || []).forEach(evt => {
        if (window.POS && typeof window.POS.applyReservationHint === 'function') {
          window.POS.applyReservationHint(evt);
        }
      });
    })
    .catch(() => {});
}

const __prefetchedRoutes = new Set();

function readUiFlag(name, fallback = false) {
  const cfg = (window.POS_CONFIG && window.POS_CONFIG.ui) ? window.POS_CONFIG.ui : null;
  const val = cfg ? cfg[name] : undefined;
  return typeof val === 'boolean' ? val : fallback;
}

function prefetchRoute(url) {
  const href = String(url || '').trim();
  if (!href) return;
  if (!readUiFlag('route_prefetch', true)) return;
  if (__prefetchedRoutes.has(href)) return;
  __prefetchedRoutes.add(href);
  fetch(href, {
    credentials: 'same-origin',
    headers: { 'Accept': 'text/html', 'X-POS-Prefetch': '1' }
  }).catch(() => {
    __prefetchedRoutes.delete(href);
  });
}

function markNavPending(el, on = true) {
  if (!el) return;
  el.classList.toggle('nav-pending', !!on);
  el.setAttribute('aria-busy', on ? 'true' : 'false');
}

function bindInstantTableNavigation() {
  if (bindInstantTableNavigation._done) return;
  bindInstantTableNavigation._done = true;

  document.querySelectorAll('.table-box[href]').forEach((a) => {
    a.addEventListener('pointerenter', () => prefetchRoute(a.href), { passive: true });
    a.addEventListener('touchstart', () => prefetchRoute(a.href), { passive: true });
  });

  document.addEventListener('click', async (e) => {
    const a = e.target.closest('.table-box[href]');
    if (!a) return;
    if (e.defaultPrevented) return;
    if (e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

    const floor = a.dataset.floor || document.querySelector('.floor-btn.active')?.dataset.floor;
    if (floor) localStorage.setItem('lastFloor', String(floor));

    if (!readUiFlag('instant_table_open', false) || !a.classList.contains('available')) {
      markNavPending(a, true);
      return;
    }

    const tableNumber = (a.dataset.table || '').trim();
    if (!tableNumber) {
      markNavPending(a, true);
      return;
    }

    e.preventDefault();
    if (a.dataset.navPending === '1') return;

    a.dataset.navPending = '1';
    markNavPending(a, true);

    try {
      const res = await fetch(`/api/table/${encodeURIComponent(tableNumber)}/quick_open`, {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Accept': 'application/json' }
      });
      const j = await res.json().catch(() => null);
      if (j && j.redirect) {
        window.location.href = j.redirect;
        return;
      }
    } catch (_) {}

    delete a.dataset.navPending;
    markNavPending(a, false);
    window.location.href = a.href;
  });
}

(function startClock(){
  const el = document.getElementById('clock');
  if (!el) return;
  const fmt = n => String(n).padStart(2,'0');
  function tick(){
    const d = new Date();
    el.textContent = `${fmt(d.getHours())}:${fmt(d.getMinutes())}:${fmt(d.getSeconds())}`;
  }
  tick();
  setInterval(tick, 1000);
})();

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay, .popup').forEach(el => {
      const style = getComputedStyle(el);
      const hidden = el.classList.contains('hidden');
      if (!hidden && style.display !== 'none') {
        if (el.classList.contains('popup')) el.classList.add('hidden');
        else el.style.display = 'none';
      }
    });
    document.body.classList.remove('modal-open');
  }
});

// ---------- Main behaviors ----------
document.addEventListener("DOMContentLoaded", () => {
  (function setDefaultResDateTime() {
    const d = new Date();
    const pad = n => String(n).padStart(2,'0');

    const dateEl = document.getElementById("res_date");
    const timeEl = document.getElementById("res_time");
    if (dateEl) dateEl.value = d.toISOString().slice(0,10);

    d.setMinutes(d.getMinutes() + (30 - (d.getMinutes() % 30 || 30)) % 30);
    if (timeEl) timeEl.value = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  })();

  ['reservationPopup','assignResModal','preorderModal','seatModal'].forEach(attachBackdropClose);

  window.openReservationPopup = () => openOverlay("reservationPopup");
  window.closeReservationPopup = (e) => { if (e) e.stopPropagation(); closeOverlay("reservationPopup"); };

  window.submitReservation = function () {
    const payload = {
      guest_name: document.getElementById("res_guest_name").value.trim(),
      phone: document.getElementById("res_phone").value.trim(),
      pax: parseInt(document.getElementById("res_pax").value,10),
      date: document.getElementById("res_date").value,
      time: document.getElementById("res_time").value,
      notes: document.getElementById("res_notes").value.trim(),
      dp_amount: parseInt(document.getElementById("res_dp").value,10) || 0,
      dp_method: document.getElementById("res_dp_method").value
    };
    if (!payload.guest_name || !payload.pax || !payload.date || !payload.time || payload.dp_amount <= 0) {
      alert("Nama, pax, tanggal, waktu, dan DP wajib diisi (DP > 0).");
      return;
    }
    fetch("/add_reservation", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload)
    })
    .then(r=>r.json())
    .then(j=>{
      if (j.status==="success") {
        refreshReservationHints();
        window.closeReservationPopup?.();
      }
      else { alert("Gagal: " + (j.message||'')); }
    });
  };

  window.openAssignResModal = (id) => {
    document.getElementById('assignResId').value = id;
    document.getElementById('assignResErr').textContent = '';
    openOverlay('assignResModal');
  };
  window.closeAssignResModal = () => closeOverlay('assignResModal');

  window.submitAssignRes = function(){
    const id = document.getElementById('assignResId').value;
    const table_number = document.getElementById('assignResTable').value.trim();
    const err = document.getElementById('assignResErr');
    err.textContent = '';
    if (!table_number) { err.textContent = 'Nomor meja wajib'; return; }

    fetch("/assign_table", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({id, table_number})
    })
    .then(r=>r.json())
    .then(j=>{
      if (j.status==='success') {
        refreshReservationHints();
        window.closeAssignResModal?.();
      }
      else err.textContent = j.message || 'Gagal';
    });
  };

  let PREORDER_RES_ID = null;

  window.openPreorderModal = function(resId, guest){
    PREORDER_RES_ID = resId;
    document.getElementById('preorderTitle').textContent = `Preorder — ${guest}`;
    document.getElementById('preorderErr').textContent = '';
    openOverlay('preorderModal');
    refreshPreorderList();
  };

  window.closePreorderModal = function(){ closeOverlay('preorderModal'); };

  function refreshPreorderList(){
    fetch(`/api/reservations/${PREORDER_RES_ID}/preorder`)
      .then(r=>r.json())
      .then(j=>{
        const box = document.getElementById('preorderList');
        box.innerHTML = '';
        (j.items||[]).forEach(it=>{
          const row = document.createElement('div');
          row.className='controls';
          row.innerHTML = `
            <div>${it.item_name} ×${it.qty} — Rp ${Number(it.price).toLocaleString('id-ID')}
              ${it.sauce?`<small> / ${it.sauce}</small>`:''}
              ${it.note?`<em> (${it.note})</em>`:''}
            </div>
            <button type="button" class="action-button danger-button" data-id="${it.id}">Hapus</button>
          `;
          row.querySelector('button').onclick = async () => {
            await fetch(`/api/reservations/preorder/${it.id}`, {method:'DELETE'});
            refreshPreorderList();
          };
          box.appendChild(row);
        });
      });
  }

  window.addPreorderItem = function(){
    const name = document.getElementById('po_item').value.trim();
    const qty  = parseInt(document.getElementById('po_qty').value,10);
    const price= parseInt(document.getElementById('po_price').value,10);
    const sauce= document.getElementById('po_sauce').value.trim() || null;
    const note = document.getElementById('po_note').value.trim() || null;
    const err  = document.getElementById('preorderErr');
    err.textContent = '';

    if (!name || !qty || !price) { err.textContent='Nama, qty, dan harga wajib.'; return; }

    fetch(`/api/reservations/${PREORDER_RES_ID}/preorder`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({item_name:name, qty, price, sauce, note})
    })
    .then(r=>r.json())
    .then(j=>{
      if (j.status==='success') {
        document.getElementById('po_item').value='';
        refreshPreorderList();
      } else {
        err.textContent = j.message || 'Gagal menambah preorder';
      }
    });
  };

  window.openSeatModal = function(resId, name, pax){
    document.getElementById('seatResId').value = resId;
    document.getElementById('seatName').value = name || '';
    document.getElementById('seatPax').value  = pax || 1;
    document.getElementById('seatTable').value= '';
    document.getElementById('seatNote').value = '';
    document.getElementById('seatErr').textContent = '';
    openOverlay('seatModal');
  };

  window.closeSeatModal = () => closeOverlay('seatModal');

  window.submitSeat = function(){
    const reservation_id = parseInt(document.getElementById('seatResId').value,10);
    const table_number   = document.getElementById('seatTable').value.trim();
    const pax            = parseInt(document.getElementById('seatPax').value,10);
    const guest_name     = document.getElementById('seatName').value.trim();
    const note           = document.getElementById('seatNote').value.trim();
    const err = document.getElementById('seatErr');

    err.textContent = '';
    if (!table_number) { err.textContent='Nomor meja wajib.'; return; }

    fetch('/seat_reservation', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({reservation_id, table_number, pax, guest_name, note})
    })
    .then(r=>r.json())
    .then(j=>{
      if (j.status==='success') { location.href = j.redirect; }
      else { err.textContent = j.message || 'Gagal seat'; }
    });
  };
});

/* =========================================================================
   Realtime dashboard integration (uses POS.socket from realtime.js)
   ========================================================================= */
(function () {
  window.POS = window.POS || {};
  const POS = window.POS;
  POS.applyReservationHint = function (evt) {
    try {
      const tn = String(evt.table_number);
      const el = document.querySelector(`.table-box[data-table="${CSS.escape(tn)}"]`);
      if (!el) return;
  
      const when = new Date(evt.ts_iso);
      const now  = new Date();
      const mins = Math.max(0, Math.floor((when - now) / 60000));
      const occupied = el.classList.contains('occupied');
  
      // clear previous reservation classes
      el.classList.remove('reserved','reserved-lockout','reserved-active','conflict-pulsate','reserved-split');
  
      if (occupied) {
        if (mins > 120) {
          el.classList.add('reserved-split');                           // half orange/half pink
        } else {
          el.classList.add('reserved-active','conflict-pulsate');       // dark pink + pulse
        }
      } else {
        el.classList.add('reserved');                                    // soft pink
        if (mins <= 120) el.classList.add('reserved-lockout');           // stronger pink
      }
    } catch (_) {}
  };
  

  // Minimal in-place tile update helpers
  function esc(sel) {
    if (window.CSS && CSS.escape) return CSS.escape(String(sel));
    return String(sel).replace(/[^a-zA-Z0-9_\-]/g, '\\$&');
  }
  function tile(tableNumber) {
    return document.querySelector(`.table-box[data-table="${esc(tableNumber)}"]`);
  }
  function setGuest(el, guestName) {
    let top = el.querySelector('.topline');
    if (guestName && guestName.trim()) {
      if (!top) { top = document.createElement('div'); top.className = 'topline'; el.prepend(top); }
      top.textContent = guestName;
    } else if (top) {
      top.remove();
    }
  }
  function flash(el) {
    const prev = el.style.outline;
    el.style.outline = '3px solid #f59e0b';
    setTimeout(() => { el.style.outline = prev || ''; }, 550);
  }
  function occupy(tableNumber, sessionId, guestName) {
    const el = tile(tableNumber);
    if (!el) return;
    el.classList.remove('available');
    el.classList.add('occupied');
    el.setAttribute('href', `/table/${tableNumber}/${sessionId}`);
    setGuest(el, guestName);
    flash(el);
  }
  function free(tableNumber) {
    const el = tile(tableNumber);
    if (!el) return;
    el.classList.remove('occupied');
    el.classList.add('available');
    el.setAttribute('href', `/table/${tableNumber}`);
    setGuest(el, null);
    flash(el);
  }

  function bindRealtime() {
    const sock = POS.socket;
    if (!sock || sock.__dashBound) return;
    sock.__dashBound = true;

    sock.on('table.state.changed', (state) => {
      if (!state || !state.table_number) return;
      POS.applyTableStateSnapshot?.(state);
      const el = tile(state.table_number);
      if (el) flash(el);
    });
    sock.on('session_items_changed', ({ table_number }) => {
      const el = tile(table_number);
      if (el) flash(el);
    });
  }
  
  document.addEventListener('DOMContentLoaded', bindRealtime);

  // First-paint: mark reserved tables within the next hours
  document.addEventListener('DOMContentLoaded', () => {
    refreshReservationHints();
  });

  // Try to auto-seat due reservations once a minute while someone has the dashboard open
  document.addEventListener('DOMContentLoaded', () => {
    const hit = () => fetch('/api/housekeeping/reservations/auto-seat').catch(()=>{});
    let autoSeatTimer = null;

    function startAutoSeat() {
      if (autoSeatTimer) return;
      hit();                            // once on start
      autoSeatTimer = setInterval(hit, 60 * 1000);
    }

    function stopAutoSeat() {
      if (!autoSeatTimer) return;
      clearInterval(autoSeatTimer);
      autoSeatTimer = null;
    }

    if (document.visibilityState === 'visible') startAutoSeat();

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') startAutoSeat();
      else stopAutoSeat();
    });
  });

})();
