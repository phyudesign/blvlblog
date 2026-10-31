# -*- coding: utf-8 -*-
"""blvl 재고·추첨 감시기 (GitHub Actions에서 10분마다 실행)

1) 라쿠텐북스: 포켓몬카드·원피스카드 상품을 상품 단위로 읽어 '주문 불가 → 구매/예약 가능'으로 바뀌면 알림
2) 추첨·공지 페이지: 포켓몬카드·원피스카드 관련 '새 줄'이 생기면 알림 (요도바시 추첨, 트레카플라자55, 옐로서브마린, 세븐넷)
알림: 텔레그램(설정된 경우) + 블로그 속보 글 자동 게시(같은 상품은 24시간 안에 다시 쓰지 않고 기존 글에 기록 추가)
상태 파일: _monitor/state.json  /  현황판: _pages/stock.html → /stock/

예의: 실행마다 각 페이지를 한 번씩만, 요청 사이 3초 쉬고, 사이트가 막으면 그 사이트는 건너뜀
"""
import os, re, json, time, html, hashlib, datetime, pathlib, urllib.parse, requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
MON = ROOT / "_monitor"; MON.mkdir(exist_ok=True)
STATE = MON / "state.json"
KST = datetime.timezone(datetime.timedelta(hours=9))
NOW = datetime.datetime.now(KST)
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 blvlblog-stock-check (+https://blvlblog.com/stock/)",
      "Accept-Language": "ja,en;q=0.8"}
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")
WATCH_WORDS = ["ポケモンカード", "ポケカ", "ONE PIECEカード", "ワンピースカード", "ONE PIECE カード"]
BOX_WORDS = ["BOX", "ボックス", "パック", "カートン", "デッキ", "セット"]
SKIP_WORDS = ["スリーブ", "シールド", "ケース", "ラバープレイマット", "プレイマット", "ローダー", "ファイル", "電子書籍"]

RAKUTEN = [
    ("ポケモンカード", "https://books.rakuten.co.jp/search?sitem=" + urllib.parse.quote("ポケモンカードゲーム") + "&g=006"),
    ("ポケモンカード", "https://books.rakuten.co.jp/search?sitem=" + urllib.parse.quote("ポケモンカードゲーム") + "&g=006&p=2"),
    ("ワンピースカード", "https://books.rakuten.co.jp/search?sitem=" + urllib.parse.quote("ONE PIECEカードゲーム") + "&g=006"),
]
PAGES = [  # 추첨·공지 페이지: 관련 '새 줄' 감지
    ("yodobashi", "요도바시 추첨", "https://limited.yodobashi.com/"),
    ("torecaplaza55", "트레카플라자55", "https://torecaplaza55.com/"),
    ("yellowsub", "옐로서브마린", "https://yellowsubmarine.co.jp/"),
    ("7net_pk", "세븐넷", "https://7net.omni7.jp/search/?keyword=" + urllib.parse.quote("ポケモンカードゲーム")),
    ("7net_op", "세븐넷", "https://7net.omni7.jp/search/?keyword=" + urllib.parse.quote("ONE PIECEカードゲーム")),
]
SHOP_KR = {"rakuten": "라쿠텐북스", "yodobashi": "요도바시", "torecaplaza55": "트레카플라자55", "yellowsub": "옐로서브마린", "7net_pk": "세븐넷", "7net_op": "세븐넷"}

def get(url):
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.status_code != 200: print("skip", r.status_code, url[:80]); return None
        return r.text
    except Exception as e:
        print("skip", type(e).__name__, url[:80]); return None
    finally:
        time.sleep(3)

def text_of(h): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()

def relevant(t):
    return any(w in t for w in WATCH_WORDS) and any(w in t for w in BOX_WORDS) and not any(w in t for w in SKIP_WORDS)

# ── 라쿠텐북스: 상품 블록 단위 파싱
def scan_rakuten(h):
    items = {}
    for blk in re.split(r'<div class="rbcomp__item-list__item(?:\s|")', h)[1:]:
        m = re.search(r'<a[^>]+href="(https://books\.rakuten\.co\.jp/rb/(\d+)/)[^"]*"[^>]*>(.*?)</a>', blk, re.S)
        if not m: continue
        url, rid, title = m.group(1), m.group(2), text_of(m.group(3))
        if not title or not relevant(title): continue
        body = text_of(blk)
        if "ご注文できない商品" in body: st = "out"
        elif re.search(r"予約する|予約受付中", body): st = "preorder"
        elif re.search(r"買い物\s*かごに入れる|かごに入れる", body): st = "instock"
        else: st = "unknown"
        pm = re.search(r"([\d,]{3,})円", body)
        items["rakuten:" + rid] = {"shop": "rakuten", "title": title, "url": url, "status": st, "price": pm.group(1) + "엔" if pm else ""}
    return items

