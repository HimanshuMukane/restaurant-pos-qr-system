(() => {
  'use strict';

  // ===== state =====
  let menu = {};
  let selectedCategory = null;
  let selectedSubcategory = null;
  let selectedDish = null;
  const MENU_STATE_KEY = 'menu_state';
  const clearMenuState = () => {
    try { sessionStorage.removeItem(MENU_STATE_KEY); } catch {}
  };

  const POS = (window.POS = window.POS || {});
  POS.menuPaging = POS.menuPaging || {};

  // ===== utils =====
  const $ = (s, r=document) => r.querySelector(s);
  const $all = (s, r=document) => [...r.querySelectorAll(s)];
  const cssNum = (el, prop) => parseFloat(getComputedStyle(el).getPropertyValue(prop)) || 0;
  const notify = (message, type = 'info', duration = 2200) => {
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
  const withBusy = async (btn, text, fn) => {
    if (POS && typeof POS.withButtonBusy === 'function') {
      return POS.withButtonBusy(btn, text, fn);
    }
    return Promise.resolve(fn());
  };

  // --- PRESET NOTES (same list you use in edit.js) ---
  const ADD_PRESET_NOTES = {
    bar: [
      "Ekstra Es","Gula Pisah","Gula Sedikit","Di Gelas","Pakai Es","Panas","Sedikit Es",
      "Tanpa Gula","Tanpa Susu","Es Gula Dikit","Es Gula Pisah","Tanpa Es","Biasa","Hangat",
      "Gula Merah","Es Pisah","Murni"
    ],
    kitchen: [
      "Pedas","Dibatok","1 Ekor","2 Ekor","3 Ekor","4 Ekor","Kuah Banyak","Tanpa Terasi",
      "1/2 Porsi","1 Porsi","2 Porsi","3 Porsi","4 Porsi","Tanpa Cabe","Tidak Pedas","Cabe Dikit",
      "Piring","Tambahan","Kuah Pisah","Rebus","Saus Padang","Saus Tiram","Lada Hitam","Tauco",
      "Jadi 2 Piring","Tanpa Kepala","Tanpa Tauco","Kupas Tanpa Micin","Bungkus","Murni","Spesial",
      "Wes Mileh","Kecil","Besar","Wes Metu","Bumbu Tebel","Kepitingnya Campur","Asem Manis",
      "Nyisain","Kipas","Bakar Rica","Masak","Steam","Nunggu Orangnya"
    ],
    default: []
  };

  // Heuristic like edit.js
  function inferStationFromNameForAdd(name){
    const s = (name || "").toLowerCase();
    return /(teh|kopi|latte|americano|espresso|capp?uccino|matcha|thai ?tea|milk|susu|cok(e|)lat|milo|chocolate|es | jus|juice|sirup|lemon|jahe|soda|sparkling|mocktail|cocktail|beer|bir|wine|spritzer|aqua|air( putih| mineral)?)/.test(s)
      ? "bar" : "kitchen";
  }
  function inferStationForAdd(){
    const cat = (selectedCategory || "").toLowerCase();
    const sub = (selectedSubcategory || "").toLowerCase();
    const dishName = (selectedDish?.name || "").toLowerCase();
    const barish = /\b(minum|minuman|drink|beverage|bar)\b/;
    if (barish.test(cat) || barish.test(sub)) return "bar";
    return inferStationFromNameForAdd(dishName);
  }

  // Local state for add modal modifiers
  const ADD_MOD_STATE = {
    station: "kitchen",
    selected: [] // tokens
  };

  // Utilities for add modal modifiers
  function add_getSelectedModifiers(){
    const chipSel = [...(document.querySelectorAll("#add-modifier-chips .chip-btn.active") || [])]
      .map(b => (b.textContent || "").trim())
      .filter(Boolean);

    const customRaw = (document.querySelector("#add-note-custom")?.value || "").trim();
    const customTokens = customRaw ? customRaw.split(/[;,|•/]+/).map(s => s.trim()).filter(Boolean) : [];

    const seen = new Set();
    return [...chipSel, ...customTokens].filter(m => {
      const k = m.toLowerCase();
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  }

  function add_renderSelectedMods(){
    const zone = document.querySelector("#add-selected-mods");
    if (!zone) return;
    const tokens = add_getSelectedModifiers();
    zone.innerHTML = "";
    tokens.forEach(tok => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.textContent = tok + " ×";
      b.addEventListener("click", () => add_removeModifierToken(tok));
      zone.appendChild(b);
    });
  }

  function add_removeModifierToken(token){
    // toggle preset off if exists
    const btn = [...(document.querySelectorAll("#add-modifier-chips .chip-btn") || [])]
      .find(b => (b.textContent||"").trim().toLowerCase() === token.toLowerCase());
    if (btn && btn.classList.contains("active")){
      btn.classList.remove("active");
      btn.setAttribute("aria-pressed","false");
    } else {
      const inp = document.querySelector("#add-note-custom");
      if (inp){
        const parts = (inp.value || "").split(/[;,|•/]+/).map(s => s.trim()).filter(Boolean);
        inp.value = parts.filter(p => p.toLowerCase() !== token.toLowerCase()).join(", ");
      }
    }
    add_renderSelectedMods();
  }

  function add_renderModifierChips(){
    const zone = document.querySelector("#add-modifier-chips");
    if (!zone) return;

    const presets = ADD_PRESET_NOTES[ADD_MOD_STATE.station] || ADD_PRESET_NOTES.default;
    zone.innerHTML = "";
    presets.forEach(txt => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip-btn";
      b.textContent = txt;
      b.setAttribute("aria-pressed","false");
      b.addEventListener("click", () => {
        const now = b.classList.toggle("active");
        b.setAttribute("aria-pressed", now ? "true" : "false");
        add_renderSelectedMods();
      });
      zone.appendChild(b);
    });

    const custom = document.querySelector("#add-note-custom");
    if (custom){
      custom.removeEventListener?.("input", add_renderSelectedMods);
      custom.addEventListener("input", add_renderSelectedMods);
    }
    add_renderSelectedMods();
  }

  function clearModifierSelections(){
    // reset preset chips
    document.querySelectorAll("#add-modifier-chips .chip-btn.active").forEach(b => {
      b.classList.remove("active");
      b.setAttribute("aria-pressed","false");
    });
    // reset custom text
    const custom = document.querySelector("#add-note-custom");
    if (custom){
      custom.value = "";
      custom.dispatchEvent(new Event("input", { bubbles:true }));
    }
    add_renderSelectedMods();
  }

  function normDish(d){
    if (typeof d==='string') return {name:d,available:true};
    if (d && typeof d==='object') return {available:true, ...d};
    return {name:String(d), available:true};
  }
  function isSubcategoryUnavailable(data){
    if (!data) return false;
    if (data.available === false) return true;
    const dishes = (data.dishes || []).map(normDish);
    if (dishes.length === 0) return data.available === false;
    return dishes.every(d => d.available === false) || data.available === false;
  }
  function isCategoryUnavailable(cat){
    const subs = Object.values(menu[cat] || {});
    if (!subs.length) return false;
    return subs.every(isSubcategoryUnavailable);
  }
  function markUnavailable(btn){
    btn.classList.add('crossed'); btn.disabled = true;
    btn.setAttribute('aria-disabled','true'); btn.setAttribute('tabindex','-1');
    btn.title = 'Stok habis';
  }

  // ===== persistence =====
  function saveMenuState(){
    const state = {
      category: selectedCategory,
      subcategory: selectedSubcategory,
      dishName: (selectedDish && selectedDish.name) ? selectedDish.name : null,
      qty: Number($('#qty')?.value || 1),
      notes: $('#add-note-custom')?.value || ''
    };
    sessionStorage.setItem(MENU_STATE_KEY, JSON.stringify(state));
  }

  function restoreMenuStateIfAny(){
    try{
      const raw = sessionStorage.getItem(MENU_STATE_KEY); if (!raw) return false;
      const st = JSON.parse(raw); if (!st || !st.category) return false;
      const catExists = !!menu[st.category];
      selectedCategory = catExists ? st.category : null;
      if (!selectedCategory) return false;

      selectedSubcategory = st.subcategory || (
        st.dishName && menu[st.category] && menu[st.category][st.dishName] ? st.dishName : null
      );
      if (selectedSubcategory && !menu[selectedCategory]?.[selectedSubcategory]) {
        selectedSubcategory = null;
      }
      selectedDish = st.dishName ? { name: st.dishName, price_override: null } : null;
      renderMenu();
      const qtyEl = $('#qty'), notesEl = $('#add-note-custom');
      if (qtyEl) qtyEl.value = st.qty ?? 1;
      if (notesEl) notesEl.value = st.notes ?? '';
      return true;
    } catch { return false; }
  }

  // ===== modal / qty presets =====
  function syncQtyPresetHighlight(){
    const input = $('#qty'); if (!input) return;
    const v = parseFloat(input.value);
    let matched = false;
    $all('.qty-btn').forEach(b => {
      const isMatch = Number.parseFloat(b.dataset.q) === v;
      b.classList.toggle('is-active', isMatch);
      if (isMatch) matched = true;
    });
    if (!matched) $all('.qty-btn').forEach(b => b.classList.remove('is-active'));
  }

  // Open the add-modal and show the custom "open item" fields when needed.
  function openAddModal(){
    // original behavior
    const modal = document.getElementById('add-modal'); if (modal) modal.style.display='flex';
    const form = document.getElementById('add-form'); if (form) form.style.display='block';
    const qty = document.getElementById('qty');
    if (qty && (!qty.value || isNaN(parseFloat(qty.value)))) qty.value = '1';
    syncQtyPresetHighlight();
    // infer default station for presets
    ADD_MOD_STATE.station = inferStationForAdd();
    add_renderModifierChips();

    // our extra: show/hide open-item inputs and sync type switch
    const openZone = document.getElementById('add-open-fields');
    if (!openZone) return;
    if (selectedDish?.open){
      openZone.style.display = '';
      const nameEl = document.getElementById('add-open-name'); if (nameEl) nameEl.value = selectedDish.name || '';
      const priceEl = document.getElementById('add-open-price'); if (priceEl) priceEl.value = selectedDish.price_override != null ? String(selectedDish.price_override) : '';

      // sync the two large type buttons
      const buttons = document.querySelectorAll('#add-open-type-switch .type-switch-btn');
      const want = (ADD_MOD_STATE.station === 'bar') ? 'bar' : 'kitchen';
      buttons.forEach(b => {
        const t = b.dataset.type;
        const on = (t === want);
        b.classList.toggle('active', on);
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
    } else {
      openZone.style.display = 'none';
    }
  }

  function closeAddModal(){
    const el = $('#add-modal'); if (el) el.style.display = 'none';
  }
  window.openAddModal = openAddModal; window.closeAddModal = closeAddModal;

  // Type switch behavior: make buttons mutually exclusive and update ADD_MOD_STATE
  document.addEventListener('click', (e) => {
    const tb = e.target.closest('.type-switch-btn');
    if (!tb) return;
    const parent = tb.parentElement;
    if (!parent) return;
    // toggle exclusive
    parent.querySelectorAll('.type-switch-btn').forEach(b => {
      const is = (b === tb);
      b.classList.toggle('active', is);
      b.setAttribute('aria-pressed', is ? 'true' : 'false');
    });
    const sel = tb.dataset.type === 'bar' ? 'bar' : 'kitchen';
    ADD_MOD_STATE.station = sel;
    // re-render modifier chips for chosen station
    add_renderModifierChips();
  });

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.qty-btn');
    if (!btn) return;
    const q = Number.parseFloat(btn.dataset.q);
    const input = $('#qty');
    if (Number.isFinite(q) && input){
      input.value = String(q);
      $all('.qty-btn').forEach(b => b.classList.toggle('is-active', b === btn));
      input.dispatchEvent(new Event('input', { bubbles:true }));
    }
  });

  // ===== pager toolbar (above grid; never overlays) =====
  function removeToolbar(container){
    const tb = container.previousElementSibling;
    if (tb && tb.classList.contains('pager-toolbar')) tb.remove();
  }
  function ensureToolbarAbove(container, { onPrev, onNext, page, total }){
    removeToolbar(container);
    if (total <= 1) return null;

    const toolbar = document.createElement('div');
    toolbar.className = 'pager-toolbar';

    const leftWrap = document.createElement('div'); leftWrap.className = 'pager-left';
    const rightWrap = document.createElement('div'); rightWrap.className = 'pager-right';

    if (page > 0){
      const prev = document.createElement('button');
      prev.className = 'pager-btn'; prev.type='button'; prev.textContent='◀';
      prev.onclick = onPrev; leftWrap.appendChild(prev);
    }

    const hud = document.createElement('span');
    hud.className = 'pager-hud'; hud.textContent = `${page + 1}/${total}`;

    if (page < total - 1){
      const next = document.createElement('button');
      next.className = 'pager-btn'; next.type='button'; next.textContent='▶';
      next.onclick = onNext; rightWrap.appendChild(next);
    }

    toolbar.appendChild(leftWrap); toolbar.appendChild(hud); toolbar.appendChild(rightWrap);
    container.before(toolbar);
    return toolbar;
  }

  // ===== breadcrumb =====
  function renderBreadcrumb(){
    const bc = $('#menu-breadcrumb');
    if (!bc) return;
    bc.innerHTML = '';

    if (!selectedCategory){
      bc.style.display = 'none';
      return;
    }
    bc.style.display = 'flex';

    const sep = () => { const s=document.createElement('span'); s.className='sep'; s.textContent='→'; return s; };

    const c1 = document.createElement('span'); c1.className='crumb';
    const b1 = document.createElement('button'); b1.type='button'; b1.textContent = selectedCategory;
    b1.onclick = () => { selectedCategory = null; selectedSubcategory = null; selectedDish = null; renderMenu(); saveMenuState(); };
    c1.appendChild(b1); bc.appendChild(c1);

    if (!selectedSubcategory){
      const pending = document.createElement('span'); pending.className='pending'; pending.textContent='…';
      bc.appendChild(pending);
      return;
    }

    bc.appendChild(sep());
    const c2 = document.createElement('span'); c2.className='crumb';
    const b2 = document.createElement('button'); b2.type='button'; b2.textContent = selectedSubcategory;
    b2.onclick = () => { selectedSubcategory = null; selectedDish = null; renderMenu(); saveMenuState(); };
    c2.appendChild(b2); bc.appendChild(c2);
  }

  // ===== grid helpers =====
  function makeBtn(label, { active=false, crossed=false, onClick }={}){
    const b = document.createElement('button');
    b.className = 'menu-btn';
    b.textContent = label;
  
    // Soft auto-fit by length
    const len = (label || '').length;
    if (len > 22 && len <= 28) b.classList.add('fit-13');
    else if (len > 28 && len <= 36) b.classList.add('fit-12');
    else if (len > 36) b.classList.add('fit-11');
  
    if (active) b.classList.add('active');
    if (crossed) markUnavailable(b);
    if (onClick) b.onclick = onClick;
    return b;
  }

  function renderWrap(grid, items){
    grid.classList.remove('paged');
    grid.style.display = 'flex';
    grid.style.removeProperty('gridTemplateColumns');
    grid.style.removeProperty('gridAutoRows');
    grid.style.removeProperty('height');
    grid.style.removeProperty('overflow');
    removeToolbar(grid);
    grid.innerHTML = '';
    for (const btn of items) grid.appendChild(btn);
  }

  function measureAvailableRows(grid, rowH, hasPager){
    // Consume full viewport height below the grid
    const SAFE_BOTTOM = 10;
    const TOOLBAR_H   = hasPager ? 36 : 0;
  
    const top = grid.getBoundingClientRect().top;
    const avail = Math.max(0, Math.floor(window.innerHeight - SAFE_BOTTOM - TOOLBAR_H - top));
  
    const cs = getComputedStyle(grid);
    const rowGap = parseFloat(cs.rowGap || cs.gap || '0') || 0;
  
    // rows * rowH + (rows - 1) * rowGap <= avail
    const rows = Math.max(1, Math.floor((avail + rowGap) / (rowH + rowGap)));
    return rows;
  }
  

  function renderPaged(grid, items, key, opts){
    const { minW=120, rowH=56, hardMaxRows=24 } = opts || {};
    grid.classList.add('paged');
    grid.innerHTML = '';

    const innerW = grid.getBoundingClientRect().width || grid.clientWidth || 0;
    const cols = Math.max(1, Math.floor(innerW / minW));

    // Pass 1: assume no toolbar
    let rows = Math.min(hardMaxRows, measureAvailableRows(grid, rowH, /*hasPager*/ false));
    let perPage = Math.max(1, cols * rows);
    let totalPages = Math.max(1, Math.ceil(items.length / perPage));
    let hasPager = totalPages > 1;

    // Pass 2: if pager is needed, remeasure with toolbar cost
    if (hasPager){
      rows = Math.min(hardMaxRows, measureAvailableRows(grid, rowH, /*hasPager*/ true));
      perPage = Math.max(1, cols * rows);
      totalPages = Math.max(1, Math.ceil(items.length / perPage));
      hasPager = totalPages > 1;
    }

    let page = POS.menuPaging[key] || 0;
    page = Math.min(Math.max(0, page), totalPages - 1);
    POS.menuPaging[key] = page;

    const cs = getComputedStyle(grid);
    const rowGap = parseFloat(cs.rowGap || cs.gap || '0') || 0;
    
    // lock layout
    grid.style.display = 'grid';
    grid.style.gridTemplateColumns = `repeat(${cols}, minmax(${minW}px, 1fr))`;
    grid.style.gridAutoRows = `${rowH}px`;
    // IMPORTANT: include (rows - 1) * rowGap, or the last row will clip
    grid.style.height = `${rows * rowH + (rows - 1) * rowGap}px`;
    grid.style.overflow = 'hidden';
    

    const start = page * perPage;
    const end   = Math.min(items.length, start + perPage);
    const slice = items.slice(start, end);

    for (const btn of slice) grid.appendChild(btn);
    for (let i = slice.length; i < perPage; i++) grid.appendChild(document.createElement('div'));

    if (hasPager){
      ensureToolbarAbove(grid, {
        onPrev: () => { if (page > 0){ POS.menuPaging[key] = page - 1; renderPaged(grid, items, key, opts); } },
        onNext: () => { if (page < totalPages - 1){ POS.menuPaging[key] = page + 1; renderPaged(grid, items, key, opts); } },
        page, total: totalPages
      });
    } else {
      removeToolbar(grid);
    }
  }

  // ===== main drilldown renderer (category → subcategory → dish) =====
  function renderMenu(){
    try {
      const grid = $('#menu-grid'); if (!grid) return;
      grid.innerHTML = '';
      grid.classList.remove('is-cats','is-subs','is-dishes','paged');
      renderBreadcrumb();

      // LEVEL 0: Categories → wrap (bigger buttons via CSS)
      if (!selectedCategory){
        grid.classList.add('is-cats');
        const cats = Object.keys(menu || {});
        // Special open-item button (custom name/price/category)
        const openBtn = makeBtn('Open Item', {
          onClick: () => {
            // prepare a transient open item and show add modal
            selectedDish = { name: '', price_override: null, open: true };
            // default station inferred as kitchen unless changed in modal
            openAddModal();
            saveMenuState();
          }
        });
        const buttons = cats.map(cat => makeBtn(cat, {
          crossed: isCategoryUnavailable(cat),
          onClick: () => {
            selectedCategory = cat; selectedSubcategory = null; selectedDish = null;
            POS.menuPaging['subs:'+cat] = 0;
            renderMenu(); saveMenuState();
          }
        }));
        // show open item last
        buttons.push(openBtn);
        renderWrap(grid, buttons);
        return;
      }

      const subDict = menu[selectedCategory] || {};
      const subs = Object.keys(subDict);

      // LEVEL 1: Subcategories (or terminal category)
      if (!selectedSubcategory){
        grid.classList.add('is-subs');

        if (subs.length === 0){
          renderWrap(grid, []);
          return;
        }

        const buttons = subs.map(sub => {
          const data = subDict[sub];
          const crossed = isSubcategoryUnavailable(data);
          return makeBtn(sub, {
            crossed,
            onClick: () => {
              const dishes = Array.isArray(data?.dishes) ? data.dishes : [];
              if (dishes.length === 0){
                if (crossed) return;
                selectedSubcategory = sub;
                selectedDish = { name: sub, price_override: null };
                openAddModal();
                saveMenuState();
                return; 
              }

              selectedSubcategory = sub; selectedDish = null;
              POS.menuPaging['dishes:'+selectedCategory+':'+sub] = 0;
              renderMenu(); saveMenuState();
            }
          });
        });

        // No-scroll paging with FULL height usage
        const key = 'subs:' + selectedCategory;

        // Base (≈1.3×)
        let minW = 140, rowH = 78;
        
        // If it's a huge list or category name matches "Minuman", shrink a bit
        const manySubs = buttons.length > 40 || /minuman/i.test(selectedCategory || '');
        if (manySubs) { minW = 116; rowH = 60; }
        
        renderPaged(grid, buttons, key, { minW, rowH, hardMaxRows: 30 });
        
        return
      }

      // ===== LEVEL 2: Dishes =====
      const item = subDict[selectedSubcategory] || {};
      const itemAvailable = (item?.available !== false);
      const dishes = (item?.dishes || []).map(normDish);

      grid.classList.add('is-dishes');

      if (!dishes.length){
        renderWrap(grid, []);
        return;
      }

      const buttons = dishes.map(d => makeBtn(d.name, {
        crossed: (!itemAvailable || d.available === false),
        onClick: () => {
          selectedDish = { name: d.name, price_override: d.price_override ?? null };
          openAddModal(); saveMenuState();
        }
      }));

      const key  = 'dishes:'+selectedCategory+':'+selectedSubcategory;

      // DISH tiles — bigger by default (≈1.3×),
      // tighten if "Minuman" or very large lists.
      let dMinW = 140, dRowH = 78;                // baseline 1.3×
      const count = buttons.length;
      const isMinuman = /minuman/i.test(selectedCategory || '');
      if (count > 40 || isMinuman) { dMinW = 116; dRowH = 60; }  // tighter
      if (count > 80)              { dMinW = 104; dRowH = 52; }  // safety for massive lists

      renderPaged(grid, buttons, key, { minW: dMinW, rowH: dRowH, hardMaxRows: 32 });
      return;
    } catch (err) {
      try { console.error('renderMenu error', err); } catch(e){}
      const grid = document.getElementById('menu-grid');
      if (grid) {
        grid.classList.remove('is-cats','is-subs','is-dishes','paged');
        grid.style.display = '';
        grid.innerHTML = '<div style="padding:12px;color:#900;background:#fff4f4;border:1px solid #f5caca;">Gagal render menu — lihat console untuk detail: ' + (err && err.message ? err.message : String(err)) + '</div>';
      }
      return;
    }
  }

  async function addToOrder(){
    const confirmBtn = $('#add-confirm');
    return withBusy(confirmBtn, 'Mengirim...', async () => {
      const qtyEl = $('#qty');
      const qty = Number(qtyEl?.value || 1);
      if (!Number.isFinite(qty) || ((qty*10)%5)!==0 || qty<=0){
        notify('Qty harus kelipatan 0.5 dan > 0', 'warn', 2400); return;
      }

      let open_cat = null;
      let openName = null;
      if (selectedDish?.open){
        openName = (document.getElementById('add-open-name')?.value || '').trim();
        const openPriceRaw = (document.getElementById('add-open-price')?.value || '').trim();
        const pressed = document.querySelector('#add-open-type-switch .type-switch-btn[aria-pressed="true"]');
        const openType = pressed ? (pressed.dataset.type || 'kitchen') : 'kitchen';
        if (!openName){ notify('Nama item harus diisi', 'warn', 2400); return; }
        const parsedPrice = Number(openPriceRaw || 0);
        selectedDish.name = openName;
        selectedDish.price_override = isFinite(parsedPrice) ? parsedPrice : 0;
        ADD_MOD_STATE.station = openType === 'bar' ? 'bar' : 'kitchen';
        open_cat = (openType === 'bar') ? 'minuman' : 'makanan';
      }

      if (!selectedDish || (!selectedDish.open && !selectedCategory)){
        notify('Lengkapi pemilihan menu terlebih dahulu', 'warn', 2400); return;
      }

      let itemData = {};
      if (selectedCategory) {
        const cat = menu[selectedCategory] || {};
        if (selectedSubcategory && cat[selectedSubcategory]) {
          itemData = cat[selectedSubcategory];
        } else if (selectedDish?.name && cat[selectedDish.name]) {
          itemData = cat[selectedDish.name];
        }
      }

      const basePrice = Number(
        itemData.price ??
        itemData.price_per_kg ??
        itemData.price_per_unit ??
        itemData.price_per_piece ??
        0
      );
      const price = Number(
        selectedDish && selectedDish.price_override != null
          ? selectedDish.price_override
          : basePrice
      );

      const note = (function(){
        const tokens = (function(){
          const chipSel = [...(document.querySelectorAll("#add-modifier-chips .chip-btn.active") || [])]
            .map(b => (b.textContent || "").trim())
            .filter(Boolean);
          const customRaw = (document.querySelector("#add-note-custom")?.value || "").trim();
          const customTokens = customRaw ? customRaw.split(/[;,|•/]+/).map(s => s.trim()).filter(Boolean) : [];
          const seen = new Set();
          return [...chipSel, ...customTokens].filter(m => {
            const k = m.toLowerCase();
            if (seen.has(k)) return false;
            seen.add(k);
            return true;
          });
        })();
        return tokens.join(" • ");
      })();

      const item_name_val = (selectedDish?.open && openName) ? openName : selectedDish.name;
      const item = { item_name: item_name_val, qty: Number(qty), price: Number(price), sauce: null, note };
      let splitActive = false;
      let activeGroup = "";
      try {
        splitActive = Array.isArray(window.SPLIT_LABELS) && window.SPLIT_LABELS.length > 0;
        if (splitActive) {
          activeGroup = (
            (typeof window.getActiveBillGroup === "function" && window.getActiveBillGroup())
            || window.ACTIVE_BILL_GROUP
            || window.CURRENT_GROUP
          ) || "";
          const g = String(activeGroup || "").trim();
          if (g && !/^all$/i.test(g) && g.toLowerCase() !== "main") {
            item.bill_group = g;
          }
        }
      } catch (_) {}
      if (open_cat) {
        item.cat = open_cat;
        item.category = open_cat;
      }
      const sessionId = document.body.dataset.sessionId;
      const tableNumber = document.body.dataset.tableNumber;

      try{
        saveMenuState();
        const res = await fetch('/add_order', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ session_id: sessionId, table_number: tableNumber, items:[item] })
        });
        let j=null; try{ j=await res.json(); }catch{}
        if(!res.ok || !j || j.status!=='success'){ notify((j&&j.message)||'Gagal tambah pesanan', 'error', 3200); return; }

        closeAddModal();
        if (splitActive) {
          const g = String(activeGroup || "").trim();
          if (g) {
            try { localStorage.setItem('table_group_key', g); } catch (_) {}
          }
        }
        try { POS.requestSessionState({ forceAll: !splitActive }); } catch (_) {}

        selectedDish = null;

        const subData = selectedCategory ? (menu[selectedCategory] || {}) : {};
        const subInfo = selectedSubcategory ? subData[selectedSubcategory] : null;
        const hasDishes = !!(subInfo && Array.isArray(subInfo.dishes) && subInfo.dishes.length > 0);
        if (selectedSubcategory && !hasDishes) {
          selectedSubcategory = null;
        }

        renderMenu();

        const qtyInput = $('#qty');
        if (qtyInput){
          qtyInput.value = '1';
          qtyInput.dispatchEvent(new Event('input', { bubbles: true }));
          syncQtyPresetHighlight();
        }
        clearModifierSelections();
        saveMenuState();
        notify('Pesanan ditambahkan.', 'success', 1500);
      }catch(err){
        notify('Network error: ' + (err?.message || err), 'error', 3200);
      }
    });
  }
  window.addToOrder = addToOrder;


  // ===== boot & resize =====
  document.addEventListener('DOMContentLoaded', async () => {
    try{
      const res = await fetch('/menu.json?v=' + Date.now());
      if (!res.ok) throw new Error('menu.json HTTP ' + res.status);
      menu = await res.json();
    }catch(e){ console.error('Failed to load menu.json:', e); menu = {}; }

    document.querySelectorAll('.back-button').forEach(btn => btn.addEventListener('click', clearMenuState));

    if (!restoreMenuStateIfAny()) renderMenu();

    let t=null;
    window.addEventListener('resize', ()=>{ clearTimeout(t); t=setTimeout(()=>renderMenu(), 60); });

    // If fonts load later and change metrics, remeasure once
    document.fonts && document.fonts.ready && document.fonts.ready.then(()=>renderMenu()).catch(()=>{});
  });

  // --- Order list custom scroller (left panel) — AUTO-CREATING VERSION ---
  if (!window.__DISABLE_MENU_SCROLLER__) {
    (function initOrderScroller(){
        let inited = false;

        function queryEls(){
          return {
            wrap:  document.querySelector('.order-table-wrap'),
            left:  document.querySelector('.left-panel'),
            footer:document.querySelector('.order-footer-bar'),
            track: document.getElementById('order-scrollbar'),
            thumb: document.getElementById('order-scrollbar-thumb'),
            bodyEl:document.getElementById('order-body'),
          };
        }

        // NEW: robust footer height & spacer applier
        function getFooter(){
          // prefer .only-actions if you use that class, else any footer bar
          return document.querySelector('.order-footer-bar.only-actions') ||
                document.querySelector('.order-footer-bar');
        }
        function getFooterHeight(){
          const f = getFooter();
          if (!f) return 0;
          const r = f.getBoundingClientRect();
          return Math.round(r.height || f.offsetHeight || 0);
        }
        function applyFooterSpacer(){
          const { wrap } = queryEls();
          if (!wrap) return;
          const h = getFooterHeight();
          // give a small breathing gap above the bar
          wrap.style.setProperty('--order-footer-spacer', (h ? h + 8 : 0) + 'px');
        }

        function start(){
          if (inited) return;
          const { wrap, left, track, thumb, bodyEl } = queryEls();
          if (!wrap || !track || !thumb){           // DOM not ready yet → try again on next frame
            requestAnimationFrame(start);
            return;
          }
          inited = true;

          // 1) Fit the scroll area to viewport between header and footer buttons
          function sizeOrderList(){
            const { wrap }   = queryEls();
            if (!wrap) return;

            // If your actions bar is a sibling (overlay/fixed), shrink the wrap height;
            // if it's inside the wrap, we don't subtract (the spacer handles it).
            const footer = getFooter();
            const footerInsideWrap = footer && wrap.contains(footer);
            const footerH = getFooterHeight();

            const SAFE_GAP = 10;
            const top = wrap.getBoundingClientRect().top;

            const subtract = (!footerInsideWrap ? footerH : 0);
            const h = Math.max(180, Math.floor(window.innerHeight - top - subtract - SAFE_GAP));
            wrap.style.height = h + 'px';
            wrap.style.maxHeight = h + 'px';

            // Always apply spacer so tfoot can scroll above the bar
            applyFooterSpacer();

            // reflow, then recompute custom scrollbar metrics
            requestAnimationFrame(updateScrollbar);
          }

          // 2) Custom scrollbar syncing
          let hideTimer = null;
          function showTrackActive(){
            track.classList.add('active');
            if (hideTimer) clearTimeout(hideTimer);
            hideTimer = setTimeout(() => track.classList.remove('active'), 600);
          }

          function updateScrollbar(){
            const { wrap, track, thumb } = queryEls();
            if (!wrap || !track || !thumb) return;

            // Native truth: does this element actually have overflow?
            const scrollRange = Math.max(0, wrap.scrollHeight - wrap.clientHeight);
            const need = scrollRange > 2;               // small epsilon avoids flicker
            track.classList.toggle('hidden', !need);
            track.style.pointerEvents = need ? 'auto' : 'none';
            if (!need) return;

            // Thumb size = visible/total proportion
            const trackH = track.getBoundingClientRect().height || wrap.clientHeight;
            // Bigger thumb so it's easy to grab
            const th     = Math.min(trackH - 12, Math.max(96, Math.round(trackH * 0.22)));

            // Map scrollTop to thumb Y
            const maxTop = Math.max(0, trackH - th);
            const ratio  = scrollRange ? (wrap.scrollTop / scrollRange) : 0;
            const top    = Math.round(ratio * maxTop);

            thumb.style.height    = th + 'px';
            thumb.style.transform = `translateY(${top}px)`;
          }

          wrap.addEventListener('scroll', () => { updateScrollbar(); showTrackActive(); });

          // Dragging the thumb
          let dragging = false, startY = 0, startTop = 0, lastPointerId = null;
          const getThumbTop = () => {
            const m = /translateY\((\d+)px\)/.exec(thumb.style.transform || '');
            return m ? parseInt(m[1],10) : 0;
          };

          thumb.addEventListener('pointerdown', (e) => {
            dragging = true;
            lastPointerId = e.pointerId;
            startY  = e.clientY;
            startTop= getThumbTop();
            thumb.setPointerCapture(lastPointerId);
            showTrackActive();
            e.preventDefault();
          });

          thumb.addEventListener('pointermove', (e) => {
            if (!dragging) return;
            const { wrap, track } = queryEls();
            const trackH  = track.getBoundingClientRect().height || wrap.clientHeight;
            const th      = thumb.offsetHeight;
            const maxTop  = Math.max(0, trackH - th);
            const newTop  = Math.max(0, Math.min(maxTop, startTop + (e.clientY - startY)));
            const range   = Math.max(1, wrap.scrollHeight - wrap.clientHeight);
            wrap.scrollTop = Math.round((newTop / maxTop) * range);
          });

          function endDrag(){
            if (!dragging) return;
            dragging = false;
            if (lastPointerId != null) { try { thumb.releasePointerCapture(lastPointerId); } catch {} }
            lastPointerId = null;
          }
          thumb.addEventListener('pointerup', endDrag);
          thumb.addEventListener('pointercancel', endDrag);
          thumb.addEventListener('lostpointercapture', endDrag);

          // Click track to page up/down
          track.addEventListener('pointerdown', (e) => {
            if (e.target === thumb) return;
            const rect = track.getBoundingClientRect();
            const clickY = e.clientY - rect.top;
            const page = Math.max(1, wrap.clientHeight - 60);
            wrap.scrollTop += (clickY < thumb.offsetTop ? -page : page);
            showTrackActive();
          });

          // Recompute when layout changes
          const ro = new ResizeObserver(() => { sizeOrderList(); });
          ro.observe(document.body);
          if (left) ro.observe(left);

          // Also watch the footer size / visibility changes
          const footer = getFooter();
          if (footer) {
            ro.observe(footer);
            // Changes in class/inline style?
            new MutationObserver(() => { applyFooterSpacer(); updateScrollbar(); })
              .observe(footer, { attributes: true, attributeFilter: ['class','style'] });
          }

          // If your rows change, keep the thumb in sync
          if (bodyEl){
            new MutationObserver(() => updateScrollbar())
              .observe(bodyEl, { childList: true, subtree: true });
          }

          // Hook into your existing refresh so it resizes after data loads
          window.POS = window.POS || {};
          const oldReq = window.POS.requestSessionState || (async function() {});
          window.POS.requestSessionState = async function(opts){
            const out = await oldReq(opts);
            sizeOrderList();
            return out;
          };

          // First paint
          sizeOrderList();
          updateScrollbar();
        }

        if (document.readyState === 'loading'){
          document.addEventListener('DOMContentLoaded', start, { once:true });
        } else {
          start();
        }
        window.addEventListener('load', start, { once:true });
      })();

  }
})();
