// ------- helpers -------
function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === 'class') e.className = v;
    else if (k.startsWith('on:')) e.addEventListener(k.slice(3), v);
    else e.setAttribute(k, v);
  });
  children.flat().forEach(c => e.append(c instanceof Node ? c : document.createTextNode(c)));
  return e;
}
const debounce = (fn, ms = 200) => { let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); }; };
const IS_ADMIN = (window.IS_ADMIN === true) || (window.IS_ADMIN === 'true');
const KNOWN_TAGS = [
  'kitchen','expediter','dapur','all','fallback',
  'bar','bar-1f','bar-2f',
  'cumi','masak','steam','bakaran','sayuran'
];

// ------- API helpers -------
async function jsonFetch(url, opts = {}) {
  const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!r.ok) {
    let msg = 'Gagal';
    try { const j = await r.json(); msg = j.message || msg; } catch {}
    throw new Error(msg);
  }
  return r.headers.get('content-type')?.includes('application/json') ? r.json() : null;
}

// ------- policy: which categories are per-item? -------
const PER_ITEM_CATEGORIES = [
  'drink','drinks',
  'extra','extras','ekstra',
  'topping','toping','side','sides',
  'dessert','lain-lain','lain2','addon','add-on'
];
const isPerItemCategory = (c) => PER_ITEM_CATEGORIES.includes(String(c || '').toLowerCase());

// ------- API -------
async function updateCategoryBulk(category, patch) {
  return jsonFetch('/api/menu/category', {
    method: 'PATCH',
    body: JSON.stringify({ category, ...patch })
  });
}
async function fetchMenu() {
  const res = await fetch('/api/menu');
  if (!res.ok) throw new Error('Gagal memuat menu');
  return res.json();
}
async function toggleItem(category, item, available) {
  return jsonFetch('/api/menu/item', {
    method: 'PATCH',
    body: JSON.stringify({ category, item, available })
  });
}
async function updateItemPrice(category, item, price_per_kg) {
  return jsonFetch('/api/menu/item', {
    method: 'PATCH',
    body: JSON.stringify({ category, item, price_per_kg: Number(price_per_kg) })
  });
}
async function updateItemQrRender(category, item, qr_render) {
  return jsonFetch('/api/menu/item', {
    method: 'PATCH',
    body: JSON.stringify({ category, item, qr_render })
  });
}
async function updateItemPrinterOverride(category, item, printer_override) {
  return jsonFetch('/api/menu/item', {
    method: 'PATCH',
    body: JSON.stringify({ category, item, printer_override: (printer_override === '' ? null : printer_override) })
  });
}
async function toggleDish(category, item, name, available) {
  return jsonFetch('/api/menu/dish', {
    method: 'PATCH',
    body: JSON.stringify({ category, item, name, available })
  });
}
async function updateDishPriceOverride(category, item, name, price_override) {
  return jsonFetch('/api/menu/dish', {
    method: 'PATCH',
    body: JSON.stringify({
      category, item, name,
      price_override: (price_override === '' ? null : Number(price_override))
    })
  });
}
async function fetchPrinters() {
  return jsonFetch('/api/printers');
}
async function updatePrinterName(id, name) {
  return jsonFetch(`/api/printers/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify({ name })
  });
}
async function triggerPrinterMock(id) {
  return jsonFetch(`/api/printers/${encodeURIComponent(id)}/mock`, { method: 'POST' });
}
async function updatePrinterTags(id, tags) {
  return jsonFetch(`/api/printers/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    body: JSON.stringify({ tags })
  });
}
async function updateDishPrinterOverride(category, item, name, printer_override) {
  return jsonFetch('/api/menu/dish', {
    method: 'PATCH',
    body: JSON.stringify({
      category, item, name,
      printer_override: (printer_override === '' ? null : printer_override)
    })
  });
}

// ------- state & filters -------
let MENU_CACHE = {};
const state = { q: '', category: '', avail: '' }; // avail: '', 'on', 'off'
const EXPANDED = new Set(); // expanded categories for Rincian
let PRINTERS_CACHE = null;
let PRINTERS_LOADED = false;

function buildCategoryList(menu) {
  return Object.keys(menu).sort((a, b) => a.localeCompare(b));
}
function normalizedDishes(itemData) {
  return (itemData.dishes || []).map(d => typeof d === 'string'
    ? { name: d, available: true, printer_override: null }
    : ({ available: true, printer_override: null, ...d })
  );
}

