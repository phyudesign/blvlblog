/* blvl blog — 홈 STOCK LIVE 전광판: 자동으로 흐르고, 손가락·마우스로 끌어서 넘기기 */
(function () {
  var t = document.querySelector(".ticker");
  if (!t) return;
  var view = t.querySelector(".tk-view"), track = t.querySelector(".tk-track"), run = track.querySelector(".tk-run");
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  t.classList.add("js");
  var SPEED = reduce ? 0 : 48;          // 자동으로 흐르는 속도(px/초)
  var x = 0, v = 0, w = 0, down = false, hover = false, dragged = false;
  var startX = 0, lastX = 0, lastT = 0, prev = performance.now();

  function measure() { w = run.offsetWidth; }
  measure();
  window.addEventListener("resize", measure);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);

  function frame(now) {
    var dt = Math.min(0.05, (now - prev) / 1000); prev = now;
    if (!down) {
      if (Math.abs(v) > SPEED + 5) { x += v * dt; v *= Math.pow(0.03, dt); }   // 튕긴 뒤 서서히 감속
      else { v = 0; if (!hover) x += SPEED * dt; }
    }
    if (w) x = ((x % w) + w) % w;
    track.style.transform = "translate3d(" + (-x) + "px,0,0)";
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  view.addEventListener("pointerdown", function (e) {
    if (e.button > 0) return;
    down = true; dragged = false; v = 0;
    startX = lastX = e.clientX; lastT = e.timeStamp;
  });
  view.addEventListener("pointermove", function (e) {
    if (!down) return;
    var dx = e.clientX - lastX;
    if (!dragged && Math.abs(e.clientX - startX) > 6) {
      dragged = true; t.classList.add("dragging");
      try { view.setPointerCapture(e.pointerId); } catch (err) {}
    }
    if (dragged) {
      var dt = Math.max(0.008, (e.timeStamp - lastT) / 1000);
      x -= dx;
      v = Math.max(-5000, Math.min(5000, 0.75 * (-dx / dt) + 0.25 * v));
    }
    lastX = e.clientX; lastT = e.timeStamp;
  });
  function end(e) {
    if (!down) return;
    down = false; t.classList.remove("dragging");
    if (e.timeStamp - lastT > 90) v = 0;          // 멈췄다 놓으면 튕기지 않음
  }
  view.addEventListener("pointerup", end);
  view.addEventListener("pointercancel", end);
  view.addEventListener("click", function (e) { if (dragged) { e.preventDefault(); e.stopPropagation(); dragged = false; } }, true);
  view.addEventListener("dragstart", function (e) { e.preventDefault(); });
  t.addEventListener("pointerenter", function (e) { if (e.pointerType === "mouse") hover = true; });
  t.addEventListener("pointerleave", function () { hover = false; });
})();
