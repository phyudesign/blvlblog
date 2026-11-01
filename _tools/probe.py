# 아마존 링크 주변 글자 구조 확인 (링크 글자와 앞뒤 짧은 문맥만 출력)
import requests, re, time, html
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 blvlblog-stock-check","Accept-Language":"ja,en;q=0.8"}
def tx(s): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s))).strip()
T=[("dengeki_art","https://dengekionline.com/article/202608/83452"),("gp_pokeca_feed","https://premium.gamepedia.jp/pokeca/feed/"),("gp_toreca_feed","https://premium.gamepedia.jp/toreca/feed/"),("famitsu_art","https://www.famitsu.com/article/202606/77986")]
for n,u in T:
    t=requests.get(u,headers=H,timeout=25).text
    if "feed" in n: t=html.unescape(t)
    print("=====",n)
    if "feed" in n:
        for it in re.findall(r"<item>(.*?)</item>",t,re.S)[:10]:
            ti=re.search(r"<title>(.*?)</title>",it,re.S); pd=re.search(r"<pubDate>(.*?)</pubDate>",it)
            print(" ITEM",tx(ti.group(1))[:90] if ti else "", pd.group(1) if pd else "", "asins:",sorted(set(re.findall(r"/dp/([A-Z0-9]{10})",it))))
    seen=set()
    for m in re.finditer(r'<a[^>]+href="([^"]*amazon\.co\.jp[^"]*?/dp/([A-Z0-9]{10})[^"]*)"[^>]*>(.*?)</a>',t,re.S):
        a=m.group(2)
        if a in seen or a[0].isdigit(): continue
        seen.add(a)
        before=tx(t[max(0,m.start()-400):m.start()])[-110:]
        print(f" {a} | link='{tx(m.group(3))[:60]}' | before='{before}'")
    time.sleep(2)
