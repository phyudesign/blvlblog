# 전격온라인 초대 판매 글에서 아마존 링크별 판정 확인
import sys, re; sys.path.insert(0, "_tools")
import monitor as m
h = m.get("https://dengekionline.com/article/202608/83452")
for x in re.finditer(r'href="[^"]*amazon\.co\.jp[^"]*?/(?:dp|gp/product)/([A-Z0-9]{10})', h):
    a = x.group(1)
    if a[0].isdigit(): continue
    ctx = m.text_of(h[max(0, x.start()-1500):x.start()])
    print(a, x.start(), "招待" in ctx, "| head:", m._heading_before(h, x.start())[:50], "| tail:", ctx[-120:])
print(m.find_invites(h))