# ── 추첨·공지 페이지: 관련 키워드가 들어간 짧은 줄 목록
def scan_lines(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    parts = re.split(r"<(?:br|/p|/li|/h\d|/a|/td|/div|/dt|/dd)[^>]*>", h)
    out = {}
    for p in parts:
        t = text_of(p)
        if 6 <= len(t) <= 160 and any(w in t for w in WATCH_WORDS) and not any(w in t for w in SKIP_WORDS):
            out[hashlib.md5(t.encode()).hexdigest()[:12]] = t
    return out

def telegram(msg):
    if not TG_TOKEN: return
    chat = TG_CHAT
    if not chat:
        try:
            ups = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", timeout=20).json().get("result", [])
            chats = [u.get("message", {}).get("chat", {}).get("id") for u in ups if u.get("message")]
            chat = str(chats[-1]) if chats else ""
        except Exception: chat = ""
    if not chat: print("텔레그램: 채팅방을 찾지 못했어요. 봇에게 /start 를 보내 주세요."); return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      json={"chat_id": chat, "text": msg, "disable_web_page_preview": True}, timeout=20)
    except Exception as e: print("텔레그램 실패", e)

STATUS_KR = {"instock": "구매 가능", "preorder": "예약 접수 중", "out": "주문 불가", "unknown": "확인 필요", "new": "새 공지"}

def slugify(s): return re.sub(r"[^0-9A-Za-z가-힣ぁ-んァ-ヶ一-龠ー]+", "-", s)[:40].strip("-")

def emo(n, line, alt):
    return (f'<div class="emo"><img src="/wp-content/uploads/emoticons/gyomyo/{n}.webp" alt="교묘 이모티콘 {alt}" width="120" height="120" loading="lazy">'
            f'<div class="bubble"><b>미친고양이 교묘</b>{line}</div></div>\n')

