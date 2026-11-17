(() => {
  const $  = (id) => document.getElementById(id);

  // Panels
  const choice        = $('choicePanel');
  const nowForm       = $('nowForm');
  const resPanel      = $('resPanel');
  const futureSection = $('futureSection'); // <-- so we can hide/show it

  // Buttons
  const btnShowNow = $('btnShowNow');
  const btnShowRes = $('btnShowRes');
  const btnBackRes = $('btnBackRes');

  // Reserv form elements
  const resForm        = $('resForm');
  const dateIso        = $('date_iso');
  const timeIso        = $('time_iso');
  const hourDisp       = $('hour_display');
  const hourVal        = $('hour_value');
  const minuteDisp     = $('minute_display');
  const minuteVal      = $('minute_value');
  const nameRes        = $('guest_name_res');
  const paxRes         = $('pax_res');

  // Pickers
  const hourModal   = $('hourModal');
  const hourGrid    = $('hourGrid');
  const minuteModal = $('minuteModal');
  const minuteGrid  = $('minuteGrid');
  let pickerForEdit = false; // false = normal form, true = edit modal

  // Edit modal
  const editModal    = $('editResModal');
  const editForm     = $('editResForm');
  const editId       = $('edit_id');
  const editName     = $('edit_name');
  const editPhone    = $('edit_phone');
  const editPax      = $('edit_pax');
  const editDP       = $('edit_dp');
  const editHour     = $('edit_hour');
  const editMin      = $('edit_minute');
  const editHourDisp = $('edit_hour_display');
  const editMinDisp  = $('edit_minute_display');
  const editDate     = $('edit_date'); // hidden field in modal (added in HTML below)

  // Future reservations DOM (optional; render if present)
  const listEl  = $('futureList');
  const emptyEl = $('futureEmpty');

  // DP method elements
  const dpAmountNow       = $('dp_amount_now');
  const dpMethodNowRow    = $('dp_method_now_row');
  const dpMethodNowInput  = $('dp_method_now');

  const dpAmountRes       = $('dp_amount_res');
  const dpMethodResRow    = $('dp_method_res_row');
  const dpMethodResInput  = $('dp_method_res');

  const dpMethodEditRow   = $('dp_method_edit_row');
  const dpMethodEditInput = $('edit_dp_method');

  let dpNowCtrl  = null;
  let dpResCtrl  = null;
  let dpEditCtrl = null;

  // ---- Utilities ----
  function todayISO() {
    const d = new Date();
    const yyyy = d.getFullYear();
    const MM = String(d.getMonth()+1).padStart(2,'0');
    const dd = String(d.getDate()).padStart(2,'0');
    return `${yyyy}-${MM}-${dd}`;
  }
  function nextQuarter(){
    const m = (new Date()).getMinutes();
    if (m < 15) return 15;
    if (m < 30) return 30;
    if (m < 45) return 45;
    return 0;
  }
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

  async function readJsonSafe(resp){
    try { return await resp.json(); } catch { return null; }
  }

  // ---- Panels ----
  function showChoice(){
    if (choice)  choice.style.display = '';
    if (nowForm) nowForm.style.display = 'none';
    if (resPanel) resPanel.style.display = 'none';
    if (futureSection) futureSection.style.display = '';   // show on the first page only
  }
  function showNow(){
    if (choice)  choice.style.display = 'none';
    if (nowForm) nowForm.style.display = '';
    if (resPanel) resPanel.style.display = 'none';
    if (futureSection) futureSection.style.display = 'none'; // hide on Now
  }
  function showRes(){
    if (choice)  choice.style.display = 'none';
    if (nowForm) nowForm.style.display = 'none';
    if (resPanel) resPanel.style.display = '';
    if (futureSection) futureSection.style.display = 'none'; // hide on Reservasi

    // set today automatically
    if (dateIso) dateIso.value = todayISO();
    // default hour/min if empty
    if (!hourVal.value)   setHour((new Date()).getHours());
    if (!minuteVal.value) setMinute(nextQuarter());
  }

  // ---- Hour/Minute picker ----
  function renderHourGrid(){
    if (!hourGrid) return;
    hourGrid.innerHTML = '';
    for (let h=10; h<=23; h++){
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'pick' + (String(h) === (pickerForEdit ? editHour.value : hourVal.value) ? ' active':'' );
      b.textContent = String(h).padStart(2,'0');
      b.onclick = () => { if (pickerForEdit) setEditHour(h); else setHour(h); closeHourPicker(); };
      hourGrid.appendChild(b);
    }
  }
  function renderMinuteGrid(){
    if (!minuteGrid) return;
    const options = [0,15,30,45];
    minuteGrid.innerHTML = '';
    for (const m of options){
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'pick' + (String(m) === (pickerForEdit ? editMin.value : minuteVal.value) ? ' active':'' );
      b.textContent = String(m).padStart(2,'0');
      b.onclick = () => { if (pickerForEdit) setEditMinute(m); else setMinute(m); closeMinutePicker(); };
      minuteGrid.appendChild(b);
    }
  }
  function openHourPicker(forEdit=false){
    pickerForEdit = !!forEdit;
    renderHourGrid();
    if (hourModal){ hourModal.style.zIndex = '38000'; hourModal.style.display = 'flex'; }
  }
  function openMinutePicker(forEdit=false){
    pickerForEdit = !!forEdit;
    renderMinuteGrid();
    if (minuteModal){ minuteModal.style.zIndex = '38000'; minuteModal.style.display = 'flex'; }
  }
  function closeHourPicker(){ if (hourModal) hourModal.style.display = 'none'; }
  function closeMinutePicker(){ if (minuteModal) minuteModal.style.display = 'none'; }
  window.openHourPicker = openHourPicker;
  window.closeHourPicker = closeHourPicker;
  window.openMinutePicker = openMinutePicker;
  window.closeMinutePicker = closeMinutePicker;

  function setHour(h){
    const hh = Math.max(0, Math.min(23, Number(h) || 0));
    hourVal.value = String(hh);
    if (hourDisp) hourDisp.value = String(hh).padStart(2,'0');
  }

  function buildTimeHHMM(hourElId, minuteElId){
    const h = (document.getElementById(hourElId)?.value || '').padStart(2,'0');
    const m = (document.getElementById(minuteElId)?.value || '').padStart(2,'0');
    if (!/^\d{2}$/.test(h) || !/^\d{2}$/.test(m)) return null;
    return `${h}:${m}`;
  }

  function setMinute(m){
    let mm = Number(m)||0;
    const allowed = [0,15,30,45];
    if (!allowed.includes(mm)) mm = 0;
    minuteVal.value = String(mm);
    if (minuteDisp) minuteDisp.value = String(mm).padStart(2,'0');
  }
  function setEditHour(h){
    const hh = Math.max(0, Math.min(23, Number(h) || 0));
    editHour.value = String(hh);
    if (editHourDisp) editHourDisp.value = String(hh).padStart(2,'0');
  }
  function setEditMinute(m){
    let mm = Number(m)||0;
    const allowed = [0,15,30,45];
    if (!allowed.includes(mm)) mm = 0;
    editMin.value = String(mm);
    if (editMinDisp) editMinDisp.value = String(mm).padStart(2,'0');
  }

  function bindDpMethodControls(amountEl, rowEl, hiddenEl) {
    if (!amountEl || !rowEl || !hiddenEl) return null;

    const buttons = Array.from(rowEl.querySelectorAll('.dp-btn'));

    function updateVisibility() {
      const val = parseInt(amountEl.value || '0', 10);
      const show = Number.isFinite(val) && val > 0;
      rowEl.style.display = show ? '' : 'none';
      if (!show) {
        hiddenEl.value = '';
        buttons.forEach(b => b.classList.remove('active'));
      }
    }

    function selectMethod(method) {
      const m = (method || '').toLowerCase();
      hiddenEl.value = m;
      buttons.forEach(btn => {
        btn.classList.toggle('active', (btn.dataset.method || '').toLowerCase() === m);
      });
    }

    amountEl.addEventListener('input', updateVisibility);

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        selectMethod(btn.dataset.method || '');
      });
    });

    // Initialize state on load
    updateVisibility();

    return { updateVisibility, selectMethod, amountEl, rowEl, hiddenEl };
  }

  // ---- Wire chooser tabs ----
  btnShowNow?.addEventListener('click', () => {
    const sid = (window.ACTIVE_SESSION_ID || '').trim();
    if (sid) {
      window.location.href = `/table/${encodeURIComponent(window.TABLE_NUMBER)}/${encodeURIComponent(sid)}`;
      return;
    }
    btnShowNow.classList.add('active');
    btnShowRes.classList.remove('active');
    showNow();
  });

  btnShowRes?.addEventListener('click', () => {
    btnShowRes.classList.add('active');
    btnShowNow.classList.remove('active');
    showRes();
  });

  btnBackRes && btnBackRes.addEventListener('click', showChoice);

  // ---- Submit reservation (create) ----
  resForm && resForm.addEventListener('submit', (e) => {
    const name = (nameRes?.value || '').trim();
    const pax  = parseInt(paxRes?.value ?? '1', 10);
    const time = buildTimeHHMM('hour_value','minute_value');

    if (!name) { e.preventDefault(); alert('Nama tamu wajib diisi.'); nameRes?.focus(); return; }
    if (!Number.isFinite(pax) || pax < 1) { e.preventDefault(); alert('PAX minimal 1.'); paxRes?.focus(); return; }
    if (!time) { e.preventDefault(); alert('Pilih jam & menit.'); return; }

    const [th, tm] = time.split(':').map(n=>parseInt(n,10));
    if (th < 10 || th > 23) { e.preventDefault(); alert('Jam harus 10–23.'); return; }
    if (![0,15,30,45].includes(tm)) { e.preventDefault(); alert('Menit harus 00/15/30/45.'); return; }

    // NEW: DP method required if DP > 0
    if (dpAmountRes && dpMethodResInput) {
      const dpVal = parseInt(dpAmountRes.value || '0', 10);
      if (dpVal > 0 && !dpMethodResInput.value) {
        e.preventDefault();
        alert('Pilih metode DP.');
        return;
      }
    }

    if (dateIso && !dateIso.value) dateIso.value = todayISO();
    if (timeIso) timeIso.value = time; // server create path already accepts HH:MM
  });


  // ---- Edit flow ----
  window.openEditReservation = async function(resId){
    try {
      const r = await fetch(`/api/reservations/${resId}`, { credentials: 'same-origin' });
      if (!r.ok) throw new Error('HTTP '+r.status);
      const { item } = await r.json();

      // Fill modal
      editId.value    = item.id;
      editName.value  = item.guest_name || '';
      editPhone.value = item.phone || '';
      editPax.value   = item.pax || 1;
      if (editDate)   editDate.value = item.date || todayISO();

      // time -> split hh:mm
      const t  = String(item.time || '');
      const tt = t.includes(':') ? t.split(':') : ['10','00'];
      const hh = parseInt(tt[0] || '10', 10);
      const mm = parseInt(tt[1] || '0', 10);
      setEditHour(hh);
      setEditMinute(isNaN(mm)?0:mm);

      editDP.value = item.dp_amount || 0;

      // Show/hide chips and preselect method (if any)
      if (dpEditCtrl) {
        dpEditCtrl.updateVisibility();
        if ((item.dp_amount || 0) > 0 && item.dp_method) {
          dpEditCtrl.selectMethod(item.dp_method);
        }
      }

      editModal.style.display = 'flex';

    } catch (e) {
      alert('Gagal memuat data reservasi.');
      console.error(e);
    }
  };
  window.closeEditModal = function(){ editModal.style.display = 'none'; };

  window.openResSession = async function(resId){
    try {
      const r = await fetch(`/api/reservations/${resId}/ensure_session`, {
        method: 'POST',
        credentials: 'same-origin'
      });
      const j = await readJsonSafe(r);
      if (!r.ok || !j || j.status !== 'ok') {
        const msg = j?.message || `HTTP ${r.status}`;
        alert(`Gagal membuka sesi.\n${msg}`);
        return;
      }
      if (j.redirect) window.location.href = j.redirect;
    } catch (e) {
      alert('Gagal membuka sesi (network).');
      console.error(e);
    }
  };

  editForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id  = editId.value;
    const nm  = (editName.value || '').trim();
    const ph  = (editPhone.value || '').trim();
    const pax = Math.max(1, parseInt(editPax.value || '1', 10));
    const dp  = Math.max(0, parseInt(editDP.value || '0', 10));
    const dpMethodVal = (dpMethodEditInput?.value || '').trim();
    const dt  = editDate ? (editDate.value || todayISO()) : todayISO();

    const timeEdit = buildTimeHHMM('edit_hour','edit_minute');
    if (!nm)      { alert('Nama wajib diisi.'); return; }
    if (!timeEdit){ alert('Pilih jam & menit.'); return; }

    const [eh, em] = timeEdit.split(':').map(n=>parseInt(n,10));
    if (eh < 10 || eh > 23) { alert('Jam harus 10–23.'); return; }
    if (![0,15,30,45].includes(em)) { alert('Menit harus 00/15/30/45.'); return; }

    // Some backends require seconds and/or date on edit:
    const payload = {
      guest_name: nm,
      phone: ph || null,
      pax,
      date: dt,                         // include date to satisfy validators
      time: `${timeEdit}:00`,           // HH:MM:SS to avoid 400
      dp_amount: dp
    };

    if (dp > 0) {
      if (!dpMethodVal) {
        alert('Pilih metode DP.');
        return;
      }
      payload.dp_method = dpMethodVal;
    }


    try {
      const r  = await fetch(`/api/reservations/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });
      const j = await readJsonSafe(r);
      if (!r.ok) {
        const msg = j?.message || (j?.error) || `HTTP ${r.status}`;
        alert(`Gagal menyimpan perubahan.\n${msg}`);
        console.error('Edit reservation failed:', r.status, j || '(no JSON)');
        return;
      }
      closeEditModal();
      loadFuture();
    } catch (err) {
      alert('Gagal menyimpan perubahan (network).');
      console.error(err);
    }
  });

  // ---- Future list (optional) ----
  async function loadFuture() {
    if (!listEl) return;
    try {
      const tn = window.TABLE_NUMBER;
      const r = await fetch(`/api/reservations/future/${encodeURIComponent(tn)}`, { credentials: 'same-origin' });
      if (!r.ok) throw new Error('HTTP '+r.status);
      const j = await r.json();
      renderFuture(j.items || []);
    } catch (_) { /* no-op */ }
  }

  function renderFuture(items) {
    if (!listEl) return;
    listEl.innerHTML = '';
    if (!items.length) {
      if (emptyEl) emptyEl.style.display = '';
      return;
    }
    if (emptyEl) emptyEl.style.display = 'none';

    for (const it of items) {
      const li = document.createElement('li');
      li.id = `res-${it.id}`;
      li.className = 'res-row';
      li.innerHTML = `
        <div class="res-main">
          <div class="res-guest"><strong>${esc(it.guest_name || '—')}</strong> — ${Number(it.pax||0)} pax</div>
          <div class="res-time">${esc(it.date)} ${esc(String(it.time).slice(0,5))}</div>
        </div>
        <div class="res-actions">
          <form method="POST" action="/reservations/${it.id}/seat" style="display:inline">
            <button class="btn small gray" type="submit">Seat</button>
          </form>
          <button class="btn small outline" data-act="session" data-id="${it.id}">Buka Sesi</button>
          <button class="btn small" data-act="edit" data-id="${it.id}">Edit</button>
          <button class="btn small danger" data-act="cancel" data-id="${it.id}">Batalkan</button>
        </div>
      `;
      listEl.appendChild(li);
    }
  }

  // delegate actions
  listEl?.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-act]');
    if (!btn) return;
    const id = btn.getAttribute('data-id');
    const act = btn.getAttribute('data-act');
    if (act === 'edit') {
      window.openEditReservation && window.openEditReservation(id);
    } else if (act === 'session') {
      window.openResSession && window.openResSession(id);
    } else if (act === 'cancel') {
      window.cancelReservation && window.cancelReservation(id, window.TABLE_NUMBER);
    }
  });

  // Cancel reservation
  window.cancelReservation = async function(resId, tableNumber){
    if (!confirm('Batalkan reservasi ini?')) return;
    try {
      const r = await fetch(`/api/reservations/${resId}/cancel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ table_number: tableNumber || null })
      });
      if (!r.ok) {
        const j = await readJsonSafe(r);
        alert('Gagal membatalkan reservasi.' + (j?.message ? `\n${j.message}` : ''));
        return;
      }
      const li = document.getElementById(`res-${resId}`);
      if (li) li.remove();
      if (listEl && !listEl.querySelector('li') && emptyEl) emptyEl.style.display = '';
    } catch (e) {
      alert('Gagal membatalkan reservasi (network).');
      console.error(e);
    }
  };

  // ---- Optional sockets ----
  function bindSocketsSafely() {
    if (typeof io !== 'function') return;
    const POS = (window.POS = window.POS || {});
    const socket = POS.socket || (POS.socket = io('/pos', { transports: ['websocket', 'polling'] }));
    socket.on('connect', () => {
      const tn = window.TABLE_NUMBER;
      if (tn) socket.emit('watch.table', { table: tn });
    });
    socket.on('reservations.changed', () => loadFuture());
    socket.on('reservations.autoseated', () => loadFuture());
    socket.on('session_created', () => loadFuture());
    socket.on('session_closed', () => loadFuture());
  }

  // ---- Boot ----
  document.addEventListener('DOMContentLoaded', () => {
    showChoice();   // futureSection visible here
    loadFuture();
    bindSocketsSafely();

    // Bind DP method chips for Now / Reservation / Edit
    dpNowCtrl  = bindDpMethodControls(dpAmountNow, dpMethodNowRow, dpMethodNowInput);
    dpResCtrl  = bindDpMethodControls(dpAmountRes, dpMethodResRow, dpMethodResInput);
    dpEditCtrl = bindDpMethodControls(editDP, dpMethodEditRow, dpMethodEditInput);

    // Validate DP method on "Now" form submit
    if (nowForm) {
      nowForm.addEventListener('submit', (e) => {
        if (!dpAmountNow || !dpMethodNowInput) return;
        const val = parseInt(dpAmountNow.value || '0', 10);
        if (val > 0 && !dpMethodNowInput.value) {
          e.preventDefault();
          alert('Pilih metode DP.');
        }
      });
    }
  });


  // Click outside modal closes
  [hourModal, minuteModal, editModal].forEach(mod => {
    if (!mod) return;
    mod.addEventListener('click', (e) => {
      if (e.target === mod) mod.style.display = 'none';
    });
  });
})();
