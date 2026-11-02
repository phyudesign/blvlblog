# -*- coding: utf-8 -*-
"""blvl blog 정적 사이트 생성기 (GitHub Pages용)

글 원본:   _posts/<slug>.html   — 맨 위 <!-- {JSON 머리말} --> + 본문 HTML
고정 페이지: _pages/<slug>.html  — 소개·개인정보처리방침·문의
실행:      python3 _tools/site.py            (저장소 루트에서)

글 머리말 필드: title, slug, date("YYYY-MM-DD HH:MM:SS"), mod, desc, thumb(정사각형 이미지 경로),
             category(tcg|minicar|toys|game|tech), tags(목록), featured(true면 홈 상단 고정)
"""
import re, json, html, shutil, urllib.parse, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://blvlblog.com"; TITLE = "blvl blog"
DESC = "포켓몬카드·미니카·피규어·게임 — 직접 모으고 즐기는 취미 기록"
ADSENSE = "ca-pub-4380904134243959"
AUTHOR = "blvl."
PER_PAGE = 10
CSS_VER = 62
JS_VER = 1

# 카테고리: (슬러그, 메뉴명, 설명)
CATS = [
    ("tcg",     "TCG",     "포켓몬카드를 비롯한 트레이딩 카드 게임 — 박스 개봉기, 시세, 신상 발매 소식"),
    ("minicar", "MINICAR", "핫휠·토미카·미니GT 등 다이캐스트 미니카 언박싱과 컬렉션"),
    ("toys",    "TOYS",    "피규어·건프라·레고·워해머 — 개봉기, 조립·도색, 디테일 리뷰, 진열 이야기"),
    ("game",    "GAME",    "직접 플레이하는 게임의 공략과 플레이 기록"),
    ("tech",    "TECH",    "작업에 쓰는 툴과 앱 사용법"),
    ("news",    "TCG LIVE", "일본 쇼핑몰 포켓몬카드·원피스카드 재고와 추첨 소식을 감시기가 잡는 즉시 올리는 짧은 속보"),
]
NEWS = "news"  # 자동 속보: 홈·최근 글·검색엔진 색인에서 빼고 이 메뉴에만 모음
CAT_NAME = {k: n for k, n, _ in CATS}
# 하위 메뉴: (슬러그, 메뉴명, 분류 단어, 설명) — 글 제목·태그에 단어가 있으면 그 하위 메뉴에 들어감. 단어가 없으면(ETC) 나머지 전부
SUBMENU = {
    "tcg": [("pokemon", "포켓몬스터", ["포켓몬", "ポケモン"], "포켓몬카드 시세, 일본 아마존·쇼핑몰 응모, 신상 발매 소식"),
            ("onepiece", "원피스", ["원피스", "ワンピース", "ONE PIECE"], "원피스카드 시세, 일본 아마존·쇼핑몰 응모, 신상 발매 소식")],
    "toys": [("onepiece", "원피스", ["원피스", "ワンピース", "ONE PIECE"], "원피스 피규어 개봉기와 리뷰"),
             ("dragonball", "드래곤볼", ["드래곤볼", "ドラゴンボール", "DRAGON BALL"], "드래곤볼 피규어 개봉기와 리뷰"),
             ("jujutsu", "주술회전", ["주술회전", "呪術廻戦"], "주술회전 피규어 개봉기와 리뷰"),
             ("gundam", "GUNDAM", ["건담", "건프라", "GUNDAM", "ガンダム", "ガンプラ"], "건프라 조립·도색과 건담 피규어"),
             ("lego", "LEGO", ["레고", "LEGO"], "레고 조립기와 리뷰"),
             ("warhammer", "WARHAMMER", ["워해머", "WARHAMMER", "Warhammer"], "워해머 미니어처 조립·도색과 게임"),
             ("etc", "ETC", [], "그 밖의 피규어와 장난감")],
    "game": [("wow", "WOW", ["WOW", "WoW", "와우", "월드 오브 워크래프트", "World of Warcraft"], "월드 오브 워크래프트 공략과 플레이 기록"),
             ("gta6", "GTA6", ["GTA6", "GTA 6", "GTA VI", "그랜드 테프트 오토"], "GTA6 소식·공략과 플레이 기록"),
             ("diablo", "디아블로", ["디아블로", "Diablo", "DIABLO"], "디아블로 공략과 플레이 기록"),
             ("umamusume", "우마무스메", ["우마무스메", "우마 무스메", "ウマ娘"], "우마무스메 육성 공략과 덱 기록")],
}
SUBS = SUBMENU["tcg"]   # 예전 코드 호환
EXTRA = {"tcg": [("TCG LIVE", "/category/news/")]}
NAV = [(n, f"/category/{k}/", [(sn, f"/category/{k}/{sk}/") for sk, sn, _, _ in SUBMENU.get(k, [])] + EXTRA.get(k, []))
                              for k, n, _ in CATS if k != "news"]
KEEP = {".git", ".github", "CNAME", "_tools", "_posts", "_pages", "_character", "_thumbs", "_monitor", "assets", "wp-content", "ads.txt", ".nojekyll", "favicon.ico", ".gitignore", "README.md"}
SEARCH_SVG = '<svg viewBox="0 0 512 512" aria-hidden="true" fill="currentColor"><path d="M208 48c-88.4 0-160 71.6-160 160s71.6 160 160 160 160-71.6 160-160S296.4 48 208 48zM0 208C0 93.1 93.1 0 208 0s208 93.1 208 208c0 48.8-16.8 93.7-45 129.2l135 135-34 34-135-135C301.7 399.2 256.8 416 208 416 93.1 416 0 322.9 0 208z"/></svg>'

