# -*- coding: utf-8 -*-
"""워드프레스 내보내기(XML) → 정적 블로그 (GitHub Pages용)"""
import re, os, sys, json, html, shutil, urllib.parse, datetime
import xml.etree.ElementTree as ET
from pathlib import Path

SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])
SITE = "https://blvlblog.com"; TITLE = "blvl blog"; DESC = "문화·생활·테크·경제 이야기를 담는 블로그"
ADSENSE = "ca-pub-4380904134243959"
NS = {'wp':'http://wordpress.org/export/1.2/','content':'http://purl.org/rss/1.0/modules/content/',
      'excerpt':'http://wordpress.org/export/1.2/excerpt/','dc':'http://purl.org/dc/elements/1.1/'}
PER_PAGE = 10

raw = re.sub(rb'[\x00-\x08\x0b\x0c\x0e-\x1f]', b'', SRC.read_bytes())
ch = ET.fromstring(raw).find('channel')
items = ch.findall('item')
T = lambda e, k: e.findtext(k, namespaces=NS) or ''

cats = {}
for c in ch.findall('wp:category', NS):
    cats[T(c, 'wp:category_nicename')] = html.unescape(T(c, 'wp:cat_name'))
attach = {T(i,'wp:post_id'): T(i,'wp:attachment_url') for i in items if T(i,'wp:post_type') == 'attachment'}
ads_txt = next((T(i,'content:encoded') for i in items if T(i,'wp:post_type') == 'adstxt'), '')

def meta(i, key):
    for m in i.findall('wp:postmeta', NS):
        if T(m,'wp:meta_key') == key: return T(m,'wp:meta_value')
    return ''

def local(u):
    """blvlblog.com 이미지 → 사이트 내부 경로 (jetpack i0.wp.com 포함)"""
    u = html.unescape(u)
    u = re.sub(r'^https?://i\d\.wp\.com/', 'https://', u)
    u = re.sub(r'^https?://(www\.)?blvlblog\.com', '', u)
    return u.split('?')[0] if u.startswith('/wp-content/') else u

def autop(t):
    if '<!-- wp:' in t:
        t = re.sub(r'<!-- /?wp:[^>]*?-->\s*', '', t)
        return t
    blocks = re.split(r'\n\s*\n', t.replace('\r\n', '\n'))
    out = []
    for b in blocks:
        b = b.strip()
        if not b: continue
        if re.match(r'^<(h\d|ul|ol|li|table|blockquote|figure|div|p|pre|hr|iframe|script|style)\b', b, re.I) or b == '&nbsp;':
            out.append(b if b != '&nbsp;' else '')
        else:
            out.append('<p>' + b.replace('\n', '<br>\n') + '</p>')
    return '\n'.join(out)

def clean(body):
    body = autop(body)
    body = re.sub(r'(src|href)="([^"]+)"', lambda m: f'{m.group(1)}="{local(m.group(2))}"', body)
    body = re.sub(r'\s(srcset|sizes)="[^"]*"', '', body)
    body = re.sub(r'<img ', '<img loading="lazy" ', body)
    body = body.replace('[ez-toc]', '')
    body = re.sub(r'\[/?[a-z_]+[^\]]*\]', '', body)  # 남은 숏코드 제거
    return body

