/* blvl blog — 홈 LIVE 슬라이드: 가운데 큰 카드, 양옆 카드가 살짝 보이고, 자동으로 넘어가며 손가락·마우스로 넘길 수 있음 */
(function () {
  var root = document.querySelector(".live-hero");
  if (!root) return;
  var stage = root.querySelector(".lh-stage"), slides = [].slice.call(root.querySelectorAll(".lh-slide"));
  var dots = [].slice.call(root.querySelectorAll(".lh-dots button")), n = slides.length;
  if (!n) return;
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var cur = 0, drag = 0, down = false, moved = false, sx = 0, sy = 0, lx = 0, lt = 0, v = 0, timer = 0, hover = false;
  function wrap(o) { var h = n / 2; o = ((o % n) + n) % n; return o > h ? o - n : o; }
  function layout(anim) {
    var w = slides[0].offsetWidth, gap = Math.max(16, w * 0.06);
    slides.forEach(function (s, i) {
      var o = n > 1 ? wrap(i - cur) : 0, x = o * (w + gap) + drag, a = Math.abs(o);
      var sc = a === 0 ? 1 : 0.86;
      s.style.transition = anim ? "" : "none";
      s.style.transform = "translateX(calc(-50% + " + x + "px)) scale(" + sc + ")";
      s.style.opacity = a > 2 ? 0 : a === 0 ? 1 : 0.55;
      s.style.zIndex = 10 - a;
      s.style.pointerEvents = a > 2 ? "none" : "";
      s.classList.toggle("on", a === 0);
      s.setAttribute("aria-hidden", a === 0 ? "false" : "true");
      s.tabIndex = a === 0 ? 0 : -1;
    });
    dots.forEach(function (d, i) { d.classList.toggle("on", i === cur); });
  }
  function go(i) { cur = ((i % n) + n) % n; drag = 0; layout(true); restart(); }
  function restart() {
    clearInterval(timer);
    if (reduce || n < 2) return;
    timer = setInterval(function () { if (!hover && !down && !document.hidden) go(cur + 1); }, 4500);
  }
  root.querySelector(".lh-prev").addEventListener("click", function () { go(cur - 1); });
  root.querySelector(".lh-next").addEventListener("click", function () { go(cur + 1); });
  dots.forEach(function (d, i) { d.addEventListener("click", function () { go(i); }); });
  root.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") hover = true; });
  root.addEventListener("pointerleave", function () { hover = false; });
  root.addEventListener("keydown", function (e) { if (e.key === "ArrowLeft") go(cur - 1); if (e.key === "ArrowRight") go(cur + 1); });

  stage.addEventListener("pointerdown", function (e) {
    if (e.button > 0) return;
    down = true; moved = false; sx = lx = e.clientX; sy = e.clientY; lt = e.timeStamp; v = 0;
  });
  stage.addEventListener("pointermove", function (e) {
    if (!down) return;
    var dx = e.clientX - sx;
    if (!moved && Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(e.clientY - sy)) {
      moved = true; root.classList.add("dragging");
      try { stage.setPointerCapture(e.pointerId); } catch (x) {}
    }
    if (moved) {
      var dt = Math.max(8, e.timeStamp - lt); v = (e.clientX - lx) / dt; lx = e.clientX; lt = e.timeStamp;
      drag = dx; layout(false);
    }
  });
  function end() {
    if (!down) return;
    down = false; root.classList.remove("dragging");
    if (!moved) return;
    var w = slides[0].offsetWidth, steps = Math.round(-drag / (w * 0.9));
    if (steps === 0 && Math.abs(v) > 0.35) steps = v < 0 ? 1 : -1;      // 휙 밀면 한 장 넘김
    if (steps === 0 && Math.abs(drag) > w * 0.18) steps = drag < 0 ? 1 : -1;
    go(cur + steps);
  }
  stage.addEventListener("pointerup", end);
  stage.addEventListener("pointercancel", end);
  stage.addEventListener("click", function (e) {
    var s = e.target.closest(".lh-slide");
    if (moved) { e.preventDefault(); moved = false; return; }
    if (s && !s.classList.contains("on")) { e.preventDefault(); go(slides.indexOf(s)); }  // 옆 카드를 누르면 가운데로
  }, true);
  stage.addEventListener("dragstart", function (e) { e.preventDefault(); });
  window.addEventListener("resize", function () { layout(false); });
  layout(false); requestAnimationFrame(function () { root.classList.add("ready"); });
  restart();
})();