esc = lambda s: html.escape(s, quote=True)
def url(slug): return "/" + urllib.parse.quote(slug.strip("/")) + "/" if slug.strip("/") else "/"
def strip_tags(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
def kdate(d): y, m, dd = d[:10].split("-"); return f"{int(y)}년 {int(m)}월 {int(dd)}일"

def load(folder):
    out = []
    for f in sorted((ROOT / folder).glob("*.html")):
        s = f.read_text(encoding="utf-8")
        m = re.match(r"\s*<!--(.*?)-->\s*", s, re.S)
        meta = json.loads(m.group(1)); meta["body"] = s[m.end():]
        meta.setdefault("slug", f.stem)
        out.append(meta)
    return out

posts = [p for p in load("_posts") if not p.get("draft")]
for p in posts:
    if p["slug"].startswith("속보-"): p["category"] = NEWS  # 예전 속보 글도 속보 메뉴로
for p in posts:
    p.setdefault("mod", p["date"]); p.setdefault("tags", []); p.setdefault("thumb", "")
    p.setdefault("desc", strip_tags(p["body"])[:150])
    assert p["category"] in CAT_NAME, f'{p["slug"]}: 알 수 없는 카테고리 {p["category"]}'
posts.sort(key=lambda p: p["date"], reverse=True)
articles = [p for p in posts if p["category"] != NEWS]  # 사람이 쓴 정식 글
pages = load("_pages")
YEAR = datetime.date.today().year

def page(title, content, desc=DESC, canon="/", og_img="", head_extra="", active="", noindex=False, ticker=True):
    def li(n, h, kids):
        on = h == active or any(ch == active for _, ch in kids)
        if not kids: return f'<li><a class="{"on" if on else ""}" href="{h}">{esc(n)}</a></li>'
        sub = "".join(f'<li><a class="{"on" if ch == active else ""}" href="{ch}">{esc(cn)}</a></li>' for cn, ch in kids)
        return f'<li class="has-sub"><a class="{"on" if on else ""}" href="{h}" aria-haspopup="true">{esc(n)}</a><ul class="sub-menu">{sub}</ul></li>'
    nav = "".join(li(*x) for x in NAV)
    full = title if title == TITLE else f"{title} | {TITLE}"
    ogi = f'<meta property="og:image" content="{esc(SITE + og_img if og_img.startswith("/") else og_img)}">' if og_img else ""
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">{robots}
<link rel="canonical" href="{SITE}{canon}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{canon}">{ogi}
<link rel="alternate" type="application/rss+xml" title="{TITLE}" href="/feed.xml">
<link rel="preload" href="/assets/fonts/NanumGothic-Regular.woff" as="font" type="font/woff" crossorigin>
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32"><link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/blog.css?v={CSS_VER}">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE}" crossorigin="anonymous"></script>
{head_extra}</head><body>
<header class="site-header" id="hd"><div class="inside-header">
<a class="site-logo" href="/" rel="home"><img src="/assets/logo.png" alt="blvl blog" width="80" height="51"></a>
<nav class="main-navigation" aria-label="메뉴"><button class="menu-toggle" type="button" onclick="document.getElementById('hd').classList.toggle('open')">☰ <span>Menu</span></button>
<ul class="main-nav">{nav}</ul><a class="nav-search" href="/search/" aria-label="검색">{SEARCH_SVG}</a></nav>
</div></header>
{f'<div class="tk-sticky">{CHROME["ticker"]}</div>' if ticker else ""}{CHROME["float"]}
{content}
<script defer src="/assets/blvl-stats.js?v={JS_VER}"></script>
<footer class="site-footer"><nav class="footer-links" aria-label="사이트 정보"><a href="/stock/">재고 현황판</a> · <a href="/about/">소개</a> · <a href="/privacy/">개인정보처리방침</a> · <a href="/contact/">문의</a></nav>© {YEAR} {TITLE}</footer>
</body></html>'''

CHROME = {"ticker": "", "float": ""}   # 모든 페이지 공통: 상단 LIVE 전광판, 오른쪽 아마존 응모 판 (아래에서 채움)

def pstat(p, hit=False):
    # 조회수·댓글 수 자리 (assets/blvl-stats.js가 채움)
    return f'<span class="pstat"{" data-hit" if hit else ""} data-slug="{esc(p["slug"])}"></span>'

def comments_box(p):
    return f'''<section id="comments" class="comments" data-slug="{esc(p["slug"])}">
