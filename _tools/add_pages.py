# -*- coding: utf-8 -*-
"""정적 사이트에 소개·개인정보처리방침·문의 페이지를 추가하고, 모든 페이지 푸터에 링크를 넣는다.
사용법: python3 _tools/add_pages.py <사이트 루트> <연락 이메일>"""
import re, sys, html, urllib.parse
from pathlib import Path

ROOT = Path(sys.argv[1]); EMAIL = sys.argv[2]
SITE = "https://blvlblog.com"; TITLE = "blvl blog"
TODAY = "2026년 10월 28일"
esc = html.escape

FOOTER_OLD = re.compile(r'<footer class="site-footer">.*?</footer>', re.S)
FOOTER_NEW = ('<footer class="site-footer"><nav class="footer-links" aria-label="사이트 정보">'
              '<a href="/about/">소개</a> · <a href="/privacy/">개인정보처리방침</a> · <a href="/contact/">문의</a>'
              '</nav>© 2026 blvl blog</footer>')

# 기존 글 하나를 틀로 사용 (헤더·사이드바 그대로 재사용)
tpl = (ROOT / '애드센스-문제-해결' / 'index.html').read_text(encoding='utf-8')
header = tpl[tpl.index('<body>') + len('<body>'):tpl.index('<div class="site-content">')]
sidebar = tpl[tpl.index('<div class="sidebar">'):tpl.index('<footer class="site-footer">')]
ads = re.search(r'<script async src="https://pagead2[^>]*></script>', tpl).group(0)

def build(slug, title, desc, body):
    canon = f'/{slug}/'
    full = f'{title} | {TITLE}'
    doc = f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{canon}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{SITE}{canon}">
