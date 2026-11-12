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
SKIP_WORDS = ["余福", "オリパ", "ブロパ", "福袋", "訳アリ", "スリーブ", "シールド", "ケース", "ラバープレイマット", "プレイマット", "ローダー", "ファイル", "電子書籍"]

RAKUTEN = [
    ("ポケモンカード", "https://books.rakuten.co.jp/search?sitem=" + urllib.parse.quote("ポケモンカードゲーム") + "&g=006"),
    ("ポケモンカード", "https://books.rakuten.co.jp/search?sitem=" + urllib.parse.quote("ポケモンカードゲーム") + "&g=006&p=2"),
    ("ワンピースカード", "https://books.rakuten.co.jp/search?sitem=" + urllib.parse.quote("ONE PIECEカードゲーム") + "&g=006"),
]
PAGES = [  # 추첨·공지 페이지: 관련 '새 줄' 감지
    ("yodobashi", "요도바시 추첨", "https://limited.yodobashi.com/"),
    # 트레카플라자55는 상품 목록이라 아래 scan_shoppro로 상품별 재고를 봄 (2026-11-04)
    ("yellowsub", "옐로서브마린", "https://yellowsubmarine.co.jp/"),
    # 세븐넷 검색 결과는 진열 순서가 바뀔 때마다 옛 상품이 '새 줄'로 잡혀서 제외 (2026-11-01)
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
# ── 트레카플라자55 (shop-pro 쇼핑몰): 첫 화면 새 상품 목록을 상품 단위로 (상품 주소·사진·가격·품절)
SHOPPRO = [("torecaplaza55", "트레카플라자55", "https://torecaplaza55.com/")]
def scan_shoppro(h, shop, base):
    items = {}
    for blk in re.split(r'<li class="c-item-list__item"', h)[1:]:
        tm = re.search(r'c-item-list__ttl">\s*<a href="\?pid=(\d+)"[^>]*>(.*?)</a>', blk, re.S)
        if not tm: continue
        pid, title = tm.group(1), text_of(tm.group(2))
        if not title or not relevant(title): continue
        im = re.search(r'<img src="(https://img\d*\.shop-pro\.jp/[^"]+)"', blk)
        pm = re.findall(r'c-item-list__price(?![^"]*strikethrough)[^"]*">\s*([\d,]+)円', blk)
        st = "out" if "is-soldout" in blk or "SOLD OUT" in blk else "instock"
        items[f"{shop}:{pid}"] = {"shop": shop, "title": title, "url": f"{base}?pid={pid}", "status": st,
                                  "price": (pm[-1] + "엔") if pm else "", "img": im.group(1) if im else ""}
    return items

def scan_rakuten(h):
    items = {}
    for blk in re.split(r'<div class="rbcomp__item-list__item"', h)[1:]:
        tm = re.search(r'class="rbcomp__item-list__item__title[^"]*">(.*?)</span>', blk, re.S)
        lm = re.search(r'href="(https://books\.rakuten\.co\.jp/rb/(\d+)/)', blk)
        if not tm or not lm: continue
        title = text_of(tm.group(1)); url, rid = lm.group(1), lm.group(2)
        if not title or not relevant(title): continue
        body = text_of(blk)
        if "ご注文できない商品" in body: st = "out"
        elif re.search(r"予約する|予約受付中", body): st = "preorder"
        elif re.search(r"買い物\s*かごに入れる|かごに入れる", body): st = "instock"
        else: st = "unknown"
        pm = re.search(r"([\d,]{3,})円", body)
        im = (re.search(r'<img[^>]+?(?:data-src|data-original|src)="((?:https:)?//[^"]*(?:thumbnail\.image\.rakuten|r10s)[^"]*)"', blk)
              or re.search(r'(?:data-src|data-original|src)="((?:https:)?//[^"]+\.(?:jpe?g|png|webp|gif)[^"]*)"', blk))
        items["rakuten:" + rid] = {"shop": "rakuten", "title": title, "url": url, "status": st, "price": pm.group(1) + "엔" if pm else "",
                                  "img": ("https:" + html.unescape(im.group(1)) if im.group(1).startswith("//") else html.unescape(im.group(1))) if im else ""}
    return items

# ── 추첨·공지 페이지: 관련 키워드가 들어간 짧은 줄 목록
def scan_lines(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    parts = re.split(r"<(?:br|/p|/li|/h\d|/a|/td|/div|/dt|/dd)[^>]*>", h)
    out = {}
    for p in parts:
        t = text_of(p)
        if 6 <= len(t) <= 160 and relevant(t):
            out[hashlib.md5(t.encode()).hexdigest()[:12]] = t
    return out

TG_FILE = MON / "tg_chat"   # 한 번 찾은 대화방 번호를 저장 (토큰 없이는 쓸모없는 숫자)
TG_NEW = False

def tg_chat():
    global TG_NEW
    if TG_CHAT: return TG_CHAT
    if TG_FILE.exists() and TG_FILE.read_text().strip(): return TG_FILE.read_text().strip()
    try:
        ups = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", timeout=20).json().get("result", [])
        chats = [u.get("message", {}).get("chat", {}).get("id") for u in ups if u.get("message")]
        if chats:
            TG_FILE.write_text(str(chats[-1])); TG_NEW = True
            return str(chats[-1])
    except Exception: pass
    return ""

def heal_alert_thumbs(state, hours=72):
    """최근 속보 중 공용 표지(blvl-stock-alert.jpg)를 쓰는 글을 교묘 속보 표지로 바꿔요. 바꾼 개수를 돌려줘요."""
    try:
        from alertcard import make_alert_thumb_emo
    except Exception as e:
        print("속보 표지 도구 없음", e); return 0
    cut = (NOW - datetime.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S"); n = 0
    for f in sorted((ROOT / "_posts").glob("속보-*.html"), reverse=True)[:30]:
        s = f.read_text(encoding="utf-8")
        m = re.search(r"<!--\s*(\{.*?\})\s*-->", s, re.S)
        if not m: continue
        fm = json.loads(m.group(1))
        if fm.get("date", "") < cut or not fm.get("thumb", "").endswith("blvl-stock-alert.jpg"): continue
        title = fm.get("title", "")
        kind = ("invite" if title.startswith("[아마존 응모]") else "krnews" if title.startswith("[국내판") else
                "lottery" if ("추첨" in title or "응모 소식" in title) else "stock")
        pimg = re.sub(r"downsize=\d+", "downsize=600", fm.get("pimg", "") or "")
        if not pimg:
            t = title.replace(" ", "")
            for a_, nm, _b, grp in INVITE_JP + INVITE_US:
                kw = re.match(r"(OP-\d+|EB-\d+|PRB-\d+|\S+)", nm).group(1)
                if not grp and len(kw) >= 3 and kw in t and (ROOT / "assets" / "products" / f"{a_}.webp").exists():
                    pimg = str(ROOT / "assets" / "products" / f"{a_}.webp"); break
        rel = f'wp-content/uploads/{fm["date"][:4]}/{fm["date"][5:7]}/blvl-alert-{hashlib.md5(f.name.encode()).hexdigest()[:8]}.jpg'
        emo_used, k = make_alert_thumb_emo(kind, pimg, ROOT / rel, state.get("alert_emo_last", ""), state.get("alert_bg_last", ""))
        if not k: continue
        state["alert_bg_last"] = k; state["alert_emo_last"] = emo_used
        f.write_text(s.replace(f'"thumb": "{fm["thumb"]}"', f'"thumb": "/{rel}"', 1), encoding="utf-8"); n += 1
        print("속보 표지 교체:", f.name, k)
    return n

TG_QUEUE = []
TG_QUEUE_FILE = ROOT / "_monitor" / "tg_queue.json"

def telegram(msg):
    """보낸 결과를 문자열로 돌려줌: ok / no_token / no_chat / 오류"""
    if not TG_TOKEN: return "no_token"
    chat = tg_chat()
    if not chat: print("텔레그램: 채팅방을 찾지 못했어요. 봇에게 /start 를 보내 주세요."); return "no_chat"
    try:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                          json={"chat_id": chat, "text": msg, "disable_web_page_preview": True}, timeout=20)
        return "ok" if r.ok else f"error {r.status_code} {r.json().get('description','')}"
    except Exception as e: print("텔레그램 실패", e); return f"error {e}"

KR_NAMES = [("ポケモンカードゲーム", "포켓몬카드"), ("スカーレット＆バイオレット", "스칼렛&바이올렛"), ("スカーレット&バイオレット", "스칼렛&바이올렛"),
    ("スターターデッキ＆ビルドセット", "스타터 덱&빌드 세트"), ("スターターデッキ", "스타터 덱"), ("古代のコライドン", "고대의 코라이돈"), ("未来のミライドン", "미래의 미라이돈"),
    ("強化拡張パック", "강화 확장팩"),
    ("キモリ", "나무지기"), ("アチャモ", "아차모"), ("ミズゴロウ", "물짱이"), ("ツタージャ", "주리비얀"), ("ポカブ", "뚜꾸리"), ("ミジュマル", "수댕이"), ("ハリマロン", "도치마론"), ("フォッコ", "푸호꼬"), ("ケロマツ", "개구마르"), ("モクロー", "나몰빼미"), ("ニャビー", "냐오불"), ("アシマリ", "누리공"), ("サルノリ", "흥나숭"), ("ヒバニー", "염버니"), ("メッソン", "울머기"), ("ニャオハ", "나오하"), ("ホゲータ", "뜨아거"), ("クワッス", "꾸왁스"), ("フシギダネ", "이상해씨"), ("ヒトカゲ", "파이리"), ("ゼニガメ", "꼬부기"), ("チコリータ", "치코리타"), ("ヒノアラシ", "브케인"), ("ワニノコ", "리아코"), ("バトルコレクション", "배틀 컬렉션"), ("スタートデッキ100", "스타트 덱 100"), ("「", ""), ("」", ""), ("ONE PIECEカードゲーム", "원피스카드"), ("ハドウシーカー", "파동시커"), ("30th CELEBRATION", "30주년"),
    ("ストームエメラルダ", "스톰 에메랄드"), ("ムニキスゼロ", "니힐제로"), ("インフェルノX", "인페르노X"), ("メガブレイブ", "메가브레이브"),
    ("メガシンフォニア", "메가심포니아"), ("アビスアイ", "어비스아이"), ("ニンジャスピナー", "닌자스피너"), ("MEGAドリームex", "메가드림EX"),
    ("エーフィ・ブラッキー", "에브이·블래키"), ("拡張パック", "확장팩"), ("ハイクラスパック", "하이클래스팩"), ("ブースターパック", "부스터팩"),
    ("プレミアムデッキセット", "프리미엄 덱 세트"), ("カードセット", "카드 세트"), ("スタートデッキ", "스타트 덱"), ("【セット商品】", ""),
    ("【クレジットカード決済限定】", ""), ("神の支配", "신의 지배"), ("世界最強の戦士", "세계 최강의 전사"), ("パック", "팩")]
def kr(t):
    for a, b in KR_NAMES: t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()

STATUS_KR = {"krnews": "국내판 공지", "invite": "아마존 응모(초대 요청) 접수 중", "instock": "구매 가능", "preorder": "예약 접수 중", "out": "주문 불가", "unknown": "판매 대기(추첨 전용)", "new": "새 공지"}

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
    is_amazon = ev["status"] == "invite" and ("아마존" in ev.get("shop_kr", "") or "amazon" in ev.get("url", ""))
    name = ev["title"]; kname = kr(name)
    is_krnews = ev["status"] == "krnews"
    title = (f'[국내판 속보] {name[:80]}' if is_krnews else
             f'[아마존 응모] {kname[:60]} — 초대 요청 접수 중' if is_amazon and not is_lottery
             else f'[아마존 응모 소식] {kname[:70]}' if is_amazon
             else f'[입고 속보] {kname[:60]} — {ev["shop_kr"]} {STATUS_KR.get(ev["status"], "")}' if not is_lottery
             else f'[추첨·판매 속보] {ev["shop_kr"]} — {kname[:60]}')
    slug = f'속보-{NOW.strftime("%Y%m%d-%H%M")}-{slugify(ev["shop_kr"])}-{hashlib.md5(key.encode()).hexdigest()[:6]}'
    korea = {"라쿠텐북스": "라쿠텐북스는 일본 배송지가 필요해요. 배송대행지 주소로 주문하는 방법은 아래 가이드 글을 참고하세요.",
             "세븐넷": "세븐넷은 일본 배송지가 필요해요.", "요도바시": "요도바시는 일본 배송지가 필요해요.",
             "트레카플라자55": "일본 카드 전문점이라 일본 배송지가 필요해요.", "옐로서브마린": "일본 카드 전문점이라 일본 배송지가 필요해요.",
             "포켓몬코리아": "국내판은 포켓몬코리아 공지에 나온 응모 방법과 일정을 따르면 돼요. 한국 주소로 바로 받을 수 있어요.",
             "포켓몬카드 공식": "국내판은 포켓몬카드 공식 사이트 공지에 나온 방법과 일정을 따르면 돼요. 한국 주소로 바로 받을 수 있어요.",
             "아마존 재팬": "아마존 재팬 초대 판매는 상품 페이지에서 '초대 요청'을 눌러 두면, 재고가 풀릴 때 추첨으로 초대 메일이 와요. 메일을 받은 사람만 정해진 시간 안에 정가로 살 수 있어요. 일본 배송지가 필요해요."}.get(ev["shop_kr"], "")
    fm = {"title": title, "slug": slug, "date": NOW.strftime("%Y-%m-%d %H:%M:%S"), "mod": NOW.strftime("%Y-%m-%d %H:%M:%S"),
          "desc": f'{ev["shop_kr"]}에서 {kname[:50]} 상태가 바뀌었어요({STATUS_KR.get(ev["status"], "")}). 감지 시각 {stamp} (한국 시간).',
          "thumb": "/wp-content/uploads/2026/10/blvl-stock-alert.jpg", "category": "news",
          "tags": ["입고 속보", "일본 쇼핑몰", ev["shop_kr"]], "pimg": ev.get("img", ""), "shop_url": ev["url"],
          "shop_kr": ev["shop_kr"], "status_kr": STATUS_KR.get(ev["status"], ""), "price": ev.get("price", "")}
    # 속보 표지: 매번 다른 포즈의 교묘 배경 + 실제 상품 사진 (alertcard.py)
    try:
        from alertcard import make_alert_thumb_emo
        kind = "invite" if is_amazon else "krnews" if is_krnews else "lottery" if is_lottery else "stock"
        pimg = re.sub(r"downsize=\d+", "downsize=600", ev.get("img", "") or "")
        if not pimg:   # 상품 사진이 없으면 응모 목록 상품 이름으로 박스 누끼를 찾아요
            t = kname.replace(" ", "")
            for a_, nm, _b, grp in INVITE_JP + INVITE_US:
                kw = re.match(r"(OP-\d+|EB-\d+|PRB-\d+|\S+)", nm).group(1)
                if not grp and len(kw) >= 3 and kw in t and (ROOT / "assets" / "products" / f"{a_}.webp").exists():
                    pimg = str(ROOT / "assets" / "products" / f"{a_}.webp"); break
        rel = f'wp-content/uploads/{NOW.strftime("%Y/%m")}/blvl-alert-{hashlib.md5((key + stamp).encode()).hexdigest()[:8]}.jpg'
        emo_used, k = make_alert_thumb_emo(kind, pimg, ROOT / rel, state.get("alert_emo_last", ""), state.get("alert_bg_last", ""))
        if k: fm["thumb"] = "/" + rel; state["alert_bg_last"] = k; state["alert_emo_last"] = emo_used
    except Exception as e:
        print("속보 표지 실패", e)
    lead = (f'<strong>아마존 재팬</strong>에서 아래 상품의 <strong>초대 요청(응모)</strong>이 열린 걸 blvl 감시기가 잡았어요. 초대 요청은 빨리 눌러 둘수록 좋으니 <strong>링크에서 바로 눌러 두세요.</strong>' if is_amazon else
            f'<strong>{html.escape(ev["shop_kr"])}</strong>에서 아래 상품의 상태가 바뀐 걸 blvl 재고 감시기가 잡았어요. 재고는 몇 분 만에 끝나는 경우가 많으니 <strong>링크에서 바로 확인</strong>하세요.')
    body = f'''<p>{lead}</p>
{emo("rare", "떴다냥! 지금 바로 확인하라냥!!!", "레어다")}
<table><tbody>
<tr><th>상품</th><td><strong>{html.escape(kname)}</strong><br><small style="color:#8a8f99">{html.escape(name)}</small></td></tr>
<tr><th>쇼핑몰</th><td>{html.escape(ev["shop_kr"])}</td></tr>
<tr><th>상태</th><td><strong>{html.escape(STATUS_KR.get(ev["status"], ""))}</strong></td></tr>
{f'<tr><th>가격</th><td>{html.escape(ev["price"])}</td></tr>' if ev.get("price") else ''}
<tr><th>감지 시각</th><td>{stamp} (한국 시간)</td></tr>
<tr><th>바로가기</th><td><a href="{html.escape(ev["url"])}" target="_blank" rel="nofollow noopener">{"아마존에서 초대 요청하기" if is_amazon and not is_lottery else html.escape(ev["shop_kr"]) + " 페이지 열기" if not is_lottery or not is_amazon else "기사 열기"}</a></td></tr>
{f'<tr><th>소식 출처</th><td><a href="{html.escape(ev["srcurl"])}" target="_blank" rel="nofollow noopener">{html.escape(ev["src"])}</a></td></tr>' if ev.get("srcurl") else ''}
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

# ── 아마존 응모(초대 요청) 상품 찾기
# 아마존은 직접 열면 로봇 확인 화면이 떠서, 일본 정보·뉴스 사이트가 소개한 '아마존 초대 판매' 링크를 모아요.
INVITE_SOURCES = [  # (id, 출처 이름, 주소, 종류)
    ("gp_pokeca", "게임피디아", "https://premium.gamepedia.jp/pokeca/feed/", "feed"),
    ("gp_toreca", "게임피디아", "https://premium.gamepedia.jp/toreca/feed/", "feed"),
    ("dengeki_pk", "전격온라인", "https://dengekionline.com/article/202608/83452", "page"),
    ("famitsu_pk", "패미통", "https://www.famitsu.com/article/202606/77986", "page"),
]
NEWS_FEEDS = [  # 새 '아마존 초대 판매' 기사 제목 감지 (구글 뉴스 검색 RSS)
    ("gnews_pk", "https://news.google.com/rss/search?q=" + urllib.parse.quote("Amazon 招待 ポケモンカード") + "&hl=ja&gl=JP&ceid=JP:ja"),
    ("gnews_op", "https://news.google.com/rss/search?q=" + urllib.parse.quote("Amazon 招待 ワンピースカード") + "&hl=ja&gl=JP&ceid=JP:ja"),
]
CARD_WORDS = ["ポケモン", "ポケカ", "ワンピース", "ONE PIECE", "30th", "MEGA"]
# 이미 확인해 둔 응모 상품 (2026-10-31 아마존에서 직접 확인)
INVITE_SEED = {
    "B0H4PQ6LR5": ("포켓몬카드 확장팩 파동시커 BOX", "6,006엔"), "B0GXCRBL5J": ("포켓몬카드 30th CELEBRATION BOX", "7,216엔"),
    "B0GXCYMRGL": ("포켓몬카드 30th 스타팅 세트", "1,200엔"), "B0GXCM4BCZ": ("포켓몬카드 에브이·블래키 덱 세트", "6,201엔"),
    "B0GP928YDZ": ("포켓몬카드 스톰 에메랄드 BOX", "6,006엔"), "B0FLCWJ1VK": ("포켓몬카드 메가드림EX BOX", "5,500엔"),
    "B0FSJXSPPX": ("포켓몬카드 니힐제로 BOX", "5,412엔"), "B0F9KJGGZ5": ("포켓몬카드 인페르노X BOX", "5,412엔"),
    "B0F18J2CJF": ("포켓몬카드 메가브레이브 BOX", "5,412엔"), "B0F189YH8W": ("포켓몬카드 메가심포니아 BOX", "5,412엔"),
    "B0HFVPJF4Q": ("원피스카드 OP-18 BOX", "5,782엔"), "B0HB3JQ6P4": ("원피스카드 EB-05 BOX", "5,782엔"),
}

# 아마존 응모 판에 보여 줄 목록 (위가 최신). 2026-11-02 TCG 브레이커 응모 목록 순서를 참고해 정리.
# (ASIN, 이름, 브랜드, 묶음)
INVITE_JP = [
    ("B0H4PQ6LR5", "파동시커 BOX", "포켓몬", ""),
    ("B0HFVPJF4Q", "OP-18 신의 지배 BOX", "원피스", ""),
    ("B0FX7X71KK", "OP-13 이어지는 의지 BOX", "원피스", ""),
    ("B0FJ7Z6RML", "EB-03 히로인즈 에디션 BOX", "원피스", ""),
    ("B0HB3JQ6P4", "EB-05 히로인즈 에디션 vol.2 BOX", "원피스", ""),
    ("B0GP928YDZ", "스톰 에메랄드 BOX", "포켓몬", ""),
    ("B0H43ZX8LK", "OP-17 세계 최강의 전사 BOX", "원피스", ""),
    ("B0GXCRBL5J", "30th CELEBRATION BOX", "포켓몬", ""),
    ("B0GXCM4BCZ", "30주년 에브이·블래키 덱 세트", "포켓몬", ""),
    ("B0GXCYMRGL", "1세대", "포켓몬", "30주년 스타팅 세트"), ("B0GXCC7W7Q", "2세대", "포켓몬", "30주년 스타팅 세트"),
    ("B0GXCX36HP", "3세대", "포켓몬", "30주년 스타팅 세트"), ("B0GXCX46KQ", "4세대", "포켓몬", "30주년 스타팅 세트"),
    ("B0GXCZ1VDC", "5세대", "포켓몬", "30주년 스타팅 세트"), ("B0GXCSGX8Y", "6세대", "포켓몬", "30주년 스타팅 세트"),
    ("B0GXCPF84C", "7세대", "포켓몬", "30주년 스타팅 세트"), ("B0GXCTRZ8L", "8세대", "포켓몬", "30주년 스타팅 세트"),
    ("B0GXCT83HB", "9세대", "포켓몬", "30주년 스타팅 세트"),
    ("B0GP9JJ4B7", "이브이 ex", "포켓몬", "스타터 세트 ex"), ("B0GP9FPZJH", "조로아·조로아크 ex", "포켓몬", "스타터 세트 ex"),
    ("B0GP9QQ1JG", "나오하·마스카나 ex", "포켓몬", "스타터 세트 ex"),
    ("B0GTTJ9X7C", "EB01 SD건담 G제네레이션 BOX", "건담", ""),
    ("B0G6J9VPN2", "ST-30 스타트 덱", "원피스", ""),
    ("B0G2VKBZML", "OP-15 BOX", "원피스", ""),
    ("B0GN5JV7JS", "OP-16 결전의 순간 BOX", "원피스", ""),
    ("B0GP9QHQ3Y", "어비스아이 BOX", "포켓몬", ""),
    ("B0G1XB2STM", "닌자스피너 BOX", "포켓몬", ""),
    ("B0FSJXSPPX", "니힐제로 BOX", "포켓몬", ""),
    ("B0FLCWJ1VK", "메가드림EX BOX", "포켓몬", ""),
    ("B0FLD7HMRP", "스타트 덱 100 배틀 컬렉션", "포켓몬", ""),
    ("B0F9KJGGZ5", "인페르노X BOX", "포켓몬", ""),
    ("B0F18J2CJF", "메가브레이브 BOX", "포켓몬", ""),
    ("B0F189YH8W", "메가심포니아 BOX", "포켓몬", ""),
    ("B0DP4586RV", "블랙볼트 BOX", "포켓몬", ""),
    ("B0D86FVG5R", "테라스탈 페스타 ex BOX", "포켓몬", ""),
    ("B0DKHFYGQM", "열풍의 아레나 BOX", "포켓몬", ""),
    ("B0D2WX4CYJ", "초전브레이커 BOX", "포켓몬", ""),
    ("B0D2WX2M3W", "낙원의 드라고나 BOX", "포켓몬", ""),
    ("B0DB56CSM6", "마리의 모르페코·오롱털 ex", "포켓몬", "스타터 세트 ex (SV)"),
    ("B0DB59JY2P", "성호의 덤벨·메타그로스 ex", "포켓몬", "스타터 세트 ex (SV)"),
    ("B0DB7VC4K5", "릴리에", "포켓몬", "컬렉션 파일 세트"), ("B0DB7KGQ22", "N", "포켓몬", "컬렉션 파일 세트"),
]
# 상품 사진 (아마존 상품 페이지 대표 이미지 주소, 2026-11-02 확인) — 홈 슬라이드·미리보기 카드 배경
AMZ_IMG = {
    "B0HPRX138T": "71I7EZSM4DL",
    "B0H4PQ6LR5": "715oCiYpb-L", "B0HFVPJF4Q": "61FmZOBIZlL", "B0FX7X71KK": "81tO30I8gwL", "B0FJ7Z6RML": "61X1xcYYFCL",
    "B0HB3JQ6P4": "61UK9XZctYL", "B0GP928YDZ": "715FaccxhwL", "B0H43ZX8LK": "61DEiJm305L", "B0GXCRBL5J": "711dPI8FndL",
    "B0GXCM4BCZ": "71RQY+K9JzL", "B0GTTJ9X7C": "81t2d6CS0eL", "B0G6J9VPN2": "91LyJj+6BZL", "B0G2VKBZML": "61EvBG8mJ-L",
    "B0GN5JV7JS": "61-i71CoRtL",
}
def amz_img(asin, size=800):
    k = AMZ_IMG.get(asin)
    return f"https://m.media-amazon.com/images/I/{k}._AC_SL{size}_.jpg" if k else ""

INVITE_US = [  # 아마존 미국 (amazon.com) — 직접 확인된 초대 판매만
    ("B0H78BB9TY", "30th Celebration 엘리트 트레이너 박스", "포켓몬", ""),
]
US_PRICE = {"B0H78BB9TY": "정가 $49.99"}
INVITE_INFO = {a: (n, "", g) for a, n, b, g in INVITE_JP}   # 예전 코드 호환

def invite_list(state, region="jp"):
    """응모 판 목록: [(asin, 이름, 가격, 브랜드, 묶음, NEW, 링크)] — 감시기가 새로 찾은 상품을 맨 위에"""
    inv = state.get("amazon", {})
    base = INVITE_JP if region == "jp" else INVITE_US
    host = "https://www.amazon.co.jp/dp/" if region == "jp" else "https://www.amazon.com/dp/"
    known = {a for a, *_ in INVITE_JP + INVITE_US}
    rows = []
    if region == "jp":   # 감시기가 새로 찾은 상품 (최근 것부터)
        for a, v in sorted(inv.items(), key=lambda kv: kv[1]["first"], reverse=True):
            if a in known or v["first"] <= "2026-11-02": continue
            nm = kr(v["name"]); brand = "원피스" if "원피스" in nm else "포켓몬"
            rows.append((a, nm.replace("포켓몬카드 ", "").replace("원피스카드 ", ""), v.get("price", ""), brand, "", True, host + a))
    for i, (a, n, b, g) in enumerate(base):
        price = (inv.get(a) or {}).get("price", "") if region == "jp" else US_PRICE.get(a, "")
        rows.append((a, n, price, b, g, i == 0 and not rows, host + a))
    return rows

def _heading_before(h, pos):
    hs = list(re.finditer(r"<h[2-4][^>]*>(.*?)</h[2-4]>", h[max(0, pos - 6000):pos], re.S))
    return text_of(hs[-1].group(1)) if hs else ""

def find_invites(h, fallback_title=""):
    """페이지(또는 피드 글) 안에서 '초대 판매'로 소개된 아마존 상품 링크를 찾아 {ASIN: (이름, 가격)}"""
    out = {}; seg = 0; last_end = 0; last_asin = ""
    for m in re.finditer(r'href="[^"]*amazon\.co\.jp[^"]*?/(?:dp|gp/product)/([A-Z0-9]{10})', h):
        asin = m.group(1)
        if asin != last_asin: seg = last_end          # 다른 상품 링크가 끝난 뒤부터만 봄 (같은 상품의 사진·버튼 링크는 이어서)
        last_end, last_asin = m.end(), asin
        start = max(seg, m.start() - 1500)
        if asin[0].isdigit() or asin in out: continue          # 숫자로 시작하는 건 책
        raw = h[start:m.start()]
        raw = raw[:raw.rfind("<")] if raw.rfind("<") > raw.rfind(">") else raw   # 링크 태그 앞부분(속성)은 버림
        ctx = text_of(raw)
        if "招待" not in ctx and not ("抽選" in ctx and "当選メール" in ctx): continue
        name = _heading_before(h, m.start()) or fallback_title
        if not name:
            pt = re.search(r"<title>(.*?)</title>", h, re.S); name = text_of(pt.group(1)) if pt else ""
        if not any(w in (name + ctx + fallback_title) for w in CARD_WORDS): continue
        pm = re.findall(r"招待販売価格】\s*([\d,]+)円", ctx)
        out[asin] = (re.sub(r"\s+", " ", name).strip()[:90], pm[-1] + "엔" if pm else "")
    return out

def scan_amazon(state, first_run):
    inv = state.setdefault("amazon", {}); news = state.setdefault("anews", [])
    seed = not inv
    if seed:
        for i, (a, (n, pr)) in enumerate(INVITE_SEED.items()):
            inv[a] = {"name": n, "price": pr, "first": "2026-10-31", "last": NOW.strftime("%Y-%m-%d"), "src": "blvl 확인", "srcurl": "", "ord": i}
    found = {}
    for sid, sname, url, kind in INVITE_SOURCES:
        h = get(url)
        if not h: continue
        if kind == "feed":
            for it in re.findall(r"<item>(.*?)</item>", h, re.S):
                ti = re.search(r"<title>(.*?)</title>", it, re.S); ln = re.search(r"<link>(.*?)</link>", it, re.S)
                body = html.unescape(it)
                for a, v in find_invites(body, text_of(html.unescape(ti.group(1))) if ti else "").items():
                    found.setdefault(a, (v, sname, ln.group(1).strip() if ln else url))
        else:
            for a, v in find_invites(h).items():
                found.setdefault(a, (v, sname, url))
    events = []
    for a, ((name, price), sname, surl) in found.items():
        if a not in inv and (a in INVITE_INFO or any(a == x[0] for x in INVITE_US)):   # 응모 판에 이미 있는 상품은 조용히 기록만
            inv[a] = {"name": name, "price": price, "first": "2026-10-31", "last": NOW.strftime("%Y-%m-%d"), "src": sname, "srcurl": surl, "ord": 500}
        if a in inv:
            inv[a]["last"] = NOW.strftime("%Y-%m-%d")
            if price and not inv[a].get("price"): inv[a]["price"] = price
            continue
        inv[a] = {"name": name, "price": price, "first": "2026-10-31" if seed else NOW.strftime("%Y-%m-%d"),   # 처음 모을 때 찾은 건 '새 응모'가 아님
                  "last": NOW.strftime("%Y-%m-%d"), "src": sname, "srcurl": surl, "ord": 100 + len(inv)}
        if not seed:
            events.append({"key": "amazon:" + a, "kind": "amazon", "shop_kr": "아마존 재팬", "title": name, "url": f"https://www.amazon.co.jp/dp/{a}",
                           "status": "invite", "price": price, "src": sname, "srcurl": surl})
    # 새 기사 제목: 상품 링크를 못 찾았어도 '아마존 초대 판매' 새 기사는 알림
    fresh_news = not news
    for nid, url in NEWS_FEEDS:
        h = get(url)
        if not h: continue
        for it in re.findall(r"<item>(.*?)</item>", h, re.S)[:20]:
            ti = text_of(html.unescape((re.search(r"<title>(.*?)</title>", it, re.S) or [None, ""])[1] or ""))
            ln = (re.search(r"<link>(.*?)</link>", it, re.S) or [None, ""])[1].strip()
            gid = hashlib.md5(ti.encode()).hexdigest()[:12]
            if gid in news: continue
            news.insert(0, gid)
            if fresh_news or "招待" not in ti or not any(w in ti for w in CARD_WORDS): continue
            pub = (re.search(r"<pubDate>(.*?)</pubDate>", it) or [None, ""])[1]
            try:
                if (NOW - datetime.datetime.strptime(pub[:25], "%a, %d %b %Y %H:%M:%S").replace(tzinfo=datetime.timezone.utc)).total_seconds() > 3 * 86400: continue
            except Exception: pass
            events.append({"key": "anews:" + gid, "kind": "page", "shop_kr": "아마존 재팬", "title": ti, "url": ln, "status": "invite", "price": ""})
    state["anews"] = news[:500]
    # 60일 동안 어디에도 다시 안 나온 상품은 목록에서 정리
    for a in [a for a, v in inv.items() if (NOW.date() - datetime.date.fromisoformat(v["last"])).days > 60]:
        inv.pop(a)
    return events, seed or bool(found)

def amazon_table(state):
    out = []
    for region, label in (("jp", "일본 아마존 (amazon.co.jp)"), ("us", "미국 아마존 (amazon.com)")):
        rows = "".join(f'<tr><td>{b} · {html.escape((g + " ") if g else "")}{html.escape(n)}{" <strong style=\"color:#e8362d\">NEW</strong>" if new else ""}</td>'
                       f'<td>{html.escape(pr)}</td><td><a href="{l}" target="_blank" rel="nofollow noopener">초대 요청하기</a></td></tr>'
                       for a, n, pr, b, g, new, l in invite_list(state, region))
        out.append(f'<h3>{label}</h3><table><thead><tr><th>상품</th><th>가격</th><th>응모</th></tr></thead><tbody>{rows}</tbody></table>')
    return "".join(out) + ('<p style="font-size:14px;color:#666">※ 아마존은 자동 확인이 막혀 있어 응모가 이미 끝난 상품이 섞여 있을 수 있어요. '
                           '새 응모 상품은 감시기가 일본 정보·뉴스 사이트에서 찾으면 맨 위에 NEW로 추가돼요.</p>')

# ── 국내판: 포켓몬코리아·포켓몬카드 공식 홈 첫 화면의 공지 링크에서 추첨·응모·판매 소식
KR_SOURCES = [("pokemonkorea", "포켓몬코리아", "https://pokemonkorea.co.kr/", r'href="((?:https://(?:www\.)?pokemonkorea\.co\.kr)?/news/2/\d+)"'),
              ("pokemoncard", "포켓몬카드 공식", "https://pokemoncard.co.kr/main", r'href="((?:https://pokemoncard\.co\.kr)?/(?:news|card|event)/\d+[^"]*)"')]
KR_WORDS = ["추첨", "응모", "판매", "발매", "예약", "입고", "재판매", "한정", "출시", "BOX", "박스", "확장팩"]

def scan_kr(state):
    kr_s = state.setdefault("kr", {}); seed = not kr_s; events = []
    for sid, sname, url, pat in KR_SOURCES:
        h = get(url)
        if not h: continue
        for m in re.finditer(r'<a[^>]+' + pat[5:] + r'[^>]*>(.*?)</a>', h, re.S):
            link = m.group(1); title = text_of(m.group(2))
            if link.startswith("/"): link = re.match(r"https://[^/]+", url).group(0) + link
            if not title or len(title) < 6 or not any(w in title for w in KR_WORDS): continue
            dm = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", title)
            posted = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}" if dm else NOW.strftime("%Y-%m-%d")
            title = re.sub(r"\s*(카드 게임|게임)?\s*\d{4}년\s*\d{1,2}월\s*\d{1,2}일.*$", "", title)
            title = re.sub(r"^(NEW|HOT)\s+", "", re.sub(r"\s+", " ", title)).strip()[:120]
            if link in kr_s:
                kr_s[link]["last"] = NOW.strftime("%Y-%m-%d"); continue
            kr_s[link] = {"title": title, "src": sname, "first": NOW.strftime("%Y-%m-%d"), "posted": posted, "last": NOW.strftime("%Y-%m-%d")}
            if not seed:
                events.append({"key": "kr:" + link, "kind": "page", "shop_kr": sname, "title": title, "url": link, "status": "krnews", "price": ""})
    for link, v in kr_s.items():   # 공지 대표 이미지 (본문 첫 사진)
        if v.get("img") or v.get("img_try", 0) >= 6: continue
        v["img_try"] = v.get("img_try", 0) + 1
        try: ph = requests.get(link, headers=UA, timeout=30).text   # 포켓몬코리아 공지는 내용이 있어도 500을 돌려줌
        except Exception: ph = ""
        time.sleep(2)
        im = re.search(r'<img[^>]+src="([^"]*s3\.php\?key=[^"]*(?:newdata|20[2-9]\d)%2F[^"]*)"', ph or "")   # 본문 첫 사진
        v["img"] = html.unescape(im.group(1)) if im else ""
        if v["img"].startswith("/"): v["img"] = re.match(r"https://[^/]+", link).group(0) + v["img"]
    for k in [k for k, v in kr_s.items() if (NOW.date() - datetime.date.fromisoformat(v["last"])).days > 45]: kr_s.pop(k)
    return events, seed

def write_board(state):
    rows = []
    for k, v in sorted(state.get("items", {}).items(), key=lambda kv: (kv[1]["status"] not in ("instock", "preorder"), kv[1]["title"])):
        if v["status"] not in ("instock", "preorder"): continue
        rows.append(f'<tr><td><a href="{html.escape(v["url"])}" target="_blank" rel="nofollow noopener">{html.escape(kr(v["title"])[:70])}</a></td>'
                    f'<td>{SHOP_KR.get(v["shop"], v["shop"])}</td><td><strong>{STATUS_KR.get(v["status"], v["status"])}</strong></td><td>{html.escape(v.get("price", ""))}</td><td>{v.get("since", "")}</td></tr>')
    ev_rows = "".join(f'<li><b>{e["at"]}</b> · {html.escape(e["shop_kr"])} · {html.escape(kr(e["title"])[:70])} → {STATUS_KR.get(e["status"], e["status"])}</li>' for e in state.get("events", [])[:30])
    body = f'''<p>blvl 재고 감시기가 일본 쇼핑몰 공개 페이지를 <strong>약 10분 간격</strong>으로 확인해서, 포켓몬카드·원피스카드 상품을 <strong>지금 살 수 있거나 예약할 수 있는 곳</strong>을 모아 보여 줘요. 마지막으로 바뀐 시각: <strong>{NOW.strftime("%Y-%m-%d %H:%M")}</strong> (한국 시간)</p>
<h2>지금 구매·예약 가능</h2>
{('<table><thead><tr><th>상품</th><th>쇼핑몰</th><th>상태</th><th>가격</th><th>감지</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table>') if rows else '<p>지금은 감시 중인 쇼핑몰에 구매 가능한 상품이 없어요. 들어오면 이곳과 속보 글로 바로 알려 드릴게요.</p>'}
<h2>아마존 재팬 응모(초대 요청) 상품</h2>
<p>아마존 재팬의 포켓몬카드·원피스카드는 <strong>초대 판매</strong>예요. 상품 페이지에서 '초대 요청'을 눌러 두면 재고가 풀릴 때 추첨으로 초대 메일이 오고, 메일을 받은 사람만 정가로 살 수 있어요. 일본 정보·뉴스 사이트에 소개된 초대 판매 링크를 모았어요.</p>
{amazon_table(state)}
<h2>최근 감지 기록</h2>
<ol>{ev_rows or "<li>아직 기록이 없어요.</li>"}</ol>
<h2>감시 중인 곳</h2>
<ul><li>라쿠텐북스 (상품별 재고·예약 상태)</li><li>트레카플라자55 · 옐로서브마린 · 요도바시 추첨 페이지 (새 판매·추첨 공지)</li><li>아마존 재팬 초대 판매 (정보·뉴스 사이트 경유)</li></ul>
<p>포켓몬센터 온라인과 아마존은 직접 확인이 막혀 있어서, 아마존 응모는 일본 정보·뉴스 사이트(게임피디아, 전격온라인, 패미통, 구글 뉴스)에 올라온 초대 판매 소식으로 모아요. 응모 방법은 <a href="/아마존-응모-포켓몬카드-원피스카드/">아마존 응모 총정리</a>를 참고하세요.</p>
<p style="font-size:14px;color:#666">※ 자동 감시 결과라 실제 재고·가격은 각 쇼핑몰 페이지가 기준이에요.</p>
'''
    fm = {"title": "일본 쇼핑몰 재고 현황판", "slug": "stock", "desc": "포켓몬카드·원피스카드를 지금 살 수 있는 일본 쇼핑몰을 약 10분 간격으로 확인해 보여 주는 재고 현황판이에요.", "updated": NOW.strftime("%Y년 %m월 %d일 %H:%M")}
    (ROOT / "_pages" / "stock.html").write_text("<!--\n" + json.dumps(fm, ensure_ascii=False, indent=1) + "\n-->\n" + body, encoding="utf-8")

def main():
    if os.environ.get("TG_TEST") == "1":
        res = telegram("🐱 blvl 재고 알림 연결 완료!\n이제 일본 쇼핑몰에 포켓몬·원피스 카드 재고가 뜨면 여기로 바로 알려 드릴게요.\n현황판: https://blvlblog.com/stock/")
        diag = ""
        try:
            me = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getMe", timeout=20).json()
            up = requests.get(f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates", timeout=20).json()
            diag = f" token_ok={me.get('ok')} bot=@{(me.get('result') or {}).get('username','?')} updates={len(up.get('result', []))} {up.get('description','')}"
        except Exception as e: diag = f" diag_error {e}"
        (MON / "tg_test.txt").write_text(f"{NOW.isoformat()} {res}{diag}\n")
        print("TG_TEST", res)
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    first_run = not state or not state.get("items")
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
        if (not old) or old["status"] != v["status"] or old.get("img", "") != v.get("img", ""): status_changed.append(k)
        if avail and not was and not first_run:
            new_events.append({"key": k, "kind": "item", "shop_kr": "라쿠텐북스", "title": v["title"], "url": v["url"], "status": v["status"], "price": v.get("price", ""), "img": v.get("img", "")})
        items[k] = v
    # 트레카플라자55 등 shop-pro 쇼핑몰
    for shop, sname, url in SHOPPRO:
        h = get(url)
        if not h: continue
        cur = scan_shoppro(h, shop, url); fresh = not any(k.startswith(shop + ":") for k in items)
        for k, v in cur.items():
            old = items.get(k)
            v["since"] = old.get("since", "") if (old and old["status"] == v["status"]) else NOW.strftime("%m/%d %H:%M")
            if (not old) or old["status"] != v["status"]: status_changed.append(k)
            if v["status"] == "instock" and not (old and old["status"] == "instock") and not first_run and not fresh:
                new_events.append({"key": k, "kind": "item", "shop_kr": sname, "title": v["title"], "url": v["url"], "status": "instock", "price": v.get("price", ""), "img": v.get("img", "")})
            items[k] = v
        # 목록에서 빠지고 오래된 상품 정리
        for k in [k for k in items if k.startswith(shop + ":") and k not in cur]:
            items.pop(k)
    # 추첨·공지 페이지
    for sid, name, url in PAGES:
        h = get(url)
        if not h: continue
        cur = scan_lines(h); prev = lines.get(sid)
        if prev is not None and not first_run:
            for hid, t in cur.items():
                if hid not in prev:
                    new_events.append({"key": f"{sid}:{hid}", "kind": "page", "shop_kr": name, "title": t, "url": url, "status": "new", "price": ""})
        # 한 번이라도 본 줄은 계속 기억 (진열 순서가 돌아도 옛 상품을 새 소식으로 착각하지 않게)
        lines[sid] = (list(cur.keys()) + [x for x in (prev or []) if x not in cur])[:3000]
    # 아마존 응모
    try:
        a_events, a_changed = scan_amazon(state, first_run)
    except Exception as e:
        print("아마존 응모 확인 실패", e); a_events, a_changed = [], False
    new_events = a_events + new_events
    try:
        k_events, k_seed = scan_kr(state)
    except Exception as e:
        print("국내판 확인 실패", e); k_events, k_seed = [], False
    new_events = k_events + new_events
    a_changed = a_changed or bool(k_events) or k_seed
    # 알림 + 글
    changed = bool(new_events) or bool(status_changed) or first_run or a_changed or TG_NEW or os.environ.get("TG_TEST") == "1"
    for ev in new_events[:8]:  # 한 번에 너무 많이 쓰지 않도록
        f = write_alert_post(ev, state)
        events.insert(0, {"at": NOW.strftime("%m/%d %H:%M"), "shop_kr": ev["shop_kr"], "title": ev["title"], "status": ev["status"]})
        # 텔레그램은 블로그에 글이 실제로 올라간 뒤 보내요(워크플로 마지막 단계 tg_flush.py) — 알림 눌렀는데 글이 없는 일 방지
        TG_QUEUE.append(f'🐱 blvl {"아마존 응모 속보" if ev["status"] == "invite" else "재고 속보"}\n{ev["shop_kr"]} · {STATUS_KR.get(ev["status"], "")}\n{kr(ev["title"])[:80]}\n{ev.get("price","")}\n{ev["url"]}\n블로그: https://blvlblog.com/{urllib.parse.quote(f[:-5])}/')
        print("EVENT", ev["shop_kr"], ev["status"], ev["title"][:60])
    if heal_alert_thumbs(state): changed = True
    if TG_QUEUE:
        TG_QUEUE_FILE.write_text(json.dumps(TG_QUEUE, ensure_ascii=False), encoding="utf-8")
    state["events"] = events[:100]
    if changed:
        write_board(state)
        STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"items={len(items)} pages={len(lines)} new_events={len(new_events)} first_run={first_run}")
    (MON / "changed").write_text("1" if changed else "0")

if __name__ == "__main__":
    main()
