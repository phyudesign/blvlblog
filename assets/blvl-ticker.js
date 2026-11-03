/* 응모 판 탭 (일본·미국·국내): 누르면 빠르게 옆으로 밀려 넘어감 */
(function () {
  document.querySelectorAll(".inv-panel").forEach(function (p) {
    var tabs = [].slice.call(p.querySelectorAll(".ip-tabs button")), bar = p.querySelector(".ip-tabs");
    var order = tabs.map(function (b) { return b.dataset.t; }), cur = order[0];
    var ind = document.createElement("span"); ind.className = "ip-ind"; bar.insertBefore(ind, bar.firstChild);
    function moveInd(t) { var i = order.indexOf(t), b = tabs[i]; ind.style.width = b.offsetWidth + "px"; ind.style.transform = "translateX(" + b.offsetLeft + "px)"; }
    function pick(t, anim) {
      if (order.indexOf(t) < 0) return;
      var dir = order.indexOf(t) > order.indexOf(cur) ? 1 : -1, prev = cur; cur = t;
      tabs.forEach(function (b) { var on = b.dataset.t === t; b.classList.toggle("on", on); b.setAttribute("aria-selected", on); });
      moveInd(t);
      p.querySelectorAll(".ip-list").forEach(function (l) {
        var show = l.dataset.t === t;
        l.hidden = !show;
        l.classList.remove("ip-in-l", "ip-in-r");
        if (show && anim && prev !== t) { void l.offsetWidth; l.classList.add(dir > 0 ? "ip-in-r" : "ip-in-l"); l.scrollTop = 0; }
      });
    }
    tabs.forEach(function (b) { b.addEventListener("click", function () { pick(b.dataset.t, true); try { localStorage.setItem("blvl_ip_tab", b.dataset.t); } catch (e) {} }); });
    try { var saved = localStorage.getItem("blvl_ip_tab"); if (saved) pick(saved, false); } catch (e) {}
    moveInd(cur); requestAnimationFrame(function () { bar.classList.add("ready"); });
    window.addEventListener("resize", function () { moveInd(cur); });
  });
  // 좁은 화면: 오른쪽 아래 버튼으로 응모 판 열고 닫기
  var fab = document.querySelector(".inv-fab"), sheet = document.querySelector(".inv-float");
  if (fab && sheet) {
    function set(open) { sheet.classList.toggle("open", open); fab.classList.toggle("open", open); fab.setAttribute("aria-expanded", open); }
    fab.addEventListener("click", function (e) { e.stopPropagation(); set(!sheet.classList.contains("open")); });
    document.addEventListener("click", function (e) { if (sheet.classList.contains("open") && !sheet.contains(e.target)) set(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") set(false); });
  }
})();
/* blvl blog — 홈 LIVE 전광판
   · 자동으로 흐름 · 손가락/마우스로 끌기, 휙 밀면 속도만큼 날아가다 감속
   · 0.5초 누르고 있기(모바일) / 0.5초 올려두기(데스크톱) → 상품 미리보기 카드 */
(function () {
  var t = document.querySelector(".ticker");
  if (!t) return;
  var view = t.querySelector(".tk-view"), track = t.querySelector(".tk-track"), run = track.querySelector(".tk-run");
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  t.classList.add("js");

  var SPEED = reduce ? 0 : 48;     // 평소 흐르는 속도(px/초)
  var FRICTION = 0.14;             // 1초 뒤 남는 속도 비율 (작을수록 빨리 멈춤)
  var HOLD = 500;                  // 미리보기까지 누르는/올려두는 시간(ms)
  var x = 0, v = 0, w = 0, skew = 0, prev = performance.now();
  var down = false, dragged = false, previewing = false, hover = false;
  var startX = 0, startY = 0, lastX = 0, samples = [], holdTimer = 0, ptype = "";

  function measure() { w = run.offsetWidth; }
  measure();
  window.addEventListener("resize", measure);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);

  /* ── 움직임 */
  function frame(now) {
    var dt = Math.min(0.05, (now - prev) / 1000); prev = now;
    if (!down && !previewing) {
      if (Math.abs(v) > SPEED + 4) { x += v * dt; v *= Math.pow(FRICTION, dt); }
      else { v = 0; if (!hover) x += SPEED * dt; }
    }
    if (w) x = ((x % w) + w) % w;
    // 속도감: 빠를수록 글자가 진행 방향으로 기울었다가, 멈추면 탄력 있게 제자리로
    var target = down && dragged ? clamp(-curVel() / 520, -12, 12) : clamp(-v / 520, -12, 12);
    skew += (target - skew) * Math.min(1, dt * 14);
    track.style.transform = "translate3d(" + (-x) + "px,0,0) skewX(" + skew.toFixed(2) + "deg)";
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  function clamp(n, a, b) { return Math.max(a, Math.min(b, n)); }
  function curVel() {   // 최근 80ms 동안의 손가락 속도(px/초, 글자 진행 방향 기준)
    var now = performance.now(), s = samples.filter(function (p) { return now - p.t < 80; });
    if (s.length < 2) return 0;
    var a = s[0], b = s[s.length - 1];
    return b.t > a.t ? -(b.x - a.x) / ((b.t - a.t) / 1000) : 0;
  }

  /* ── 미리보기 카드 */
  var card = document.createElement("div");
  card.className = "tk-peek"; card.setAttribute("aria-hidden", "true");
  card.innerHTML = '<div class="tp-img"><img alt="" referrerpolicy="no-referrer"></div><div class="tp-txt"><b></b><span></span><em></em></div>';
  document.body.appendChild(card);
  var cImg = card.querySelector("img"), cName = card.querySelector("b"), cSub = card.querySelector("span"), cCta = card.querySelector("em");
  var cBox = card.querySelector(".tp-img");
  // 상품 사진이 없거나 못 불러오면 사진 칸 없이 글자만 보여 줌 (속보 그림으로 대신하지 않음)
  cImg.onerror = function () { cBox.hidden = true; };
  var shownItem = null, armed = null;

  function itemAt(cx, cy) {
    var el = document.elementFromPoint(cx, cy);
    return el && el.closest ? el.closest(".tk-item[data-name]") : null;
  }
  function show(item, cx) {
    if (!item) return;
    if (item !== shownItem) {
      shownItem = item;
      if (item.dataset.img) { cBox.hidden = false; cImg.src = item.dataset.img; }
      else { cBox.hidden = true; cImg.removeAttribute("src"); }
      cName.textContent = item.dataset.name || "";
      cSub.textContent = item.dataset.sub || "";
      cCta.textContent = (ptype === "touch" ? "짧게 탭하면 " : "클릭하면 ") + (item.dataset.cta || "열기");
    }
    var r = t.getBoundingClientRect(), cw = card.offsetWidth || 240;
    var left;
    if (ptype === "touch") {   // 손가락에 가리지 않게 손가락 오른쪽에, 자리가 없으면 왼쪽에
      left = cx + 44;
      if (left + cw > window.innerWidth - 8) left = cx - 44 - cw;
      left = clamp(left, 8, window.innerWidth - cw - 8);
    } else left = clamp(cx - cw / 2, 10, window.innerWidth - cw - 10);
    card.style.left = left + "px";
    card.style.top = (r.bottom + 10) + "px";
    card.classList.add("on");
    previewing = true;
  }
  function hide() { card.classList.remove("on"); previewing = false; shownItem = null; armed = null; }
  function arm(cx, cy) {
    clearTimeout(holdTimer);
    holdTimer = setTimeout(function () {
      var it = itemAt(cx, cy);
      if (it) { show(it, cx); if (navigator.vibrate && ptype === "touch") navigator.vibrate(8); }
    }, HOLD);
  }

  /* ── 손가락·마우스 */
  view.addEventListener("pointerdown", function (e) {
    if (e.button > 0) return;
    ptype = e.pointerType; down = true; dragged = false; v = 0;
    startX = lastX = e.clientX; startY = e.clientY; samples = [{ x: e.clientX, t: performance.now() }];
    if (ptype !== "mouse") arm(e.clientX, e.clientY); else hide();
  });
  view.addEventListener("pointermove", function (e) {
    if (!down) {   // 데스크톱 마우스 올려두기
      if (e.pointerType !== "mouse") return;
      ptype = "mouse";
      if (previewing) { var it = itemAt(e.clientX, e.clientY); if (it) show(it, e.clientX); else hide(); }
      else { var a = itemAt(e.clientX, e.clientY); if (a !== armed) { armed = a; if (a) arm(e.clientX, e.clientY); else clearTimeout(holdTimer); } }
      return;
    }
    if (previewing && ptype !== "mouse") {      // 누른 채로 옆 상품으로 옮기면 미리보기만 바뀜
      var it2 = itemAt(e.clientX, e.clientY); if (it2) show(it2, e.clientX);
      return;
    }
    var dx = e.clientX - lastX;
    if (!dragged && Math.abs(e.clientX - startX) > 6) {
      dragged = true; clearTimeout(holdTimer); hide(); t.classList.add("dragging");
      try { view.setPointerCapture(e.pointerId); } catch (err) {}
    }
    if (dragged) x -= dx;
    lastX = e.clientX;
    samples.push({ x: e.clientX, t: performance.now() }); if (samples.length > 12) samples.shift();
  });
  function end(e) {
    clearTimeout(holdTimer);
    if (!down) return;
    down = false; t.classList.remove("dragging");
    if (dragged) v = clamp(curVel() * 1.15, -12000, 12000);   // 휙 민 속도 그대로 날려 보내기
    if (previewing && ptype !== "mouse") { hide(); dragged = true; }   // 미리보기 후 손 떼면 링크 열지 않음
  }
  view.addEventListener("pointerup", end);
  view.addEventListener("pointercancel", function (e) { end(e); hide(); });
  view.addEventListener("click", function (e) { if (dragged) { e.preventDefault(); e.stopPropagation(); dragged = false; } }, true);
  view.addEventListener("dragstart", function (e) { e.preventDefault(); });
  view.addEventListener("contextmenu", function (e) { e.preventDefault(); });
  t.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") hover = true; });
  t.addEventListener("pointerleave", function (e) { if (e.pointerType === "mouse") { hover = false; clearTimeout(holdTimer); hide(); } });
  window.addEventListener("scroll", function () { if (previewing && !down) hide(); }, { passive: true });
})();

/* 사이드바 칸을 문서 끝(바닥글 직전)까지 늘려, 스크롤 끝에서도 응모 판 머리가 전광판에 가리지 않게 */
(function () {
  var sb = document.querySelector(".sidebar .inside-right-sidebar");
  if (!sb) return;
  var busy = false;
  function fit() {
    if (busy) return; busy = true;
    sb.style.setProperty("--sb-ext", "0px");
    var r = sb.getBoundingClientRect(), f = document.querySelector(".site-footer");
    var end = f ? f.getBoundingClientRect().top : document.documentElement.scrollHeight - window.scrollY;
    sb.style.setProperty("--sb-ext", Math.max(0, Math.round(end - r.bottom - 16)) + "px");
    busy = false;
  }
  window.addEventListener("load", fit); window.addEventListener("resize", fit);
  if (window.ResizeObserver) { var c = document.querySelector(".site-content"); if (c) new ResizeObserver(function () { requestAnimationFrame(fit); }).observe(c); }
  fit();
})();
/* 넓은 화면 홈: 응모 판 윗선을 Featured 첫 썸네일과 맞추고, 스크롤하면 위로 따라 올라가 화면 위쪽에 붙음 */
(function () {
  var f = document.querySelector(".inv-float"), a = document.querySelector(".feat .gimg") || document.querySelector(".lgrid .gimg");
  if (!f || !a) return;
  function place() {
    if (innerWidth < 1660) { f.style.top = ""; f.style.maxHeight = ""; return; }
    var t = Math.max(20, a.getBoundingClientRect().top);
    f.style.top = t + "px"; f.style.maxHeight = (innerHeight - t - 20) + "px";
  }
  addEventListener("scroll", place, { passive: true }); addEventListener("resize", place); addEventListener("load", place); place();
})();
