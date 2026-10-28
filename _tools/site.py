# -*- coding: utf-8 -*-
"""blvl blog 정적 사이트 생성기 (GitHub Pages용)

글 원본:   _posts/<slug>.html   — 맨 위 <!-- {JSON 머리말} --> + 본문 HTML
고정 페이지: _pages/<slug>.html  — 소개·개인정보처리방침·문의
실행:      python3 _tools/site.py            (저장소 루트에서)

글 머리말 필드: title, slug, date("YYYY-MM-DD HH:MM:SS"), mod, desc, thumb(정사각형 이미지 경로),
             category(tcg|minicar|figure|game|tech), tags(목록), featured(true면 홈 상단 고정)
"""
import re, json, html, shutil, urllib.parse, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://blvlblog.com"; TITLE = "blvl blog"
DESC = "포켓몬카드·미니카·피규어·게임 — 직접 모으고 즐기는 취미 기록"
ADSENSE = "ca-pub-4380904134243959"
AUTHOR = "blvl."
PER_PAGE = 10
CSS_VER = 6

# 카테고리: (슬러그, 메뉴명, 설명)
CATS = [
    ("tcg",     "TCG",     "포켓몬카드를 비롯한 트레이딩 카드 게임 — 박스 개봉기, 시세, 신상 발매 소식"),
    ("minicar", "MINICAR", "핫휠·토미카·미니GT 등 다이캐스트 미니카 언박싱과 컬렉션"),
    ("figure",  "FIGURE",  "피규어 개봉기, 디테일 리뷰, 진열 이야기"),
    ("game",    "GAME",    "직접 플레이하는 게임의 공략과 플레이 기록"),
    ("tech",    "TECH",    "작업에 쓰는 툴과 앱 사용법"),
]
CAT_NAME = {k: n for k, n, _ in CATS}
NAV = [("HOME", "/"), ("BLOG", "/blog/")] + [(n, f"/category/{k}/") for k, n, _ in CATS]
KEEP = {".git", ".github", "CNAME", "_tools", "_posts", "_pages", "assets", "wp-content", "ads.txt", ".nojekyll", "favicon.ico", ".gitignore", "README.md"}
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
    p.setdefault("mod", p["date"]); p.setdefault("tags", []); p.setdefault("thumb", "")
    p.setdefault("desc", strip_tags(p["body"])[:150])
    assert p["category"] in CAT_NAME, f'{p["slug"]}: 알 수 없는 카테고리 {p["category"]}'
posts.sort(key=lambda p: p["date"], reverse=True)
pages = load("_pages")
YEAR = datetime.date.today().year

def page(title, content, desc=DESC, canon="/", og_img="", head_extra="", active="", noindex=False):
    nav = "".join(f'<li><a class="{"on" if h == active else ""}" href="{h}">{esc(n)}</a></li>' for n, h in NAV)
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
{content}
<footer class="site-footer"><nav class="footer-links" aria-label="사이트 정보"><a href="/about/">소개</a> · <a href="/privacy/">개인정보처리방침</a> · <a href="/contact/">문의</a></nav>© {YEAR} {TITLE}</footer>
</body></html>'''

def catlink(k): return f'<a href="/category/{k}/">{esc(CAT_NAME[k])}</a>'

def gcard(p, exc=False):
    img = f'<img loading="lazy" src="{esc(p["thumb"])}" alt="{esc(p["title"])}">' if p["thumb"] else ""
    ex = f'<p class="gexc">{esc(p["desc"][:110])}…</p>' if exc else ""
    return f'''<div class="gbc"><a class="gimg" href="{url(p["slug"])}">{img}</a>
<div class="gcat">{catlink(p["category"])}</div><h2 class="gtitle"><a href="{url(p["slug"])}">{esc(p["title"])}</a></h2>
<div class="gmeta"><span>Written by:</span><b>{AUTHOR}</b><span>/</span><time>{kdate(p["date"])}</time></div>{ex}</div>'''

def sidebar():
    rec = "".join(f'<li><a href="{url(q["slug"])}">{esc(q["title"])}</a></li>' for q in posts[:5])
    cl = "".join(f'<li><a href="/category/{k}/">{esc(n)}</a></li>' for k, n, _ in CATS)
    return f'''<div class="sidebar"><div class="inside-right-sidebar">
