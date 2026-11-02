/* 모바일 전체화면 메뉴: 1단계 큰 메뉴 → 하위 메뉴로 밀려 들어감, 위쪽 뒤로가기 (apple.com 방식) */
(function () {
  var m = document.getElementById("mnav"), btn = document.querySelector(".menu-toggle");
  if (!m || !btn) return;
  var back = m.querySelector(".mn-back"), root = m.querySelector(".mn-root"), cur = null;
  function open() {
    m.hidden = false; document.documentElement.classList.add("mn-lock");
    requestAnimationFrame(function () { m.classList.add("on"); });
    btn.setAttribute("aria-expanded", "true"); showRoot(true);
  }
  function close() {
    m.classList.remove("on"); btn.setAttribute("aria-expanded", "false");
    document.documentElement.classList.remove("mn-lock");
    setTimeout(function () { if (!m.classList.contains("on")) m.hidden = true; }, 280);
  }
  function showRoot(instant) {
    if (cur) { cur.classList.remove("in"); var c = cur; setTimeout(function () { c.hidden = true; }, instant ? 0 : 300); cur = null; }
    root.classList.remove("out"); back.hidden = true;
  }
  function showSub(id) {
    var p = m.querySelector('.mn-sub[data-p="' + id + '"]'); if (!p) return;
    p.hidden = false; void p.offsetWidth; p.classList.add("in"); root.classList.add("out"); cur = p; back.hidden = false;
  }
  btn.addEventListener("click", function () { m.classList.contains("on") ? close() : open(); });
  m.querySelector(".mn-close").addEventListener("click", close);
  back.addEventListener("click", function () { showRoot(false); });
  m.querySelectorAll("[data-go]").forEach(function (b) { b.addEventListener("click", function () { showSub(b.dataset.go); }); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && m.classList.contains("on")) close(); });
  window.addEventListener("resize", function () { if (innerWidth > 768 && m.classList.contains("on")) close(); });
})();