// ------- render table -------
function renderTable(menu) {
  const body = document.getElementById('menuBody');
  body.innerHTML = '';

  const q = state.q.trim().toLowerCase();

  const buildPrinterOverride = (category, itemName, currentOverride) => {
    const label = currentOverride ? `Override: ${currentOverride}` : 'Auto (routing)';
    const btn = el('button', {
      class: 'ghost',
      'on:click': (ev) => {
        ev.stopPropagation();
        openOverrideModal(label, KNOWN_TAGS, async (val) => {
          try { await updateItemPrinterOverride(category, itemName, val || ''); await init(false); }
          catch (e) { alert(e.message || 'Gagal set override'); }
        });
      }
    }, label);
    return el('div', { class: 'override-picker-wrap' }, btn);
  };

  const buildQrToggle = (category, itemName, currentVal) => {
    const enabled = currentVal !== false;
    const badge = el('span', { class: 'badge ' + (enabled ? 'on' : 'off') }, enabled ? 'QR ON' : 'QR OFF');
    const btn = el('button', {
      class: 'mini',
      'on:click': async (ev) => {
        ev.stopPropagation();
        try {
          await updateItemQrRender(category, itemName, !enabled);
          await init(false);
        } catch (e) { alert(e.message || 'Gagal ubah QR'); }
      }
    }, enabled ? 'Sembunyikan QR' : 'Tampilkan QR');
    const resetBtn = el('button', {
      class: 'mini ghost',
      'on:click': async (ev) => {
        ev.stopPropagation();
        try { await updateItemQrRender(category, itemName, null); await init(false); }
        catch (e) { alert(e.message || 'Gagal reset QR'); }
      }
    }, 'Default');
    return el('div', { class: 'vstack-qr' }, badge, el('div', { class: 'hstack mt-4' }, btn, resetBtn));
  };

  for (const [category, items] of Object.entries(menu)) {
    if (state.category && state.category !== category) continue;

    const perItemMode = isPerItemCategory(category);

    if (!perItemMode) {
      // ---------- CATEGORY MODE ----------
      const itemArr = Object.entries(items);
      const allAvail = itemArr.every(([, it]) => it.available !== false);
      const prices = new Set(itemArr.map(([, it]) => Number(it.price_per_kg || 0)));
      const unifiedPrice = prices.size === 1 ? [...prices][0] : '';

      // text match over cat+items+variants
      if (q) {
        const hay = [
          category,
          ...itemArr.map(([n]) => n),
          ...itemArr.flatMap(([, it]) => normalizedDishes(it).map(d => d.name))
        ].join(' ').toLowerCase();
        if (!hay.includes(q)) continue;
      }

      // Bulk controls (show hint if prices differ)
      const priceInput = el('input', {
        type: 'number', value: unifiedPrice, min: '0',
        placeholder: prices.size > 1 ? 'harga bervariasi' : ''
      });
      if (prices.size > 1) priceInput.title = 'Harga item berbeda-beda. Ubah per item via "Lihat Rincian".';

      const saveBtn = el('button', {
        'on:click': async () => {
          try {
            if (priceInput.value === '' || isNaN(Number(priceInput.value))) {
              alert('Masukkan harga yang valid untuk set semua item.');
              return;
            }
            await updateCategoryBulk(category, { price_per_kg: Number(priceInput.value || 0) });
            await init();
          } catch (e) { alert(e.message || 'Gagal menyimpan'); }
        }
      }, 'Simpan');

      const toggleBtn = el('button', {
        'on:click': async () => {
          try { await updateCategoryBulk(category, { available: !allAvail }); await init(); }
          catch (e) { alert(e.message || 'Gagal mengubah status'); }
        }
      }, allAvail ? 'Set Habis' : 'Set Tersedia');

      const expanded = EXPANDED.has(category);
      const expandBtn = el('button', {
        'on:click': () => { expanded ? EXPANDED.delete(category) : EXPANDED.add(category); renderTable(MENU_CACHE); }
      }, expanded ? 'Sembunyikan Rincian' : 'Lihat Rincian');

      const row = el('tr', {},
        el('td', { colspan: '2', style: 'font-weight:700;' }, category),
        el('td', {},
          el('div', { class: 'hstack' }, priceInput, saveBtn),
          el('div', { class: 'muted small' },
            prices.size > 1 ? 'Harga beragam — edit per item pada “Rincian”.' : 'Mode kategori (set harga/status semua item).'
          )
        ),
        el('td', {},
          el('span', { class: 'badge ' + (allAvail ? 'on' : 'off') }, allAvail ? 'TERSEDIA' : 'HABIS'),
          el('div', { class: 'mt-6' }, toggleBtn)
        ),
        el('td', {}, el('span', { class: 'muted' }, 'Set per item/varian')),
        el('td', {}, expandBtn)
      );
      body.appendChild(row);

      // ---------- Rincian per-item (EDIT PRICE + TOGGLE + VARIAN) ----------
      if (expanded) {
        for (const [itemName, itemData] of itemArr) {
          const avail = itemData.available !== false;

          if (state.avail === 'on' && !avail) continue;
          if (state.avail === 'off' && avail) continue;

          if (q) {
            const hay = [itemName, ...(normalizedDishes(itemData).map(d => d.name))].join(' ').toLowerCase();
            if (!hay.includes(q)) continue;
          }

          // per-item price edit (this is what you want for categories like "cumi")
          const priceInput = el('input', { type: 'number', min: '0', value: itemData.price_per_kg ?? '' });
          const saveItemBtn = el('button', {
            'on:click': async () => {
              try { await updateItemPrice(category, itemName, priceInput.value); await init(false); }
              catch (e) { alert(e.message || 'Gagal simpan harga item'); }
            }
          }, 'Simpan');

          // per-item toggle (this is what you want for ikan->gurame,baronang,…)
          const toggleItemBtn = el('button', {
            'on:click': async () => {
              try { await toggleItem(category, itemName, !avail); await init(false); }
              catch (e) { alert(e.message || 'Gagal ubah status item'); }
            }
          }, avail ? 'Set Habis' : 'Set Tersedia');

          // varian (dish overrides) if any
          const dishes = normalizedDishes(itemData);
          const varianBtn = dishes.length
            ? el('button', { 'on:click': () => openDishModal(category, itemName, itemData) }, `Kelola Varian (${dishes.length})`)
            : el('span', { class: 'muted' }, '—');

          const sub = el('tr', { class: 'subrow' },
            el('td', { class: 'muted' }, '↳'), // indent
            el('td', {}, itemName),
            el('td', {},
              el('div', { class: 'hstack' }, priceInput, saveItemBtn),
              el('div', { class: 'muted small' },
                (itemData.unit ? `Satuan: ${itemData.unit}` : ''), (itemData.portion_info ? ` — ${itemData.portion_info}` : '')
              )
            ),
            el('td', {},
              el('span', { class: 'badge ' + (avail ? 'on' : 'off') }, avail ? 'TERSEDIA' : 'HABIS'),
              el('div', { class: 'mt-6' }, toggleItemBtn),
              el('div', { class: 'mt-6' }, buildQrToggle(category, itemName, itemData.qr_render))
            ),
            el('td', {}, buildPrinterOverride(category, itemName, itemData.printer_override)),
            el('td', {}, varianBtn)
          );
          body.appendChild(sub);
        }
      }

      continue; // done with this category
    }

    // ---------- PER-ITEM MODE (drinks, extras, etc) ----------
    for (const [itemName, itemData] of Object.entries(items)) {
      const avail = (itemData.available !== false);

      if (state.avail === 'on' && !avail) continue;
      if (state.avail === 'off' && avail) continue;

      if (q) {
        const hay = [category, itemName, ...(normalizedDishes(itemData).map(d => d.name))].join(' ').toLowerCase();
        if (!hay.includes(q)) continue;
      }

      const priceInput = el('input', { type: 'number', value: itemData.price_per_kg ?? '', min: '0' });
      const saveBtn = el('button', {
        'on:click': async () => {
          try { await updateItemPrice(category, itemName, priceInput.value); await init(); }
          catch (e) { alert(e.message || 'Gagal menyimpan'); }
        }
      }, 'Simpan');

      const toggleBtn = el('button', {
        'on:click': async () => {
          try { await toggleItem(category, itemName, !avail); await init(); }
          catch (e) { alert(e.message || 'Gagal mengubah status'); }
        }
      }, avail ? 'Set Habis' : 'Set Tersedia');

      const dishes = normalizedDishes(itemData);
      const varianBtn = dishes.length
        ? el('button', { 'on:click': () => openDishModal(category, itemName, itemData) }, `Kelola Varian (${dishes.length})`)
        : el('span', { class: 'muted' }, '—');

      const row = el('tr', {},
        el('td', {}, category),
        el('td', {}, itemName),
        el('td', {},
          el('div', { class: 'hstack' }, priceInput, saveBtn),
          el('div', { class: 'muted small' }, itemData.unit ? `Satuan: ${itemData.unit}` : '')
        ),
        el('td', {},
          el('span', { class: 'badge ' + (avail ? 'on' : 'off') }, avail ? 'TERSEDIA' : 'HABIS'),
          el('div', { class: 'mt-6' }, toggleBtn),
          el('div', { class: 'mt-6' }, buildQrToggle(category, itemName, itemData.qr_render))
        ),
        el('td', {}, buildPrinterOverride(category, itemName, itemData.printer_override)),
        el('td', {}, varianBtn)
      );
      body.appendChild(row);
    }
  }

  if (!body.children.length) {
    body.appendChild(
      el('tr', {},
        el('td', { colspan: '6', class: 'muted', style: 'text-align:center; padding:16px;' },
          'Tidak ada data sesuai filter.')
      )
    );
  }
}

