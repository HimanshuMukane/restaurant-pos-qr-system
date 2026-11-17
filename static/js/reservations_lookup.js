// static/js/reservations_lookup.js
(() => {
    const $ = (s, r=document) => r.querySelector(s);
    const $$ = (s, r=document) => [...r.querySelectorAll(s)];
  
    const qInput   = $('#q');
    const btnUp    = $('#btnUpcoming');
    const btnCan   = $('#btnShowCancelled');
    const btnSubmit= $('#btnSubmit');
    const btnSort  = $('#btnSortName');
    const table    = $('#resTable');
    const tbody    = table?.querySelector('tbody');
    const btnNew   = $('#btnNewRes');
    const newModal = $('#newResModal');
    const newForm  = $('#newResForm');
    const newErr   = $('#newResErr');
    const btnNewClose  = $('#btnNewResClose');
    const btnNewCancel = $('#btnNewResCancel');

    const newName   = $('#new_name');
    const newPhone  = $('#new_phone');
    const newPax    = $('#new_pax');
    const newTable  = $('#new_table');
    const newDate   = $('#new_date');
    const newHour   = $('#new_hour');
    const newMin    = $('#new_min');
    const newTime   = $('#new_time');
    const newNotes  = $('#new_notes');
    const newDpAmt  = $('#new_dp_amount');
    const newDpRow  = $('#new_dp_method_row');
    const newDpMeth = $('#new_dp_method');

    const btnPickTable = $('#btnPickTable');
    const pickModal = $('#tablePickerModal');
    const pickClose = $('#btnPickTableClose');
    const floorTabs = $('#tableFloorTabs');
    const tableGrid = $('#tableGrid');
    const tablesData = Array.isArray(window.TABLES) ? window.TABLES : [];
    let currentFloor = null;
  
    // Parse initial states from aria-pressed
    let showUpcomingOnly = (btnUp?.getAttribute('aria-pressed') === 'true');
    let showCancelled    = (btnCan?.getAttribute('aria-pressed') === 'true');
  
    function parseRowInfo(tr){
      const name   = (tr.dataset.name || '').toLowerCase();
      const phone  = (tr.dataset.phone || '').toLowerCase();
      const table  = (tr.dataset.table || '').toLowerCase();
      const status = (tr.dataset.status || '').toLowerCase();
      const kind   = (tr.dataset.kind || 'reservation').toLowerCase();
      const dtISO  = tr.dataset.dt; // YYYY-MM-DDTHH:MM
      let when = null;
      if (dtISO) {
        // Safe parse: treat as local time
        const [d,t] = dtISO.split('T');
        const [Y,M,D] = d.split('-').map(n=>parseInt(n,10));
        const [h,m] = (t || '00:00').split(':').map(n=>parseInt(n,10));
        when = new Date(Y, (M-1), D, h||0, m||0, 0, 0);
      }
      return { name, phone, table, status, kind, when };
    }
  
    function nowLocal(){ return new Date(); }
  
    function rowMatches(tr, q){
      const { name, phone, table, status, kind, when } = parseRowInfo(tr);
    
      // Base visibility: confirmed/seated/pending + active sessions
      const baseAllowed = (
        status === 'confirmed' ||
        status === 'seated' ||
        status === 'pending' ||
        status === 'active' ||
        kind === 'session'
      );
    
      // Optional allowances
      const allowCancelled = (status === 'cancelled' && showCancelled);
      const allowFinished  = (status === 'finished'  && showFinished);
    
      if (!(baseAllowed || allowCancelled || allowFinished)) return false;
    
      // Upcoming-only filter
      if (showUpcomingOnly && kind !== 'session') { if (when && when < nowLocal()) return false; }
    
      if (!q) return true;
      const hay = `${name} ${phone} ${table}`;
      return hay.includes(q);
    }
    
    const btnFin   = $('#btnShowFinished');
    let showFinished = (btnFin?.getAttribute('aria-pressed') === 'true');
    let sortByName   = (btnSort?.getAttribute('aria-pressed') === 'true');
    
    function setPressed(btn, on){
      if (!btn) return;
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    }

    function ensureRowOrder(){
      if (!tbody) return;
      $$('tr[data-id]', tbody).forEach((tr, idx) => {
        if (!tr.dataset.order) tr.dataset.order = String(idx);
      });
    }

    function sortRows(){
      if (!tbody) return;
      ensureRowOrder();
      const rows = $$('tr[data-id]', tbody);
      rows.sort((a,b) => {
        if (sortByName) {
          const cmp = (a.dataset.name || '').localeCompare((b.dataset.name || ''), undefined, { sensitivity:'base' });
          if (cmp !== 0) return cmp;
        }
        const oa = parseInt(a.dataset.order || '0', 10);
        const ob = parseInt(b.dataset.order || '0', 10);
        return oa - ob;
      });
      rows.forEach(r => tbody.appendChild(r));
    }
    
  
    // Debounce helper
    function debounce(fn, ms=120){
      let t; return (...args) => { clearTimeout(t); t=setTimeout(()=>fn(...args), ms); };
    }

    function readJsonSafe(resp){
      return resp.json().catch(() => null);
    }
  
    function filterRows(){
      if (!tbody) return;
      const q = (qInput?.value || '').trim().toLowerCase();
      const rows = $$('tr[data-id]', tbody);
  
      let anyVisible = false;
      for (const tr of rows){
        const vis = rowMatches(tr, q);
        tr.classList.toggle('is-hidden', !vis);
        if (vis) anyVisible = true;
      }
  
      // hide "Tidak ada hasil." row if not needed
      const empty = tbody.querySelector('.no-rows');
      if (empty) empty.style.display = anyVisible ? 'none' : '';
  
      // Single-letter jump: scroll to first matching NAME starting with that letter
      if (q.length === 1 && /^[a-z0-9]$/.test(q)) {
        const target = rows.find(tr => !tr.classList.contains('is-hidden') && (tr.dataset.name || '').startsWith(q));
        if (target) target.scrollIntoView({ block:'center', behavior:'smooth' });
      }
    }
  
    const filterRowsDebounced = debounce(filterRows, 75);
  
    // Wire live search
    qInput?.addEventListener('input', filterRowsDebounced);
    
    btnFin?.addEventListener('click', () => {
      showFinished = !showFinished;
      setPressed(btnFin, showFinished);
      filterRows();
    });
    btnSort?.addEventListener('click', () => {
      sortByName = !sortByName;
      setPressed(btnSort, sortByName);
      sortRows();
    });

    
    // Toggles
    btnUp?.addEventListener('click', () => {
      showUpcomingOnly = !showUpcomingOnly;
      setPressed(btnUp, showUpcomingOnly);
      filterRows();
    });
    btnCan?.addEventListener('click', () => {
      showCancelled = !showCancelled;
      setPressed(btnCan, showCancelled);
      filterRows();
    });
  
    // Optional fallback submit → keep server-side flow if desired
    btnSubmit?.addEventListener('click', () => {
      // build a simple query string using current UI state
      const params = new URLSearchParams();
      const q = (qInput?.value || '').trim();
      if (q) params.set('q', q);
      if (showUpcomingOnly) params.set('upcoming', '1');
      if (showCancelled) params.set('show_cancelled', '1');
      const qs = params.toString();
      window.location.search = qs ? `?${qs}` : '';
    });
  
    // Inline cancel
    tbody?.addEventListener('click', async (e) => {
      const btn = e.target.closest('.js-cancel');
      if (!btn) return;
      const id = btn.getAttribute('data-id');
      if (!id) return;
      if (!confirm('Batalkan reservasi ini?')) return;
  
      try {
        const r = await fetch(`/api/reservations/${encodeURIComponent(id)}/cancel`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin'
        });
        if (!r.ok) throw new Error('HTTP '+r.status);
  
        // Update row status + badge without reload
        const tr = tbody.querySelector(`tr[data-id="${CSS.escape(id)}"]`);
        if (tr) {
          tr.dataset.status = 'cancelled';
          const badge = tr.querySelector('.badge');
          if (badge) { badge.textContent = 'cancelled'; badge.className = 'badge cancelled'; }
        }
        // Re-run filter (hide it if "show cancelled" is off)
        filterRows();
      } catch (err) {
        alert('Gagal membatalkan reservasi.');
        console.error(err);
      }
    });
  
    // Boot
    document.addEventListener('DOMContentLoaded', () => {
      ensureRowOrder();
      if (sortByName) sortRows();
      filterRows();
    });

    function setNewDefaults(){
      if (!newDate || !newHour || !newMin) return;
      const d = new Date();
      const pad = n => String(n).padStart(2,'0');
      newDate.value = d.toISOString().slice(0,10);
      const h = d.getHours();
      const defaultHour = (h >= 11 && h <= 23) ? h : 11;
      newHour.value = pad(defaultHour);
      newMin.value = '00';
      if (newTime) newTime.value = `${pad(defaultHour)}:00`;
    }

    function openNewModal(){
      if (!newModal) return;
      if (newErr) newErr.textContent = '';
      setNewDefaults();
      if (newTable) newTable.value = '';
      if (newDpAmt) newDpAmt.value = '';
      if (newDpMeth) newDpMeth.value = '';
      if (newDpRow) newDpRow.style.display = '';
      newModal.style.display = 'flex';
    }

    function closeNewModal(){
      if (!newModal) return;
      newModal.style.display = 'none';
    }

    btnNew?.addEventListener('click', openNewModal);
    btnNewClose?.addEventListener('click', closeNewModal);
    btnNewCancel?.addEventListener('click', closeNewModal);
    newModal?.addEventListener('click', (e) => {
      if (e.target === newModal) closeNewModal();
    });
    newDpAmt?.addEventListener('input', () => {});
    newHour?.addEventListener('change', () => {
      if (newTime && newHour && newMin) newTime.value = `${newHour.value}:${newMin.value}`;
    });
    newMin?.addEventListener('change', () => {
      if (newTime && newHour && newMin) newTime.value = `${newHour.value}:${newMin.value}`;
    });

    function floorsFromTables(){
      const set = new Set();
      tablesData.forEach(t => {
        if (t && t.floor !== undefined && t.floor !== null) set.add(String(t.floor));
      });
      const arr = Array.from(set);
      arr.sort((a,b) => a.localeCompare(b, undefined, { numeric: true }));
      return arr;
    }

    function sortTables(list){
      return list.slice().sort((a,b) => String(a.number || '').localeCompare(String(b.number || ''), undefined, { numeric: true }));
    }

    function renderFloorTabs(){
      if (!floorTabs) return;
      const floors = floorsFromTables();
      if (!floors.length) return;
      if (!currentFloor) {
        const def = String(window.TABLE_DEFAULT_FLOOR || '');
        currentFloor = floors.includes(def) ? def : floors[0];
      }
      floorTabs.innerHTML = '';
      floors.forEach(f => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'floor-tab' + (f === currentFloor ? ' active' : '');
        btn.textContent = `Lantai ${f}`;
        btn.addEventListener('click', () => {
          currentFloor = f;
          renderFloorTabs();
          renderTableGrid();
        });
        floorTabs.appendChild(btn);
      });
    }

    function renderTableGrid(){
      if (!tableGrid) return;
      const list = sortTables(tablesData.filter(t => String(t.floor ?? '') === String(currentFloor)));
      tableGrid.innerHTML = '';
      list.forEach(t => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'table-btn';
        btn.textContent = String(t.number || '');
        btn.addEventListener('click', () => {
          if (newTable) newTable.value = String(t.number || '');
          closeTablePickerUI();
        });
        tableGrid.appendChild(btn);
      });
    }

    function openTablePickerUI(){
      if (!pickModal) return;
      const def = String(window.TABLE_DEFAULT_FLOOR || '');
      currentFloor = def || currentFloor;
      renderFloorTabs();
      renderTableGrid();
      pickModal.style.display = 'flex';
    }

    function closeTablePickerUI(){
      if (!pickModal) return;
      pickModal.style.display = 'none';
    }

    btnPickTable?.addEventListener('click', openTablePickerUI);
    newTable?.addEventListener('focus', () => {
      if (tablesData.length) openTablePickerUI();
    });
    pickClose?.addEventListener('click', closeTablePickerUI);
    pickModal?.addEventListener('click', (e) => {
      if (e.target === pickModal) closeTablePickerUI();
    });

    window.renderTablePicker = () => {
      renderFloorTabs();
      renderTableGrid();
    };

    newForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (newErr) newErr.textContent = '';

      if (newTime && newHour && newMin) {
        newTime.value = `${newHour.value}:${newMin.value}`;
      }

      const guest_name = (newName?.value || '').trim();
      const phone = (newPhone?.value || '').trim();
      const pax = parseInt(newPax?.value || '1', 10);
      const table_number = (newTable?.value || '').trim();
      const date = (newDate?.value || '').trim();
      const time = (newTime?.value || '').trim();
      const notes = (newNotes?.value || '').trim();
      const dp_amount = parseInt(newDpAmt?.value || '0', 10) || 0;
      const dp_method = (newDpMeth?.value || '').trim();

      if (!guest_name) { if (newErr) newErr.textContent = 'Nama tamu wajib diisi.'; return; }
      if (!table_number) { if (newErr) newErr.textContent = 'Nomor meja wajib diisi.'; return; }
      if (!Number.isFinite(pax) || pax < 1) { if (newErr) newErr.textContent = 'PAX tidak valid.'; return; }
      if (!date || !time) { if (newErr) newErr.textContent = 'Tanggal & jam wajib diisi.'; return; }

      const tparts = time.split(':');
      const hh = parseInt(tparts[0] || '0', 10);
      const mm = parseInt(tparts[1] || '0', 10);
      if (hh < 11 || hh > 23) { if (newErr) newErr.textContent = 'Jam harus 11–23.'; return; }
      if (![0,15,30,45].includes(mm)) { if (newErr) newErr.textContent = 'Menit harus 00/15/30/45.'; return; }

      if (dp_amount <= 0) { if (newErr) newErr.textContent = 'DP wajib diisi (> 0).'; return; }
      if (!dp_method) { if (newErr) newErr.textContent = 'Metode DP wajib dipilih.'; return; }

      try {
        const r = await fetch('/api/reservations/create_with_table', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({
            guest_name,
            phone: phone || null,
            pax,
            table_number,
            date,
            time,
            notes: notes || null,
            dp_amount,
            dp_method: dp_method || null
          })
        });
        const j = await readJsonSafe(r);
        if (!r.ok || j?.status !== 'success') {
          const msg = j?.message || `Gagal membuat reservasi (HTTP ${r.status})`;
          if (newErr) newErr.textContent = msg;
          return;
        }
        closeNewModal();
        window.location.reload();
      } catch (err) {
        if (newErr) newErr.textContent = 'Gagal membuat reservasi (network).';
        console.error(err);
      }
    });
  })();
  
