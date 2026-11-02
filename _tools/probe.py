# 국내 공지 목록 구조 확인: 글 링크와 제목만 출력
import requests, re, time, html
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 blvlblog-stock-check","Accept-Language":"ko"}
def tx(s): return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",s))).strip()
for u in ["https://pokemonkorea.co.kr/news","https://pokemonkorea.co.kr/news/2","https://pokemoncard.co.kr/news","https://pokemonstore.co.kr/pages/product/list.html?depth=1&categoryNo=870548"]:
    t=requests.get(u,headers=H,timeout=20).text
    print("=====",u,len(t))
    seen=set()
    for m in re.finditer(r'<a[^>]+href="([^"]*(?:/news/\d+/\d+|/card/\d+|/news/\d+|product/detail[^"]*))"[^>]*>(.*?)</a>',t,re.S):
        if m.group(1) in seen: continue
        seen.add(m.group(1)); print(" ",m.group(1)[:80],"|",tx(m.group(2))[:90])
        if len(seen)>25: break
    if not seen: print(tx(t)[:600])
    for m in re.finditer(r'(fetch|axios|ajax|api)[^"\']{0,20}["\']([^"\']+)["\']',t): print(" api?",m.group(2)[:100])
    time.sleep(1)