def strip_tags(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()

posts = []
for i in items:
    if T(i,'wp:post_type') != 'post' or T(i,'wp:status') != 'publish': continue
    link = T(i,'link'); path = urllib.parse.unquote(urllib.parse.urlparse(link).path).strip('/')
    pcats = [c.get('nicename') for c in i.findall('category') if c.get('domain') == 'category']
    tags = [html.unescape(c.text or '') for c in i.findall('category') if c.get('domain') == 'post_tag']
    body = clean(T(i,'content:encoded'))
    thumb = local(attach.get(meta(i,'_thumbnail_id'), '')) if meta(i,'_thumbnail_id') else ''
    if not thumb:
        m = re.search(r'<img[^>]+src="([^"]+)"', body); thumb = m.group(1) if m else ''
    desc = meta(i,'rank_math_description') or strip_tags(body)[:150]
    posts.append(dict(title=strip_tags(T(i,'title')), path=path, date=T(i,'wp:post_date'), mod=T(i,'wp:post_modified') or T(i,'wp:post_date'),
                      cats=[c for c in pcats if c != 'uncategorized'] or pcats, tags=tags, body=body, thumb=thumb, desc=desc))
posts.sort(key=lambda p: p['date'], reverse=True)

def esc(s): return html.escape(s, quote=True)
def url(path): return '/' + urllib.parse.quote(path.strip('/')) + '/' if path.strip('/') else '/'
NAV = [('HOME', '/'), ('BLOG', '/blog/')] + [(cats[k], f'/category/{k}/') for k in ('art-culture','life-tips','tech','economy') if k in cats]
AUTHOR = 'blvl.'
SEARCH_SVG = '<svg viewBox="0 0 512 512" aria-hidden="true" fill="currentColor"><path d="M208 48c-88.4 0-160 71.6-160 160s71.6 160 160 160 160-71.6 160-160S296.4 48 208 48zM0 208C0 93.1 93.1 0 208 0s208 93.1 208 208c0 48.8-16.8 93.7-45 129.2l135 135-34 34-135-135C301.7 399.2 256.8 416 208 416 93.1 416 0 322.9 0 208z"/></svg>'

def kdate(d):
    y, m, dd = d[:10].split('-'); return f'{int(y)}년 {int(m)}월 {int(dd)}일'

def page(title, content, desc=DESC, canon='/', og_img='', head_extra='', active=''):
    nav = ''.join(f'<li><a class="{"on" if h == active else ""}" href="{h}">{esc(n)}</a></li>' for n, h in NAV)
    full = title if title == TITLE else f'{title} | {TITLE}'
    ogi = f'<meta property="og:image" content="{esc(SITE + og_img if og_img.startswith("/") else og_img)}">' if og_img else ''
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{canon}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{canon}">{ogi}
<link rel="alternate" type="application/rss+xml" title="{TITLE}" href="/feed.xml">
<link rel="preload" href="/assets/fonts/NanumGothic-Regular.woff" as="font" type="font/woff" crossorigin>
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32"><link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/blog.css?v=5">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE}" crossorigin="anonymous"></script>
{head_extra}</head><body>
<header class="site-header" id="hd"><div class="inside-header">
<a class="site-logo" href="/" rel="home"><img src="/assets/logo.png" alt="blvl blog" width="80" height="51"></a>
<nav class="main-navigation" aria-label="메뉴"><button class="menu-toggle" type="button" onclick="document.getElementById('hd').classList.toggle('open')">☰ <span>Menu</span></button>
<ul class="main-nav">{nav}</ul><a class="nav-search" href="/search/" aria-label="검색">{SEARCH_SVG}</a></nav>
</div></header>
{content}
<footer class="site-footer"><nav class="footer-links" aria-label="사이트 정보"><a href="/about/">소개</a> · <a href="/privacy/">개인정보처리방침</a> · <a href="/contact/">문의</a></nav>© {datetime.date.today().year} {TITLE}</footer>
</body></html>'''

def catlink(p):
    k = p['cats'][0] if p['cats'] else ''
    return f'<a href="/category/{k}/">{esc(cats.get(k, k))}</a>' if k else ''

def gcard(p, exc=False):
    img = f'<img loading="lazy" src="{esc(p["thumb"])}" alt="{esc(p["title"])}">' if p['thumb'] else ''
    ex = f'<p class="gexc">{esc(p["desc"][:110])}…</p>' if exc else ''
    return f'''<div class="gbc"><a class="gimg" href="{url(p["path"])}">{img}</a>
<div class="gcat">{catlink(p)}</div><h2 class="gtitle"><a href="{url(p["path"])}">{esc(p["title"])}</a></h2>
<div class="gmeta"><span>Written by:</span><b>{AUTHOR}</b><span>/</span><time>{kdate(p["date"])}</time></div>{ex}</div>'''

def sidebar():
    rec = ''.join(f'<li><a href="{url(q["path"])}">{esc(q["title"])}</a></li>' for q in posts[:5])
    cl = ''.join(f'<li><a href="/category/{k}/">{esc(n)}</a></li>' for k, n in cats.items() if any(k in q['cats'] for q in posts) and k != 'uncategorized')
    return f'''<div class="sidebar"><div class="inside-right-sidebar">
