# 쇼핑몰 접속 시험: 상태 코드, 크기, 판매 관련 키워드 포함 여부만 출력 (내용은 저장하지 않음)
import requests, urllib.parse as u, re, time
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 blvlblog-stock-check","Accept-Language":"ja,en;q=0.8"}
q=u.quote
T=[("yodobashi_search","https://www.yodobashi.com/?word="+q("ハドウシーカー")),
   ("yodobashi_limited","https://limited.yodobashi.com/"),
   ("amiami_search","https://slist.amiami.jp/top/search/list?s_keywords="+q("ハドウシーカー")),
   ("hobbysearch_search","https://www.1999.co.jp/search?searchkey="+q("ハドウシーカー")),
   ("rakutenbooks_search","https://books.rakuten.co.jp/search?sitem="+q("ハドウシーカー")),
   ("aeon_lottery","https://aeonretail.com/Page/k-lottery_sale.aspx"),
   ("pco_lottery","https://www.pokemoncenter-online.com/lottery/apply.html"),
   ("yellowsub","https://yellowsubmarine.co.jp/"),
   ("torecaplaza55","https://torecaplaza55.com/"),
   ("7net","https://7net.omni7.jp/search/?keyword="+q("ハドウシーカー")),
   ("pbandai","https://p-bandai.jp/search/?text="+q("ワンピースカード"))]
KW=["在庫あり","カートに入れる","予約受付中","抽選","品切れ","販売終了","在庫なし","ハドウシーカー"]
for name,url in T:
    try:
        r=requests.get(url,headers=H,timeout=25); t=r.text
        hits=[k for k in KW if k in t]
        print(f"{name}\t{r.status_code}\t{len(t)}\t{','.join(hits)}\t{r.url[:90]}")
    except Exception as e:
        print(f"{name}\tERR\t{type(e).__name__}")
    time.sleep(2)