<h2 class="cm-title">댓글 <span class="cm-count">0</span></h2>
<p class="cm-empty">아직 댓글이 없어요. 첫 댓글을 남겨 주세요!</p>
<ol class="cm-list"></ol>
<form class="cm-form" autocomplete="off">
<div class="cm-row"><input name="nick" maxlength="20" placeholder="닉네임" aria-label="닉네임" required><input name="pw" type="password" maxlength="30" placeholder="비밀번호 (삭제용)" aria-label="비밀번호" required></div>
<input name="website" class="cm-trap" tabindex="-1" aria-hidden="true" autocomplete="off">
<textarea name="body" maxlength="1000" rows="4" placeholder="로그인 없이 자유롭게 남겨 주세요. 링크는 넣을 수 없어요." aria-label="댓글 내용" required></textarea>
<div class="cm-actions"><span class="cm-note" role="status"></span><button type="submit">댓글 등록</button></div>
<p class="cm-policy">댓글을 남기면 닉네임과 내용이 공개되며, 스팸 방지를 위해 <a href="/privacy/">개인정보처리방침</a>에 따라 처리돼요.</p>
</form></section>'''

def catlink(k): return f'<a href="/category/{k}/">{esc(CAT_NAME[k])}</a>'

def gcard(p, exc=False):
    img = f'<img loading="lazy" src="{esc(p["thumb"])}" alt="{esc(p["title"])}">' if p["thumb"] else ""
    ex = f'<p class="gexc">{esc(p["desc"][:110])}…</p>' if exc else ""
    return f'''<div class="gbc"><a class="gimg" href="{url(p["slug"])}">{img}</a>
<div class="gcat">{catlink(p["category"])}</div><h2 class="gtitle"><a href="{url(p["slug"])}">{esc(p["title"])}</a></h2>
<div class="gmeta"><span>Written by:</span><b>{AUTHOR}</b><span>/</span><time>{kdate(p["date"])}</time>{pstat(p)}</div>{ex}</div>'''

def sidebar():
    rec = "".join(f'<li><a href="{url(q["slug"])}">{esc(q["title"])}</a></li>' for q in articles[:5])
    nw = [q for q in posts if q["category"] == NEWS][:5]
    news = (f'<aside class="widget widget_recent_entries"><h2 class="widget-title">TCG LIVE</h2><ul>' +
            "".join(f'<li><a href="{url(q["slug"])}">{esc(q["title"].replace("[추첨·판매 속보] ", ""))}</a> <small>{q["date"][5:16]}</small></li>' for q in nw) +
            '<li><a href="/category/news/">속보 전체 보기 →</a></li></ul></aside>') if nw else ""
    cl = "".join(f'<li><a href="/category/{k}/">{esc(n)}</a></li>' for k, n, _ in CATS)
    # 순서: Recent Posts → 아마존 응모 판 → 검색 (응모 판·검색은 스크롤해도 따라옴)
    return f'''<div class="sidebar"><div class="inside-right-sidebar">
<aside class="widget widget_recent_entries"><h2 class="widget-title">Recent Posts</h2><ul>{rec}</ul>
<form class="search-form side-search" action="/search/"><input name="q" placeholder="검색 …" aria-label="검색"><button aria-label="검색">{SEARCH_SVG.replace("<svg", '<svg width="16" height="16"')}</button></form></aside>
<div class="side-sticky">{invite_panel("widget")}</div>
</div></div>'''

# ── 홈 상단 속보 전광판: 최근 48시간 속보 글 + 지금 구매·예약 가능한 상품
def live_rows():
    """전광판·홈 슬라이드에 쓰는 줄: (종류, 꼬리표, 문장, 링크, 시각, 외부링크, 미리보기정보)"""
    try:
        import sys; sys.path.insert(0, str(ROOT / "_tools"))
        from monitor import kr, STATUS_KR, SHOP_KR
    except Exception:
        kr = lambda t: t; STATUS_KR = {}; SHOP_KR = {}
    try: st = json.loads((ROOT / "_monitor" / "state.json").read_text(encoding="utf-8"))
    except Exception: st = {}
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).replace(tzinfo=None)
    rows = []
    for q in posts:
        if q["category"] != NEWS: continue
        try: t = datetime.datetime.strptime(q["date"], "%Y-%m-%d %H:%M:%S")
        except ValueError: continue
        if (now - t).total_seconds() > 48 * 3600: break
        if "amazon.co.jp/dp/" in q.get("shop_url", ""): continue   # 아마존 응모 상품은 아래 '응모 중' 줄로 보여 줌
        name = q["title"].replace("[추첨·판매 속보] ", "").replace("[입고 속보] ", "")
        sub = " · ".join(x for x in (q.get("shop_kr", ""), q.get("status_kr", ""), q.get("price", "")) if x)
        rows.append(("hot", "속보", name, url(q["slug"]), q["date"][5:16].replace("-", "/"), False,
                     {"img": re.sub(r"downsize=\d+", "downsize=400", q.get("pimg") or ""), "name": name, "sub": sub or "TCG LIVE 속보", "cta": "속보 글 보기"}))
    try:
        from monitor import invite_list, amz_img
        for a, name, price, brand, grp, new, link in [r for r in invite_list(st, "jp") if not r[4]][:6]:
            sub = " · ".join(x for x in ("아마존 재팬", "초대 요청 접수 중", price) if x)
            rows.append(("inv", "새 응모" if new else "응모 중", f"{brand} {name} — 아마존 초대 요청", link, "", True,
                         {"img": amz_img(a), "name": f"{brand} {name}", "sub": sub, "cta": "아마존에서 초대 요청하기", "asin": a}))
    except Exception: pass
    for u, v in sorted(st.get("kr", {}).items(), key=lambda kv: kv[1].get("posted", kv[1]["first"]), reverse=True)[:4]:
        rows.append(("kr", "국내판", v["title"], u, "", True, {"img": v.get("img", ""), "name": v["title"], "sub": v["src"] + " 공지", "cta": "공지 보기", "kr": "1"}))
    for v in st.get("items", {}).values():
        if v.get("status") not in ("instock", "preorder"): continue
        name = re.sub(r"^\s+|\s+$", "", kr(v["title"]))[:48]
        extra = " · ".join(x for x in (SHOP_KR.get(v.get("shop"), ""), STATUS_KR.get(v["status"], ""), v.get("price", "")) if x)
        rows.append(("on", "판매 중" if v["status"] == "instock" else "예약 중", f"{name} — {extra}", v["url"], "", True,
                     {"img": re.sub(r"downsize=\d+", "downsize=400", v.get("img") or ""), "name": re.sub(r"^\s+|\s+$", "", kr(v["title"])), "sub": extra, "cta": "쇼핑몰에서 보기"}))
    return rows[:14]

def ticker():
    rows = live_rows()
    if not rows:
        track = '<span class="tk-item"><span class="tk-tag idle">감시 중</span>지금은 새로 풀린 재고가 없어요 · 10분마다 일본 쇼핑몰을 확인하고 있어요</span>'
    else:
        def one(r):
            kind, tag, text, href, when, ext, pv = r
            attrs = ' target="_blank" rel="nofollow noopener"' if ext else ""
            w = f'<time>{esc(when)}</time>' if when else ""
            data = "".join(f' data-{k}="{esc(v)}"' for k, v in pv.items())
            return f'<a class="tk-item" href="{esc(href)}"{attrs}{data}><span class="tk-tag {kind}">{tag}</span>{esc(text)}{w}</a>'
        track = "".join(one(r) for r in rows)
    dur = max(28, min(120, len(re.sub(r"<[^>]+>", "", track)) // 5))
    return f'''<section class="ticker" aria-label="TCG LIVE 실시간 재고 속보">
