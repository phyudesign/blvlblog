# 국내판 포켓몬카드 정보원 접속 시험 (상태·크기·관련 단어만)
import requests, re, time
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 blvlblog-stock-check","Accept-Language":"ko,en;q=0.8"}
T=["https://pokemoncard.co.kr/","https://pokemoncard.co.kr/news","https://www.pokemonkorea.co.kr/","https://pokemonkorea.co.kr/news",
   "https://www.pokemonstore.co.kr/","https://pokemonstore.co.kr/","https://www.pokemoncenter.co.kr/","https://pokemoncenter.co.kr/",
   "https://www.pokemoncenter-online.co.kr/","https://store.pokemonkorea.co.kr/","https://pokemoncenter-korea.com/"]
KW=["응모","추첨","판매","품절","입고","확장팩","포켓몬카드","공지","재고","예약","포켓몬센터","포켓몬스토어"]
for u in T:
    try:
        r=requests.get(u,headers=H,timeout=20); t=r.text
        title=(re.search(r"<title>(.*?)</title>",t,re.S) or [None,""])[1].strip()[:60]
        print(f"{u}\t{r.status_code}\t{len(t)}\t{title}\t{','.join(k for k in KW if k in t)}\t-> {r.url[:70]}")
    except Exception as e: print(u,"ERR",type(e).__name__)
    time.sleep(1)
