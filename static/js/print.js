(function () {
  let kitchenPrinting = false;
  const POS = (window.POS = window.POS || {});
  const isDemoMode = () =>
    typeof POS.isDemoMode === "function" ? POS.isDemoMode() : window.POS_DEMO_MODE === true;

  function showDemoPrintModal(config) {
    if (typeof POS.showDemoPrintModal === "function") {
      POS.showDemoPrintModal(config);
      return;
    }
    notify("Print preview staged locally.", "info", 2600);
  }

  // ---- tiny UX helpers ----
  function ensureToastHost() {
    let host = document.getElementById("pos-toast-host");
    if (!host) {
      host = document.createElement("div");
      host.id = "pos-toast-host";
      host.className = "pos-toast-host";
      document.body.appendChild(host);
    }
    return host;
  }

  function toast(message, opts) {
    const options = opts || {};
    const type = options.type || "info";
    const duration = Number.isFinite(options.duration) ? options.duration : 2200;
    const host = ensureToastHost();
    const el = document.createElement("div");
    el.className = `pos-toast pos-toast--${type}`;
    el.textContent = String(message || "");
    host.appendChild(el);
    requestAnimationFrame(() => el.classList.add("show"));
    setTimeout(() => {
      el.classList.remove("show");
      setTimeout(() => el.remove(), 220);
    }, duration);
    return el;
  }

  if (!POS.toast) POS.toast = toast;
  if (!POS.notify) POS.notify = notify;
  if (!POS.setButtonBusy) POS.setButtonBusy = setButtonBusy;
  if (!POS.withButtonBusy) POS.withButtonBusy = withButtonBusy;

  function setButtonBusy(btn, busyText) {
    if (!btn) return () => {};
    const prev = {
      text: btn.textContent,
      disabled: btn.disabled,
    };
    btn.disabled = true;
    btn.classList.add("is-busy");
    if (busyText) btn.textContent = busyText;
    return () => {
      btn.disabled = prev.disabled;
      btn.classList.remove("is-busy");
      btn.textContent = prev.text;
    };
  }

  async function withButtonBusy(btn, busyText, fn) {
    if (!btn) return fn();
    if (btn.dataset.busy === "1") return;
    btn.dataset.busy = "1";
    const restore = setButtonBusy(btn, busyText);
    try {
      return await Promise.resolve(fn());
    } finally {
      restore();
      delete btn.dataset.busy;
    }
  }

  function notify(message, type, duration) {
    if (POS.toast) {
      POS.toast(message, { type: type || "info", duration });
    } else {
      alert(message);
    }
  }

  async function softSessionRefresh() {
    if (window.POS && typeof window.POS.requestSessionState === "function") {
      try {
        await window.POS.requestSessionState({ skipRows: false });
        return true;
      } catch (_) {}
    }
    return false;
  }

  if (!POS.softSessionRefresh) POS.softSessionRefresh = softSessionRefresh;
  // ---- tiny helper: print a URL via hidden iframe (works with kiosk-printing) ----
  function printClient(url, opts) {
    const options = opts || {};
    const allowPopup = options.popup && window.ALLOW_PRINT_POPUP === true;
    if (allowPopup) {
      return new Promise((resolve) => {
        const w = window.open(url, "_blank");
        if (!w) return resolve();
  
        let done = false;
        function finish() {
          if (done) return;
          done = true;
          try { w.close(); } catch (_) {}
          resolve();
        }
  
        function onLoad() {
          try {
            if ('onafterprint' in w) {
              w.onafterprint = finish;
            }
            setTimeout(finish, 3000);
  
            try { w.focus(); } catch (_) {}
            if (!(w && w.__POS_AUTOPRINT__ === true)) {
              try { w.print(); } catch (_) {}
            }
          } catch (_) {
            finish();
          }
        }
  
        try {
          w.addEventListener("load", onLoad, { once: true });
        } catch (_) {
          const poll = setInterval(() => {
            try {
              if (w.document && w.document.readyState === "complete") {
                clearInterval(poll);
                onLoad();
              }
            } catch (_) {}
          }, 200);
          setTimeout(() => {
            clearInterval(poll);
            finish();
          }, 5000);
        }
      });
    }
  
    return new Promise((resolve) => {
      const iframe = document.createElement('iframe');
      iframe.style.position = 'fixed';
      iframe.style.right = '0';
      iframe.style.bottom = '0';
      iframe.style.width = '1px';
      iframe.style.height = '1px';
      iframe.style.border = '0';
      iframe.src = url;
  
      let done = false;
      function finish() {
        if (done) return;
        done = true;
        try { iframe.remove(); } catch (_) {}
        resolve();
      }
  
      iframe.onload = () => {
        try {
          const w = iframe.contentWindow;
          // Resolve when the print dialog closes (best effort).
          if (w && 'onafterprint' in w) {
            w.onafterprint = finish;
          }
          // Fallback: if the browser doesn't fire onafterprint for iframes,
          // give it a little time to spawn the dialog.
          setTimeout(finish, 2500);
  
          try { w.focus(); } catch (_) {}
          if (!(w && w.__POS_AUTOPRINT__ === true)) {
            try { w.print(); } catch (_) {}
          }
        } catch (_) {
          // If anything fails, still resolve so callers can continue.
          finish();
        }
      };
  
      document.body.appendChild(iframe);
    });
  }
  window.printClient = printClient;

  function sanitizeFilePart(value, fallback) {
    const cleaned = String(value || "")
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
    return cleaned || (fallback || "print");
  }

  function buildPreviewFilename(prefix, id, variant) {
    const parts = [
      sanitizeFilePart(prefix, "print"),
      sanitizeFilePart(id, "preview"),
      variant ? sanitizeFilePart(variant, "") : "",
    ].filter(Boolean);
    return `${parts.join("-")}.html`;
  }

  function openPreviewWindow(url) {
    const target = String(url || "");
    if (!target) return;
    const w = window.open(target, "_blank", "noopener,noreferrer");
    if (!w) window.location.href = target;
  }

  async function downloadPreviewFile(url, filename) {
    const target = String(url || "");
    if (!target) return;
    const response = await fetch(target, {
      credentials: "same-origin",
      headers: { Accept: "text/html,application/xhtml+xml" },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const contentType = (response.headers.get("content-type") || "").toLowerCase();
    let blob = null;
    if (contentType.includes("text/html")) {
      let html = await response.text();
      html = html.replace(/<script\b[^>]*>[\s\S]*?window\.print\([\s\S]*?<\/script>/gi, "");
      if (!/<base\s/i.test(html) && /<head[^>]*>/i.test(html)) {
        html = html.replace(/<head([^>]*)>/i, `<head$1><base href="${location.origin}/">`);
      }
      blob = new Blob([html], { type: "text/html;charset=utf-8" });
    } else {
      blob = await response.blob();
    }
    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = filename || "print-preview.html";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
  }

  async function dispatchPrintTarget(config) {
    const options = config || {};
    const url = String(options.url || "");
    const hexUrl = options.hexUrl ? String(options.hexUrl) : "";
    if (!url) return false;
    if (hexUrl && window.printBridgeHex) {
      return window.printBridgeHex(hexUrl, url, { fallback: options.fallback });
    }
    return printClient(url, { popup: options.popup === true });
  }

  function openPrintPreviewOptions(config) {
    const options = config || {};
    const url = String(options.url || "");
    const printUrl = String(options.printUrl || url);
    const viewUrl = String(options.viewUrl || url);
    const downloadUrl = String(options.downloadUrl || viewUrl || url);
    const hexUrl = options.hexUrl ? String(options.hexUrl) : "";
    const titleText = options.title || "Receipt actions";
    const bodyText = options.message || "Choose whether to print now, open the preview, or keep a local copy.";
    const metaText = options.meta || "The preview opens from this browser session only.";
    const filename = options.filename || buildPreviewFilename("print", "preview");
    if (!url) return Promise.resolve(false);

    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "pos-print-sheet";
      overlay.innerHTML = `
        <div class="pos-print-sheet__card" role="dialog" aria-modal="true" aria-labelledby="pos-print-sheet-title">
          <div class="pos-print-sheet__topline">
            <span class="pos-print-sheet__badge">Receipt Desk</span>
            <button type="button" class="pos-print-sheet__close" aria-label="Close">&times;</button>
          </div>
          <h3 id="pos-print-sheet-title"></h3>
          <p class="pos-print-sheet__text"></p>
          <p class="pos-print-sheet__meta"></p>
          <div class="pos-print-sheet__actions"></div>
        </div>
      `;

      const title = overlay.querySelector("#pos-print-sheet-title");
      const text = overlay.querySelector(".pos-print-sheet__text");
      const meta = overlay.querySelector(".pos-print-sheet__meta");
      const actions = overlay.querySelector(".pos-print-sheet__actions");
      const closeBtn = overlay.querySelector(".pos-print-sheet__close");

      if (title) title.textContent = titleText;
      if (text) text.textContent = bodyText;
      if (meta) meta.textContent = metaText;

      let closed = false;
      function close(result) {
        if (closed) return;
        closed = true;
        document.removeEventListener("keydown", onKeyDown);
        try { overlay.remove(); } catch (_) {}
        resolve(result);
      }

      function onKeyDown(event) {
        if (event.key === "Escape") close(false);
      }

      function addAction(label, description, className, handler) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `pos-print-sheet__action ${className || ""}`.trim();
        btn.innerHTML = `<strong>${label}</strong><span>${description}</span>`;
        btn.addEventListener("click", async () => {
          const restore = className && className.includes("primary")
            ? setButtonBusy(btn, "Preparing...")
            : null;
          try {
            const result = await Promise.resolve(handler());
            close(result !== false);
          } catch (error) {
            console.warn("print action failed", error);
            notify(`Print action failed: ${error?.message || error}`, "error", 3400);
            if (restore) restore();
          }
        });
        actions?.appendChild(btn);
      }

      addAction(
        options.printLabel || "Print now",
        options.printDescription || "Send the current receipt preview to the configured printer flow.",
        "pos-print-sheet__action--primary",
        () => dispatchPrintTarget({ url: printUrl, hexUrl, fallback: options.fallback, popup: options.popup })
      );
      addAction(
        options.viewLabel || "View preview",
        options.viewDescription || "Open the rendered receipt in a new browser tab before printing.",
        "",
        () => {
          openPreviewWindow(viewUrl);
          return true;
        }
      );
      addAction(
        options.downloadLabel || "Download file",
        options.downloadDescription || "Save this exact HTML receipt preview to the device.",
        "",
        () => downloadPreviewFile(downloadUrl, filename)
      );
      addAction(
        options.cancelLabel || "Cancel",
        options.cancelDescription || "Close this sheet without printing or saving anything.",
        "pos-print-sheet__action--ghost",
        () => false
      );

      overlay.addEventListener("click", (event) => {
        if (event.target === overlay) close(false);
      });
      closeBtn?.addEventListener("click", () => close(false));
      document.addEventListener("keydown", onKeyDown);
      document.body.appendChild(overlay);
    });
  }

  window.openPrintPreviewOptions = openPrintPreviewOptions;
  POS.openPrintPreviewOptions = openPrintPreviewOptions;
  POS.buildPreviewFilename = buildPreviewFilename;

  // ---- bridge helper: fetch hex from server and send to local bridge ----
  const BRIDGE_URL = window.POS_BRIDGE_URL || "http://127.0.0.1:5000/print-raw";
  const BRIDGE_LOG_URL = window.POS_BRIDGE_LOG_URL || "http://127.0.0.1:5000/log-error";
  const BRIDGE_TIMEOUT_MS = Number(window.POS_BRIDGE_TIMEOUT_MS || 2000);
  const HEX_TIMEOUT_MS = Number(window.POS_HEX_TIMEOUT_MS || 8000);

  function fetchWithTimeout(url, options, timeoutMs) {
    if (!timeoutMs) return fetch(url, options);
    if (typeof AbortController !== "undefined") {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), timeoutMs);
      return fetch(url, { ...(options || {}), signal: controller.signal })
        .finally(() => clearTimeout(id));
    }
    return Promise.race([
      fetch(url, options),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error("bridge timeout")), timeoutMs)
      ),
    ]);
  }

  async function fetchHex(url) {
    const r = await fetchWithTimeout(url, { headers: { "Accept": "application/json" } }, HEX_TIMEOUT_MS);
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(j.message || `HTTP ${r.status}`);
    if (!j.hex) throw new Error("No hex payload");
    return j.hex;
  }

  async function sendHexToBridge(hex) {
    const r = await fetchWithTimeout(BRIDGE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data: hex }),
    }, BRIDGE_TIMEOUT_MS);
    if (!r.ok) {
      let detail = "";
      try { detail = await r.text(); } catch (_) {}
      throw new Error(detail || `Bridge HTTP ${r.status}`);
    }
  }

  function bridgeDisabled() {
    try {
      if (window.DISABLE_BRIDGE_PRINT === true) return true;
      if (window.POS_DISABLE_BRIDGE_PRINT === true) return true;
    } catch (_) {}
    return false;
  }

  async function logBridgeError(err, context) {
    try {
      const payload = {
        ts: new Date().toISOString(),
        message: String(err && err.message ? err.message : err),
        stack: String(err && err.stack ? err.stack : ''),
        context: context || {}
      };
      await fetch(BRIDGE_LOG_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    } catch (_) {}
  }

  async function printBridgeHex(hexUrl, fallbackUrl, opts) {
    const fallbackMode = (opts && opts.fallback)
      ? String(opts.fallback).toLowerCase()
      : "iframe";
    if (bridgeDisabled()) {
      if (fallbackUrl && typeof printClient === "function") {
        return printClient(fallbackUrl, { popup: fallbackMode !== "iframe" });
      }
      return false;
    }
    try {
      const hex = await fetchHex(hexUrl);
      await sendHexToBridge(hex);
      return true;
    } catch (e) {
      console.warn("bridge print failed", e);
      logBridgeError(e, { hex_url: hexUrl, fallback_url: fallbackUrl });
      if (fallbackUrl && typeof printClient === "function") {
        return printClient(fallbackUrl, { popup: fallbackMode !== "iframe" });
      }
      throw e;
    }
  }
  window.printBridgeHex = printBridgeHex;
  

  // ---- bill printing shared helpers ----
  async function markBilling(sessionId) {
    try {
      await fetch(`/billing/mark_billing/${encodeURIComponent(sessionId)}`, { method: "POST" });
    } catch (e) {
      console.warn('mark_billing failed', e);
    }
  }

  // ===== SPLIT/GROUP helpers =====
  function normalizeGroupKey(k) {
    if (k == null) return '';
    const s = String(k).trim();
    // treat '', 'null', 'None', 'NULL' as no-group
    if (s === '' || /^null$/i.test(s) || /^none$/i.test(s)) return '';
    return s;
  }

  function splitMetaName(label) {
    const meta = Array.isArray(window.SPLIT_META) ? window.SPLIT_META : [];
    const key = String(label ?? '').trim();
    if (!key) return '';
    const hit = meta.find(m => String(m.key ?? m.label ?? m.id ?? m.group ?? '').trim() === key);
    const name = (hit?.name ?? hit?.title ?? '').toString().trim();
    return name || '';
  }

  function displayGroupLabel(label) {
    const name = splitMetaName(label);
    return name || `Bill ${label}`;
  }

  function getSplitGroups() {
    // Highest-confidence: SPLIT_LABELS (either array ["1","2"] or object {"1":"A",...})
    if (window.SPLIT_LABELS) {
      const lbl = window.SPLIT_LABELS;
      const keys = Array.isArray(lbl) ? lbl : Object.keys(lbl || {});
      return keys.map(normalizeGroupKey).filter(Boolean);
    }
    // Fallback: GROUP_SUBTOTALS keys (object of group -> subtotal)
    if (window.GROUP_SUBTOTALS && typeof window.GROUP_SUBTOTALS === 'object') {
      return Object.keys(window.GROUP_SUBTOTALS).map(normalizeGroupKey).filter(Boolean);
    }
    // Last resort: GROUP_STATUS (object) keys
    if (window.GROUP_STATUS && typeof window.GROUP_STATUS === 'object') {
      return Object.keys(window.GROUP_STATUS).map(normalizeGroupKey).filter(Boolean);
    }
    return [];
  }

  function hasSplits() {
    return getSplitGroups().length > 0;
  }

  function readDiscountInputs() {
    const pctRaw = parseInt(document.getElementById('discount_percent')?.value || '0', 10);
    const valEl = document.getElementById('discount_value') || document.getElementById('discount_amount');
    const valRaw = parseInt(valEl?.value || '0', 10);

    const pct = Number.isFinite(pctRaw) ? Math.max(0, Math.min(pctRaw, 100)) : 0;
    const amt = Number.isFinite(valRaw) ? Math.max(0, valRaw) : 0;
    return { pct, amt };
  }

  function addDiscountParams(u) {
    const { pct, amt } = readDiscountInputs();
    if (amt > 0) {
      u.searchParams.set('discount_amount', String(amt));
    } else if (pct > 0) {
      u.searchParams.set('discount_percent', String(pct));
    }
  }

  function packagingSelected() {
    const chk = document.getElementById('apply-packaging');
    if (chk) return !!chk.checked;
    return !!window.__pkgOn;
  }

  function addPackagingParam(u) {
    if (packagingSelected()) u.searchParams.set('packaging', '1');
  }

  // 1) Robust current group reading: fall back to the label text if global isn't set.
  function readGroupFromLabel() {
    const el = document.getElementById('grp-name');
    if (!el) return '';
    const txt = (el.textContent || '').trim(); // e.g., "ALL" or "Split 1" or "1"
    if (!txt) return '';
    if (/^(all|semua)$/i.test(txt)) return 'ALL';
    // Try "Split 2" -> "2"
    const m = txt.match(/\d+/);
    return m ? m[0] : txt; // if it was already "1", keep it
  }

  function currentGroupRaw() {
    // Prefer explicit global
    let g = window.CURRENT_GROUP;
    if (g == null || String(g).trim() === '') {
      g = window.ACTIVE_BILL_GROUP;
    }
    if (g == null || String(g).trim() === '') {
      // Fallback to visible label in the UI
      g = readGroupFromLabel();
    }
    return normalizeGroupKey(g);
  }

  function isAllView() {
    const raw = (currentGroupRaw() || '').trim().toLowerCase();
    return raw === '' || raw === 'all' || raw === 'semua';
  }

  // 2) When the UI navigates groups, refresh the DP button.
  //    Hook prev/next if present, and also observe #grp-name text changes.
  document.addEventListener('DOMContentLoaded', () => {
    const prev = document.getElementById('grp-prev');
    const next = document.getElementById('grp-next');
    if (prev) prev.addEventListener('click', () => setTimeout(refreshDpButton, 0));
    if (next) next.addEventListener('click', () => setTimeout(refreshDpButton, 0));

    const lbl = document.getElementById('grp-name');
    if (lbl && window.MutationObserver) {
      const obs = new MutationObserver(() => refreshDpButton());
      obs.observe(lbl, { childList: true, characterData: true, subtree: true });
    }
  });

  // ===== DP per-group prefs (drives the visual ON/OFF & query flag) =====
  // Persist ON/OFF per split; when no split, we auto-ON if DP exists.
  window.DP_PREFS = window.DP_PREFS || {}; // e.g. { "1": true, "2": false }

  function dpAvailable() {
    return Number(window.DP_AMOUNT || 0) > 0 && Number(window.DP_REMAINING || 0) > 0;
  }

  function getDpForCurrentView() {
    if (!hasSplits()) {
      // single bill → auto apply if available, unless a checkbox overrides
      const chk = document.getElementById('apply_dp') || document.getElementById('apply-dp');
      return chk ? !!(chk.checked || chk.value === '1') : dpAvailable();
    }
    if (isAllView()) return false; // ambiguous in ALL
    return !!window.DP_PREFS[currentGroupRaw()];
  }

  function setDpForCurrentGroup(on) {
    if (!hasSplits()) {
      const chk = document.getElementById('apply_dp') || document.getElementById('apply-dp');
      if (chk) chk.checked = !!on;
      return;
    }
    const g = currentGroupRaw();
    if (!g) return;
    window.DP_PREFS[g] = !!on;
  }

  function refreshDpButton() {
    const btn = document.getElementById('btn-dp-inline');
    if (!btn) return;

    if (!hasSplits()) {
      const on = getDpForCurrentView();
      btn.disabled = false;
      btn.classList.toggle('is-on', on);
      btn.textContent = on ? 'Gunakan DP (ON)' : 'Gunakan DP (OFF)';
      return;
    }

    if (isAllView()) {
      btn.disabled = true;
      btn.classList.remove('is-on');
      btn.textContent = 'Gunakan DP (pilih grup)';
      return;
    }

    const on = getDpForCurrentView();
    btn.disabled = false;
    btn.classList.toggle('is-on', on);
    btn.textContent = on ? 'Gunakan DP (ON)' : 'Gunakan DP (OFF)';
  }

  // Back-compat bridge (your other code may call this)
  window.isApplyDpChecked = function () {
    return getDpForCurrentView();
  };

  // ===== URL builders =====
  function applyDiscountParams(u) {
    addDiscountParams(u);
  }

  function applyDpParamIfApplicable(u, forAllWithSplits) {
    // In ALL view with splits → ambiguous which group uses DP, so don't send
    if (forAllWithSplits) return;
    u.searchParams.set('apply_dp', getDpForCurrentView() ? '1' : '0');
  }

  function buildBillHexUrl(sessionId) {
    return new URL(`/api/print/get-hex/${encodeURIComponent(sessionId)}`, location.origin);
  }

  // ==== helper: print a list of groups sequentially ====
  function printGroupsInSequence(sessionId, groups) {
    let i = 0;
    const delayMs = 800; // tiny gap so browsers keep the gesture chain

    function next() {
      if (i >= groups.length) return;

      const g = groups[i++];
      const u = new URL(`/print/preview/${encodeURIComponent(sessionId)}`, location.origin);
      u.searchParams.set('group', g);

      const hx = buildBillHexUrl(sessionId);
      hx.searchParams.set('group', g);

      // carry discounts (same for all splits; tweak if you want per-split discounts)
      addDiscountParams(u);
      addDiscountParams(hx);
      addPackagingParam(u);
      addPackagingParam(hx);

      // DO NOT set apply_dp here (ambiguous across multiple groups)
      if (window.printBridgeHex) {
        window.printBridgeHex(hx.toString(), u.toString());
      } else {
        printClient(u.toString());
      }

      setTimeout(next, delayMs);
    }

    if (groups.length > 0) next();
  }

  function hasSplitsData() {
    const groups = getSplitGroups();
    return Array.isArray(groups) && groups.length > 0;
  }
  
  function addCommonMoneyParams(u) {
    addDiscountParams(u);
    addPackagingParam(u);
    // Always apply DP if available
    const hasDp = Number(window.DP_AMOUNT || 0) > 0;
    u.searchParams.set('apply_dp', hasDp ? '1' : (isApplyDpChecked() ? '1' : '0'));
  }

  function openReceiptOptions(config) {
    return openPrintPreviewOptions(config);
  }
  
  // Toolbar “Print All”
  window.printBillAll = async function (sessionId) {
    await markBilling(sessionId);
    if (isDemoMode()) {
      showDemoPrintModal({
        title: "Bill printed (demo)",
        url: new URL(`/print/preview/${encodeURIComponent(sessionId)}?group=main`, location.origin).toString(),
      });
      return;
    }
    const u = new URL(`/print/preview/${encodeURIComponent(sessionId)}`, location.origin);
    const hx = buildBillHexUrl(sessionId);
  
    if (hasSplitsData()) {
      // SPLIT → combine into a single ticket
      u.searchParams.set('aggregate', '1');
      hx.searchParams.set('aggregate', '1');
      addPackagingParam(u);
      addPackagingParam(hx);
      // (no DP flag here; ambiguous)
    } else {
      // NO SPLIT → explicitly target the main (NULL) group
      u.searchParams.set('group', 'main');   // <-- key line
      hx.searchParams.set('group', 'main');
      addCommonMoneyParams(u);
      addCommonMoneyParams(hx);
    }
  
    return openReceiptOptions({
      title: "Bill output",
      message: "Choose how to handle this bill preview.",
      meta: "You can print now, open the preview, or download a copy before handing it over.",
      url: u.toString(),
      hexUrl: hx.toString(),
      filename: buildPreviewFilename("bill", sessionId, hasSplitsData() ? "all" : "main"),
    });
  };
  
    // ---- Checker: full order, local print by preview ----
    window.printChecker = function (sessionId, opts = {}) {
      if (isDemoMode()) {
        showDemoPrintModal({
          title: "Checker printed (demo)",
          url: new URL(`/print/checker/preview/${encodeURIComponent(sessionId)}?include_cancelled=1&collapse_voids=1&printed_only=1`, location.origin).toString(),
        });
        return Promise.resolve();
      }
      const params = new URLSearchParams();
      if (opts.include_cancelled === false) params.set('include_cancelled', '0');
      else params.set('include_cancelled', '1');

      if (opts.collapse_voids === false) params.set('collapse_voids', '0');
      else params.set('collapse_voids', '1');

      // NEW: printed-only view
      params.set('printed_only', '1');
      if (hasSplits() && !isAllView()) {
        const g = currentGroupRaw();
        if (g) params.set('group', g);
      }

      const u = new URL(`/print/checker/preview/${encodeURIComponent(sessionId)}`, location.origin);
      u.search = params.toString();
      const hx = new URL(`/api/print/checker_hex/${encodeURIComponent(sessionId)}`, location.origin);
      hx.search = params.toString();
      const viewUrl = new URL(u.toString());
      viewUrl.searchParams.set("client_print", "1");
      return openReceiptOptions({
        title: "Checker output",
        message: "Choose whether to print the checker now or inspect it first.",
        meta: "Printed-only lines are already applied to this preview.",
        url: u.toString(),
        viewUrl: viewUrl.toString(),
        downloadUrl: viewUrl.toString(),
        hexUrl: hx.toString(),
        filename: buildPreviewFilename("checker", sessionId, params.get("group") || "printed"),
      });
    };

    window.printAdminChecker = function (sessionId, opts = {}) {
      if (isDemoMode()) {
        showDemoPrintModal({
          title: "Admin checker printed (demo)",
          url: new URL(`/print/admin_checker/preview/${encodeURIComponent(sessionId)}?printed_only=1`, location.origin).toString(),
        });
        return Promise.resolve();
      }
      const params = new URLSearchParams();
      params.set('printed_only', opts.printed_only === false ? '0' : '1');
      if (hasSplits() && !isAllView()) {
        const g = currentGroupRaw();
        if (g) params.set('group', g);
      }

      const u = new URL(`/print/admin_checker/preview/${encodeURIComponent(sessionId)}`, location.origin);
      u.search = params.toString();
      const hx = new URL(`/api/print/admin_checker_hex/${encodeURIComponent(sessionId)}`, location.origin);
      hx.search = params.toString();
      const viewUrl = new URL(u.toString());
      viewUrl.searchParams.set("client_print", "1");
      return openReceiptOptions({
        title: "Admin checker",
        message: "Choose whether to print the admin checker now or open the preview.",
        meta: "This version follows the current printed-only setting for the selected bill.",
        url: u.toString(),
        viewUrl: viewUrl.toString(),
        downloadUrl: viewUrl.toString(),
        hexUrl: hx.toString(),
        filename: buildPreviewFilename("admin-checker", sessionId, params.get("group") || "printed"),
      });
    };

    function openCheckerChooser(sessionId) {
      const overlay = document.createElement('div');
      overlay.style.cssText = `
        position:fixed; inset:0; background:rgba(0,0,0,0.45);
        display:flex; align-items:center; justify-content:center; z-index:99999;
      `;
      const card = document.createElement('div');
      card.style.cssText = `
        background:#fff; border-radius:10px; padding:16px; min-width:260px;
        box-shadow:0 10px 32px rgba(0,0,0,0.22); font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
      `;
      const title = document.createElement('h3');
      title.textContent = 'Print Checker';
      title.style.margin = '0 0 10px';
      card.appendChild(title);

      const wrap = document.createElement('div');
      wrap.style.display = 'grid';
      wrap.style.gap = '8px';

      function close() { overlay.remove(); }
      function addBtn(label, handler, opts = {}) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = label;
        btn.style.cssText = 'padding:10px 12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;font-weight:700;cursor:pointer;text-align:left;';
        btn.onclick = async () => {
          if (opts.busy === false) {
            handler();
            return;
          }
          const restore = setButtonBusy(btn, 'Mencetak...');
          try {
            close();
            await Promise.resolve(handler());
          } finally {
            restore();
          }
        };
        wrap.appendChild(btn);
      }

      addBtn('Checker', () =>
        window.printChecker(sessionId, {
          include_cancelled: true,
          collapse_voids: false,
          printed_only: true
        })
      );
      addBtn('Admin Checker', () => window.printAdminChecker(sessionId, { printed_only: true }));
      addBtn('Batal', close, { busy: false });

      card.appendChild(wrap);
      overlay.appendChild(card);
      document.body.appendChild(overlay);
    }

    // ---- QR-only checker (QR-origin, defaults to unprinted/new) ----
    window.printQrOrders = function (sessionId, opts = {}) {
      if (isDemoMode()) {
        showDemoPrintModal({
          title: "QR orders printed (demo)",
          url: new URL(`/print/qr_checker/preview/${encodeURIComponent(sessionId)}?unprinted=1`, location.origin).toString(),
        });
        return Promise.resolve();
      }
      const params = new URLSearchParams();
      if (opts.unprinted === false) params.set('unprinted', '0');
      else params.set('unprinted', '1');

      const u = new URL(`/print/qr_checker/preview/${encodeURIComponent(sessionId)}`, location.origin);
      u.search = params.toString();
      const hx = new URL(`/api/print/qr_checker_hex/${encodeURIComponent(sessionId)}`, location.origin);
      hx.search = params.toString();
      const viewUrl = new URL(u.toString());
      viewUrl.searchParams.set("client_print", "1");
      return openReceiptOptions({
        title: "QR order slips",
        message: "Choose whether to print these QR-origin order slips or open the preview first.",
        meta: opts.unprinted === false ? "This view includes every QR-origin slip for the session." : "This view is limited to QR-origin slips that have not been printed yet.",
        url: u.toString(),
        viewUrl: viewUrl.toString(),
        downloadUrl: viewUrl.toString(),
        hexUrl: hx.toString(),
        filename: buildPreviewFilename("qr-orders", sessionId, opts.unprinted === false ? "all" : "unprinted"),
      });
    };


    
  // Inline “Print Bill” (left footer)
  window.printBillSmart = async function (sessionId, opts = {}) {
    await markBilling(sessionId);
    if (isDemoMode()) {
      showDemoPrintModal({
        title: "Bill printed (demo)",
        url: new URL(`/print/preview/${encodeURIComponent(sessionId)}?group=main`, location.origin).toString(),
      });
      return;
    }
    const skipChooser = !!opts.skipChooser;
    const forceCombine = !!opts.combine;
    const targetSession = (opts.target || sessionId || '').trim();
    const companion = forceCombine
      ? (opts.combineWith || (window.COMPANION_SESSION_ID || '')).trim()
      : '';
    const hasCompanion = !!companion && !skipChooser && !forceCombine;
    const splitLabels = getSplitGroups();
    const splitActive = splitLabels.length > 0;
    const inAll = (() => {
      const txt = (document.getElementById('grp-name')?.textContent || '').trim().toLowerCase();
      return txt === '' || txt === 'all' || txt === 'semua';
    })();

    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position:fixed; inset:0; background:rgba(0,0,0,0.45);
      display:flex; align-items:center; justify-content:center; z-index:99999;
    `;
    const card = document.createElement('div');
    card.style.cssText = `
      background:#fff; border-radius:10px; padding:16px; min-width:260px;
      box-shadow:0 10px 32px rgba(0,0,0,0.22); font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
    `;
    const title = document.createElement('h3');
    title.textContent = 'Print Bill';
    title.style.margin = '0 0 10px';
    card.appendChild(title);

    const btnWrap = document.createElement('div');
    btnWrap.style.display = 'grid';
    btnWrap.style.gap = '8px';

    function closeOverlay() { overlay.remove(); }

    function addBtn(label, handler) {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = label;
      b.style.cssText = 'padding:10px 12px;border-radius:8px;border:1px solid #ddd;background:#f7f7f7;font-weight:700;cursor:pointer;text-align:left;';
      b.onclick = () => { closeOverlay(); handler(); };
      btnWrap.appendChild(b);
    }

    function buildMainUrl(groupLabel) {
      const u = new URL(`/print/preview/${encodeURIComponent(sessionId)}`, location.origin);
      if (groupLabel) {
        u.searchParams.set('group', groupLabel);
        addCommonMoneyParams(u);
      } else if (inAll && splitActive) {
        u.searchParams.set('aggregate', '1');
        addPackagingParam(u);
      } else {
        u.searchParams.set('group', 'main');
        addCommonMoneyParams(u);
      }
      return u;
    }

    function buildMainHexUrl(groupLabel) {
      const u = buildBillHexUrl(sessionId);
      if (groupLabel) {
        u.searchParams.set('group', groupLabel);
        addCommonMoneyParams(u);
      } else if (inAll && splitActive) {
        u.searchParams.set('aggregate', '1');
        addPackagingParam(u);
      } else {
        u.searchParams.set('group', 'main');
        addCommonMoneyParams(u);
      }
      return u;
    }

    function buildTaUrl() {
      const u = new URL(`/print/preview/${encodeURIComponent(companion)}`, location.origin);
      u.searchParams.set('group', 'main');
      u.searchParams.set('apply_dp', '1');
      addPackagingParam(u);
      return u;
    }

    function buildTaHexUrl() {
      const u = buildBillHexUrl(companion);
      u.searchParams.set('group', 'main');
      u.searchParams.set('apply_dp', '1');
      addPackagingParam(u);
      return u;
    }

    function openBillOutput(urlObj, hexObj, variant, titleText, metaText) {
      return openReceiptOptions({
        title: titleText || "Bill output",
        message: "Choose whether to print this bill now or open the preview first.",
        meta: metaText || "You can also download the exact preview as an HTML file.",
        url: urlObj.toString(),
        hexUrl: hexObj ? hexObj.toString() : "",
        filename: buildPreviewFilename("bill", targetSession || sessionId, variant),
      });
    }

    if (forceCombine && companion) {
      const u = buildMainUrl();
      u.searchParams.set('combine', '1');
      u.searchParams.set('companion', companion);
      u.searchParams.set('apply_dp', '1');
      const hx = buildMainHexUrl();
      hx.searchParams.set('combine', '1');
      hx.searchParams.set('companion', companion);
      hx.searchParams.set('apply_dp', '1');
      return openBillOutput(u, hx, "combined", "Combined bill", "This preview merges the dine-in and take-away sections into one receipt.");
    }

    if (skipChooser) {
      // targeted single print
      if (opts.target) {
        const u = new URL(`/print/preview/${encodeURIComponent(opts.target)}`, location.origin);
        u.searchParams.set('group', 'main');
        addCommonMoneyParams(u);
        const hx = buildBillHexUrl(opts.target);
        hx.searchParams.set('group', 'main');
        addCommonMoneyParams(hx);
        return openBillOutput(u, hx, "main", "Bill output", "This shortcut opens the main bill for the selected session.");
      }
      return openBillOutput(
        buildMainUrl(),
        buildMainHexUrl(),
        inAll && splitActive ? "aggregate" : "main",
        "Bill output",
        inAll && splitActive
          ? "This preview aggregates the split bills into a single ticket."
          : "This preview follows the current bill selection."
      );
    }

    if (splitActive) {
      splitLabels.forEach(lbl => addBtn(displayGroupLabel(lbl), () => {
        const pu = buildMainUrl(lbl);
        const hx = buildMainHexUrl(lbl);
        return openBillOutput(pu, hx, lbl, displayGroupLabel(lbl), "Review, print, or download this split bill.");
      }));
      if (hasCompanion) addBtn('Take Away', () => {
        const pu = buildTaUrl();
        const hx = buildTaHexUrl();
        return openBillOutput(pu, hx, "take-away", "Take Away bill", "This opens the standalone take-away receipt for the linked session.");
      });
      addBtn('Batal', closeOverlay);
      card.appendChild(btnWrap);
      overlay.appendChild(card);
      document.body.appendChild(overlay);
      return;
    }

    if (hasCompanion) {
      addBtn('Dine In saja', () => {
        const pu = buildMainUrl();
        const hx = buildMainHexUrl();
        return openBillOutput(pu, hx, "dine-in", "Dine In bill", "Print or review only the dine-in receipt.");
      });
      addBtn('Take Away saja', () => {
        const pu = buildTaUrl();
        const hx = buildTaHexUrl();
        return openBillOutput(pu, hx, "take-away", "Take Away bill", "Print or review only the take-away receipt.");
      });
      addBtn('Gabung (1 struk)', () => {
        const u = buildMainUrl();
        u.searchParams.set('combine', '1');
        u.searchParams.set('companion', companion);
        u.searchParams.set('apply_dp', '1');
        const hx = buildMainHexUrl();
        hx.searchParams.set('combine', '1');
        hx.searchParams.set('companion', companion);
        hx.searchParams.set('apply_dp', '1');
        return openBillOutput(u, hx, "combined", "Combined bill", "Merge the dine-in and take-away sections into one receipt before printing.");
      });
      addBtn('Batal', closeOverlay);
      card.appendChild(btnWrap);
      overlay.appendChild(card);
      document.body.appendChild(overlay);
      return;
    }

    // default: single bill, no companion
    return openBillOutput(buildMainUrl(), buildMainHexUrl(), "main", "Bill output", "Print, preview, or download the current main bill.");
  };
  
  // Legacy “Print Current”
  window.printBillCurrent = async function (sessionId) {
    await markBilling(sessionId);
    if (isDemoMode()) {
      showDemoPrintModal({
        title: "Bill printed (demo)",
        url: new URL(`/print/preview/${encodeURIComponent(sessionId)}?group=main`, location.origin).toString(),
      });
      return;
    }
    const u = new URL(`/print/preview/${encodeURIComponent(sessionId)}`, location.origin);
    const g = hasSplitsData() ? (currentGroupRaw() || 'main') : 'main'; // <-- always 'main' when no split
    u.searchParams.set('group', g);
    addCommonMoneyParams(u);
    const hx = buildBillHexUrl(sessionId);
    hx.searchParams.set('group', g);
    addCommonMoneyParams(hx);
    return openReceiptOptions({
      title: "Current bill",
      message: "Choose whether to print the current bill or open the preview first.",
      meta: "The selected split group is already applied to this preview.",
      url: u.toString(),
      hexUrl: hx.toString(),
      filename: buildPreviewFilename("bill", sessionId, g || "main"),
    });
  };

  // ---- Kitchen printing (unchanged) ----
  window.sendToKitchen = async function (sessionId) {
    if (kitchenPrinting) return;
    const kitchenBtn = document.getElementById("btn-print-kitchen") || document.querySelector(".btn-kitchen");
    const restoreKitchenBtn = setButtonBusy(kitchenBtn, "Mengirim...");
    kitchenPrinting = true;
    try {
      let previewDone = Promise.resolve();
  
      // 1) PEEK: ask server if there are printables (no side effects)
      try {
        const peekResp = await fetch(
          `/print/kitchen/send/${encodeURIComponent(sessionId)}?dryrun=1`,
          { method: "POST", headers: { "Accept": "application/json" } }
        );
  
        let peekJson = null;
        try { peekJson = await peekResp.json(); } catch {}
  
        if (!peekResp.ok) {
          const msg = (peekJson && peekJson.message) || `HTTP ${peekResp.status}`;
          notify("Gagal kirim ke dapur: " + msg, "error", 4200);
          return;
        }
        if (!peekJson || peekJson.status !== "ok" || !peekJson.has_printables) {
          notify("Tidak ada item baru/edited untuk dicetak.", "warn", 2500);
          return;
        }
        if (isDemoMode()) {
          const demoResp = await fetch(`/print/kitchen/send/${encodeURIComponent(sessionId)}`, {
            method: "POST",
            headers: { "Accept": "application/json" }
          });
          const demoJson = await demoResp.json().catch(() => null);
          const okStatus = demoJson && (demoJson.status === "success" || demoJson.status === "partial_success");
          if (!demoResp.ok || !okStatus) {
            const msg = (demoJson && demoJson.message) || `HTTP ${demoResp.status}`;
            notify("Gagal kirim ke dapur: " + msg, "error", 4200);
            return;
          }
          const stationItems = (demoJson.station_items && typeof demoJson.station_items === "object")
            ? demoJson.station_items
            : {};
          const stationEntries = Object.entries(stationItems).filter(([, ids]) => ids.length > 0);
          const stationLabels = stationEntries.length
            ? stationEntries.map(([s]) => s.charAt(0).toUpperCase() + s.slice(1))
            : ["Kitchen"];
          const previewUrls = stationEntries.length
            ? stationEntries.map(([, ids]) =>
                `/print/kitchen/preview/${encodeURIComponent(sessionId)}?ids=${ids.join(",")}&client_print=1`
              )
            : [`/print/kitchen/preview/${encodeURIComponent(sessionId)}?client_print=1`];
          showDemoPrintModal({
            title: `Kitchen printed (demo) — ${stationLabels.join(", ")}`,
            url: previewUrls[0],
            previewUrls,
            actions: stationLabels,
          });
          setTimeout(async () => {
            const ok = await softSessionRefresh();
            if (!ok) window.location.replace(window.location.href);
          }, 120);
          return;
        }
      } catch (e) {
        notify("Network error: " + (e.message || e), "error", 4200);
        return;
      }
  
      // 2) PREVIEW: open client preview, give it a brief head start
      const previewUrl = `/print/kitchen/preview/${encodeURIComponent(sessionId)}?t=${Date.now()}&silent=1&client_print=1`;
      const hexUrl = `/api/print/kitchen_hex/${encodeURIComponent(sessionId)}`;
      try {
        if (window.printBridgeHex) {
          const ok = await window.printBridgeHex(hexUrl);
          if (!ok && window.printClient) {
            previewDone = window.printClient(previewUrl);
          }
        } else if (window.printClient) {
          previewDone = window.printClient(previewUrl);
        }
        // Let the preview page fetch before we mark as printed
        await new Promise((r) => setTimeout(r, 350));
      } catch (_) {
        if (window.printClient) {
          previewDone = window.printClient(previewUrl);
        } else {
          previewDone = Promise.resolve();
        }
      }
  
      // 3) SEND: actually print & mark printed (retry once on transient failure)
      try {
        const sendOnce = async () => {
          const r = await fetch(`/print/kitchen/send/${encodeURIComponent(sessionId)}`, {
            method: "POST",
            headers: { "Accept": "application/json" }
          });
          let j = null;
          try { j = await r.json(); } catch {}
          const okStatus = j && (j.status === "success" || j.status === "partial_success");
          const nothing = j && j.status === "nothing_to_print";
          return { r, j, okStatus, nothing };
        };

        let res = await sendOnce();
        if (!res.okStatus && !res.nothing) {
          // brief retry for transient printer/CUPS/network hiccups
          await new Promise((r) => setTimeout(r, 650));
          res = await sendOnce();
        }

        if (res.okStatus) {
          if (res.j && res.j.errors && res.j.errors.length) {
            notify("Sebagian gagal dicetak:\n" + res.j.errors.join("\n"), "warn", 4500);
          }
          notify("Terkirim ke dapur.", "success", 1800);
          await previewDone;                     // ensure preview dialog lifecycle completes
          setTimeout(async () => {
            const ok = await softSessionRefresh();
            if (!ok) window.location.replace(window.location.href);
          }, 150);
        } else if (res.nothing) {
          notify("Tidak ada item baru/edited untuk dicetak.", "warn", 2500);
        } else {
          const detail = (res.j && res.j.errors && res.j.errors.length) ? ("\n" + res.j.errors.join("\n")) : "";
          const msg = (res.j && res.j.message) || `HTTP ${res.r?.status || "error"}`;
          notify("Gagal kirim ke dapur: " + msg + detail, "error", 4200);
        }
      } catch (e) {
        notify("Network error: " + (e.message || e), "error", 4200);
      }
    } finally {
      kitchenPrinting = false;
      restoreKitchenBtn();
    }
  };
  
  

  // ---- QR button hook ----
  document.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('btn-print-qr');
    if (!btn) return;
    const sid = document.body?.dataset?.sessionId;
    const table = document.body?.dataset?.tableNumber;
    const url = window.QR_TICKET_URL;
    if (!sid || !table) return;
    const hexUrl = `/api/print/qr_hex/${encodeURIComponent(table)}/${encodeURIComponent(sid)}`;
    btn.addEventListener('click', () => {
      return withButtonBusy(btn, "Mencetak...", () => {
        if (isDemoMode()) {
          showDemoPrintModal({
            title: "QR ticket printed (demo)",
            url: url || "",
          });
          return Promise.resolve();
        }
        if (!url) return Promise.resolve();
        return openReceiptOptions({
          title: "QR ticket",
          message: "Choose whether to print this QR ticket now or open the preview.",
          meta: "You can also download the ticket preview as a local HTML file.",
          url,
          hexUrl,
          filename: buildPreviewFilename("qr-ticket", sid, table),
        });
      });
    });
  });

  // ---- Wire the inline buttons + DP visuals ----
  document.addEventListener('DOMContentLoaded', () => {
    const sid = document.body?.dataset?.sessionId;

    const printBtn = document.getElementById('btn-print-bill');
    if (printBtn && sid) {
      printBtn.addEventListener('click', () =>
        withButtonBusy(printBtn, "Mencetak...", () => window.printBillSmart(sid))
      );
    }

    const checkerBtn = document.getElementById('btn-print-checker');
    if (checkerBtn && sid) {
      checkerBtn.addEventListener('click', () => {
        if (isDemoMode()) {
          return withButtonBusy(checkerBtn, "Menyiapkan...", () => {
            showDemoPrintModal({
              title: "Checker printed (demo)",
              url: new URL(`/print/checker/preview/${encodeURIComponent(sid)}?include_cancelled=1&collapse_voids=1&printed_only=1`, location.origin).toString(),
            });
          });
        }
        if (window.IS_ADMIN === true) {
          openCheckerChooser(sid);
          return;
        }
        return withButtonBusy(checkerBtn, "Mencetak...", () =>
          window.printChecker(sid, {
            include_cancelled: true,
            collapse_voids: false,
            printed_only: true
          })
        );
      });
    }

    const qrCheckerBtn = document.getElementById('btn-print-qr-orders');
    if (qrCheckerBtn && sid) {
      qrCheckerBtn.addEventListener('click', () =>
        withButtonBusy(qrCheckerBtn, "Mencetak...", () => {
          if (isDemoMode()) {
            showDemoPrintModal({
              title: "QR orders printed (demo)",
              url: new URL(`/print/qr_checker/preview/${encodeURIComponent(sid)}?unprinted=1`, location.origin).toString(),
            });
            return Promise.resolve();
          }
          return window.printQrOrders(sid, { unprinted: true });
        })
      );
    }

    const dpBtn = document.getElementById('btn-dp-inline');
    if (dpBtn) {
      // initial state: auto-ON if single bill & DP exists
      if (!hasSplits() && dpAvailable()) {
        setDpForCurrentGroup(true);
      }
      refreshDpButton();

      dpBtn.addEventListener('click', () => {
        if (hasSplits() && isAllView()) return; // disabled state protects this too
        const on = getDpForCurrentView();
        setDpForCurrentGroup(!on);

        // mirror to hidden checkbox if present
        const chk = document.getElementById('apply_dp') || document.getElementById('apply-dp');
        if (chk) chk.checked = !on;

        // update visuals
        refreshDpButton();
      });
    }
  });

  // NOTE: if your group navigation changes window.CURRENT_GROUP,
  // call refreshDpButton() after switching groups.
})();
