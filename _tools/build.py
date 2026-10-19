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
PER_PAGE = 12

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

def page(title, content, desc=DESC, canon='/', og_img='', head_extra=''):
    nav = ''.join(f'<a href="{h}">{esc(n)}</a>' for n, h in NAV)
    full = title if title == TITLE else f'{title} | {TITLE}'
    ogi = f'<meta property="og:image" content="{esc(SITE + og_img if og_img.startswith("/") else og_img)}">' if og_img else ''
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{canon}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{canon}">{ogi}
<link rel="alternate" type="application/rss+xml" title="{TITLE}" href="/feed.xml">
<link rel="stylesheet" href="/assets/blog.css">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE}" crossorigin="anonymous"></script>
{head_extra}</head><body>
<header class="hd"><div class="wrap"><a class="brand" href="/">{TITLE}</a>
<nav>{nav}<a href="/search/" aria-label="검색">검색</a></nav></div></header>
<main class="wrap">{content}</main>
<footer class="ft"><div class="wrap">© {datetime.date.today().year} {TITLE}</div></footer>
</body></html>'''

def card(p):
    img = f'<img loading="lazy" src="{esc(p["thumb"])}" alt="">' if p['thumb'] else '<div class="noimg"></div>'
    c = cats.get(p['cats'][0], '') if p['cats'] else ''
    return f'''<a class="card" href="{url(p["path"])}"><div class="th">{img}</div><div class="cb">
<span class="cat">{esc(c)}</span><h3>{esc(p["title"])}</h3><p>{esc(p["desc"][:90])}</p><time>{p["date"][:10]}</time></div></a>'''

def listing(base, plist, heading, desc=DESC):
    pages_n = max(1, (len(plist) + PER_PAGE - 1) // PER_PAGE)
    for n in range(1, pages_n + 1):
        chunk = plist[(n-1)*PER_PAGE: n*PER_PAGE]
        pg = ''
        if pages_n > 1:
            pg = '<nav class="pager">' + ''.join(
                f'<a class="{"on" if k == n else ""}" href="{base if k == 1 else f"{base}page/{k}/"}">{k}</a>' for k in range(1, pages_n+1)) + '</nav>'
        content = f'<h1 class="lh">{esc(heading)}</h1><div class="grid">{"".join(card(p) for p in chunk)}</div>{pg}'
        canon = base if n == 1 else f'{base}page/{n}/'
        write(canon, page(heading if heading != '최신 글' else TITLE, content, desc, canon))

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
    c_links = ' '.join(f'<a class="cat" href="/category/{k}/">{esc(cats.get(k,k))}</a>' for k in p['cats'])
    tag_html = ''.join(f'<span class="tag">#{esc(t)}</span>' for t in p['tags'])
    newer = posts[idx-1] if idx > 0 else None; older = posts[idx+1] if idx+1 < len(posts) else None
    nav = '<nav class="pn">' + (f'<a href="{url(older["path"])}"><small>이전 글</small>{esc(older["title"])}</a>' if older else '<span></span>') + \
          (f'<a class="r" href="{url(newer["path"])}"><small>다음 글</small>{esc(newer["title"])}</a>' if newer else '<span></span>') + '</nav>'
    related = [q for q in posts if q is not p and set(q['cats']) & set(p['cats'])][:3]
    rel = f'<section class="rel"><h2>함께 보면 좋은 글</h2><div class="grid g3">{"".join(card(q) for q in related)}</div></section>' if related else ''
    ld = json.dumps({"@context":"https://schema.org","@type":"BlogPosting","headline":p['title'],"datePublished":p['date'].replace(' ','T')+"+09:00",
                     "dateModified":p['mod'].replace(' ','T')+"+09:00","description":p['desc'],"mainEntityOfPage":SITE+url(p['path'])}, ensure_ascii=False)
    content = f'''<article class="post"><header><div class="meta">{c_links}<time>{p["date"][:10]}</time></div><h1>{esc(p["title"])}</h1></header>
<div class="ad"><ins class="adsbygoogle" style="display:block" data-ad-client="{ADSENSE}" data-ad-format="auto" data-full-width-responsive="true"></ins><script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></div>
<div class="entry">{p["body"]}</div><div class="tags">{tag_html}</div></article>{nav}{rel}'''
    write(url(p['path']), page(p['title'], content, p['desc'], url(p['path']), p['thumb'], f'<script type="application/ld+json">{ld}</script>'))

listing('/', posts, '최신 글')
listing('/blog/', posts, 'BLOG')
for k, name in cats.items():
    pl = [p for p in posts if k in p['cats']]
    if pl: listing(f'/category/{k}/', pl, name, f'{name} 카테고리의 글')

# 검색
(OUT / 'search.json').write_text(json.dumps([{"t":p['title'],"u":url(p['path']),"d":p['date'][:10],"x":strip_tags(p['body'])[:600],"i":p['thumb']} for p in posts], ensure_ascii=False), encoding='utf-8')
write('/search/', page('검색', '''<h1 class="lh">검색</h1><input id="q" class="q" placeholder="검색어를 입력하세요" autofocus><div id="r" class="grid"></div>
<script>
let D=[];fetch('/search.json').then(r=>r.json()).then(j=>{D=j;const q=new URLSearchParams(location.search).get('q');if(q){I.value=q;go()}});
const I=document.getElementById('q'),R=document.getElementById('r');
const e=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function go(){const w=I.value.trim().toLowerCase().split(/\\s+/).filter(Boolean);if(!w.length){R.innerHTML='';return}
const hit=D.filter(p=>w.every(k=>(p.t+' '+p.x).toLowerCase().includes(k)));
R.innerHTML=hit.length?hit.map(p=>`<a class="card" href="${p.u}"><div class="th">${p.i?`<img src="${e(p.i)}" alt="">`:'<div class="noimg"></div>'}</div><div class="cb"><h3>${e(p.t)}</h3><p>${e(p.x.slice(0,90))}</p><time>${p.d}</time></div></a>`).join(''):'<p class="none">검색 결과가 없어요.</p>'}
I.addEventListener('input',go);
</script>''', '블로그 검색', '/search/'))

# 404, ads.txt, sitemap, rss, robots
(OUT / '404.html').write_text(page('페이지를 찾을 수 없어요', '<div class="nf"><h1>404</h1><p>요청한 페이지를 찾을 수 없어요.</p><a href="/">홈으로</a></div>', canon='/404.html'), encoding='utf-8')
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

imgs = set()
for p in posts:
    imgs |= set(re.findall(r'src="(/wp-content/[^"]+)"', p['body']))
    if p['thumb'].startswith('/wp-content/'): imgs.add(p['thumb'])
(OUT.parent / 'needed_images.txt').write_text('\n'.join(sorted(imgs)), encoding='utf-8')
print(f'posts={len(posts)} images_needed={len(imgs)}')
