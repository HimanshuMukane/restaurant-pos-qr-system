// edit.js (drop-in)
(() => {
  // ------------------------------------------------------------
  // State
  // ------------------------------------------------------------
  const CURRENT_EDIT = {
    ids: [],
    name: "",
    station: "kitchen",
    prevQty: 0,
    wasPrinted: false,
    existingMods: []
  };

  // ------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------
  const qs  = (sel, root = document) => root.querySelector(sel);
  const qsa = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const POS = (window.POS = window.POS || {});
  const isDemoMode = () =>
    typeof POS.isDemoMode === "function" ? POS.isDemoMode() : window.POS_DEMO_MODE === true;
  const notify = (message, type = "info", duration = 2400) => {
    if (POS && typeof POS.notify === "function") {
      POS.notify(message, type, duration);
      return;
    }
    if (POS && typeof POS.toast === "function") {
      POS.toast(message, { type, duration });
      return;
    }
    alert(String(message || ""));
  };
  const showDemoPrintModal = (config) => {
    if (POS && typeof POS.showDemoPrintModal === "function") {
      POS.showDemoPrintModal(config);
      return;
    }
    notify("Print preview staged locally.", "info", 2200);
  };
  const withBusy = async (btn, text, fn) => {
    if (POS && typeof POS.withButtonBusy === "function") {
      return POS.withButtonBusy(btn, text, fn);
    }
    return Promise.resolve(fn());
  };
  const softRefresh = async () => {
    if (POS && typeof POS.softSessionRefresh === "function") {
      return POS.softSessionRefresh();
    }
    if (POS && typeof POS.requestSessionState === "function") {
      try {
        await POS.requestSessionState({ forceAll: true });
        return true;
      } catch (_) {}
    }
    return false;
  };

  function parseQtyText(s) {
    if (!s) return 0;
    const num = Number(String(s).trim().replace(",", "."));
    return Number.isFinite(num) ? num : 0;
  }

  async function fetchJSON(url, opts = {}) {
    const res  = await fetch(url, {
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      ...opts
    });
    const text = await res.text();
    let data;
    try { data = JSON.parse(text); }
    catch { throw new Error(`Non-JSON response (${res.status})`); }
    if (!res.ok && data?.message) throw new Error(data.message);
    return data;
  }

  function notifyVoidIssue(msg) {
    notify(msg, "warn", 4200);
  }

  function fireVoidPrint(sid, name, reducedBy, noteForVoid) {
    if (!sid || !reducedBy) return;
    if (isDemoMode()) {
      (async () => {
        try {
          const r = await fetch(`/print/kitchen/void/${encodeURIComponent(sid)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            body: JSON.stringify({ lines: [{ name, qty: reducedBy, note: noteForVoid }] })
          });
          const jv = await r.json().catch(() => null);
          if (!r.ok || !jv || (jv.status !== "success" && jv.status !== "partial_success")) {
            notifyVoidIssue(jv?.message || `Void print failed (HTTP ${r.status})`);
            return;
          }
          showDemoPrintModal({
            title: "Void printed (demo)",
            url: `/print/kitchen/void_preview/${encodeURIComponent(sid)}?` +
              new URLSearchParams({ name, qty: String(reducedBy), note: noteForVoid || '', t: Date.now(), client_print: '1' }).toString(),
          });
        } catch (e) {
          notifyVoidIssue("Network error: " + (e?.message || e));
        }
      })();
      return;
    }
    try {
      previewVoidLocally(sid, name, reducedBy, noteForVoid).catch(() => {});
    } catch (_) {}

    (async () => {
      try {
        const r = await fetch(`/print/kitchen/void/${encodeURIComponent(sid)}`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ lines: [{ name, qty: reducedBy, note: noteForVoid }] })
        });
        const jv = await r.json().catch(() => null);
        if (!r.ok || !jv || (jv.status !== "success" && jv.status !== "partial_success")) {
          if (jv?.errors?.length) notifyVoidIssue("Void print issue:\n" + jv.errors.join("\n"));
          else notifyVoidIssue(jv?.message || `Void print failed (HTTP ${r.status})`);
          return;
        }
        if (jv.status === "partial_success" && jv.errors?.length) {
          notifyVoidIssue("Sebagian void gagal dicetak:\n" + jv.errors.join("\n"));
        }
      } catch (e) {
        notifyVoidIssue("Network error: " + (e?.message || e));
      }
    })();
  }

  // Light-weight name heuristics to decide bar vs kitchen when row has no station
  const KNOWN_DRINK_NAMES = new Set([
    "teh tawar","soda","es teh tawar","teh manis","es teh manis","teh botol","mineral water biasa","mineral water dingin",
    "air putih hangat","air putih biasa","air putih es","jeruk hangat","jeruk murni","es jeruk","nipis hangat","es jeruk nipis",
    "kelapa muda","kelapa jeruk","kelapa kopyor","kelapa kopyor jeruk","kelapa susu","kopyor kerok","es buah campur",
    "es cendol durian","es cendol tanpa durian","es kacang merah","es lemon tea","coca cola","fanta","sprite","kopi","kopi susu",
    "lychee tea es","lemon squash","lemon tea hangat","orange juice","orange juice spesial","susu coklat es","susu coklat hangat",
    "susu putih es","susu putih hangat","timun serut","juice alpukat","juice belimbing","juice jambu","juice mangga","juice melon",
    "juice mix","juice nanas","juice pepaya","juice semangka","juice sirsak","juice strawberry","juice timun","juice tomat",
    "jahe sereh hangat","buah campur potong","juice buah naga","juice wortel","es batu","aqua 600ml","aqua 330ml",
    "es teh manis pitcher","es teh tawar pitcher","teh tawar pitcher","teh manis pitcher","soda gembira","fruit tea","es durian",
    "salad buah","jahe susu","puding mangga","puding strawberry","puding melon","puding coklat","jus durian"
  ]);

  function inferStationFromName(name) {
    const s = (name || "").toLowerCase().trim();
    if (!s) return "kitchen";
    if (KNOWN_DRINK_NAMES.has(s)) return "bar";

    // broader keyword sweep for drinks/desserts
    if (/(teh|kopi|latte|americano|kopypr|espresso|capuccino|matcha|thai ?tea|milk|susu|coklat|cokelat|milo|chocolate|es |es\b|jus|juice|sirup|lemon|lychee|squash|jahe|bandrek|wedang|soda|sparkling|mocktail|cocktail|beer|bir|wine|spritzer|aqua|air( putih| mineral)?|kelapa|kopyor|puding|cendol|kacang|durian|salad)/.test(s)) {
      return "bar";
    }
    return "kitchen";
  }
  

  // ------------------------------------------------------------
  // Modifier presets
  // ------------------------------------------------------------
  const PRESET_NOTES = {
    bar: [
      "Ekstra Es",
      "Gula Pisah",
      "Gula Sedikit",
      "Di Gelas",
      "Pakai Es",
      "Panas",
      "Sedikit Es",
      "Tanpa Gula",
      "Tanpa Susu",
      "Es Gula Dikit",
      "Es Gula Pisah",
      "Tanpa Es",
      "Biasa",
      "Hangat",
      "Gula Merah",
      "Es Pisah",
      "Murni"
    ],

    kitchen: [
      "Pedas",
      "Dibatok",
      "1 Ekor",
      "2 Ekor",
      "3 Ekor",
      "4 Ekor",
      "Kuah Banyak",
      "Tanpa Terasi",
      "1/2 Porsi",
      "1 Porsi",
      "2 Porsi",
      "3 Porsi",
      "4 Porsi",
      "Tanpa Cabe",
      "Tidak Pedas",
      "Cabe Dikit",
      "Piring",
      "Tambahan",
      "Kuah Pisah",
      "Rebus",
      "Saus Padang",
      "Saus Tiram",
      "Lada Hitam",
      "Tauco",
      "Jadi 2 Piring",
      "Tanpa Kepala",
      "Tanpa Tauco",
      "Kupas Tanpa Micin",
      "Bungkus",
      "Murni",
      "Spesial",
      "Wes Mileh",
      "Kecil",
      "Besar",
      "Wes Metu",
      "Bumbu Tebel",
      "Kepitingnya Campur",
      "Asem Manis",
      "Nyisain",
      "Kipas",
      "Bakar Rica",
      "Masak",
      "Steam",
      "Nunggu Orangnya",
    ],

    default: []
  };


  // ------------------------------------------------------------
  // Qty presets inside edit modal
  // ------------------------------------------------------------
  function ensureEditQtyPresets() {
    const host = qs("#edit-qty-presets");
    if (!host) return;
    if (host.__inited) return;
    host.__inited = true;

    for (let i = 0; i <= 10; i++) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "qty-btn";
      b.textContent = String(i);
      b.dataset.q = String(i);
      b.addEventListener("click", () => {
        const input = qs("#edit-qty");
        if (!input) return;
        input.value = String(i);
        input.dispatchEvent(new Event("input", { bubbles: true }));
      });
      host.appendChild(b);
    }
  }

  // ------------------------------------------------------------
  // Selected modifiers chips (removable)
  // ------------------------------------------------------------
  function getSelectedModifiers() {
    const chipSel = qsa("#modifier-chips .chip-btn.active")
      .map(b => (b.textContent || "").trim())
      .filter(Boolean);

    const customRaw = (qs("#edit-note-custom")?.value || "").trim();
    const customTokens = customRaw
      ? customRaw.split(/[;,|•/]+/).map(s => s.trim()).filter(Boolean)
      : [];

    const seen = new Set();
    return [...chipSel, ...customTokens].filter(m => {
      const k = m.toLowerCase();
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  }

  async function previewVoidLocally(sessionId, name, qty, note) {
    const url = `/print/kitchen/void_preview/${encodeURIComponent(sessionId)}?` +
      new URLSearchParams({ name, qty: String(qty), note, t: Date.now(), client_print: "1" }).toString();
    const hexUrl = `/api/print/void_hex/${encodeURIComponent(sessionId)}?` +
      new URLSearchParams({ name, qty: String(qty), note }).toString();
    try {
      if (window.printBridgeHex) {
        const ok = await window.printBridgeHex(hexUrl);
        if (!ok && window.printClient) {
          await window.printClient(url);
        }
      } else if (window.printClient) {
        await window.printClient(url);
      }
      // give the preview a brief head-start to fetch HTML before server print
      await new Promise(r => setTimeout(r, 300));
    } catch (_) {
      if (window.printClient) {
        await window.printClient(url);
      }
    }
  }
  

  function removeModifierToken(token) {
    // If it's a preset chip, toggle it off
    const btn = qsa("#modifier-chips .chip-btn").find(b => (b.textContent||"").trim().toLowerCase() === token.toLowerCase());
    if (btn && btn.classList.contains("active")) {
      btn.classList.remove("active");
      btn.setAttribute("aria-pressed","false");
    } else {
      // Otherwise remove from custom input tokens
      const inp = qs("#edit-note-custom");
      if (inp) {
        const parts = (inp.value || "").split(/[;,|•/]+/).map(s => s.trim()).filter(Boolean);
        inp.value = parts.filter(p => p.toLowerCase() !== token.toLowerCase()).join(", ");
      }
    }
    renderSelectedMods();
  }

  function renderSelectedMods() {
    const zone = qs("#selected-mods");
    if (!zone) return;
    const tokens = getSelectedModifiers();
    zone.innerHTML = "";
    tokens.forEach(tok => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.textContent = tok + " ×";
      b.addEventListener("click", () => removeModifierToken(tok));
      zone.appendChild(b);
    });
  }

  function normalizeTokens(arr){
    return (arr || []).map(s => s.toLowerCase().trim()).filter(Boolean).sort();
  }
  function sameTokens(a, b){
    const A = normalizeTokens(a), B = normalizeTokens(b);
    if (A.length !== B.length) return false;
    for (let i = 0; i < A.length; i++) if (A[i] !== B[i]) return false;
    return true;
  }

  
  // ------------------------------------------------------------
  // Modifier chips
  // ------------------------------------------------------------
  function renderModifierChips() {
    const zone = qs("#modifier-chips");
    if (!zone) return;

    const presets = PRESET_NOTES[CURRENT_EDIT.station] || PRESET_NOTES.default;
    const selectedLower = new Set(CURRENT_EDIT.existingMods.map(s => s.toLowerCase()));

    zone.innerHTML = "";
    presets.forEach(txt => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip-btn";
      b.textContent = txt;
      const active = selectedLower.has(txt.toLowerCase());
      if (active) b.classList.add("active");
      b.setAttribute("aria-pressed", active ? "true" : "false");
      b.addEventListener("click", () => {
        const now = b.classList.toggle("active");
        b.setAttribute("aria-pressed", now ? "true" : "false");
        renderSelectedMods();
      });
      zone.appendChild(b);
    });

    // Put non-preset existing tokens into the custom input
    const leftovers = CURRENT_EDIT.existingMods.filter(m =>
      !presets.some(p => p.toLowerCase() === m.toLowerCase())
    );
    const custom = qs("#edit-note-custom");
    if (custom) {
      custom.value = leftovers.join(", ");
      custom.removeEventListener?.("input", renderSelectedMods);
      custom.addEventListener("input", renderSelectedMods);
    }

    renderSelectedMods();
  }

  // ------------------------------------------------------------
  // Modal open/close
  // ------------------------------------------------------------
  
  function inferStationFromRow(tr, fallbackName) {
    const stationData = (tr?.dataset?.station || '').trim().toLowerCase();
    if (stationData) return stationData;

    // Try category hints
    let catsRaw = tr?.dataset?.cats || tr?.dataset?.category || tr?.dataset?.categories || tr?.dataset?.categoryPath || '';
    try {
      const maybeArr = JSON.parse(catsRaw);
      if (Array.isArray(maybeArr)) catsRaw = maybeArr.join(' > ');
    } catch (_) { /* not JSON, ignore */ }
    if (typeof catsRaw === 'string' && /minum/.test(catsRaw.toLowerCase())) return 'bar';

    // fallback to name heuristic
    return inferStationFromName(fallbackName);
  }

  window.openEditModalFromRow = function openEditModalFromRow(tr) {
    if (!tr) return;

    // ids to edit (combined row may carry multiple row IDs)
    let ids = [];
    try { ids = JSON.parse(tr.dataset.ids || "[]"); } catch (_) { ids = []; }
    if ((!Array.isArray(ids) || !ids.length) && tr.dataset.id) {
      ids = [Number(tr.dataset.id)];
    }
    if (!Array.isArray(ids) || !ids.length) return;

    CURRENT_EDIT.ids       = ids;
    CURRENT_EDIT.name      = tr.dataset.name || (qs("td:first-child", tr)?.childNodes?.[0]?.textContent || "").trim();
    CURRENT_EDIT.prevQty   = parseQtyText(qs("td:nth-child(2)", tr)?.textContent);
    CURRENT_EDIT.wasPrinted = tr.classList.contains("row-print-printed") ||
                              tr.classList.contains("row-print-partial");

    const rawNote = (tr.dataset.note || "").trim();
    CURRENT_EDIT.existingMods = rawNote
      ? rawNote.split(/[;,|•/]+/).map(s => s.trim()).filter(Boolean)
      : [];

    const stationRaw = (tr.dataset.station || "").trim().toLowerCase();
    CURRENT_EDIT.station = inferStationFromRow(tr, CURRENT_EDIT.name);

    // Title
    qs("#edit-title").textContent = `Edit: ${CURRENT_EDIT.name || "Item"}`;

    // Show BOTH panels side-by-side; hide chooser forever
    const chooser = qs("#edit-chooser");
    const qtyP    = qs("#edit-qty-panel");
    const modP    = qs("#edit-mod-panel");
    const body    = qs("#edit-modal .modal-body");
    if (chooser) chooser.style.display = "none";
    if (qtyP) qtyP.style.display = "block";
    if (modP) modP.style.display = "block";
    if (body) {
      body.style.display = "grid";
      body.style.gridTemplateColumns = "1fr 1.35fr";
      body.style.gap = "12px";
    }

    // Ensure qty presets exist in edit panel
    ensureEditQtyPresets();

    // Open modal
    const modal = qs("#edit-modal");
    modal.style.display = "flex";

    // Prepare modifier UI
    renderModifierChips();

   // Pre-fill qty but DO NOT focus (avoid auto-numpad)
    const qtyEl = qs("#edit-qty");
    if (qtyEl) qtyEl.value = String(CURRENT_EDIT.prevQty ?? "");

  };

  async function applyEdits(opts = {}){
    const { skipClose = false, skipRefresh = false } = opts;
    const errQty = qs("#edit-qty-err");
    const errMod = qs("#edit-mod-err");
    if (errQty) errQty.textContent = "";
    if (errMod) errMod.textContent = "";
  
    // --- read qty (optional) ---
    const qtyRaw = (qs("#edit-qty")?.value || "").trim();
    const hasQtyInput = qtyRaw.length > 0;
    let qtyNum = null;
  
    if (hasQtyInput) {
      qtyNum = Number(qtyRaw.replace(",", "."));
      const halfStepOk = Number.isFinite(qtyNum) && qtyNum >= 0 && Math.abs((qtyNum * 10) % 5) < 1e-9;
      if (!halfStepOk) {
        if (errQty) errQty.textContent = "Qty harus 0 atau kelipatan 0.5 (mis. 1, 1.5, 2).";
        return { ok: false };
      }
    }
  
    // --- read modifiers (optional) ---
    const newMods = getSelectedModifiers();                    // array of strings
    const oldMods = CURRENT_EDIT.existingMods || [];
    const modsChanged = !sameTokens(oldMods, newMods);
    const note = newMods.join(" • ");
  
    // --- decide what to save ---
    const qtyChanged = hasQtyInput && qtyNum !== CURRENT_EDIT.prevQty;
  
    // If nothing changed, optionally close and return early
    if (!qtyChanged && !modsChanged) {
      if (!skipClose) closeEditModal();
      return { ok: true, changed: false };
    }
  
    try {
      // Save quantity first (so we get void slip info), then notes
      if (qtyChanged) {
        const j = await fetchJSON("/edit_item", {
          method: "POST",
          body: JSON.stringify({ item_ids: CURRENT_EDIT.ids, new_qty: qtyNum })
        });
  
        if (j.status !== "success") {
          errQty && (errQty.textContent = j.message || "Gagal menyimpan jumlah.");
          return { ok: false };
        }
  
        // If this item was printed and quantity reduced, print void slip
        const reducedBy = +(j.void_qty || 0);
        if (CURRENT_EDIT.wasPrinted && reducedBy > 0) {
          const sid = window.SESSION_ID || document.body?.dataset?.sessionId;
          const noteForVoid = (modsChanged ? newMods : CURRENT_EDIT.existingMods).join(" • ");
          fireVoidPrint(sid, CURRENT_EDIT.name, reducedBy, noteForVoid);
        }

        CURRENT_EDIT.prevQty = qtyNum;
      }
  
      if (modsChanged) {
        const j2 = await fetchJSON("/edit_item_note", {
          method: "POST",
          body: JSON.stringify({ item_ids: CURRENT_EDIT.ids, note })
        });
        if (j2.status !== "success") {
          errMod && (errMod.textContent = j2.message || "Gagal menyimpan catatan.");
          return { ok: false };
        }
        CURRENT_EDIT.existingMods = newMods.slice();
      }
  
      if (!skipClose) closeEditModal();
      if (!skipRefresh) {
        await softRefresh();
      }
      return { ok: true, changed: (qtyChanged || modsChanged) };
    } catch (e) {
      // generic network fallback
      const msg = e?.message || "Network error.";
      if (qtyChanged && errQty) errQty.textContent = msg;
      else if (modsChanged && errMod) errMod.textContent = msg;
      return { ok: false };
    }
  }

  window.submitEditAll = async function submitEditAll(){
    return withBusy(qs("#edit-save-all"), "Menyimpan...", () => applyEdits());
  };

  window.sendCurrentItemToKitchen = async function sendCurrentItemToKitchen(){
    const btn = qs("#edit-send-kitchen");
    const originalLabel = btn ? btn.textContent : null;
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Mengirim...";
    }

    // Save any edits silently, keep modal open for the send flow
    const saved = await applyEdits({ skipClose: true, skipRefresh: true });
    if (!saved?.ok) {
      if (btn) {
        btn.disabled = false;
        btn.textContent = originalLabel || "Dapur";
      }
      return;
    }

    const ids = Array.isArray(CURRENT_EDIT.ids) ? CURRENT_EDIT.ids : [];
    if (!ids.length) {
      notify("Tidak ada item yang dipilih.", "warn", 2600);
      if (btn) {
        btn.disabled = false;
        btn.textContent = originalLabel || "Dapur";
      }
      return;
    }

    const sid = window.SESSION_ID || document.body?.dataset?.sessionId;
    if (!sid) {
      notify("Session tidak ditemukan.", "error", 3200);
      if (btn) {
        btn.disabled = false;
        btn.textContent = originalLabel || "Dapur";
      }
      return;
    }

    // Peek: ensure there is something to print
    try {
      const peek = await fetch(`/print/kitchen/send_item/${encodeURIComponent(sid)}?dryrun=1`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ item_ids: ids })
      });
      let jPeek = null;
      try { jPeek = await peek.json(); } catch (_) {}
      if (!peek.ok) {
        notify((jPeek && jPeek.message) || `HTTP ${peek.status}`, "error", 3600);
        if (btn) { btn.disabled = false; btn.textContent = originalLabel || "Dapur"; }
        return;
      }
      if (!jPeek || jPeek.status !== "ok" || !jPeek.has_printables) {
        notify("Tidak ada item baru/edited untuk dicetak.", "warn", 2400);
        if (btn) { btn.disabled = false; btn.textContent = originalLabel || "Dapur"; }
        return;
      }
    } catch (e) {
      notify("Network error: " + (e?.message || e), "error", 3600);
      if (btn) { btn.disabled = false; btn.textContent = originalLabel || "Dapur"; }
      return;
    }

    if (isDemoMode()) {
      try {
        const demoRes = await fetch(`/print/kitchen/send_item/${encodeURIComponent(sid)}`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ item_ids: ids })
        });
        const demoJson = await demoRes.json().catch(() => null);
        const okStatus = demoJson && (
          demoJson.status === "success" ||
          demoJson.status === "partial_success" ||
          demoJson.status === "nothing_to_print"
        );
        if (!demoRes.ok || !okStatus) {
          notify((demoJson && demoJson.message) || "Gagal mengirim ke dapur.", "error", 3600);
          if (btn) {
            btn.disabled = false;
            btn.textContent = originalLabel || "Dapur";
          }
          return;
        }
        if (demoJson.status === "nothing_to_print") {
          notify(demoJson.message || "Tidak ada item baru untuk dikirim.", "warn", 2400);
        } else {
          const stationItems = (demoJson.station_items && typeof demoJson.station_items === "object")
            ? demoJson.station_items
            : {};
          const stEntries = Object.entries(stationItems).filter(([, ids]) => ids.length > 0);
          const stLabels = stEntries.length
            ? stEntries.map(([s]) => s.charAt(0).toUpperCase() + s.slice(1))
            : ["Kitchen"];
          const previewUrls = stEntries.length
            ? stEntries.map(([, ids]) =>
                `/print/kitchen/preview/${encodeURIComponent(sid)}?ids=${ids.join(",")}&client_print=1`
              )
            : [`/print/kitchen/preview/${encodeURIComponent(sid)}?client_print=1`];
          showDemoPrintModal({
            title: `Kitchen printed (demo) — ${stLabels.join(", ")}`,
            url: previewUrls[0],
            previewUrls,
            actions: stLabels,
          });
        }
        await softRefresh();
        closeEditModal();
        if (btn) {
          btn.disabled = false;
          btn.textContent = originalLabel || "Dapur";
        }
        return;
      } catch (e) {
        notify("Network error: " + (e?.message || e), "error", 3600);
        if (btn) {
          btn.disabled = false;
          btn.textContent = originalLabel || "Dapur";
        }
        return;
      }
    }

    // Local preview to the POS-connected printer (subset of items)
    let previewDone = Promise.resolve();
    const url = new URL(`/print/kitchen/preview/${encodeURIComponent(sid)}`, location.origin);
    url.searchParams.set("ids", ids.join(","));
    url.searchParams.set("t", Date.now());
    url.searchParams.set("silent", "1");
    url.searchParams.set("client_print", "1");
    const hexUrl = `/api/print/kitchen_hex/${encodeURIComponent(sid)}?ids=${encodeURIComponent(ids.join(","))}`;
    try {
      if (window.printBridgeHex) {
        const ok = await window.printBridgeHex(hexUrl);
        if (!ok && window.printClient) {
          previewDone = window.printClient(url.toString());
        }
      } else if (window.printClient) {
        previewDone = window.printClient(url.toString());
      }
      await new Promise(r => setTimeout(r, 300));
    } catch (_) {
      if (window.printClient) {
        previewDone = window.printClient(url.toString());
      } else {
        previewDone = Promise.resolve();
      }
    }

    try {
      const res = await fetch(`/print/kitchen/send_item/${encodeURIComponent(sid)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ item_ids: ids })
      });
      const j = await res.json().catch(() => null);
      if (!res.ok || !j || (j.status !== "success" && j.status !== "partial_success" && j.status !== "nothing_to_print")) {
        notify((j && j.message) || "Gagal mengirim ke dapur.", "error", 3600);
        if (btn) {
          btn.disabled = false;
          btn.textContent = originalLabel || "Dapur";
        }
        return;
      }

      if (j.status === "nothing_to_print") {
        notify(j.message || "Tidak ada item baru untuk dikirim.", "warn", 2400);
      }
      if (j.errors && j.errors.length) {
        notify("Sebagian gagal dicetak:\n" + j.errors.join("\n"), "warn", 4200);
      }
    } catch (e) {
      notify("Network error: " + (e?.message || e), "error", 3600);
      if (btn) {
        btn.disabled = false;
        btn.textContent = originalLabel || "Dapur";
      }
      return;
    }

    await softRefresh();
    notify("Item terkirim ke dapur.", "success", 1600);
    closeEditModal();
    Promise.resolve(previewDone).catch(() => {});
    if (btn) {
      btn.disabled = false;
      btn.textContent = originalLabel || "Dapur";
    }
  };
  

  window.closeEditModal = function closeEditModal() {
    const m = qs("#edit-modal");
    if (m) m.style.display = "none";
    const e1 = qs("#edit-qty-err");     if (e1) e1.textContent = "";
    const e2 = qs("#edit-mod-err");     if (e2) e2.textContent = "";
    const q  = qs("#edit-qty");         if (q)  q.value = "";
    // Don't clear selected-mods UI—it will re-render on next open anyway
  };

  // ------------------------------------------------------------
  // Submit handlers
  // ------------------------------------------------------------
  window.submitEditQty = async function submitEditQty() {
    const out = qs("#edit-qty-err");
    if (out) out.textContent = "";

    const raw = (qs("#edit-qty")?.value || "").trim();
    if (!raw.length) { out && (out.textContent = "Isikan jumlah."); return; }

    const num = Number(raw.replace(",", "."));
    const halfStepOk = Number.isFinite(num) && num >= 0 && Math.abs((num * 10) % 5) < 1e-9;
    if (!halfStepOk) { out && (out.textContent = "Qty harus 0 atau kelipatan 0.5 (mis. 1, 1.5, 2)."); return; }

    try {
      const j = await fetchJSON("/edit_item", {
        method: "POST",
        body: JSON.stringify({ item_ids: CURRENT_EDIT.ids, new_qty: num })
      });

      if (j.status === "success") {
        const reducedBy = +(j.void_qty || 0);
        if (CURRENT_EDIT.wasPrinted && reducedBy > 0) {
          const sid = window.SESSION_ID || document.body?.dataset?.sessionId;
          const liveMods = getSelectedModifiers();
          const noteForVoid = (liveMods.length ? liveMods : CURRENT_EDIT.existingMods).join(" • ");
          fireVoidPrint(sid, CURRENT_EDIT.name, reducedBy, noteForVoid);
        }
        closeEditModal?.();
        await softRefresh();
        notify("Jumlah diperbarui.", "success", 1500);
      } else {
        out && (out.textContent = j.message || "Gagal menyimpan.");
      }
    } catch (e) {
      out && (out.textContent = e?.message || "Network error.");
    }
  };

  window.confirmCancelItem = async function confirmCancelItem() {
    if (!confirm("Set item ini menjadi 0 (hapus)?")) return;

    return withBusy(qs("#edit-void-item"), "Memvoid...", async () => {
      try {
        const j = await fetchJSON("/edit_item", {
          method: "POST",
          body: JSON.stringify({ item_ids: CURRENT_EDIT.ids, new_qty: 0 })
        });

        if (j.status === "success") {
          const reducedBy = +(j.void_qty || 0);
          if (CURRENT_EDIT.wasPrinted && reducedBy > 0) {
            const sid = window.SESSION_ID || document.body?.dataset?.sessionId;
            const liveMods = getSelectedModifiers();
            const noteForVoid = (liveMods.length ? liveMods : CURRENT_EDIT.existingMods).join(" • ");
            fireVoidPrint(sid, CURRENT_EDIT.name, reducedBy, noteForVoid);
          }
          closeEditModal?.();
          await softRefresh();
          notify("Item dihapus.", "success", 1500);
        } else {
          notify(j.message || "Gagal menghapus.", "error", 3200);
        }
      } catch (e) {
        notify(e?.message || "Network error.", "error", 3200);
      }
    });
  };

  window.submitEditModifier = async function submitEditModifier() {
    const err = qs("#edit-mod-err");
    if (err) err.textContent = "";

    // For now we serialize to text (backward compatible). If you add a JSON column later,
    // you can also POST { modifiers: [...] } to a new route.
    const modifiers = getSelectedModifiers();
    const note = modifiers.join(" • "); // allow empty to clear

    try {
      const j = await fetchJSON("/edit_item_note", {
        method: "POST",
        body: JSON.stringify({ item_ids: CURRENT_EDIT.ids, note })
      });
      if (j.status === "success") {
        closeEditModal?.();
        await softRefresh();
        notify("Catatan diperbarui.", "success", 1500);
      } else {
        err && (err.textContent = j.message || "Gagal menyimpan catatan.");
      }
    } catch (e) {
      err && (err.textContent = e?.message || "Network error.");
    }
  };

  // ------------------------------------------------------------
  // Row click to open modal
  // ------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", () => {
    const tbody = qs(".order-table tbody");
    if (!tbody) return;

    tbody.addEventListener("click", (e) => {
      if (e.target.closest(".col-bill-group .action-button")) return;
      if (e.target.closest(".row-actions")) return;
      const tr = e.target.closest("tr");
      if (!tr || tr.classList.contains("total-row")) return;
      openEditModalFromRow(tr);
    });
  });
})();