def write_alert_post(ev, state):
    """같은 키로 24시간 안에 쓴 글이 있으면 기록만 추가, 없으면 새 글"""
    key = ev["key"]; posts = state.setdefault("posts", {})
    stamp = NOW.strftime("%Y-%m-%d %H:%M")
    row = f'<li><b>{stamp}</b> · {html.escape(ev["shop_kr"])} · {html.escape(STATUS_KR.get(ev["status"], ev["status"]))}{(" · " + html.escape(ev["price"])) if ev.get("price") else ""}</li>'
    prev = posts.get(key)
    if prev and (NOW - datetime.datetime.fromisoformat(prev["at"])).total_seconds() < 86400:
        p = ROOT / "_posts" / prev["file"]
        if p.exists():
            s = p.read_text(encoding="utf-8")
            s = s.replace("<ol class=\"stock-log\">", "<ol class=\"stock-log\">" + row, 1)
            s = re.sub(r'"mod": "[^"]+"', f'"mod": "{NOW.strftime("%Y-%m-%d %H:%M:%S")}"', s, 1)
            p.write_text(s, encoding="utf-8"); return prev["file"]
    is_lottery = ev["kind"] == "page"
    name = ev["title"]
    title = (f'[입고 속보] {name[:60]} — {ev["shop_kr"]} {STATUS_KR.get(ev["status"], "")}' if not is_lottery
             else f'[추첨·판매 속보] {ev["shop_kr"]} — {name[:60]}')
    slug = f'속보-{NOW.strftime("%Y%m%d-%H%M")}-{slugify(ev["shop_kr"])}-{hashlib.md5(key.encode()).hexdigest()[:6]}'
    korea = {"라쿠텐북스": "라쿠텐북스는 일본 배송지가 필요해요. 배송대행지 주소로 주문하는 방법은 아래 가이드 글을 참고하세요.",
             "세븐넷": "세븐넷은 일본 배송지가 필요해요.", "요도바시": "요도바시는 일본 배송지가 필요해요.",
             "트레카플라자55": "일본 카드 전문점이라 일본 배송지가 필요해요.", "옐로서브마린": "일본 카드 전문점이라 일본 배송지가 필요해요."}.get(ev["shop_kr"], "")
    fm = {"title": title, "slug": slug, "date": NOW.strftime("%Y-%m-%d %H:%M:%S"), "mod": NOW.strftime("%Y-%m-%d %H:%M:%S"),
          "desc": f'{ev["shop_kr"]}에서 {name[:50]} 상태가 바뀌었어요({STATUS_KR.get(ev["status"], "")}). 감지 시각 {stamp} (한국 시간).',
          "thumb": "/wp-content/uploads/2026/10/blvl-stock-alert.jpg", "category": "tcg",
          "tags": ["입고 속보", "일본 쇼핑몰", ev["shop_kr"]]}
    body = f'''<p><strong>{html.escape(ev["shop_kr"])}</strong>에서 아래 상품의 상태가 바뀐 걸 blvl 재고 감시기가 잡았어요. 재고는 몇 분 만에 끝나는 경우가 많으니 <strong>링크에서 바로 확인</strong>하세요.</p>
{emo("rare", "떴다냥! 지금 바로 확인하라냥!!!", "레어다")}
<table><tbody>
<tr><th>상품</th><td>{html.escape(name)}</td></tr>
<tr><th>쇼핑몰</th><td>{html.escape(ev["shop_kr"])}</td></tr>
<tr><th>상태</th><td><strong>{html.escape(STATUS_KR.get(ev["status"], ""))}</strong></td></tr>
{f'<tr><th>가격</th><td>{html.escape(ev["price"])}</td></tr>' if ev.get("price") else ''}
<tr><th>감지 시각</th><td>{stamp} (한국 시간)</td></tr>
<tr><th>바로가기</th><td><a href="{html.escape(ev["url"])}" target="_blank" rel="nofollow noopener">{html.escape(ev["shop_kr"])} 페이지 열기</a></td></tr>
</tbody></table>
<h2>한국에서 살 수 있을까?</h2>
<p>{korea} 쇼핑몰별 응모·구매 조건은 <a href="/일본-카드-쇼핑몰-추첨-총정리/">일본 카드 쇼핑몰 추첨 총정리</a>, 아마존 응모는 <a href="/아마존-응모-포켓몬카드-원피스카드/">아마존 응모 총정리</a>를 참고하세요.</p>
<h2>감지 기록</h2>
<ol class="stock-log">{row}</ol>
<p>지금 다른 쇼핑몰 상태는 <a href="/stock/">재고 현황판</a>에서 볼 수 있어요.</p>
{emo("price-check", "이 글은 감시기가 자동으로 쓴 속보다냥. 품절됐어도 원망은 하지 말라냥…", "시세보는중")}
<p style="font-size:14px;color:#666">※ blvl 재고 감시기가 쇼핑몰 공개 페이지를 약 10분 간격으로 확인해 자동으로 작성한 속보예요. 실제 재고·가격·응모 조건은 쇼핑몰 페이지가 기준이에요. 이 글의 링크는 제휴 링크가 아니에요.</p>
'''
    (ROOT / "_posts" / f"{slug}.html").write_text("<!--\n" + json.dumps(fm, ensure_ascii=False, indent=1) + "\n-->\n" + body, encoding="utf-8")
    posts[key] = {"file": f"{slug}.html", "at": NOW.isoformat()}
    return f"{slug}.html"