// ------- varian modal -------
let _dishCtx = null; // {category, itemName}

async function openDishModal(category, itemName, itemData) {
  _dishCtx = { category, itemName };
  document.getElementById('dish-modal-title').textContent = `Kelola Varian — ${itemName}`;
  const body = document.getElementById('dish-modal-body');
  body.innerHTML = '';

  const dishes = normalizedDishes(itemData);
  if (!dishes.length) {
    body.appendChild(el('p', { class: 'muted' }, 'Item ini tidak mempunyai varian.'));
  } else {
    const list = el('div', { class: 'dish-list' });
    dishes.forEach(d => {
      const badge = el('span', { class: 'badge ' + (d.available === false ? 'off' : 'on') },
        d.available === false ? 'HABIS' : 'TERSEDIA');

      const toggle = el('button', {
        'on:click': async () => {
          try {
            await toggleDish(category, itemName, d.name, !(d.available !== false));
            d.available = !(d.available !== false);
            badge.className = 'badge ' + (d.available === false ? 'off' : 'on');
            badge.textContent = d.available === false ? 'HABIS' : 'TERSEDIA';
            toggle.textContent = d.available === false ? 'Set Tersedia' : 'Set Habis';
            await init(false);
          } catch (e) { alert(e.message || 'Gagal mengubah varian'); }
        }
      }, d.available === false ? 'Set Tersedia' : 'Set Habis');

      const price = el('input', {
        type: 'number', min: '0', value: (d.price_override ?? ''),
        placeholder: 'Override (Rp)'
      });
      price.addEventListener('change', debounce(async () => {
        try { await updateDishPriceOverride(category, itemName, d.name, price.value); await init(false); }
        catch (e) { alert(e.message || 'Gagal update harga varian'); }
      }, 250));

      const printerBtn = (() => {
        const label = d.printer_override ? `Override: ${d.printer_override}` : 'Auto (routing)';
        const btn = el('button', { class: 'ghost' }, label);
        btn.addEventListener('click', (ev) => {
          ev.stopPropagation();
          openOverrideModal('Pilih printer untuk varian', KNOWN_TAGS, async (val) => {
            try {
              await updateDishPrinterOverride(category, itemName, d.name, val || '');
              d.printer_override = val || null;
              btn.textContent = val ? `Override: ${val}` : 'Auto (routing)';
              await init(false);
            } catch (e) {
              alert(e.message || 'Gagal update printer varian');
            }
          });
        });
        return btn;
      })();

      const row = el('div', { class: 'dish-row' },
        el('div', { class: 'dish-name' }, d.name),
        el('div', { class: 'dish-actions' },
          badge, toggle,
          el('span', { class: 'ovr-label' }, 'Harga override:'),
          price,
          el('span', { class: 'ovr-label' }, 'Printer override:'),
          printerBtn
        )
      );
      list.appendChild(row);
    });
    body.appendChild(list);
  }

  document.getElementById('dish-modal').style.display = 'flex';
}
function closeDishModal() {
  document.getElementById('dish-modal').style.display = 'none';
  _dishCtx = null;
}

