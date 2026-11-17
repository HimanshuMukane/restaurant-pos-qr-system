(function () {
  const POS = (window.POS = window.POS || {});

  function isDemoMode() {
    return window.POS_DEMO_MODE === true;
  }

  function ensureModal() {
    let modal = document.getElementById("demo-print-modal");
    if (modal) return modal;

    modal = document.createElement("div");
    modal.id = "demo-print-modal";
    modal.className = "demo-print-modal";
    modal.hidden = true;
    modal.innerHTML = `
      <div class="demo-print-card" role="dialog" aria-modal="true" aria-labelledby="demo-print-title">
        <div class="demo-print-topline">
          <span class="demo-print-badge">Print Preview</span>
          <button type="button" class="demo-print-close" aria-label="Close">&times;</button>
        </div>
        <h3 id="demo-print-title"></h3>
        <p class="demo-print-text"></p>
        <div class="demo-print-actions"></div>
        <div class="demo-print-previews"></div>
        <div class="demo-print-footer">
          <button type="button" class="demo-print-btn">Close</button>
        </div>
      </div>
    `;

    function closeModal() {
      modal.hidden = true;
      const previews = modal.querySelector(".demo-print-previews");
      if (previews) previews.innerHTML = "";
    }

    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeModal();
    });
    modal.querySelector(".demo-print-close")?.addEventListener("click", closeModal);
    modal.querySelector(".demo-print-btn")?.addEventListener("click", closeModal);
    document.body.appendChild(modal);
    return modal;
  }

  function showDemoPrintModal(config) {
    if (!isDemoMode()) return false;
    const options = config || {};
    const modal = ensureModal();
    const title = modal.querySelector("#demo-print-title");
    const text = modal.querySelector(".demo-print-text");
    const actions = modal.querySelector(".demo-print-actions");
    if (title) title.textContent = options.title || "Preview staged";
    if (text) {
      if (options.message) {
        text.hidden = false;
        text.textContent = options.message;
      } else {
        text.hidden = true;
        text.textContent = "";
      }
    }

    if (actions) {
      actions.innerHTML = "";
      (options.actions || []).forEach((label) => {
        const chip = document.createElement("div");
        chip.className = "demo-print-chip";
        chip.textContent = String(label || "");
        actions.appendChild(chip);
      });
    }

    // Miniaturized iframe previews (one per station/URL)
    const previews = modal.querySelector(".demo-print-previews");
    const url = options.url ? String(options.url) : "";
    const urls = Array.isArray(options.previewUrls) && options.previewUrls.length
      ? options.previewUrls
      : (url ? [url] : []);
    if (previews) {
      previews.innerHTML = "";
      urls.forEach((u) => {
        const viewport = document.createElement("div");
        viewport.className = "demo-print-thumb-viewport";
        const frame = document.createElement("iframe");
        frame.className = "demo-print-thumb-frame";
        frame.src = String(u);
        frame.setAttribute("frameborder", "0");
        frame.setAttribute("scrolling", "no");
        viewport.appendChild(frame);
        previews.appendChild(viewport);
      });
    }

    modal.hidden = false;
    return true;
  }

  POS.isDemoMode = isDemoMode;
  POS.showDemoPrintModal = showDemoPrintModal;
})();
