# 홈 슬라이드용 상품 사진 배경 지우기: 아마존 대표 사진을 받아 가장자리부터 이어진 흰 바탕만 투명하게 → assets/products/<ASIN>.webp
import sys, io, pathlib, requests
from collections import deque
from PIL import Image, ImageFilter
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from monitor import AMZ_IMG, amz_img
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "products"; OUT.mkdir(parents=True, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}

def cut(im, tol=26, size=700):
    im = im.convert("RGB"); im.thumbnail((size, size)); w, h = im.size; px = im.load()
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

# 슬라이드 배경용 박스 아트 크롭 (배경 지운 박스 기준 비율: 왼쪽, 위, 오른쪽, 아래)
CROP = {
    "B0FJ7Z6RML": (0.0, 0.40, 0.56, 0.76), "B0FX7X71KK": (0.02, 0.12, 0.66, 0.55), "B0GP928YDZ": (0.08, 0.0, 0.78, 0.42),
    "B0GXCM4BCZ": (0.03, 0.10, 0.65, 0.48), "B0GXCRBL5J": (0.20, 0.02, 0.75, 0.42), "B0H43ZX8LK": (0.0, 0.12, 0.60, 0.55),
    "B0H4PQ6LR5": (0.08, 0.0, 0.75, 0.42), "B0HB3JQ6P4": (0.0, 0.28, 0.58, 0.75), "B0HFVPJF4Q": (0.0, 0.05, 0.60, 0.55),
}
ART = OUT.parent / "art"; ART.mkdir(exist_ok=True)
for asin, (l, t, r, b) in CROP.items():
    try:
        rq = requests.get(amz_img(asin, 1500), headers=H, timeout=30); rq.raise_for_status()
        c = cut(Image.open(io.BytesIO(rq.content)), size=1500); w, h = c.size
        art = c.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
        bg = Image.new("RGB", art.size, (255, 255, 255)); bg.paste(art, mask=art.split()[3])
        bg.save(ART / f"{asin}.jpg", "JPEG", quality=86); print("art", asin, bg.size)
    except Exception as e: print("art fail", asin, e)

for asin in AMZ_IMG:
    try:
        r = requests.get(amz_img(asin, 1000), headers=H, timeout=30); r.raise_for_status()
        cut(Image.open(io.BytesIO(r.content))).save(OUT / f"{asin}.webp", "WEBP", quality=88)
        print("ok", asin)
    except Exception as e: print("fail", asin, e)