<aside class="widget"><form class="search-form" action="/search/"><input name="q" placeholder="검색 …" aria-label="검색"><button aria-label="검색">{SEARCH_SVG.replace('<svg', '<svg width="16" height="16"')}</button></form></aside>
<aside class="widget widget_recent_entries"><h2 class="widget-title">Recent Posts</h2><ul>{rec}</ul></aside>
<aside class="widget"><h2 class="widget-title">Categories</h2><ul>{cl}</ul></aside>
</div></div>'''

def with_sidebar(main):
    return f'<div class="site-content"><main class="content-area">{main}</main>{sidebar()}</div>'

def arch_item(p):
    img = f'<div class="post-image"><a href="{url(p["path"])}"><img loading="lazy" src="{esc(p["thumb"])}" alt="{esc(p["title"])}"></a></div>' if p['thumb'] else ''
    return f'''<article class="inside-article"><header><h2 class="entry-title"><a href="{url(p["path"])}">{esc(p["title"])}</a></h2>
<div class="entry-meta"><time>{kdate(p["date"])}</time> by {AUTHOR}</div></header>{img}
<div class="entry-summary"><p>{esc(p["desc"])}</p></div><a class="read-more" href="{url(p["path"])}">더 보기</a></article>'''

def listing(base, plist, heading, desc=DESC, head_html=''):
    pages_n = max(1, (len(plist) + PER_PAGE - 1) // PER_PAGE)
    for n in range(1, pages_n + 1):
        chunk = plist[(n-1)*PER_PAGE: n*PER_PAGE]
        pg = ''
        if pages_n > 1:
            href = lambda k: base if k == 1 else f"{base}page/{k}/"
            pg = '<nav class="paging-navigation">' + (f'<a href="{href(n-1)}">« 이전</a>' if n > 1 else '') + ''.join(
                (f'<span class="current">{k}</span>' if k == n else f'<a href="{href(k)}">{k}</a>') for k in range(1, pages_n+1)) + \
                (f'<a href="{href(n+1)}">다음 »</a>' if n < pages_n else '') + '</nav>'
        main = head_html + ''.join(arch_item(p) for p in chunk) + pg
        canon = base if n == 1 else f'{base}page/{n}/'
        write(canon, page(heading, with_sidebar(main), desc, canon, active=base))

def write(path, s):
    d = OUT / urllib.parse.unquote(path).strip('/')
    d.mkdir(parents=True, exist_ok=True)
    (d / 'index.html').write_text(s, encoding='utf-8')

if OUT.exists():
    for x in OUT.iterdir():
        if x.name in ('wp-content', '.git', 'CNAME', '_tools'): continue
        shutil.rmtree(x) if x.is_dir() else x.unlink()
OUT.mkdir(parents=True, exist_ok=True)
shutil.copytree(Path(__file__).parent / 'assets', OUT / 'assets', dirs_exist_ok=True)

# 글
for idx, p in enumerate(posts):
    tag_html = ''.join(f'<span class="button tag">{esc(t)}</span>' for t in p['tags'] if t != 'Featured Post')
    newer = posts[idx-1] if idx > 0 else None; older = posts[idx+1] if idx+1 < len(posts) else None
    nav = '<nav class="post-navigation">' + (f'<div><a href="{url(older["path"])}">« {esc(older["title"])}</a></div>' if older else '<div></div>') + \
          (f'<div class="nn"><a href="{url(newer["path"])}">{esc(newer["title"])} »</a></div>' if newer else '<div></div>') + '</nav>'
    ld = json.dumps({"@context":"https://schema.org","@type":"BlogPosting","headline":p['title'],"datePublished":p['date'].replace(' ','T')+"+09:00",
                     "dateModified":p['mod'].replace(' ','T')+"+09:00","description":p['desc'],"mainEntityOfPage":SITE+url(p['path'])}, ensure_ascii=False)
    cl = ', '.join(f'<a href="/category/{k}/">{esc(cats.get(k,k))}</a>' for k in p['cats'])
    fimg = f'<div class="single-featured-image"><img src="{esc(p["thumb"])}" alt="{esc(p["title"])}"></div>' if p['thumb'] and p['thumb'] not in p['body'] else ''
    main = f'''<article class="inside-article"><header><h1 class="entry-title">{esc(p["title"])}</h1>
