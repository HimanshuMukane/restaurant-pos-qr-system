// static/js/lock.js
(function () {
  const body = document.body;
  const sessionId = body?.dataset?.sessionId;
  const nonce = body?.dataset?.lockNonce || window.LOCK_NONCE;
  if (!sessionId || !nonce) return;

  const HEARTBEAT_MS = 15000; // must be < LEASE_SECONDS
  let hbTimer = null;
  let consecutiveFails = 0;
  let stopped = false;

  // Try to pick up CSRF token if you use Flask-WTF / SeaSurf
  function getCsrf() {
    const m =
      document.querySelector('meta[name="csrf-token"]') ||
      document.querySelector('meta[name="csrf_token"]');
    return m?.content || null;
  }
  const CSRF = getCsrf();
  const csrfHeaderName = "X-CSRFToken"; // change to X-CSRF-Token for SeaSurf

  async function hb() {
    if (stopped) return;
    try {
      const res = await fetch(`/session_lock/${sessionId}/heartbeat`, {
        method: "POST",
        credentials: "same-origin",
        keepalive: true,
        headers: Object.assign(
          { "Content-Type": "application/json" },
          CSRF ? { [csrfHeaderName]: CSRF } : {}
        ),
        body: JSON.stringify({ nonce })
      });

      if (res.ok) {
        consecutiveFails = 0;
        return;
      }

      // Non-200: allow one retry window before we boot the user
      consecutiveFails += 1;
      if (consecutiveFails >= 2) {
        stopped = true;
        clearInterval(hbTimer);
        alert("Sesi dikunci oleh pengguna lain. Halaman akan ditutup.");
        window.location.href = "/";
      }
    } catch (_) {
      // Network hiccup—don't count this as a hard failure
    }
  }

  function release() {
    try {
      const url = `/session_lock/${sessionId}/release`;
      const data = JSON.stringify({ nonce });

      // Prefer sendBeacon so it fires during unload reliably
      const blob = new Blob([data], { type: "application/json" });
      if (!navigator.sendBeacon || !navigator.sendBeacon(url, blob)) {
        fetch(url, {
          method: "POST",
          credentials: "same-origin",
          keepalive: true,
          headers: Object.assign(
            { "Content-Type": "application/json" },
            CSRF ? { [csrfHeaderName]: CSRF } : {}
          ),
          body: data
        });
      }
    } catch (_) {}
  }

  window.addEventListener("load", () => {
    hb(); // ping once immediately
    hbTimer = setInterval(hb, HEARTBEAT_MS);
  });

  // Release on navigation/close without using beforeunload, which can make
  // page transitions feel slower on touch devices and may interfere with caching.
  window.addEventListener("pagehide", release); // iOS/Safari + standard navigations
})();
