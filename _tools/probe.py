# 아마존 응모 소식을 전하는 뉴스·정보 사이트 피드 접속 시험 (상태·크기·관련 글 수만 출력)
import requests, re, time
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 blvlblog-stock-check","Accept-Language":"ja,en;q=0.8"}
T=[("dengeki_rss","https://dengekionline.com/rss"),("dengeki_feed","https://dengekionline.com/feed"),("dengeki_art","https://dengekionline.com/article/202608/83452"),
   ("famitsu_rss","https://www.famitsu.com/rss/fcom_all.rdf"),("famitsu_art","https://www.famitsu.com/article/202606/77986"),
   ("usedoor_feed","https://usedoor.jp/feed/"),("usedoor_art","https://usedoor.jp/news/2023-09-12-amazon-pokemon-card-game-kodai-no-houkou-mirai-no-issen-shoutai-request/"),
   ("torecamap_feed","https://torecamap.co.jp/feed/"),("torecamap_col","https://torecamap.co.jp/column/amazon-lottery/"),
   ("gp_pokeca_feed","https://premium.gamepedia.jp/pokeca/feed/"),("gp_toreca_feed","https://premium.gamepedia.jp/toreca/feed/"),
   ("snkrdunk_32581","https://snkrdunk.com/articles/32581/"),("pokemoncard_info","https://www.pokemon-card.com/info/"),("onepiece_news","https://www.onepiece-cardgame.com/news/")]
for n,u in T:
    try:
        r=requests.get(u,headers=H,timeout=25); t=r.text
        asins=sorted(set(re.findall(r"amazon\.co\.jp/(?:[^\"'\s<>]*/)?(?:dp|gp/product)/([A-Z0-9]{10})",t)))
        inv=t.count("招待")
        items=len(re.findall(r"<item[ >]",t)) or len(re.findall(r"<entry[ >]",t))
        print(f"{n}\t{r.status_code}\t{len(t)}\titems={items}\t招待={inv}\tasins={len(asins)} {asins[:8]}\t{r.url[:80]}")
    except Exception as e: print(n,"ERR",type(e).__name__)
    time.sleep(2)