<a class="tk-label" href="/category/news/"><i aria-hidden="true"></i>LIVE</a>
<div class="tk-view"><div class="tk-track" style="--dur:{dur}s"><div class="tk-run">{track}</div><div class="tk-run" aria-hidden="true">{track}</div></div></div>
<a class="tk-more" href="/stock/">현황판 →</a></section>
<script defer src="/assets/blvl-ticker.js?v=8"></script>'''

# ── 홈 LIVE 슬라이드 (포켓몬센터 온라인 홈처럼 가운데 큰 카드 + 양옆이 살짝 보이는 슬라이드)
LH_COLORS = ["#FFD54A", "#7FE0B0", "#FF8A80", "#8FD0FF", "#C9B2FF", "#FFAE5C", "#C8F060"]
LH_EMO = {"kr": ["watching", "sounds-good", "best"], "inv": ["lets-go", "kyaa", "happy-cards", "great", "hoho", "best"], "hot": ["rare", "heok"], "on": ["good", "mine"]}
LH_LAYOUTS = ["tilt", "split", "bleed", "stamp", "burst"]
# 상품별 스튜디오 색 (밝은 배경 두 색, 글자·띠 색) — 박스 아트 색에 맞춤
LH_THEME = {
    "B0H4PQ6LR5": ("#e6f6f1", "#bfe5d9", "#0d5646"),  # 파동시커: 청록
    "B0HFVPJF4Q": ("#f7ebe9", "#e8c4bf", "#6e1220"),  # OP-18: 진홍
    "B0FX7X71KK": ("#fbeee3", "#f0cba9", "#7f3409"),  # OP-13: 주황
    "B0FJ7Z6RML": ("#fdecf1", "#f4c4d3", "#871b3e"),  # EB-03: 분홍
    "B0HB3JQ6P4": ("#f2eafb", "#d8c6f2", "#45267a"),  # EB-05: 라벤더
    "B0GP928YDZ": ("#e4f6ec", "#b1e0c6", "#0b5a39"),  # 스톰 에메랄드
    "B0H43ZX8LK": ("#e8eef9", "#bfcfea", "#13244a"),  # OP-17: 남색
    "B0GXCRBL5J": ("#fcf5e2", "#eedcab", "#6a4806"),  # 30th: 금색
    "B0GXCM4BCZ": ("#eeeaf5", "#cbbfe1", "#2c1e4b"),  # 에브이·블래키: 보라
}
LH_THEME_ROT = [("#e9f0f8", "#c3d3e8", "#16294d"), ("#fbefe6", "#f0cfb4", "#6b2e0c"), ("#eef7e9", "#c9e6bb", "#20501a"), ("#f6ecf8", "#dec7ea", "#4a1f5c")]
LH_STAGES = ["podium", "block", "arch"]
# OpenAI로 만든 스튜디오 배경 (assets/studio/<키>.webp)과 그 안의 무대 위치: (가로 중심 %, 상품 바닥 %, 상품 폭 %)
LH_BG = {
    "B0FJ7Z6RML": (70, 73, 48), "B0FX7X71KK": (72, 63, 44), "B0GP928YDZ": (72, 70, 46), "B0GXCM4BCZ": (77, 72, 44),
    "B0GXCRBL5J": (70, 65, 46), "B0H43ZX8LK": (67, 63, 46), "B0H4PQ6LR5": (70, 61, 50), "B0HB3JQ6P4": (69, 80, 44),
    "B0HFVPJF4Q": (66, 72, 46), "default1": (72, 67, 46), "default2": (70, 59, 42), "default3": (69, 80, 44),
}
LH_LABEL = {"kr": "국내판 소식", "inv": "아마존 응모", "hot": "TCG 속보", "on": "지금 구매 가능"}
def live_hero():
    rows = live_rows()
    if not rows: return ""
    cnt = {}
    slides = []
    for i, (kind, tag, text, href, when, ext, pv) in enumerate(rows[:10]):
        k = cnt.get(kind, 0); cnt[kind] = k + 1
        emo = LH_EMO.get(kind, ["great"])[k % len(LH_EMO.get(kind, ["great"]))]
        name = pv.get("name") or text
        brand = ""
        for b in ("포켓몬", "원피스", "건담"):
            if name.startswith(b + " "): brand, name = b, name[len(b) + 1:]
        attrs = ' target="_blank" rel="nofollow noopener"' if ext else ""
        new = '<em>NEW</em>' if tag in ("새 응모", "속보") else ""
        img = pv.get("img", "")
        if img:   # 상품 사진 + 스튜디오 연출 (상품마다 색·무대가 다름)
            th = LH_THEME.get(pv.get("asin", ""), LH_THEME_ROT[i % len(LH_THEME_ROT)])
            stage = LH_STAGES[i % len(LH_STAGES)]
            bgk = pv.get("asin", "") if pv.get("asin", "") in LH_BG else f"default{i % 3 + 1}"
            px, py, pw = LH_BG[bgk]
            cut = ROOT / "assets" / "products" / f'{pv.get("asin", "")}.webp'
            prod_src, prod_cls = (f"/assets/products/{cut.name}", "st-prod cut") if pv.get("asin") and cut.exists() else (img, "st-prod")
            if pv.get("kr"): prod_src, prod_cls = "", ""
            art = ROOT / "assets" / "art" / f'{pv.get("asin", "")}.jpg'
            use_art = bool(pv.get("asin")) and art.exists() and "cut" in prod_cls   # 박스 아트 크롭 배경
            back = f"/assets/art/{art.name}" if use_art else f"/assets/studio/{bgk}.webp"
            if pv.get("kr"): use_art, back = True, img
            title = re.sub(r"\s*BOX$", "", name)
            slides.append(f'''<a class="lh-slide studio st-bg{" st-art" if use_art else ""}" href="{esc(href)}"{attrs} style="--b1:{th[0]};--b2:{th[1]};--ac:{th[2]};--px:{px}%;--py:{py}%;--pw:{pw}%" draggable="false">
