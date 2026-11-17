(function() {
  let target = null;
  let originalVal = "";
  let displayEl = null;
  let replaceNext = false;   

  function fmtPreview(val){
    const raw = String(val ?? "").trim();
    if (!raw) return "—";
    const neg  = raw.startsWith("-");
    const body = neg ? raw.slice(1) : raw;
    const parts = body.split(".");
    const intPart  = (parts.shift() || "").replace(/\D/g, "") || "0";
    const fracPart = (parts.join(".") || "").replace(/\D/g, "");
    const groupedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return (neg ? "-" : "") + groupedInt + (fracPart ? "," + fracPart : "");
  }


  function isNumericInput(el){
    if(!el) return false;
    const t=(el.type||"").toLowerCase();
    const im=(el.getAttribute("inputmode")||"").toLowerCase();
    return t==="number" || im==="numeric" || im==="decimal" || el.dataset.numpad==="true";
  }

  function commitFirst(wantDot=false){
    if (!target || !replaceNext) return false;
  
    // If first key is ".", start with "0."
    if (wantDot) {
      target.value = "0.";
      replaceNext = false;
      target.dispatchEvent(new Event("input",{bubbles:true}));
      updateDisplay();
      return true; // consumed
    }
  
    // Otherwise, hard-clear so the next insert truly replaces
    target.value = "";
    replaceNext = false;
    return false; // not consumed; caller should insert the key next
  }
  

  const dock = document.createElement("div");
  dock.className = "numpad-dock numpad-hidden";
  dock.setAttribute("role","dialog");
  dock.setAttribute("aria-label","Numeric keypad");
  dock.innerHTML = `
    <div class="numpad-display" id="__np_disp">—</div>
    <div class="numpad-grid">
      <button type="button" class="numpad-btn" data-k="7">7</button>
      <button type="button" class="numpad-btn" data-k="8">8</button>
      <button type="button" class="numpad-btn" data-k="9">9</button>

      <button type="button" class="numpad-btn" data-k="4">4</button>
      <button type="button" class="numpad-btn" data-k="5">5</button>
      <button type="button" class="numpad-btn" data-k="6">6</button>

      <button type="button" class="numpad-btn" data-k="1">1</button>
      <button type="button" class="numpad-btn" data-k="2">2</button>
      <button type="button" class="numpad-btn" data-k="3">3</button>

      <button type="button" class="numpad-btn" data-k=".">.</button>
      <button type="button" class="numpad-btn" data-k="0">0</button>
      <button type="button" class="numpad-btn numpad-aux" data-k="del">⌫</button>

      <button type="button" class="numpad-btn numpad-aux numpad-wide-2" data-k="cancel">Cancel</button>
      <button type="button" class="numpad-btn numpad-aux" data-k="ok">OK</button>
    </div>
  `;

  function caretStart(el){
    const v=String(el.value ?? "");
    const s=Number(el.selectionStart);
    if (document.activeElement !== el) return v.length;
    return Number.isFinite(s) ? s : v.length;
  }
  function caretEnd(el){
    const v=String(el.value ?? "");
    const e=Number(el.selectionEnd);
    if (document.activeElement !== el) return v.length;
    return Number.isFinite(e) ? e : v.length;
  }

  function isSecureTarget(el){
    if (!el) return false;
    const t = (el.type || "").toLowerCase();
    if (t === "password") return true;
    const ds = (el.dataset && el.dataset.numpadSecure) || "";
    if (String(ds).toLowerCase() === "true") return true;
    return false;
  }

  function updateDisplay(){
    if(!displayEl) return;
    const secure = isSecureTarget(target);
    dock.classList.toggle("numpad-secure", secure);
    if (secure) {
      displayEl.textContent = "••••";
      return;
    }
    const v = target ? String(target.value ?? "") : "";
    displayEl.textContent = v.length ? fmtPreview(v) : "—";
  }

  function showDock(){
    const isNumType = target && (target.type||"").toLowerCase()==="number";
    replaceNext = true; // <-- arm first stroke to replace on every (re)open
    dock.classList.toggle("is-number", !!isNumType);
    dock.classList.remove("numpad-hidden");
    updateDisplay();
  }
  
  function hideDock(){
    dock.classList.add("numpad-hidden");
    dock.classList.remove("numpad-secure");
    target = null;
    replaceNext = false;
    updateDisplay();
  }

  function setTarget(el){
  if(!isNumericInput(el)) return;
  target = el;
  originalVal = el.value;
  replaceNext = true;                        

  const len = String(el.value ?? "").length;
  try { el.focus(); } catch(_){}
  try { el.select && el.select(); } catch(_){}
  try { el.setSelectionRange && el.setSelectionRange(0, len); } catch(_){}

  showDock();
  }


  function insertText(txt){
    if(!target) return;
    const isNumType = (target.type||"").toLowerCase()==="number";

    if(isNumType){
      target.value = String(target.value ?? "") + txt;
      target.dispatchEvent(new Event("input",{bubbles:true}));
      updateDisplay();
      return;
    }

    const v = String(target.value ?? "");
    const start = caretStart(target);
    const end   = caretEnd(target);
    const next  = v.slice(0,start)+txt+v.slice(end);

    target.value = next;
    const pos = start + txt.length;
    if(typeof target.setSelectionRange==="function"){
      try{ target.setSelectionRange(pos,pos);}catch(_){}
    }
    target.dispatchEvent(new Event("input",{bubbles:true}));
    updateDisplay();
  }

  function handleDigit(d){
    if(!target) return;
    // If it's the first stroke, clear first; then always insert
    commitFirst(false);
    insertText(String(d));
  }
  


  function handleDot(){
    if(!target) return;
    const isNumType = (target.type||"").toLowerCase()==="number";
    if(isNumType) return; // no decimals for type=number
  
    // If first stroke is ".", commit as "0." and stop
    if (commitFirst(true)) return;
  
    // (continue with your existing before/after '.' check)
    const v = String(target.value ?? "");
    const start = caretStart(target);
    const end   = caretEnd(target);
    const before=v.slice(0,start), after=v.slice(end);
    if(before.includes(".") || after.includes(".")) return;
    insertText(".");
  }
  


  function handleDelete(){
    if(!target) return;
    const wasArmed = replaceNext;
    replaceNext = false;                       
    const isNumType = (target.type||"").toLowerCase()==="number";
    const v = String(target.value ?? "");

    // If this is the first action after focusing, clear everything
    if (wasArmed) {
      target.value = "";
      target.dispatchEvent(new Event("input",{bubbles:true}));
      updateDisplay();
      return;
    }

    if(isNumType){
      target.value = v.slice(0,-1);
      target.dispatchEvent(new Event("input",{bubbles:true}));
      updateDisplay();
      return;
    }

    const start = caretStart(target);
    const end   = caretEnd(target);

    if(start!==end){
      target.value = v.slice(0,start) + v.slice(end);
      if(typeof target.setSelectionRange==="function"){
        try{ target.setSelectionRange(start,start);}catch(_){}
      }
    }else if(start>0){
      target.value = v.slice(0,start-1) + v.slice(end);
      if(typeof target.setSelectionRange==="function"){
        try{ target.setSelectionRange(start-1,start-1);}catch(_){}
      }
    }
    target.dispatchEvent(new Event("input",{bubbles:true}));
    updateDisplay();
  }

  function handleCancel(){
    if(!target) return hideDock();
    target.value = originalVal;
    target.dispatchEvent(new Event("input",{bubbles:true}));
    target.dispatchEvent(new Event("change",{bubbles:true}));
    replaceNext = false;
    hideDock();
  }

  // ----- NEW: submit helper + OK behavior -----
  function submitFrom(el){
    if (!el) return;

    // 1) explicit selector or function
    const sel   = el.getAttribute('data-submit');
    const fnStr = el.getAttribute('data-submit-fn');
    if (sel) {
      const btn = document.querySelector(sel);
      if (btn) { btn.click(); return; }
    }
    if (fnStr && typeof window[fnStr] === 'function') {
      try { window[fnStr](el); return; } catch(_) {}
    }

    // 2) submit enclosing form
    const form = el.form;
    if (form && typeof form.requestSubmit === 'function') { form.requestSubmit(); return; }
    if (form) {
      const fallback = form.querySelector('[type=submit], button:not([type=button])');
      if (fallback) { fallback.click(); return; }
    }

    // 3) fallback: default action in modal/popup
    const scope = el.closest('.modal-card, .popup-content') || document;
    const okBtn = scope.querySelector('[data-default-action], .action-button.add-button, [type=submit], #add-confirm, #move-confirm, #merge-confirm');
    if (okBtn) okBtn.click();
  }

  function handleOk(){
    if(!target) { hideDock(); return; }
    replaceNext = false;
    target.dispatchEvent(new Event("input",{bubbles:true}));
    target.dispatchEvent(new Event("change",{bubbles:true}));
    hideDock();                              
  }

  // --------------------------------------------

  dock.addEventListener("pointerdown",(e)=>{
    const btn = e.target.closest(".numpad-btn");
    if(!btn) return;
    e.preventDefault(); // keep focus on the input
    const k = btn.dataset.k;
    if(k==="del")    return handleDelete();
    if(k==="cancel") return handleCancel();
    if(k==="ok")     return handleOk();
    if(k===".")      return handleDot();
    if(/^\d$/.test(k)) return handleDigit(k);
  },{passive:false});

  document.addEventListener("focusin",(e)=>{
    if(isNumericInput(e.target)) setTarget(e.target);
    updateDisplay();
  });

  document.addEventListener("input",(e)=>{
    if(e.target===target) updateDisplay();
  });

  document.addEventListener("pointerdown",(evt)=>{
    if (dock.contains(evt.target)) return;
  
    const input = evt.target.closest("input,textarea");
    if (isNumericInput(input)) {
      // If they tap a numeric input again, treat it like a fresh entry
      setTarget(input);         // sets target and replaceNext = true
      updateDisplay();
      return;
    }
  
    hideDock();
  },{capture:true});
  

  document.addEventListener("keydown",(e)=>{
    if (e.key === "Enter" && !dock.classList.contains("numpad-hidden") && document.activeElement === target) {
      e.preventDefault();
      replaceNext = false;
      target.dispatchEvent(new Event("input",{bubbles:true}));
      target.dispatchEvent(new Event("change",{bubbles:true}));
      hideDock();                            
    }
    if (e.key === "Escape") hideDock();
  });

  document.addEventListener("DOMContentLoaded",()=>{
    document.body.appendChild(dock);
    displayEl = document.getElementById("__np_disp");
    updateDisplay();
  });
})();