// ------- tabs & filters wiring -------
function bindTabs() {
  document.querySelectorAll('.tab[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab[data-tab]').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const panel = document.getElementById('tab-' + btn.dataset.tab);
      if (panel) panel.classList.add('active');
      if (btn.dataset.tab === 'printers') {
        renderPrintersTab();
      }
    });
  });
}
function bindToolbar(menu) {
  const sel = document.getElementById('categoryFilter');
  const cats = buildCategoryList(menu);
  sel.innerHTML = '<option value="">Semua Kategori</option>' + cats.map(c => `<option value="${c}">${c}</option>`).join('');
  sel.value = state.category;
  sel.addEventListener('change', () => { state.category = sel.value; renderTable(MENU_CACHE); });

  const av = document.getElementById('availabilityFilter');
  av.value = state.avail;
  av.addEventListener('change', () => { state.avail = av.value; renderTable(MENU_CACHE); });

  const q = document.getElementById('searchInput');
  q.value = state.q;
  q.addEventListener('input', debounce(() => {
    state.q = q.value;
    renderTable(MENU_CACHE);
  }, 200));
}

// ------- add item form -------
function bindAddForm() {
  document.getElementById('addItemForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const qrRaw = fd.get('qr_render');
    let qr_render = null;
    if (qrRaw === 'true') qr_render = true;
    if (qrRaw === 'false') qr_render = false;
    const body = {
      category: (fd.get('category') || '').trim(),
      item: (fd.get('item') || '').trim(),
      price_per_kg: Number(fd.get('price_per_kg')),
      portion_info: (fd.get('portion_info') || '').trim(),
      unit: (fd.get('unit') || '').trim(),
      available: fd.get('available') === 'true',
      printer_override: (fd.get('printer_override') || '').trim(),
      dishes: (fd.get('dishes_raw') || '').split(',').map(s => s.trim()).filter(Boolean),
      ...(qr_render === null ? {} : { qr_render })
    };
    try {
      const res = await fetch('/api/menu/item', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.message || 'Gagal menambah item');
      }
      e.target.reset();
      await init();
    } catch (err) { alert(err.message || 'Gagal menambah item'); }
  });
}