<div class="entry-meta"><time>{kdate(p["date"])}</time> by {AUTHOR}</div></header>{fimg}
<div class="entry-content">{p["body"]}</div>
<footer><div class="entry-meta">카테고리: {cl}</div><div class="gp-custom-tag-section">{tag_html}</div>{nav}</footer></article>'''
    write(url(p['path']), page(p['title'], with_sidebar(main), p['desc'], url(p['path']), p['thumb'], f'<script type="application/ld+json">{ld}</script>'))

# 홈: Featured Posts (Featured Post 태그 1+4) · Latest Posts 9
feat = [p for p in posts if 'Featured Post' in p['tags']]
feat = (feat + [p for p in posts if p not in feat])[:5]
home = f'''<div style="height:30px"></div>
<section class="gb-section"><h2 class="custom-title">Featured Posts</h2>
<div class="feat"><div class="big">{gcard(feat[0], True)}</div><div class="small">{"".join(gcard(p) for p in feat[1:5])}</div></div></section>
<section class="gb-section latest"><h2 class="custom-title">Latest Posts</h2>
<div class="lgrid">{"".join(gcard(p) for p in posts[:9])}</div>
<div class="gbtn-wrap"><a class="gbtn" href="/blog/">Read All Article</a></div></section>'''
write('/', page(TITLE, home, DESC, '/', active='/'))
listing('/blog/', posts, 'BLOG')
for k, name in cats.items():
    pl = [p for p in posts if k in p['cats']]
    if pl: listing(f'/category/{k}/', pl, name, f'{name} 카테고리의 글', f'<header class="page-header"><h1>{esc(name)}</h1></header>')

# 검색
(OUT / 'search.json').write_text(json.dumps([{"t":p['title'],"u":url(p['path']),"d":p['date'][:10],"x":strip_tags(p['body'])[:600],"i":p['thumb']} for p in posts], ensure_ascii=False), encoding='utf-8')
write('/search/', page('검색', with_sidebar('''<article class="inside-article"><h1 class="entry-title">검색</h1><input id="q" class="q" placeholder="검색어를 입력하세요" autofocus><div id="r" class="sres"></div></article>
<script>
let D=[];fetch('/search.json').then(r=>r.json()).then(j=>{D=j;const q=new URLSearchParams(location.search).get('q');if(q){I.value=q;go()}});
const I=document.getElementById('q'),R=document.getElementById('r');
const e=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function go(){const w=I.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);if(!w.length){R.innerHTML='';return}
const hit=D.filter(p=>w.every(k=>(p.t+' '+p.x).toLowerCase().includes(k)));
R.innerHTML=hit.length?hit.map(p=>`<article><h2><a href="${p.u}">${e(p.t)}</a></h2><p>${e(p.x.slice(0,120))}…</p></article>`).join(''):'<p>검색 결과가 없어요.</p>'}
I.addEventListener('input',go);
</script>'''), '블로그 검색', '/search/'))

# 404, ads.txt, sitemap, rss, robots
(OUT / '404.html').write_text(page('페이지를 찾을 수 없어요', with_sidebar('<article class="inside-article"><h1 class="entry-title">페이지를 찾을 수 없어요</h1><div class="entry-content"><p>요청한 페이지가 없거나 주소가 바뀌었어요. <a href="/">홈으로 가기</a></p></div></article>'), canon='/404.html'), encoding='utf-8')
if ads_txt: (OUT / 'ads.txt').write_text(ads_txt.strip() + '\n', encoding='utf-8')
(OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', f'<url><loc>{SITE}/</loc></url>']
sm += [f'<url><loc>{SITE}{url(p["path"])}</loc><lastmod>{p["mod"][:10]}</lastmod></url>' for p in posts]
sm += [f'<url><loc>{SITE}/category/{k}/</loc></url>' for k in cats if any(k in p['cats'] for p in posts)]
(OUT / 'sitemap.xml').write_text('\n'.join(sm + ['</urlset>']), encoding='utf-8')
def rfc(d): return datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S').strftime('%a, %d %b %Y %H:%M:%S +0900')
rss = ''.join(f'<item><title>{esc(p["title"])}</title><link>{SITE}{url(p["path"])}</link><guid>{SITE}{url(p["path"])}</guid><pubDate>{rfc(p["date"])}</pubDate><description>{esc(p["desc"])}</description></item>' for p in posts[:20])
(OUT / 'feed.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{TITLE}</title><link>{SITE}</link><description>{DESC}</description>{rss}</channel></rss>', encoding='utf-8')
write('/feed/', '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/feed.xml">')
(OUT / '.nojekyll').write_text('')
shutil.copy(OUT / 'assets' / 'favicon.ico', OUT / 'favicon.ico')

imgs = set()
for p in posts:
    imgs |= set(re.findall(r'src="(/wp-content/[^"]+)"', p['body']))
    if p['thumb'].startswith('/wp-content/'): imgs.add(p['thumb'])
(OUT.parent / 'needed_images.txt').write_text('\n'.join(sorted(imgs)), encoding='utf-8')
print(f'posts={len(posts)} images_needed={len(imgs)}')
