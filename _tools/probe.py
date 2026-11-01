# 아마존 상품 페이지 구조 확인: 버튼·재고·판매자 관련 부분만 짧게 출력 (내용 전체는 저장하지 않음)
import requests, re, time
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36","Accept-Language":"ja-JP,ja;q=0.9"}
def txt(s): return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",s)).strip()
for asin in ["B0H4PQ6LR5","B0GXCRBL5J","B0HFVPJF4Q","B0FSJXSPPX","B0H43ZX8LK"]:
    try:
        r=requests.get(f"https://www.amazon.co.jp/dp/{asin}",headers=H,timeout=25); h=r.text
        print(f"== {asin} {r.status_code} {len(h)} captcha={'captcha' in h.lower() or 'validateCaptcha' in h}")
        m=re.search(r'id="productTitle"[^>]*>(.*?)</span>',h,re.S); print(" title:",txt(m.group(1))[:80] if m else None)
        for key in ["招待","invitation","inviteButton","add-to-cart-button","buy-now-button","現在在庫切れ","在庫あり","一時的に在庫切れ","予約","出荷元","販売元","merchant-info","priceToPay","a-price-whole","landingImage","outOfStock","availability"]:
            i=h.find(key)
            if i>=0: print(f" [{key}]", txt(h[max(0,i-150):i+250])[:220])
            else: print(f" [{key}] -")
        for m in re.finditer(r'id="(availability|merchantInfoFeature_feature_div|offerDisplayFeatures_desktop|invitation[^"]*|[^"]*[Ii]nvit[^"]*)"',h): print(" id:",m.group(1))
        im=re.search(r'"hiRes":"(https://[^"]+)"',h) or re.search(r'id="landingImage"[^>]+src="([^"]+)"',h); print(" img:",im.group(1) if im else None)
    except Exception as e: print(asin,"ERR",e)
    time.sleep(4)