<aside class="widget"><form class="search-form" action="/search/"><input name="q" placeholder="검색 …" aria-label="검색"><button aria-label="검색">{SEARCH_SVG.replace("<svg", '<svg width="16" height="16"')}</button></form></aside>
<aside class="widget widget_recent_entries"><h2 class="widget-title">Recent Posts</h2><ul>{rec}</ul></aside>
<aside class="widget"><h2 class="widget-title">Categories</h2><ul>{cl}</ul></aside>
</div></div>'''

def with_sidebar(main): return f'<div class="site-content"><main class="content-area">{main}</main>{sidebar()}</div>'

def arch_item(p):
    img = f'<div class="post-image"><a href="{url(p["slug"])}"><img loading="lazy" src="{esc(p["thumb"])}" alt="{esc(p["title"])}"></a></div>' if p["thumb"] else ""
    return f'''<article class="inside-article"><header><h2 class="entry-title"><a href="{url(p["slug"])}">{esc(p["title"])}</a></h2>
<div class="entry-meta"><time>{kdate(p["date"])}</time> by {AUTHOR}</div></header>{img}
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
        body = "".join(arch_item(p) for p in chunk) or f'<article class="inside-article"><div class="entry-content"><p>{esc(empty_msg)}</p></div></article>'
        canon = base if n == 1 else f"{base}page/{n}/"
        write(canon, page(heading, with_sidebar(head_html + body + pg), desc, canon, active=base, noindex=not plist))

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
<div class="entry-meta"><time>{kdate(p["date"])}</time>{upd} by {AUTHOR}</div></header>{fimg}
<div class="entry-content">{p["body"]}</div>
<footer><div class="entry-meta">카테고리: {catlink(p["category"])}</div><div class="gp-custom-tag-section">{tag_html}</div>{nav}</footer></article>'''
    write(url(p["slug"]), page(p["title"], with_sidebar(main), p["desc"], url(p["slug"]), p["thumb"], f'<script type="application/ld+json">{ld}</script>'))

# ── 고정 페이지
for pg in pages:
    main = f'''<article class="inside-article"><header><h1 class="entry-title">{esc(pg["title"])}</h1>
<div class="entry-meta">최종 수정일: {esc(pg["updated"])}</div></header>
<div class="entry-content">{pg["body"]}</div></article>'''
    write(url(pg["slug"]), page(pg["title"], with_sidebar(main), pg["desc"], url(pg["slug"])))

# ── 홈
feat = [p for p in posts if p.get("featured")]
feat = (feat + [p for p in posts if p not in feat])[:5]
featured = ""
if feat:
    featured = f'''<section class="gb-section"><h2 class="custom-title">Featured Posts</h2>
<div class="feat"><div class="big">{gcard(feat[0], True)}</div><div class="small">{"".join(gcard(p) for p in feat[1:5])}</div></div></section>'''
home = f'''<div style="height:30px"></div>{featured}
<section class="gb-section latest"><h2 class="custom-title">Latest Posts</h2>
<div class="lgrid">{"".join(gcard(p) for p in posts[:9])}</div>
<div class="gbtn-wrap"><a class="gbtn" href="/blog/">Read All Article</a></div></section>'''
write("/", page(TITLE, home, DESC, "/", active="/"))
listing("/blog/", posts, "BLOG")
for k, name, cdesc in CATS:
    pl = [p for p in posts if p["category"] == k]
    listing(f"/category/{k}/", pl, name, cdesc, f'<header class="page-header"><h1>{esc(name)}</h1><p>{esc(cdesc)}</p></header>',
            "첫 글을 준비하고 있어요. 곧 올라올 예정이에요.")

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
sm += [f'<url><loc>{SITE}{url(p["slug"])}</loc><lastmod>{p["mod"][:10]}</lastmod></url>' for p in posts]
sm += [f"<url><loc>{SITE}/category/{k}/</loc></url>" for k, _, _ in CATS if any(p["category"] == k for p in posts)]
sm += [f'<url><loc>{SITE}{url(pg["slug"])}</loc></url>' for pg in pages]
(ROOT / "sitemap.xml").write_text("\n".join(sm + ["</urlset>"]), encoding="utf-8")
def rfc(d): return datetime.datetime.strptime(d, "%Y-%m-%d %H:%M:%S").strftime("%a, %d %b %Y %H:%M:%S +0900")
rss = "".join(f'<item><title>{esc(p["title"])}</title><link>{SITE}{url(p["slug"])}</link><guid>{SITE}{url(p["slug"])}</guid><pubDate>{rfc(p["date"])}</pubDate><description>{esc(p["desc"])}</description></item>' for p in posts[:20])
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
    if f.is_file() and "/" + str(f.relative_to(ROOT)) not in used:
        f.unlink(); removed += 1
for d in sorted((ROOT / "wp-content").rglob("*"), reverse=True):
    if d.is_dir() and not any(d.iterdir()): d.rmdir()
print(f"글 {len(posts)}개, 페이지 {len(pages)}개 생성 · 안 쓰는 이미지 {removed}개 삭제")