def write_board(state):
    rows = []
    for k, v in sorted(state.get("items", {}).items(), key=lambda kv: (kv[1]["status"] not in ("instock", "preorder"), kv[1]["title"])):
        if v["status"] == "out": continue
        rows.append(f'<tr><td><a href="{html.escape(v["url"])}" target="_blank" rel="nofollow noopener">{html.escape(v["title"][:70])}</a></td>'
                    f'<td>{SHOP_KR.get(v["shop"], v["shop"])}</td><td><strong>{STATUS_KR.get(v["status"], v["status"])}</strong></td><td>{html.escape(v.get("price", ""))}</td><td>{v.get("since", "")}</td></tr>')
    ev_rows = "".join(f'<li><b>{e["at"]}</b> · {html.escape(e["shop_kr"])} · {html.escape(e["title"][:70])} → {STATUS_KR.get(e["status"], e["status"])}</li>' for e in state.get("events", [])[:30])
    body = f'''<p>blvl 재고 감시기가 일본 쇼핑몰 공개 페이지를 <strong>약 10분 간격</strong>으로 확인해서, 포켓몬카드·원피스카드 상품을 <strong>지금 살 수 있거나 예약할 수 있는 곳</strong>을 모아 보여 줘요. 마지막으로 바뀐 시각: <strong>{NOW.strftime("%Y-%m-%d %H:%M")}</strong> (한국 시간)</p>
<h2>지금 구매·예약 가능</h2>
{('<table><thead><tr><th>상품</th><th>쇼핑몰</th><th>상태</th><th>가격</th><th>감지</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table>') if rows else '<p>지금은 감시 중인 쇼핑몰에 구매 가능한 상품이 없어요. 들어오면 이곳과 속보 글로 바로 알려 드릴게요.</p>'}
<h2>최근 감지 기록</h2>
<ol>{ev_rows or "<li>아직 기록이 없어요.</li>"}</ol>
<h2>감시 중인 곳</h2>
<ul><li>라쿠텐북스 (상품별 재고·예약 상태)</li><li>요도바시 추첨 페이지 · 세븐넷 · 트레카플라자55 · 옐로서브마린 (새 판매·추첨 공지)</li></ul>
<p>포켓몬센터 온라인과 아마존은 자동 확인이 막혀 있어서 여기엔 나오지 않아요. 아마존 응모는 <a href="/아마존-응모-포켓몬카드-원피스카드/">아마존 응모 총정리</a>를 참고하세요.</p>
<p style="font-size:14px;color:#666">※ 자동 감시 결과라 실제 재고·가격은 각 쇼핑몰 페이지가 기준이에요.</p>
'''
    fm = {"title": "일본 쇼핑몰 재고 현황판", "slug": "stock", "desc": "포켓몬카드·원피스카드를 지금 살 수 있는 일본 쇼핑몰을 약 10분 간격으로 확인해 보여 주는 재고 현황판이에요.", "updated": NOW.strftime("%Y년 %m월 %d일 %H:%M")}
    (ROOT / "_pages" / "stock.html").write_text("<!--\n" + json.dumps(fm, ensure_ascii=False, indent=1) + "\n-->\n" + body, encoding="utf-8")

def main():
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    first_run = not state
    items = state.setdefault("items", {}); lines = state.setdefault("lines", {}); events = state.setdefault("events", [])
    new_events = []
    # 라쿠텐
    seen = {}; status_changed = []
    for _, url in RAKUTEN:
        h = get(url)
        if h: seen.update(scan_rakuten(h))
    for k, v in seen.items():
        old = items.get(k)
        avail = v["status"] in ("instock", "preorder")
        was = old and old["status"] in ("instock", "preorder")
        v["since"] = old.get("since", "") if (old and old["status"] == v["status"]) else NOW.strftime("%m/%d %H:%M")
        if (not old) or old["status"] != v["status"]: status_changed.append(k)
        if avail and not was and not first_run:
            new_events.append({"key": k, "kind": "item", "shop_kr": "라쿠텐북스", "title": v["title"], "url": v["url"], "status": v["status"], "price": v.get("price", "")})
        items[k] = v
    # 추첨·공지 페이지
    for sid, name, url in PAGES:
        h = get(url)
        if not h: continue
        cur = scan_lines(h); prev = lines.get(sid)
        if prev is not None and not first_run:
            for hid, t in cur.items():
                if hid not in prev:
                    new_events.append({"key": f"{sid}:{hid}", "kind": "page", "shop_kr": name, "title": t, "url": url, "status": "new", "price": ""})
        lines[sid] = list(cur.keys())
    # 알림 + 글
    changed = bool(new_events) or bool(status_changed) or first_run
    for ev in new_events[:8]:  # 한 번에 너무 많이 쓰지 않도록
        f = write_alert_post(ev, state)
        events.insert(0, {"at": NOW.strftime("%m/%d %H:%M"), "shop_kr": ev["shop_kr"], "title": ev["title"], "status": ev["status"]})
        telegram(f'🐱 blvl 재고 속보\n{ev["shop_kr"]} · {STATUS_KR.get(ev["status"], "")}\n{ev["title"][:80]}\n{ev.get("price","")}\n{ev["url"]}\n블로그: https://blvlblog.com/{urllib.parse.quote(f[:-5])}/')
        print("EVENT", ev["shop_kr"], ev["status"], ev["title"][:60])
    state["events"] = events[:100]
    if changed:
        write_board(state)
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"items={len(items)} pages={len(lines)} new_events={len(new_events)} first_run={first_run}")
    (MON / "changed").write_text("1" if changed else "0")

if __name__ == "__main__":
    main()
