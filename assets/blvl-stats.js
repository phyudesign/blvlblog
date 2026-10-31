/* blvl blog — 조회수·댓글 (Supabase RPC) */
(function () {
  var API = "https://udfluclrwnnxlwfpmmim.supabase.co/rest/v1/rpc/";
  var KEY = "sb_publishable_UHUDDrIVjb_B2i81jmS_SA_rkOPGmLS";
  var EYE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5C6.5 5 2.7 9.2 1.5 12c1.2 2.8 5 7 10.5 7s9.3-4.2 10.5-7C21.3 9.2 17.5 5 12 5zm0 11.2A4.2 4.2 0 1 1 12 7.8a4.2 4.2 0 0 1 0 8.4zm0-6.6a2.4 2.4 0 1 0 0 4.8 2.4 2.4 0 0 0 0-4.8z"/></svg>';
  var BUBBLE = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H9l-5 4v-4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/></svg>';
  var MSG = {
    nickname_length: "닉네임은 2~20자로 적어 주세요.",
    password_length: "비밀번호는 4자 이상으로 적어 주세요.",
    body_length: "댓글은 2~1,000자로 적어 주세요.",
    reserved_nickname: "사용할 수 없는 닉네임이에요.",
    no_links: "링크나 웹 주소는 댓글에 넣을 수 없어요.",
    too_fast: "조금만 천천히! 30초 뒤에 다시 써 주세요.",
    daily_limit: "오늘 쓸 수 있는 댓글 수를 넘었어요.",
    duplicate: "같은 내용의 댓글이 이미 있어요.",
    wrong_password: "비밀번호가 맞지 않아요.",
    too_many_tries: "비밀번호를 너무 많이 틀렸어요. 1시간 뒤에 다시 시도해 주세요.",
    not_found: "이미 삭제된 댓글이에요."
  };

  function rpc(fn, body) {
    return fetch(API + fn, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: KEY, Authorization: "Bearer " + KEY },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok) { var e = new Error((j && j.message) || "error"); e.code = j && j.message; throw e; }
        return j;
      });
    });
  }
  function visitor() {
    var k = "blvl_vid", v = null;
    try { v = localStorage.getItem(k); } catch (e) {}
    if (!v) {
      v = "v" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      try { localStorage.setItem(k, v); } catch (e) {}
    }
    return v;
  }
  function fmt(n) { n = n || 0; return n >= 10000 ? (n / 10000).toFixed(1).replace(/\.0$/, "") + "만" : n.toLocaleString("ko-KR"); }
  function fill(el, s) {
    el.innerHTML = '<span class="ps-v" title="조회수">' + EYE + "조회 " + fmt(s && s.views) + "</span>" +
      '<span class="ps-c" title="댓글 수">' + BUBBLE + "댓글 " + fmt(s && s.comments) + "</span>";
    el.classList.add("ready");
  }
  function when(d) {
    var t = new Date(d), diff = (Date.now() - t) / 1000;
    if (diff < 60) return "방금";
    if (diff < 3600) return Math.floor(diff / 60) + "분 전";
    if (diff < 86400) return Math.floor(diff / 3600) + "시간 전";
    return t.getFullYear() + "." + (t.getMonth() + 1) + "." + t.getDate();
  }
  function text(tag, cls, s) { var e = document.createElement(tag); if (cls) e.className = cls; if (s != null) e.textContent = s; return e; }

  var stats = Array.prototype.slice.call(document.querySelectorAll(".pstat[data-slug]"));
  var hitEl = document.querySelector(".pstat[data-hit]");
  var counters = {};
  stats.forEach(function (el) { (counters[el.dataset.slug] = counters[el.dataset.slug] || []).push(el); });

  function updateCount(slug, s) { (counters[slug] || []).forEach(function (el) { fill(el, s); }); }

  if (hitEl) {
    rpc("blog_hit", { p_slug: hitEl.dataset.slug, p_visitor: visitor() })
      .then(function (s) { updateCount(hitEl.dataset.slug, s); })
      .catch(function () { hitEl.style.display = "none"; });
  }
  var others = Object.keys(counters).filter(function (s) { return !hitEl || s !== hitEl.dataset.slug; });
  if (others.length) {
    rpc("blog_stats", { p_slugs: others }).then(function (rows) {
      var m = {}; rows.forEach(function (r) { m[r.slug] = r; });
      others.forEach(function (s) { updateCount(s, m[s]); });
    }).catch(function () { stats.forEach(function (el) { if (el !== hitEl) el.style.display = "none"; }); });
  }

  /* 댓글 */
  var box = document.getElementById("comments");
  if (!box) return;
  var slug = box.dataset.slug, list = box.querySelector(".cm-list"), countEl = box.querySelector(".cm-count");
  var form = box.querySelector(".cm-form"), note = box.querySelector(".cm-note");

  function setCount(n) { countEl.textContent = n; }
  function render(c) {
    var li = text("li", "cm-item");
    var head = text("div", "cm-head");
    head.appendChild(text("b", "cm-nick", c.nickname));
    head.appendChild(text("span", "cm-time", when(c.created_at)));
    var del = text("button", "cm-del", "삭제"); del.type = "button";
    head.appendChild(del);
    li.appendChild(head);
    li.appendChild(text("p", "cm-body", c.body));
    var df = document.createElement("form"); df.className = "cm-delform"; df.hidden = true;
    var pw = document.createElement("input"); pw.type = "password"; pw.placeholder = "작성할 때 쓴 비밀번호"; pw.autocomplete = "off"; pw.required = true;
    var ok = text("button", "", "삭제하기"); ok.type = "submit";
    var cancel = text("button", "cm-cancel", "취소"); cancel.type = "button";
    var msg = text("span", "cm-delmsg", "");
    [pw, ok, cancel, msg].forEach(function (x) { df.appendChild(x); });
    li.appendChild(df);
    del.onclick = function () { df.hidden = !df.hidden; if (!df.hidden) pw.focus(); };
    cancel.onclick = function () { df.hidden = true; msg.textContent = ""; };
    df.onsubmit = function (e) {
      e.preventDefault(); ok.disabled = true; msg.textContent = "";
      rpc("blog_comment_delete", { p_id: c.id, p_password: pw.value }).then(function () {
        li.remove(); setCount(list.children.length);
        box.querySelector(".cm-empty").hidden = list.children.length > 0;
        refreshHitCount();
      }).catch(function (err) { msg.textContent = MSG[err.code] || "삭제하지 못했어요. 잠시 뒤 다시 시도해 주세요."; })
        .then(function () { ok.disabled = false; });
    };
    return li;
  }
  function refreshHitCount() {
    rpc("blog_stats", { p_slugs: [slug] }).then(function (rows) { updateCount(slug, rows[0]); }).catch(function () {});
  }
  function load() {
    rpc("blog_comments", { p_slug: slug }).then(function (rows) {
      list.innerHTML = ""; rows.forEach(function (c) { list.appendChild(render(c)); });
      setCount(rows.length);
      box.querySelector(".cm-empty").hidden = rows.length > 0;
    }).catch(function () { note.textContent = "댓글을 불러오지 못했어요."; });
  }
  form.onsubmit = function (e) {
    e.preventDefault();
    var f = form.elements, btn = form.querySelector("button[type=submit]");
    note.textContent = ""; note.className = "cm-note"; btn.disabled = true;
    try { localStorage.setItem("blvl_nick", f.nick.value.trim()); } catch (x) {}
    rpc("blog_comment_add", {
      p_slug: slug, p_nickname: f.nick.value, p_password: f.pw.value, p_body: f.body.value, p_trap: f.website.value
    }).then(function (c) {
      if (c && c.id) {
        list.appendChild(render(c)); setCount(list.children.length);
        box.querySelector(".cm-empty").hidden = true;
        refreshHitCount();
      }
      f.body.value = ""; note.textContent = "댓글이 등록됐어요."; note.className = "cm-note ok";
    }).catch(function (err) {
      note.textContent = MSG[err.code] || "댓글을 등록하지 못했어요. 잠시 뒤 다시 시도해 주세요."; note.className = "cm-note err";
    }).then(function () { btn.disabled = false; });
  };
  try { var saved = localStorage.getItem("blvl_nick"); if (saved) form.elements.nick.value = saved; } catch (x) {}
  load();
})();
