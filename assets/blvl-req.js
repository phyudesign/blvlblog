/* 아마존 초대 요청 "신청했어요" 표시
   방문자가 직접 눌러 두는 체크예요. 이 브라우저(localStorage)에만 저장되고 어디로도 보내지 않아요. */
(() => {
  const K = "blvl_req", KF = "blvl_req_todo";
  let S;
  try { S = new Set(JSON.parse(localStorage.getItem(K) || "[]")); } catch (e) { S = new Set(); }
  let todo = false;
  try { todo = localStorage.getItem(KF) === "1"; } catch (e) {}
  const save = () => { try { localStorage.setItem(K, JSON.stringify([...S])); } catch (e) {} };
  const asinOf = h => { const m = /amazon\.[a-z.]+\/(?:[^/?#]+\/)?(?:dp|gp\/product)\/([A-Z0-9]{10})/i.exec(h || ""); return m ? m[1].toUpperCase() : ""; };

  const mkBtn = (id, mini) => {
    const b = document.createElement("button");
    b.type = "button"; b.className = "req-btn" + (mini ? " mini" : ""); b.dataset.asin = id;
    return b;
  };

  function decorate() {
    // 응모 판(사이드바·떠 있는 판·LIVE 현황판): 상품 줄마다 체크 버튼
    document.querySelectorAll(".inv-panel a[href*='amazon.']").forEach(a => {
      if (a.dataset.reqd) return;
      const id = asinOf(a.href); if (!id) return;
      a.dataset.reqd = "1";
      if (a.parentElement.classList.contains("ip-chips")) {
        const w = document.createElement("span"); w.className = "req-chip"; w.dataset.asin = id;
        a.replaceWith(w); w.append(a, mkBtn(id, true));
      } else {
        const li = a.closest("li"); li.classList.add("req-row"); li.dataset.asin = id;
        a.after(mkBtn(id));
      }
    });
    // 아마존 응모 속보 글 본문의 "아마존에서 초대 요청하기" 링크 옆
    document.querySelectorAll(".entry-content a[href*='amazon.']").forEach(a => {
      if (a.dataset.reqd || !/초대\s*요청/.test(a.textContent)) return;
      const id = asinOf(a.href); if (!id) return;
      a.dataset.reqd = "1"; a.after(mkBtn(id, false));
      a.nextSibling.classList.add("big");
    });
    // 응모 판 머리에 "안 한 것만" 거르기
    document.querySelectorAll(".inv-panel .ip-head").forEach(h => {
      if (h.querySelector(".req-filter")) return;
      const f = document.createElement("button"); f.type = "button"; f.className = "req-filter";
      h.append(f);
    });
  }

  function paint() {
    document.querySelectorAll("[data-asin]").forEach(el => {
      if (el.classList.contains("tk-item")) return;
      el.classList.toggle("req-on", S.has(el.dataset.asin));
    });
    document.querySelectorAll(".req-btn").forEach(b => {
      const on = S.has(b.dataset.asin);
      b.setAttribute("aria-pressed", on);
      b.textContent = b.classList.contains("mini") ? (on ? "✓" : "") : (on ? "✓ 신청함" : "신청했어요");
      b.title = on ? "신청 표시 지우기" : "아마존에서 초대 요청했으면 눌러 두세요 (이 브라우저에만 저장돼요)";
      b.setAttribute("aria-label", on ? "신청함 표시 지우기" : "신청했어요로 표시");
    });
    document.querySelectorAll(".req-filter").forEach(f => {
      f.setAttribute("aria-pressed", todo);
      f.textContent = todo ? "✓ 안 한 것만 보는 중" : "안 한 것만 보기";
    });
    document.querySelectorAll(".inv-panel").forEach(p => p.classList.toggle("req-todo", todo));
    // 묶음 줄: 전부 신청했으면 줄도 숨김 대상
    document.querySelectorAll(".inv-panel .ip-group").forEach(g => {
      const c = g.querySelectorAll(".req-chip"); if (!c.length) return;
      g.classList.toggle("req-on", [...c].every(x => x.classList.contains("req-on")));
    });
  }

  document.addEventListener("click", e => {
    const b = e.target.closest(".req-btn, .req-filter"); if (!b) return;
    e.preventDefault(); e.stopPropagation();
    if (b.classList.contains("req-filter")) {
      todo = !todo; try { localStorage.setItem(KF, todo ? "1" : "0"); } catch (err) {}
    } else {
      const id = b.dataset.asin; S.has(id) ? S.delete(id) : S.add(id); save();
    }
    paint();
  }, true);
  window.addEventListener("storage", e => { if (e.key === K) { try { S = new Set(JSON.parse(e.newValue || "[]")); } catch (err) {} paint(); } });

  const run = () => { decorate(); paint(); };
  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", run) : run();
})();