<img class="st-back" src="{esc(back)}" referrerpolicy="no-referrer" alt="" loading="{"eager" if i < 3 else "lazy"}" draggable="false">
{f'<img class="{prod_cls}" src="{esc(prod_src)}" alt="{esc(name)} 상품 사진" loading="{"eager" if i < 3 else "lazy"}" referrerpolicy="no-referrer" draggable="false">' if prod_src else ""}
<span class="st-text"><span class="st-pill"><i></i><b>LIVE</b>· {LH_LABEL.get(kind, "TCG LIVE")}{new}</span>
<span class="st-rib">{esc(brand or "TCG")}</span><b class="st-title">{esc(title)}</b><span class="st-line"></span>
<span class="st-sub">{esc(pv.get("sub", ""))}</span><span class="st-cta">{esc(pv.get("cta", "자세히 보기"))} →</span></span></a>''')
            continue
        th = LH_THEME_ROT[i % len(LH_THEME_ROT)]; bgk = f"default{i % 3 + 1}"; px, py, pw = LH_BG[bgk]
        slides.append(f'''<a class="lh-slide studio st-bg st-noimg" href="{esc(href)}"{attrs} style="--b1:{th[0]};--b2:{th[1]};--ac:{th[2]};--px:{px}%;--py:{py}%;--pw:{pw}%" draggable="false">
<img class="st-back" src="/assets/studio/{bgk}.webp" alt="" loading="lazy" draggable="false">
<img class="st-prod cut" src="/wp-content/uploads/emoticons/gyomyo/{emo}.webp" alt="" loading="lazy" draggable="false">
<span class="st-text"><span class="st-pill"><i></i><b>LIVE</b>· {LH_LABEL.get(kind, "TCG LIVE")}{new}</span>
<span class="st-rib">{esc(brand or "TCG")}</span><b class="st-title">{esc(name)}</b><span class="st-line"></span>
<span class="st-sub">{esc(pv.get("sub", ""))}</span><span class="st-cta">{esc(pv.get("cta", "자세히 보기"))} →</span></span></a>''')
        continue
        slides.append(f'''<a class="lh-slide" href="{esc(href)}"{attrs} style="--c:{LH_COLORS[i % len(LH_COLORS)]}" draggable="false">
