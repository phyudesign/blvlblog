# 쇼핑몰 접속 시험: 상태 코드, 크기, 판매 관련 키워드 포함 여부만 출력 (내용은 저장하지 않음)
import requests, urllib.parse as u, re, time
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 blvlblog-stock-check","Accept-Language":"ja,en;q=0.8"}
q=u.quote
T=[("gp_pokeca_feed","https://premium.gamepedia.jp/pokeca/feed/"),
   ("gp_toreca_feed","https://premium.gamepedia.jp/toreca/feed/"),
   ("gp_shopping_feed","https://premium.gamepedia.jp/shopping/feed/"),
   ("gp_pokeca_156","https://premium.gamepedia.jp/pokeca/archives/156"),
   ("snkrdunk_32581","https://snkrdunk.com/articles/32581/"),
   ("altema_op","https://altema.jp/onepiececard/soukaityuusen"),
   ("altema_pk","https://altema.jp/pokemoncard/"),
   ("pokemoncard_info","https://www.pokemon-card.com/info/"),
   ("pco_news","https://www.pokemoncenter-online.com/news/"),
   ("pco_top","https://www.pokemoncenter-online.com/"),
   ("onepiece_news","https://www.onepiece-cardgame.com/news/"),
   ("amazon_asin","https://www.amazon.co.jp/dp/B0H4PQ6LR5"),
]
KW=["Amazon","ポケモンセンター","ホビーサーチ","駿河屋","在庫あり","カートに入れる","予約受付中","抽選","品切れ","販売終了","在庫なし","ハドウシーカー"]
for name,url in T:
    try:
        r=requests.get(url,headers=H,timeout=25); t=r.text
        hits=[k for k in KW if k in t]
        print(f"{name}\t{r.status_code}\t{len(t)}\t{','.join(hits)}\t{r.url[:90]}")
        if r.status_code != 200:
            print("   ", re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S)))[:300])
            print("   server:", r.headers.get("server"), r.headers.get("x-cache", ""), r.headers.get("cf-ray", ""))
    except Exception as e:
        print(f"{name}\tERR\t{type(e).__name__}")
    time.sleep(2)
