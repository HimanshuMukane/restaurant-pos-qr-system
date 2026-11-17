// On-screen QWERTY keyboard for non-numeric inputs/textareas
(function () {
  let target = null;
  let displayEl = null;
  let caps = false;
  let shift = false;

  // ---- helpers ----
  function isNumericInput(el) {
    if (!el) return false;
    const t = (el.type || "").toLowerCase();
    const im = (el.getAttribute("inputmode") || "").toLowerCase();
    return (
      t === "number" ||
      im === "numeric" ||
      im === "decimal" ||
      el.dataset.numpad === "true"
    );
  }
  function isTextualCandidate(el) {
    if (!el || el.disabled || el.readOnly) return false;
    if (!(el.tagName === "INPUT" || el.tagName === "TEXTAREA")) return false;

    // explicit overrides
    if (el.dataset.kbd === "false") return false;
    if (el.dataset.kbd === "true") return true;

    if (isNumericInput(el)) return false; // let numpad own these

    const t = (el.type || "text").toLowerCase();
    return (
      ["text", "search", "email", "password", "url", "tel"].includes(t) ||
      el.tagName === "TEXTAREA"
    );
  }

  function getCaret(el) {
    // fallback to end if browser doesn’t expose it
    const v = String(el.value ?? "");
    let s = Number(el.selectionStart),
      e = Number(el.selectionEnd);
    if (!Number.isFinite(s)) s = v.length;
    if (!Number.isFinite(e)) e = v.length;
    return { s, e, v };
  }
  function setCaret(el, pos) {
    // rAF avoids some browsers snapping the caret to 0 during fast edits
    requestAnimationFrame(() => {
      try {
        el.focus({ preventScroll: true });
        el.setSelectionRange(pos, pos);
      } catch (_) {}
    });
  }
  function updateDisplay() {
    if (!displayEl) return;
    const v = target ? String(target.value ?? "") : "";
    displayEl.textContent = v.length ? v : "—";
  }
  function hideNumpadIfAny() {
    const np = document.querySelector(".numpad-dock");
    if (np) np.classList.add("numpad-hidden");
  }

  // ---- build dock ----
  const dock = document.createElement("div");
  dock.className = "kbd-dock kbd-xl kbd-square kbd-full kbd-hidden";
  dock.setAttribute("role", "dialog");
  dock.setAttribute("aria-label", "On-screen keyboard");
  dock.innerHTML = `
    <div class="kbd-display" id="__kbd_disp">—</div>
    <div class="kbd-rows">
      <div class="kbd-row" data-row="num"></div>
      <div class="kbd-row" data-row="row1"></div>
      <div class="kbd-row" data-row="row2"></div>
      <div class="kbd-row" data-row="row3"></div>
      <div class="kbd-row" data-row="row4"></div>
    </div>
  `;

  const NUM = [
    { k: "1", s: "!" },
    { k: "2", s: "@" },
    { k: "3", s: "#" },
    { k: "4", s: "$" },
    { k: "5", s: "%" },
    { k: "6", s: "^" },
    { k: "7", s: "&" },
    { k: "8", s: "*" },
    { k: "9", s: "(" },
    { k: "0", s: ")" },
    { k: "-", s: "_" },
    { k: "=", s: "+" },
    { k: "backspace", label: "⌫", cls: "xwide mod" },
  ];
  const ROW1 = "q w e r t y u i o p [ ] \\".split(" ").map((v) => ({ k: v }));
  const ROW2 = [{ k: "caps", label: "Caps", cls: "wide mod" }]
    .concat("a s d f g h j k l ; '".split(" ").map((v) => ({ k: v })))
    .concat([{ k: "enter", label: "Enter", cls: "xwide mod" }]);
  const ROW3 = [{ k: "shift", label: "Shift", cls: "wide mod" }]
    .concat("z x c v b n m , . /".split(" ").map((v) => ({ k: v })))
    .concat([{ k: "shift", label: "Shift", cls: "wide mod" }]);
  const ROW4 = [
    { k: "left", label: "◀", cls: "mod" },
    { k: "space", label: "Space", cls: "space" },
    { k: "right", label: "▶", cls: "mod" },
    { k: "hide", label: "Hide", cls: "wide mod" },
  ];

  function makeKey(spec) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `kbd-key ${spec.cls || ""}`.trim();
    btn.dataset.k = spec.k;
    btn.textContent = spec.label || spec.k;
    return btn;
  }
  function renderRow(rowEl, specs) {
    rowEl.innerHTML = "";
    specs.forEach((s) => rowEl.appendChild(makeKey(s)));
  }
  function renderAll() {
    renderRow(dock.querySelector('[data-row="num"]'), NUM);
    renderRow(dock.querySelector('[data-row="row1"]'), ROW1);
    renderRow(dock.querySelector('[data-row="row2"]'), ROW2);
    renderRow(dock.querySelector('[data-row="row3"]'), ROW3);
    renderRow(dock.querySelector('[data-row="row4"]'), ROW4);
    applyCaseToLetters();
    applyShiftToNumRow();
    updateModsUI();
  }

  function applyCaseToLetters() {
    const up = caps ^ shift;
    dock.querySelectorAll(".kbd-key").forEach((btn) => {
      const k = btn.dataset.k;
      if (/^[a-z]$/.test(k))
        btn.textContent = up ? k.toUpperCase() : k.toLowerCase();
    });
  }
  function applyShiftToNumRow() {
    const row = dock.querySelector('[data-row="num"]');
    [...row.querySelectorAll(".kbd-key")].forEach((b) => {
      const k = b.dataset.k;
      if (!k || k === "backspace") return;
      const spec = NUM.find((x) => x.k === k);
      if (!spec) return;
      b.textContent = shift ? spec.s || spec.k : spec.k;
    });
  }
  function updateModsUI() {
    dock
      .querySelectorAll('.kbd-key[data-k="caps"]')
      .forEach((b) => b.classList.toggle("on", !!caps));
    dock
      .querySelectorAll('.kbd-key[data-k="shift"]')
      .forEach((b) => b.classList.toggle("on", !!shift));
  }

  function showDock() {
    hideNumpadIfAny();
    dock.classList.remove("kbd-hidden");
    updateDisplay();
  }
  function hideDock() {
    dock.classList.add("kbd-hidden");
    target = null;
    shift = false;
    updateModsUI();
    applyShiftToNumRow();
    applyCaseToLetters();
  }
  function setTarget(el) {
    if (!isTextualCandidate(el)) return;
    target = el;
    try {
      target.focus({ preventScroll: true });
    } catch (_) {}
    showDock();
  }

  const SHIFT_ALT = {
    "[": "{",
    "]": "}",
    "\\": "|",
    ";": ":",
    "'": '"',
    ",": "<",
    ".": ">",
    "/": "?",
  };

  function insertText(txt) {
    if (!target) return;
    const { s, e, v } = getCaret(target);
    const next = v.slice(0, s) + txt + v.slice(e);
    target.value = next;
    const pos = s + txt.length;
    target.dispatchEvent(new Event("input", { bubbles: true }));
    setCaret(target, pos);
    updateDisplay();

    // one-shot shift
    if (shift) {
      shift = false;
      updateModsUI();
      applyShiftToNumRow();
      applyCaseToLetters();
    }
  }
  function handleBackspace() {
    if (!target) return;
    const { s, e, v } = getCaret(target);
    let ns = s,
      ne = e,
      nv = v;

    if (s !== e) {
      // delete selection
      nv = v.slice(0, s) + v.slice(e);
      ns = ne = s;
    } else if (s > 0) {
      nv = v.slice(0, s - 1) + v.slice(e);
      ns = ne = s - 1;
    } else {
      ns = ne = 0; // nothing to delete
    }

    target.value = nv;
    target.dispatchEvent(new Event("input", { bubbles: true }));
    setCaret(target, ns);
    updateDisplay();
  }
  function moveCaret(dir) {
    if (!target) return;
    const { s, e } = getCaret(target);
    const pos = dir < 0 ? Math.max(0, Math.min(s, e) - 1) : Math.max(s, e) + 1;
    setCaret(target, pos);
  }

  function keypress(k, label) {
    if (!target) return;
    try {
      target.focus({ preventScroll: true });
    } catch (_) {}

    if (k === "backspace") return handleBackspace();
    if (k === "space") return insertText(" ");
    if (k === "left") return moveCaret(-1);
    if (k === "right") return moveCaret(+1);
    if (k === "caps") {
      caps = !caps;
      updateModsUI();
      applyCaseToLetters();
      return;
    }
    if (k === "shift") {
      shift = !shift;
      updateModsUI();
      applyShiftToNumRow();
      applyCaseToLetters();
      return;
    }
    if (k === "hide") {
      target.dispatchEvent(new Event("change", { bubbles: true }));
      return hideDock();
    }
    if (k === "enter") {
      if (target.tagName === "TEXTAREA") insertText("\n");
      else {
        target.dispatchEvent(new Event("change", { bubbles: true }));
        hideDock();
      }
      return;
    }

    let out = label || k;
    if (/^[a-z]$/i.test(k)) {
      out = caps ^ shift ? k.toUpperCase() : k.toLowerCase();
    } else if (SHIFT_ALT[k] && shift) {
      out = SHIFT_ALT[k];
    }
    insertText(out);
  }

  dock.addEventListener(
    "pointerdown",
    (e) => {
      const btn = e.target.closest(".kbd-key");
      if (!btn) return;
      e.preventDefault(); // keep focus on input
      keypress(btn.dataset.k, btn.textContent);
    },
    { passive: false },
  );

  document.addEventListener("focusin", (e) => {
    if (isTextualCandidate(e.target)) setTarget(e.target);
    updateDisplay();
  });

  document.addEventListener("input", (e) => {
    if (e.target === target) updateDisplay();
  });

  document.addEventListener(
    "pointerdown",
    (evt) => {
      if (dock.contains(evt.target)) return;
      const input = evt.target.closest("input,textarea");
      if (isTextualCandidate(input)) return;
      hideDock();
    },
    { capture: true },
  );

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hideDock();
  });

  document.addEventListener("DOMContentLoaded", () => {
    document.body.appendChild(dock);
    displayEl = document.getElementById("__kbd_disp");
    renderAll();
    updateDisplay();
    // tiny log for sanity in dev
    if (window.location.search.includes("debugkbd")) console.log("[kbd] ready");
  });
})();