<span class="lh-top"><i></i>LIVE · {LH_LABEL.get(kind, "TCG LIVE")}{new}</span>
<span class="lh-brand">{esc(brand or "TCG")}</span><b class="lh-title">{esc(name)}</b>
<span class="lh-sub">{esc(pv.get("sub", ""))}</span><span class="lh-cta">{esc(pv.get("cta", "자세히 보기"))} →</span>
<img class="lh-emo" src="/wp-content/uploads/emoticons/gyomyo/{emo}.webp" alt="" loading="lazy" draggable="false"></a>''')
    dots = "".join(f'<button type="button" aria-label="{i+1}번째"></button>' for i in range(len(slides)))
    return (f'<section class="live-hero" aria-label="TCG LIVE 응모·재고 슬라이드"><div class="lh-stage">{"".join(slides)}</div>'
            f'<button type="button" class="lh-nav lh-prev" aria-label="이전"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg></button><button type="button" class="lh-nav lh-next" aria-label="다음"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg></button>'
            f'<div class="lh-dots">{dots}</div><a class="lh-all" href="/stock/">LIVE 현황판 전체 보기 →</a></section>'
            '<script defer src="/assets/blvl-hero.js?v=1"></script><script defer src="/assets/blvl-ticker.js?v=8"></script>')

# ── 아마존 응모 판 (일본·미국 탭) — 모든 페이지 오른쪽 여백 / 좁은 화면은 글 사이드바
def invite_panel(cls):
    try:
        import sys; sys.path.insert(0, str(ROOT / "_tools"))
        from monitor import invite_list
        st = json.loads((ROOT / "_monitor" / "state.json").read_text(encoding="utf-8"))
    except Exception:
        return ""
    def items(region):
        out, groups, order = [], {}, []
        for a, name, price, brand, grp, new, link in invite_list(st, region):
            if grp:
                key = (brand, grp)
                if key not in groups: groups[key] = []; order.append(("g", key))
                groups[key].append((name, link)); continue
            badge = '<em class="ip-new">NEW</em>' if new else ""
            order.append(("o", f'<li><a href="{link}" target="_blank" rel="nofollow noopener"><span class="ip-name"><i>{brand}</i>{esc(name)}{badge}</span>'
                               f'{f"<span class=ip-meta>{esc(price)}</span>" if price else ""}</a></li>'))
        for kind, v in order:
            if kind == "o": out.append(v); continue
            chips = "".join(f'<a href="{l}" target="_blank" rel="nofollow noopener">{esc(n)}</a>' for n, l in groups[v])
            out.append(f'<li class="ip-group"><span class="ip-name"><i>{v[0]}</i>{esc(v[1])}</span><span class="ip-meta">{len(groups[v])}종</span><div class="ip-chips">{chips}</div></li>')
        return "".join(out)
    jp, us = items("jp"), items("us")
    krs = sorted(st.get("kr", {}).items(), key=lambda kv: (kv[1].get("posted", kv[1]["first"]), kv[0]), reverse=True)[:20]
    kr_html = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="nofollow noopener"><span class="ip-name"><i>{esc(v["src"].replace("포켓몬카드 공식", "카드 공식"))}</i>{esc(v["title"])}'
                      f'{"<em class=ip-new>NEW</em>" if v["first"] >= (datetime.date.today() - datetime.timedelta(days=3)).isoformat() and v["first"] > "2026-11-02" else ""}</span>'
                      f'<span class="ip-meta">{int(v.get("posted", v["first"])[5:7])}/{int(v.get("posted", v["first"])[8:10])} 공지</span></a></li>' for u, v in krs) or \
              '<li class="ip-note">아직 모은 국내판 소식이 없어요. 포켓몬코리아·포켓몬카드 공식 공지를 10분마다 확인하고 있어요.</li>'
    uid = "ip-" + cls.split()[0]
    return (f'<aside class="inv-panel {cls}" aria-label="아마존 응모 중인 상품"><div class="ip-head"><b>응모 중</b><span>아마존 초대 요청 · 국내판 추첨 · 위가 최신</span></div>'
            f'<div class="ip-tabs" role="tablist"><button type="button" role="tab" class="on" aria-selected="true" data-t="jp">🇯🇵 일본</button>'
            f'<button type="button" role="tab" aria-selected="false" data-t="us">🇺🇸 미국</button>'
            f'<button type="button" role="tab" aria-selected="false" data-t="kr">🇰🇷 국내</button></div>'
            f'<ol class="ip-list" data-t="jp">{jp}</ol><ol class="ip-list" data-t="us" hidden>{us}'
            f'<li class="ip-note">미국 아마존은 초대 판매 상품이 적어요. 확인되는 대로 추가할게요.</li></ol>'
            f'<ol class="ip-list" data-t="kr" hidden>{kr_html}<li class="ip-note">국내판은 포켓몬코리아·포켓몬카드 공식 공지의 추첨·응모·판매 소식이에요.</li></ol>'
            f'<a class="ip-all" href="/stock/">전체 목록 · 응모 방법 →</a></aside>')

def with_sidebar(main): return f'<div class="site-content"><main class="content-area">{main}</main>{sidebar()}</div>'

CHROME["ticker"] = ticker()
CHROME["float"] = invite_panel("inv-float") + ('<button type="button" class="inv-fab" aria-expanded="false" aria-label="아마존 응모 중인 상품 보기">'
                                              '<i aria-hidden="true"></i>응모 중</button>')
def arch_item(p):
    img = f'<div class="post-image"><a href="{url(p["slug"])}"><img loading="lazy" src="{esc(p["thumb"])}" alt="{esc(p["title"])}"></a></div>' if p["thumb"] else ""
    return f'''<article class="inside-article"><header><h2 class="entry-title"><a href="{url(p["slug"])}">{esc(p["title"])}</a></h2>