function paintPrinters(data) {
  const body = document.getElementById('printersBody');
  if (!body) return;
  body.innerHTML = '';
  const printers = (data?.printers) || [];

  printers.forEach(p => {
    const nameInput = el('input', { type: 'text', value: (p.name || ''), placeholder: p.id, style: 'width:140px;' });
    const saveName = IS_ADMIN ? el('button', {
      'on:click': async () => {
        try { await updatePrinterName(p.id, nameInput.value.trim()); await renderPrintersTab(true); }
        catch (e) { alert(e.message || 'Gagal update nama printer'); }
      }
    }, 'Simpan') : null;

    const nameCell = IS_ADMIN
      ? el('div', { class: 'hstack' }, nameInput, saveName)
      : el('span', {}, p.name || '—');

    const tagsList = p.tags || [];
    const tagBtn = el('button', {
      class: 'ghost',
      'on:click': (ev) => {
        ev.stopPropagation();
        const open = tagMenu.style.display === 'block';
        document.querySelectorAll('.tag-picker-panel').forEach(pn => pn.style.display = 'none');
        tagMenu.style.display = open ? 'none' : 'block';
      }
    }, tagsList.length ? tagsList.join(', ') : 'Pilih tags');

    const tagMenu = el('div', { class: 'tag-picker-panel', style: 'display:none;' });
    KNOWN_TAGS.forEach(tag => {
      const id = `tag-${p.id}-${tag}`;
      const cb = el('input', { type: 'checkbox', id, checked: tagsList.includes(tag) });
      const lbl = el('label', { for: id }, tag);
      tagMenu.appendChild(el('div', { class: 'tag-row' }, cb, lbl));
    });
    const saveTags = IS_ADMIN ? el('button', {
      class: 'mini',
      'on:click': async (ev) => {
        ev.stopPropagation();
        try {
          const selected = Array.from(tagMenu.querySelectorAll('input[type="checkbox"]'))
            .filter(cb => cb.checked).map(cb => cb.id.split('-').slice(2).join('-'));
          await updatePrinterTags(p.id, selected);
          await renderPrintersTab(true);
        } catch (e) { alert(e.message || 'Gagal update tags'); }
      }
    }, 'Simpan') : null;
    const cancelTags = el('button', {
      class: 'mini ghost',
      'on:click': (ev) => { ev.stopPropagation(); tagMenu.style.display = 'none'; }
    }, 'Tutup');
    tagMenu.appendChild(el('div', { class: 'tag-menu-actions' }, saveTags || '', cancelTags));
    const tagWrapper = el('div', { class: 'tag-picker-wrap' }, tagBtn, tagMenu);

    const fallbackTag = (data.fallback_printer_id && data.fallback_printer_id === p.id)
      ? el('span', { class: 'badge on' }, 'Fallback')
      : null;

    const actionCell = IS_ADMIN
      ? el('button', {
          'on:click': async () => {
            try {
              const res = await triggerPrinterMock(p.id);
              alert(`Test dikirim ke ${p.id}: ${res.job}${res.mocked ? ' (mock)' : ''}`);
            } catch (e) { alert(e.message || 'Gagal kirim mock print'); }
          }
        }, 'Mock Print')
      : el('span', { class: 'muted small' }, 'Admin only');

    body.appendChild(el('tr', {},
      el('td', {}, nameCell, fallbackTag ? el('div', {}, fallbackTag) : ''),
      el('td', {}, p.id),
      el('td', {}, `${p.ip}:${p.port || 9100}`),
      el('td', {}, tagWrapper),
      el('td', {}, (p.floors || []).join(', ') || 'all'),
      el('td', {}, actionCell)
    ));
  });

  if (!body.children.length) {
    body.appendChild(
      el('tr', {},
        el('td', { colspan: '6', class: 'muted', style: 'text-align:center; padding:12px;' }, 'Belum ada printer.')
      )
    );
  }
}

