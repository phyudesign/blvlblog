import requests, re
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 blvlblog-stock-check"}
for u in ["https://pokemonkorea.co.kr/news/2/21508","https://pokemoncard.co.kr/card/976"]:
    t=requests.get(u,headers=H,timeout=20).text
    print("=====",u,len(t))
    for m in re.finditer(r'<img[^>]+src="([^"]+)"[^>]*>',t): print(" ",m.group(1)[:140], "|", (re.search(r'alt="([^"]*)"',m.group(0)) or [None,""])[1][:40])