<div class="entry-meta"><time>{kdate(p["date"])}</time> by {AUTHOR}{pstat(p)}</div></header>{img}
<div class="entry-summary"><p>{esc(p["desc"])}</p></div><a class="read-more" href="{url(p["slug"])}">더 보기</a></article>'''

def write(path, s):
    d = ROOT / urllib.parse.unquote(path).strip("/")
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(s, encoding="utf-8")

def listing(base, plist, heading, desc=DESC, head_html="", empty_msg=""):
    pages_n = max(1, (len(plist) + PER_PAGE - 1) // PER_PAGE)
    for n in range(1, pages_n + 1):
        chunk = plist[(n-1)*PER_PAGE: n*PER_PAGE]
        pg = ""
        if pages_n > 1:
            href = lambda k: base if k == 1 else f"{base}page/{k}/"
            pg = '<nav class="paging-navigation">' + (f'<a href="{href(n-1)}">« 이전</a>' if n > 1 else "") + "".join(
                (f'<span class="current">{k}</span>' if k == n else f'<a href="{href(k)}">{k}</a>') for k in range(1, pages_n+1)) + \
                (f'<a href="{href(n+1)}">다음 »</a>' if n < pages_n else "") + "</nav>"
        body = (f'<div class="lgrid cat-grid">{"".join(gcard(p) for p in chunk)}</div>' if chunk     # 한 줄에 3개씩 카드
                else f'<article class="inside-article"><div class="entry-content"><p>{empty_msg}</p></div></article>')
        canon = base if n == 1 else f"{base}page/{n}/"
        write(canon, page(heading, head_html.replace('class="page-header"', 'class="page-header cat-head"') + with_sidebar(body + pg), desc, canon, active=base, noindex=not plist))

# ── 이전 결과물 정리 (원본·자산은 보존)
for x in ROOT.iterdir():
    if x.name in KEEP: continue
    shutil.rmtree(x) if x.is_dir() else x.unlink()

# ── 글
for idx, p in enumerate(posts):
    tag_html = "".join(f'<span class="button tag">{esc(t)}</span>' for t in p["tags"])
    newer = posts[idx-1] if idx > 0 else None; older = posts[idx+1] if idx+1 < len(posts) else None
    nav = '<nav class="post-navigation">' + (f'<div><a href="{url(older["slug"])}">« {esc(older["title"])}</a></div>' if older else "<div></div>") + \
          (f'<div class="nn"><a href="{url(newer["slug"])}">{esc(newer["title"])} »</a></div>' if newer else "<div></div>") + "</nav>"
    ld = json.dumps({"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"],
                     "datePublished": p["date"].replace(" ", "T") + "+09:00", "dateModified": p["mod"].replace(" ", "T") + "+09:00",
                     "author": {"@type": "Person", "name": "blvl"}, "description": p["desc"], "mainEntityOfPage": SITE + url(p["slug"]),
                     **({"image": SITE + p["thumb"]} if p["thumb"].startswith("/") else {})}, ensure_ascii=False)
    fimg = f'<div class="single-featured-image"><img src="{esc(p["thumb"])}" alt="{esc(p["title"])}"></div>' if p["thumb"] and p["thumb"] not in p["body"] else ""
    upd = f' · 수정 {kdate(p["mod"])}' if p["mod"][:10] != p["date"][:10] else ""
    main = f'''<article class="inside-article"><header><h1 class="entry-title">{esc(p["title"])}</h1>
<div class="entry-meta"><time>{kdate(p["date"])}</time>{upd} by {AUTHOR}{pstat(p, hit=True)}</div></header>{fimg}
<div class="entry-content">{p["body"]}</div>
<footer><div class="entry-meta">카테고리: {catlink(p["category"])}</div><div class="gp-custom-tag-section">{tag_html}</div>{nav}</footer></article>
{comments_box(p)}'''
    write(url(p["slug"]), page(p["title"], with_sidebar(main), p["desc"], url(p["slug"]), p["thumb"], f'<script type="application/ld+json">{ld}</script>', noindex=p["category"] == NEWS))

# ── 고정 페이지
for pg in pages:
    main = f'''<article class="inside-article"><header><h1 class="entry-title">{esc(pg["title"])}</h1>
<div class="entry-meta">최종 수정일: {esc(pg["updated"])}</div></header>
<div class="entry-content">{pg["body"]}</div></article>'''
    write(url(pg["slug"]), page(pg["title"], with_sidebar(main), pg["desc"], url(pg["slug"])))

feat = [p for p in articles if p.get("featured")]
feat = (feat + [p for p in articles if p not in feat])[:5]
featured = ""
if feat:
    featured = f'''<section class="gb-section"><h2 class="custom-title">Featured Posts</h2>
