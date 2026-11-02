# 홈 슬라이드용 상품 사진 배경 지우기: 아마존 대표 사진을 받아 가장자리부터 이어진 흰 바탕만 투명하게 → assets/products/<ASIN>.webp
import sys, io, pathlib, requests
from collections import deque
from PIL import Image, ImageFilter
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from monitor import AMZ_IMG, amz_img
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "products"; OUT.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}

def cut(im, tol=26):
    im = im.convert("RGB"); im.thumbnail((700, 700)); w, h = im.size; px = im.load()
    bg = [[False] * w for _ in range(h)]; q = deque()
    for x in range(w): q.append((x, 0)); q.append((x, h - 1))
    for y in range(h): q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or bg[y][x]: continue
        r, g, b = px[x, y]
        if min(r, g, b) < 255 - tol or max(r, g, b) - min(r, g, b) > 18: continue
        bg[y][x] = True; q.extend(((x+1, y), (x-1, y), (x, y+1), (x, y-1)))
    a = Image.new("L", (w, h), 255); ap = a.load()
    for y in range(h):
        for x in range(w):
            if bg[y][x]: ap[x, y] = 0
    a = a.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = im.convert("RGBA"); out.putalpha(a)
    return out.crop(out.getbbox() or (0, 0, w, h))

for asin in AMZ_IMG:
    try:
        r = requests.get(amz_img(asin, 1000), headers=H, timeout=30); r.raise_for_status()
        cut(Image.open(io.BytesIO(r.content))).save(OUT / f"{asin}.webp", "WEBP", quality=88)
        print("ok", asin)
    except Exception as e: print("fail", asin, e)
