// reserve_only.js

// default date/time -> today, next 30-min slot
(function initDateTime(){
    const d = new Date();
    const pad = n => String(n).padStart(2,'0');
    const dd = pad(d.getDate()), mm = pad(d.getMonth()+1), yy = d.getFullYear();
    const eDate = document.getElementById('res_date_dd');
    if (eDate) eDate.value = `${dd}/${mm}/${yy}`;
  
    const m = d.getMinutes(); d.setMinutes(m + ((30 - (m % 30 || 30)) % 30));
    const eHour = document.getElementById('res_hour');
    const eMin  = document.getElementById('res_min');
    if (eHour) eHour.value = pad(d.getHours());
    if (eMin)  eMin.value  = pad(d.getMinutes());
  })();
  
  // convert dd/mm/yyyy + HH + MM -> hidden ISO fields on submit
  document.addEventListener('submit', (e) => {
    const form = e.target.closest('form');
    if (!form) return;
    if (!form.querySelector('#date_iso')) return;
  
    const dd = (document.getElementById('res_date_dd').value || '').trim();
    const hh = String(document.getElementById('res_hour').value || '').padStart(2,'0');
    const mi = document.getElementById('res_min').value;
  
    const m = dd.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!m) { e.preventDefault(); alert('Tanggal harus dd/mm/yyyy'); return; }
  
    document.getElementById('date_iso').value = `${m[3]}-${m[2]}-${m[1]}`;
    document.getElementById('time_hm').value  = `${hh}:${mi}`;
  });
  
  // right panel
  const TABLE = window.TABLE;
  
  async function reloadRes(){
    const box = document.getElementById('resList');
    box.innerHTML = '<div class="res-row">Loading…</div>';
    try{
      const r = await fetch(`/api/reservations/by_table/${encodeURIComponent(TABLE)}`);
      const j = await r.json();
      const items = j.items || [];
      box.innerHTML = '';
      if (!items.length){
        box.innerHTML = '<div class="res-row">Belum ada reservasi.</div>';
        return;
      }
      items.forEach(row => {
        const div = document.createElement('div');
        div.className = 'res-row';
        const date_dd = row.date_iso ? row.date_iso.split('-').reverse().join('/') : '';
        div.innerHTML = `
          <div class="res-title">${row.guest_name || '(tanpa nama)'} — ${row.pax} org</div>
          <div class="res-meta">Tanggal: ${date_dd} • Jam: ${row.time_str} • DP: Rp ${(row.dp_amount||0).toLocaleString('id-ID')}</div>
          <div class="res-meta">Catatan: ${row.notes || '—'}</div>
          <div class="actions">
            <button class="btn" data-act="edit">Edit</button>
            <button class="btn" data-act="pre">Preorder</button>
            <button class="btn primary" data-act="seat">Seat sekarang</button>
            <button class="btn warn" data-act="cancel">Batal</button>
          </div>
        `;
        div.querySelector('[data-act="pre"]').onclick  = () => window.openPreorderForStart(row.id, row.guest_name || '');
        div.querySelector('[data-act="seat"]').onclick = () => location.href = `/sessions/reservations/${row.id}/seat`;
        div.querySelector('[data-act="cancel"]').onclick = async () => {
          if (!confirm('Batalkan reservasi ini?')) return;
          const r = await fetch(`/api/reservations/${row.id}/cancel`, {method:'POST'});
          if (r.ok) reloadRes(); else alert('Gagal membatalkan');
        };
        div.querySelector('[data-act="edit"]').onclick = () => editRow(div, row);
        box.appendChild(div);
      });
    } catch(e) {
      box.innerHTML = '<div class="res-row">Gagal memuat.</div>';
    }
  }
  
  function editRow(container, row){
    const dd = row.date_iso ? row.date_iso.split('-').reverse().join('/') : '';
    container.innerHTML = `
      <div class="res-title">Edit — ID ${row.id}</div>
      <div class="grid2">
        <label>Nama<input id="e_name" value="${row.guest_name||''}"></label>
        <label>PAX <input id="e_pax" type="number" value="${row.pax||1}"></label>
      </div>
      <div class="grid2">
        <label>Tanggal (dd/mm/yyyy)
          <input id="e_date" value="${dd}">
        </label>
        <label>Jam (HH:MM) <input id="e_time" value="${row.time_str||''}"></label>
      </div>
      <label>DP <input id="e_dp" type="number" value="${row.dp_amount||0}"></label>
      <label>Catatan <input id="e_notes" value="${row.notes||''}"></label>
      <div class="actions">
        <button class="btn primary" id="e_save">Simpan</button>
        <button class="btn" id="e_cancel">Batal</button>
      </div>
    `;
    container.querySelector('#e_cancel').onclick = reloadRes;
    container.querySelector('#e_save').onclick = async () => {
      const payload = {
        guest_name: container.querySelector('#e_name').value.trim(),
        pax: parseInt(container.querySelector('#e_pax').value,10)||1,
        date: container.querySelector('#e_date').value.trim(), // dd/mm/yyyy OK (server parses)
        time: container.querySelector('#e_time').value.trim(),
        dp_amount: parseInt(container.querySelector('#e_dp').value,10)||0,
        notes: container.querySelector('#e_notes').value.trim()
      };
      const r = await fetch(`/api/reservations/${row.id}/update`, {
        method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
      });
      if (r.ok) reloadRes(); else alert('Gagal menyimpan');
    };
  }
  
  // preorder hook (reuse global if present)
  window.openPreorderForStart = function(resId, guest){
    if (typeof window.openPreorderModal === 'function') {
      window.openPreorderModal(resId, guest);
    } else {
      alert('Preorder modal tidak tersedia di halaman ini.');
    }
  };
  
  reloadRes();
  