async function renderPrintersTab(forceReload = false) {
  const body = document.getElementById('printersBody');
  if (!body) return;
  if (!forceReload && PRINTERS_LOADED && PRINTERS_CACHE) {
    paintPrinters(PRINTERS_CACHE);
    return;
  }
  try {
    const data = await fetchPrinters();
    PRINTERS_CACHE = data;
    PRINTERS_LOADED = true;
    paintPrinters(data);
  } catch (e) {
    alert(e.message || 'Gagal memuat printer');
  }
}

function openOverrideModal(title, options, onSelect) {
  const overlay = el('div', { class: 'picker-overlay', 'on:click': () => document.body.removeChild(overlay) });
  const card = el('div', { class: 'picker-card', 'on:click': (ev) => ev.stopPropagation() });
  card.appendChild(el('h3', {}, title || 'Pilih Override'));
  const grid = el('div', { class: 'picker-grid' });
  options.forEach(opt => {
    grid.appendChild(el('button', {
      class: 'picker-btn',
      'on:click': (ev) => {
        ev.stopPropagation();
        onSelect && onSelect(opt);
        document.body.removeChild(overlay);
      }
    }, opt));
  });
  grid.appendChild(el('button', {
    class: 'picker-btn ghost',
    'on:click': (ev) => {
      ev.stopPropagation();
      onSelect && onSelect('');
      document.body.removeChild(overlay);
    }
  }, 'Auto (reset)'));
  card.appendChild(grid);
  overlay.appendChild(card);
  document.body.appendChild(overlay);
}

// ------- init -------
async function init(reloadModal = true) {
  try {
    MENU_CACHE = await fetchMenu();
    bindToolbar(MENU_CACHE);
    renderTable(MENU_CACHE);

    if (_dishCtx && reloadModal) {
      const data = MENU_CACHE[_dishCtx.category]?.[_dishCtx.itemName];
      if (data) openDishModal(_dishCtx.category, _dishCtx.itemName, data);
    }
  } catch (e) {
    alert(e.message || 'Gagal memuat menu');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  bindTabs();
  bindAddForm();
  init();
  const activeTab = document.querySelector('.tab[data-tab].active');
  if (activeTab && activeTab.dataset.tab === 'printers') {
    renderPrintersTab();
  }
});