<div class="feat"><div class="big">{gcard(feat[0], True)}</div><div class="small">{"".join(gcard(p) for p in feat[1:5])}</div></div></section>'''
home = f'''{live_hero()}{featured}
<section class="gb-section latest"><h2 class="custom-title">Latest Posts</h2>
<div class="lgrid">{"".join(gcard(p) for p in articles[:9])}</div>
<div class="gbtn-wrap"><a class="gbtn" href="/blog/">Read All Article</a></div></section>'''
write("/", page(TITLE, home, DESC, "/", active="/", ticker=False))
listing("/blog/", articles, "BLOG")
for k, name, cdesc in CATS:
    pl = [p for p in posts if p["category"] == k]
    listing(f"/category/{k}/", pl, name, cdesc, f'<header class="page-header"><h1>{esc(name)}</h1><p>{esc(cdesc)}</p></header>',
            "아직 잡힌 속보가 없어요. 감시기가 10분마다 일본 쇼핑몰을 확인하고 있으니, 재고가 뜨면 여기에 바로 올라와요. 지금 판매 중인 상품은 <a href='/stock/'>재고 현황판</a>에서 볼 수 있어요." if k == NEWS else "첫 글을 준비하고 있어요. 곧 올라올 예정이에요.")

# ── 하위 메뉴 페이지
def sub_posts(parent, words, sk):
    inp = [p for p in articles if p["category"] == parent]
    if sk == "etc":
        known = [w for _, _, ws, _ in SUBMENU[parent] for w in ws]
        return [p for p in inp if not any(w in p["title"] + " ".join(p.get("tags", [])) for w in known)]
    return [p for p in inp if any(w in p["title"] + " ".join(p.get("tags", [])) for w in words)]
for parent, subs in SUBMENU.items():
    for sk, sn, words, sdesc in subs:
        listing(f"/category/{parent}/{sk}/", sub_posts(parent, words, sk), f"{CAT_NAME[parent]} · {sn}", sdesc,
                f'<header class="page-header"><h1>{esc(sn)}</h1><p>{esc(sdesc)}</p></header>', "첫 글을 준비하고 있어요. 곧 올라올 예정이에요.")

# ── 검색
(ROOT / "search.json").write_text(json.dumps([{"t": p["title"], "u": url(p["slug"]), "d": p["date"][:10], "x": strip_tags(p["body"])[:600], "i": p["thumb"]} for p in posts], ensure_ascii=False), encoding="utf-8")
write("/search/", page("검색", with_sidebar('''<article class="inside-article"><h1 class="entry-title">검색</h1><input id="q" class="q" placeholder="검색어를 입력하세요" autofocus><div id="r" class="sres"></div></article>
<script>
let D=[];fetch('/search.json').then(r=>r.json()).then(j=>{D=j;const q=new URLSearchParams(location.search).get('q');if(q){I.value=q;go()}});
const I=document.getElementById('q'),R=document.getElementById('r');
const e=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function go(){const w=I.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);if(!w.length){R.innerHTML='';return}
const hit=D.filter(p=>w.every(k=>(p.t+' '+p.x).toLowerCase().includes(k)));
R.innerHTML=hit.length?hit.map(p=>`<article><h2><a href="${p.u}">${e(p.t)}</a></h2><p>${e(p.x.slice(0,120))}…</p></article>`).join(''):'<p>검색 결과가 없어요.</p>'}
I.addEventListener('input',go);
</script>'''), "블로그 검색", "/search/", noindex=True))

# ── 404, robots, sitemap, rss
(ROOT / "404.html").write_text(page("페이지를 찾을 수 없어요", with_sidebar('<article class="inside-article"><h1 class="entry-title">페이지를 찾을 수 없어요</h1><div class="entry-content"><p>요청한 페이지가 없거나 블로그 개편으로 정리된 글이에요. <a href="/">홈으로 가기</a></p></div></article>'), canon="/404.html", noindex=True), encoding="utf-8")
(ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', f"<url><loc>{SITE}/</loc></url>"]
sm += [f'<url><loc>{SITE}{url(p["slug"])}</loc><lastmod>{p["mod"][:10]}</lastmod></url>' for p in articles]
sm += [f"<url><loc>{SITE}/category/{k}/</loc></url>" for k, _, _ in CATS if k != NEWS and any(p["category"] == k for p in posts)]
sm += [f"<url><loc>{SITE}/category/{pa}/{sk}/</loc></url>" for pa, subs in SUBMENU.items() for sk, _, words, _ in subs if sub_posts(pa, words, sk)]
sm += [f'<url><loc>{SITE}{url(pg["slug"])}</loc></url>' for pg in pages]
(ROOT / "sitemap.xml").write_text("\n".join(sm + ["</urlset>"]), encoding="utf-8")
def rfc(d): return datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S").strftime("%a, %d %b %Y %H:%M:%S +0900")
rss = "".join(f'<item><title>{esc(p["title"])}</title><link>{SITE}{url(p["slug"])}</link><guid>{SITE}{url(p["slug"])}</guid><pubDate>{rfc(p["date"])}</pubDate><description>{esc(p["desc"])}</description></item>' for p in articles[:20])
(ROOT / "feed.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{TITLE}</title><link>{SITE}</link><description>{DESC}</description>{rss}</channel></rss>', encoding="utf-8")
write("/feed/", '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/feed.xml">')
(ROOT / ".nojekyll").write_text("")

# ── 안 쓰는 이미지 정리
used = set()
for p in posts:
    used |= {urllib.parse.unquote(u) for u in re.findall(r'src="(/wp-content/[^"]+)"', p["body"])}
    if p["thumb"].startswith("/wp-content/"): used.add(urllib.parse.unquote(p["thumb"]))
removed = 0
for f in (ROOT / "wp-content").rglob("*"):
    if "emoticons" in f.parts or f.name.startswith("blvl-stock-alert"): continue  # 이모티콘·속보용 공용 썸네일은 보존
    if f.is_file() and "/" + str(f.relative_to(ROOT)) not in used:
        f.unlink(); removed += 1
for d in sorted((ROOT / "wp-content").rglob("*"), reverse=True):
    if d.is_dir() and not any(d.iterdir()): d.rmdir()
print(f"글 {len(posts)}개, 페이지 {len(pages)}개 생성 · 안 쓰는 이미지 {removed}개 삭제")
