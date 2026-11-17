// static/js/session.js
(() => {
  // ---------- tiny utils ----------
  const $  = (s, r=document) => r.querySelector(s);
  const fmtRp = (n) => `Rp ${parseInt(n||0,10).toLocaleString('id-ID')}`;
  const sanitizeRupiahToInt = (v) => {
    if (v == null) return 0;
    const s = String(v).replace(/[^\d]/g, "");
    return s ? parseInt(s, 10) : 0;
  };
  const show = (el, on=true) => { if (el) el.style.display = on ? "" : "none"; };
  const warmNav = (url) => {
    const href = String(url || '').trim();
    if (!href) return;
    fetch(href, {
      credentials: 'same-origin',
      headers: { 'Accept': 'text/html', 'X-POS-Prefetch': '1' }
    }).catch(() => {});
  };

  function getSessionId() {
    return document.body?.dataset?.sessionId
        || $("#session-card")?.dataset?.sessionId
        || window.SESSION_ID
        || null;
  }

  function isTakeaway(card) {
    return String(card?.dataset?.isTakeaway || "0") === "1";
  }

  // ---------- paint the small session card ----------
  function repaint(meta) {
    const card = $("#session-card");
    if (!card) return;

    const $c = (sel) => card.querySelector(sel);
    const setTextCard = (sel, txt) => { const el = $c(sel); if (el) el.textContent = txt ?? ""; };

    const take = isTakeaway(card);

    const pax        = meta?.pax ?? (parseInt(card.dataset.pax || "1", 10) || 1);
    const guest_name = meta?.guest_name ?? (card.dataset.guest || "");
    const dp_amount  = meta?.dp_amount ?? (parseInt(card.dataset.dp || "0", 10) || 0);
    const note       = meta?.note ?? (card.dataset.note || "");
    const pickup     = meta?.pickup_time ?? (card.dataset.pickup || "");

    // title
    const titleEl = $("#session-title") || $(".session-title");
    if (titleEl) {
      if (take) {
        titleEl.textContent = `Take Away${guest_name ? " – " + guest_name : ""}`;
      } else {
        const tn = document.body?.dataset?.tableNumber || card.dataset.tableNumber || "";
        titleEl.textContent = `Meja ${tn}${guest_name ? " - " + guest_name : ""}`;
      }
    }

    // rows (SCOPED TO CARD)
    show($c("#row-pickup"), take);
    show($c("#row-pax"),    !take);
    show($c("#row-dp"),     !take);

    setTextCard("#info-pax", String(pax));

    if (guest_name?.trim()) { setTextCard("#info-guest", guest_name); show($c("#row-guest"), true); }
    else { setTextCard("#info-guest",""); show($c("#row-guest"), false); }

    if (!take && dp_amount > 0) { setTextCard("#info-dp", fmtRp(dp_amount)); show($c("#row-dp"), true); }
    else if (!take) { setTextCard("#info-dp",""); show($c("#row-dp"), false); }

    if (note?.trim()) { setTextCard("#info-note", note); show($c("#row-note"), true); }
    else { setTextCard("#info-note",""); show($c("#row-note"), false); }

    if (take) {
      if (pickup?.trim()) { setTextCard("#info-pickup", pickup); show($c("#row-pickup"), true); }
      else { setTextCard("#info-pickup",""); show($c("#row-pickup"), false); }
    }
  }

  // ---------- DP method helpers (modal) ----------
  function syncDpMethodRow(modal) {
    if (!modal) return;
    const dpInput   = modal.querySelector("#edit-dp");
    const rowMethod = modal.querySelector("#row-dp-method");
    const hidden    = modal.querySelector("#edit-dp-method");
    const buttons   = modal.querySelectorAll(".dp-method-btn");
    if (!dpInput || !rowMethod) return;

    const val = sanitizeRupiahToInt(dpInput.value);
    if (val > 0) {
      rowMethod.style.display = "";
    } else {
      rowMethod.style.display = "none";
      if (hidden) hidden.value = "";
      buttons.forEach(btn => btn.classList.remove("active"));
    }
  }

  function selectDpMethod(method) {
    const modal = $("#session-edit-modal");
    if (!modal) return;
    const hidden  = modal.querySelector("#edit-dp-method");
    const buttons = modal.querySelectorAll(".dp-method-btn");
    if (!hidden) return;
    hidden.value = method;
    buttons.forEach(btn => {
      btn.classList.toggle("active", btn.dataset.method === method);
    });
  }
  window.selectDpMethod = selectDpMethod;

  // ---------- modal open / close / submit ----------
  function openSessionEdit() {
    const card  = document.querySelector("#session-card");
    const modal = document.querySelector("#session-edit-modal");
    if (!card || !modal) return;

    // 1) Make sure the modal is on top of everything
    if (modal.parentNode !== document.body) document.body.appendChild(modal);
    modal.style.setProperty("z-index", "38000", "important");

    // 2) Scoped query inside the modal (avoids clashing with card rows)
    const $m = (s) => modal.querySelector(s);

    // 3) Takeaway vs dine-in controls
    const take = String(card.dataset.isTakeaway || "0") === "1";
    const rPickup = $m("#row-pickup");
    const rPax    = $m("#row-pax");
    const rDp     = $m("#row-dp");
    if (rPickup) rPickup.style.display = take ? "" : "none";
    if (rPax)    rPax.style.display    = !take ? "" : "none";
    if (rDp)     rDp.style.display     = !take ? "" : "none";

    // 4) Fill inputs from the session card dataset
    const f = {
      pax:    $m("#edit-pax"),
      guest:  $m("#edit-guest"),
      dp:     $m("#edit-dp"),
      note:   $m("#edit-note"),
      pickup: $m("#edit-pickup"),
    };
    if (f.pax)    f.pax.value    = card.dataset.pax || 1;
    if (f.guest)  f.guest.value  = card.dataset.guest || "";
    if (f.dp)     f.dp.value     = card.dataset.dp || "";
    if (f.note)   f.note.value   = card.dataset.note || "";
    if (f.pickup) f.pickup.value = (card.dataset.pickup || "").replace(" ", "T");

    // DP method row + preselect
    const dpMethodInput = $m("#edit-dp-method");
    const dpMethodRow   = $m("#row-dp-method");
    if (dpMethodInput) {
      const existing = card.dataset.dpmethod || window.DP_METHOD || "";
      dpMethodInput.value = existing || "";
      const buttons = modal.querySelectorAll(".dp-method-btn");
      buttons.forEach(btn => {
        btn.classList.toggle("active", btn.dataset.method === existing);
      });
    }
    if (dpMethodRow) {
      // show/hide based on current DP value
      syncDpMethodRow(modal);
    }
    if (f.dp && !f.dp._dpListenerBound) {
      f.dp.addEventListener("input", () => syncDpMethodRow(modal));
      f.dp._dpListenerBound = true;
    }

    const err = $m("#session-edit-err");
    if (err) err.textContent = "";

    // 5) Show modal (display handled via class)
    modal.classList.add("open");
    modal.style.setProperty("display", "flex", "important");

    // 6) Focus a sensible field
    const focusEl = take ? (f.pickup || f.guest) : (f.pax || f.guest);
    if (focusEl && typeof focusEl.focus === "function") {
      focusEl.focus();
    }
  }
  window.openSessionEdit = openSessionEdit;

  window.closeSessionEdit = function() {
    const m = document.querySelector("#session-edit-modal");
    if (!m) return;
    m.classList.remove("open");
    m.style.removeProperty("display");
  };

  window.submitSessionEdit = async function() {
    const card = $("#session-card");
    if (!card) return;

    const sessionId  = getSessionId();
    const take       = isTakeaway(card);

    const pax     = parseInt($("#edit-pax")?.value || "1", 10);
    const guest   = ($("#edit-guest")?.value || "").trim();
    const dpRaw   = $("#edit-dp")?.value || "";
    const note    = ($("#edit-note")?.value || "").trim();
    const pickup  = $("#edit-pickup")?.value || "";
    const dpMethodInput = $("#edit-dp-method");

    const errEl = $("#session-edit-err");
    if (errEl) errEl.textContent = "";

    if (!take && (!Number.isFinite(pax) || pax < 1)) {
      if (errEl) errEl.textContent = "PAX minimal 1.";
      return;
    }

    const dp_amount = take ? null : sanitizeRupiahToInt(dpRaw);
    const dp_method = (!take && dp_amount > 0 && dpMethodInput)
      ? (dpMethodInput.value || "").trim()
      : "";

    if (!take && dp_amount > 0 && !dp_method) {
      if (errEl) errEl.textContent = "Pilih metode DP.";
      return;
    }

    try {
      const res = await fetch(`/session/update/${encodeURIComponent(sessionId)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({
          pax: take ? undefined : pax,
          guest_name: guest,
          dp_amount: dp_amount,
          dp_method: (!take && dp_amount > 0) ? dp_method : null,
          note,
          pickup_time: take ? (pickup || null) : undefined
        })
      });
      const j = await res.json().catch(() => null);
      if (!res.ok || !j || j.status !== "success") {
        if (errEl) errEl.textContent = (j && j.message) || `Gagal menyimpan (HTTP ${res.status}).`;
        return;
      }

      // update dataset for next open
      if (!take) {
        card.dataset.pax      = String(j.data.pax);
        card.dataset.dp       = String(j.data.dp_amount || 0);
        card.dataset.dpmethod = j.data.dp_method || "";
        window.DP_METHOD      = j.data.dp_method || "";
      }
      card.dataset.guest  = j.data.guest_name || "";
      card.dataset.note   = j.data.note || "";
      if (take) {
        card.dataset.pickup = j.data.pickup_time || "";
      }

      repaint(j.data);

      try { await window.POS?.requestSessionState?.({ skipRows: true }); } catch {}

      window.closeSessionEdit();
    } catch (e) {
      if (errEl) errEl.textContent = e?.message || "Network error.";
    }
  };

  // ---------- meta fetching ----------
  let lastSocketTick = 0;
  let pollTimer = null;
  let hookedSocket = false;

  async function fetchMetaOnce() {
    const sid = getSessionId();
    if (!sid) return false;
    if (document.visibilityState === "hidden") return false;
    try {
      const r = await fetch(`/api/session_meta/${encodeURIComponent(sid)}`, {
        headers: { "Accept": "application/json" }
      });
      const j = await r.json().catch(() => null);
      if (j && (j.status === "ok" || j.status === "success") && j.data) {
        // also sync dataset so future opens are correct
        const card = $("#session-card");
        if (card) {
          if (j.data.pax != null)        card.dataset.pax    = String(j.data.pax);
          if (j.data.dp_amount != null)  card.dataset.dp     = String(j.data.dp_amount || 0);
          if (j.data.dp_method != null) {
            card.dataset.dpmethod = j.data.dp_method || "";
            window.DP_METHOD      = j.data.dp_method || "";
          }
          if (j.data.guest_name != null) card.dataset.guest  = j.data.guest_name || "";
          if (j.data.note != null)       card.dataset.note   = j.data.note || "";
          if (j.data.pickup_time != null)card.dataset.pickup = j.data.pickup_time || "";
        }
        repaint(j.data);
        return true;
      }
    } catch (_e) {}
    return false;
  }

  function startPoller() {
    stopPoller();
    if (document.visibilityState === "hidden") return;
    // aggressive until we see a socket tick; then we back off
    pollTimer = setInterval(async () => {
      const now = Date.now();
      if (now - lastSocketTick < 12000) return; // socket recently ticked, skip this cycle
      await fetchMetaOnce();
    }, 7000);
  }
  function stopPoller() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
  }

  // ---------- socket hookup ----------
  function hookSocket(sock) {
    if (!sock || hookedSocket) return;
    hookedSocket = true;

    const bump = () => { lastSocketTick = Date.now(); /* also do a light refresh */ fetchMetaOnce(); };

    // Be liberal with event names — different builds sometimes differ
    const names = [
      'session.state.changed',
      'session.meta.changed',
      'session.changed',
      'session:changed',
      'rows.changed',
      'order.changed',
      'billing.changed',
      'kitchen.changed'
    ];
    names.forEach(n => { try { sock.on(n, (evt) => {
      const sid = getSessionId();
      if (!sid) return;
      if (evt?.session_id && evt.session_id !== sid) return;
      bump();
    }); } catch(_){} });

    // mark first contact
    lastSocketTick = Date.now();
  }

  // If POS.socket appears later, hook it
  function waitForSocket() {
    const POS = (window.POS = window.POS || {});
    if (POS.socket) hookSocket(POS.socket);

    // These custom DOM events are fired by your boot code
    document.addEventListener('pos:socket-ready',     (e) => hookSocket(e.detail?.socket));
    document.addEventListener('pos:socket-connected', (e) => hookSocket(e.detail?.socket));
  }

  // ---------- resilient delegates (open modal by clicking the card) ----------
  function attachCardDelegates() {
    if (attachCardDelegates._done) return;
    attachCardDelegates._done = true;

    document.addEventListener('click', (e) => {
      const card = e.target.closest?.('#session-card');
      if (!card) return;
      e.preventDefault();
      openSessionEdit();
    });

    document.addEventListener('keydown', (e) => {
      const inCard = e.target?.closest?.('#session-card');
      if (!inCard) return;
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openSessionEdit();
      }
    });
  }

  function bindFastBackNavigation() {
    const back = document.querySelector('.back-button[href]');
    if (!back || bindFastBackNavigation._done) return;
    bindFastBackNavigation._done = true;

    const queueWarm = window.requestIdleCallback
      ? () => window.requestIdleCallback(() => warmNav(back.href), { timeout: 1500 })
      : () => window.setTimeout(() => warmNav(back.href), 250);
    queueWarm();

    back.addEventListener('pointerenter', () => warmNav(back.href), { passive: true });
    back.addEventListener('touchstart', () => warmNav(back.href), { passive: true });
    back.addEventListener('click', () => {
      document.body.classList.add('nav-pending');
      back.classList.add('nav-pending');
      back.setAttribute('aria-busy', 'true');
    });
  }

  // ---------- boot ----------
  function boot() {
    attachCardDelegates();
    bindFastBackNavigation();
    waitForSocket();

    // 1) immediate paint from whatever dataset exists (no flicker)
    repaint();

    // 2) start background poller until socket events are observed
    startPoller();

    // 3) refresh when tab becomes visible again
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') {
        fetchMetaOnce();
        startPoller();
      } else {
        stopPoller();
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