<link rel="alternate" type="application/rss+xml" title="{TITLE}" href="/feed.xml">
<link rel="preload" href="/assets/fonts/NanumGothic-Regular.woff" as="font" type="font/woff" crossorigin>
<link rel="icon" href="/assets/favicon-32.png" sizes="32x32"><link rel="icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/blog.css?v=5">
{ads}
</head><body>{header}<div class="site-content"><main class="content-area"><article class="inside-article"><header><h1 class="entry-title">{esc(title)}</h1>
<div class="entry-meta">최종 수정일: {TODAY}</div></header>
<div class="entry-content">
{body}
</div></article></main>{sidebar}{FOOTER_NEW}
</body></html>'''
    d = ROOT / slug; d.mkdir(exist_ok=True)
    (d / 'index.html').write_text(doc, encoding='utf-8')

mail = f'<a href="mailto:{esc(EMAIL)}">{esc(EMAIL)}</a>'

build('about', '블로그 소개', 'blvl blog는 직접 써 보고 겪은 테크·크리에이티브·생활 정보를 기록하는 개인 블로그입니다.', f'''
<p><strong>blvl blog</strong>는 blvl이 운영하는 개인 블로그입니다. 직접 써 보고, 만들어 보고, 겪어 본 것만 기록하는 것을 원칙으로 합니다.</p>
<h2>주로 다루는 이야기</h2>
<ul>
<li><strong>TECH</strong> — AI 이미지·영상 도구, 맥(Mac) 활용 팁, 작업용 소프트웨어 사용기</li>
<li><strong>ART &amp; CULTURE</strong> — 디자인·브랜딩, 전시와 공연, 크리에이티브 작업 이야기</li>
<li><strong>LIFE TIPS</strong> — 일상에서 바로 써먹을 수 있는 실용 정보</li>
<li><strong>ECONOMY</strong> — 산업과 기술 변화에 대한 생각</li>
</ul>
<h2>글을 쓰는 원칙</h2>
<ul>
<li>사용해 보지 않은 제품·서비스를 써 본 것처럼 소개하지 않습니다.</li>
<li>가격·일정처럼 바뀌는 정보는 작성일을 함께 밝히고, 바뀐 사실을 알게 되면 고칩니다.</li>
<li>대가를 받고 작성한 글이 있다면 글 안에 그 사실을 분명히 표시합니다.</li>
</ul>
<h2>연락처</h2>
<p>잘못된 정보 제보, 협업 제안 등은 {mail} 로 보내 주세요. 자세한 내용은 <a href="/contact/">문의</a> 페이지를 참고해 주세요.</p>
''')

build('privacy', '개인정보처리방침', 'blvl blog의 개인정보처리방침 — 쿠키와 Google 애드센스 광고에 관한 안내입니다.', f'''
<p>blvl blog(이하 "블로그", <a href="{SITE}/">{SITE.replace("https://", "")}</a>)는 방문자의 개인정보를 소중히 여기며, 「개인정보 보호법」 등 관련 법령을 준수합니다. 이 방침은 블로그 이용 시 어떤 정보가 어떻게 처리되는지 안내합니다.</p>
<h2>1. 블로그가 직접 수집하는 개인정보</h2>
<p>블로그는 회원가입, 댓글 등 방문자가 직접 개인정보를 입력하는 기능을 운영하지 않으므로 이름, 연락처 등의 개인정보를 직접 수집하지 않습니다. 다만 방문자가 이메일로 문의하는 경우, 답변을 위해 보낸 분의 이메일 주소와 문의 내용을 받게 되며, 이 정보는 답변 목적으로만 사용하고 처리가 끝나면 지체 없이 삭제합니다.</p>
<h2>2. 자동으로 수집되는 정보와 쿠키</h2>
<p>블로그는 GitHub Pages로 호스팅되며, 호스팅 제공자는 서비스 운영과 보안을 위해 방문자의 IP 주소 등 접속 기록을 처리할 수 있습니다. 또한 아래의 제3자 광고 서비스가 쿠키를 사용할 수 있습니다.</p>
<h2>3. Google 애드센스 광고와 쿠키</h2>
<ul>
<li>블로그는 Google 애드센스를 통해 광고를 게재합니다.</li>
<li>Google을 포함한 제3자 공급업체는 쿠키를 사용하여 방문자가 이 블로그 및 다른 웹사이트를 이전에 방문한 기록을 바탕으로 광고를 게재합니다.</li>
<li>Google은 광고 쿠키를 사용하여 방문자가 이 블로그나 인터넷의 다른 사이트를 방문한 기록을 바탕으로 Google과 파트너가 맞춤 광고를 게재할 수 있도록 합니다.</li>
<li>방문자는 <a href="https://adssettings.google.com/" target="_blank" rel="noopener">Google 광고 설정</a>에서 맞춤 광고를 해제할 수 있으며, <a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener">www.aboutads.info</a>에서 제3자 공급업체의 맞춤 광고용 쿠키 사용을 해제할 수 있습니다.</li>
<li>Google의 데이터 사용 방식은 <a href="https://policies.google.com/technologies/partner-sites" target="_blank" rel="noopener">Google 파트너 사이트 정보 사용 방식</a>에서 확인할 수 있습니다.</li>
</ul>
<h2>4. 쿠키 거부 방법</h2>
<p>방문자는 웹 브라우저 설정에서 쿠키 저장을 거부하거나 저장된 쿠키를 삭제할 수 있습니다. 쿠키를 거부해도 블로그 글을 읽는 데에는 지장이 없으나, 일부 광고가 맞춤형이 아닌 일반 광고로 표시될 수 있습니다.</p>
<h2>5. 외부 링크</h2>
<p>블로그 글에는 외부 사이트로 연결되는 링크가 포함될 수 있습니다. 링크된 사이트의 개인정보 처리에 대해서는 해당 사이트의 방침이 적용됩니다.</p>
<h2>6. 문의처</h2>
<p>개인정보와 관련한 문의는 {mail} 로 보내 주시면 성실히 답변드리겠습니다.</p>
<h2>7. 방침의 변경</h2>
<p>이 방침은 {TODAY}부터 적용됩니다. 내용이 바뀌는 경우 이 페이지를 통해 알려 드립니다.</p>
''')

build('contact', '문의', 'blvl blog에 정보 제보, 수정 요청, 협업 제안을 보내는 방법입니다.', f'''
<p>blvl blog에 관한 문의는 아래 이메일로 보내 주세요.</p>
<p style="font-size:1.15em"><strong>이메일:</strong> {mail}</p>
<h2>이런 내용을 보내 주세요</h2>
<ul>
<li>글 속 정보가 틀렸거나 바뀐 경우 — 해당 글 주소와 함께 알려 주시면 확인 후 고치겠습니다.</li>
<li>글에 대한 질문</li>
<li>협업·리뷰 제안</li>
</ul>
<p>보내 주신 이메일 주소와 내용은 답변을 위해서만 사용합니다. 자세한 내용은 <a href="/privacy/">개인정보처리방침</a>을 참고해 주세요.</p>
''')

# 모든 페이지 푸터에 링크 추가
n = 0
for f in ROOT.rglob('*.html'):
    if '.git' in f.parts: continue
    s = f.read_text(encoding='utf-8')
    t = FOOTER_OLD.sub(FOOTER_NEW, s)
    if t != s:
        f.write_text(t, encoding='utf-8'); n += 1

# 사이트맵에 추가
sm = ROOT / 'sitemap.xml'
s = sm.read_text(encoding='utf-8')
for slug in ('about', 'privacy', 'contact'):
    loc = f'<url><loc>{SITE}/{slug}/</loc><lastmod>2026-10-28</lastmod></url>'
    if f'{SITE}/{slug}/' not in s:
        s = s.replace('</urlset>', loc + '\n</urlset>')
sm.write_text(s, encoding='utf-8')
print('footer updated:', n)