// Global click debounce to prevent accidental double clicks.
(function () {
  const DEFAULT_MS = 100;
  const MAX_MS = 1000;
  let lastClickAt = 0;

  function readDebounceMs() {
    let ms = window.POS_CLICK_DEBOUNCE_MS;
    if (!Number.isFinite(ms) && window.POS_CONFIG && window.POS_CONFIG.ui) {
      ms = window.POS_CONFIG.ui.click_debounce_ms;
    }
    if (!Number.isFinite(ms)) {
      const raw =
        document.body?.dataset?.clickDebounceMs ||
        document.documentElement?.dataset?.clickDebounceMs;
      if (raw !== undefined) ms = Number(raw);
    }
    if (!Number.isFinite(ms)) ms = DEFAULT_MS;
    ms = Math.max(0, Math.min(MAX_MS, ms));
    return ms;
  }

  document.addEventListener(
    "click",
    (e) => {
      if (!e.isTrusted) return;
      if (e.defaultPrevented) return;
      if (e.target && e.target.closest('[data-click-debounce="off"]')) return;
      const ms = readDebounceMs();
      if (!ms) return;
      const now =
        window.performance && performance.now ? performance.now() : Date.now();
      if (now - lastClickAt < ms) {
        e.preventDefault();
        e.stopImmediatePropagation();
        return;
      }
      lastClickAt = now;
    },
    true,
  );
})();
