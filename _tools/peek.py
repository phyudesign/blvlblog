"""본문 공식 카드·상품 이미지에 교묘를 섞어요: 카드 뒤에 숨어 있다가 앞발로 카드를 잡고 빼꼼.

    python3 _tools/peek.py 카드이미지 top|wave|side 저장경로.webp [위치 0~1]

교묘 스티커 원본: _thumbs/out/gyomyo-peek-{top,side,wave}-1.png (흰 배경 → 투명 처리, 잘린 면 정리)
결과는 투명 배경 webp (카드 위·옆으로 교묘가 튀어나와서 캔버스가 카드보다 커요).
"""
import sys, pathlib
from collections import deque
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_thumbs" / "out"
_cache = {}


def _cut_white(im):
    im = im.convert("RGBA"); w, h = im.size; px = im.load(); seen = bytearray(w * h); q = deque()
    for x in range(w): q += [(x, 0), (x, h - 1)]
    for y in range(h): q += [(0, y), (w - 1, y)]
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or seen[y * w + x]: continue
        r, g, b, a = px[x, y]
        if min(r, g, b) < 228: continue
        seen[y * w + x] = 1; px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    a = im.split()[3].filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.6))
    im.putalpha(a)
    return im


def sprite(kind):
    if kind in _cache: return _cache[kind]
    im = _cut_white(Image.open(SRC / f"gyomyo-peek-{kind}-1.png"))
    a = im.split()[3]; w, h = im.size
    if kind == "wave":   # 바닥 선과 그 아래(꼬리)를 잘라내요
        dark = [sum(1 for x in range(w) if im.getpixel((x, y))[3] > 0 and sum(im.getpixel((x, y))[:3]) < 200) for y in range(h)]
        line = max(range(h // 2, h), key=lambda y: dark[y])
        im = im.crop((0, 0, w, line - 2))
    if kind == "side":   # 오른쪽 세로 선(벽)을 잘라내요
        dark = [sum(1 for y in range(h) if im.getpixel((x, y))[3] > 0 and sum(im.getpixel((x, y))[:3]) < 200) for x in range(w)]
        line = max(range(w // 2, w), key=lambda x: dark[x])
        im = im.crop((0, 0, line - 3, h))
    im = im.crop(im.getbbox())
    _cache[kind] = im
    return im


def make(card, kind, out, pos=.5, scale=.62):
    c = Image.open(card).convert("RGBA")
    W, H = c.size; s = sprite(kind)
    if kind == "side":
        sh = int(H * scale * .62); s = s.resize((int(s.width * sh / s.height), sh), Image.LANCZOS)
        grip = int(s.width * .07)                        # 앞발이 카드 왼쪽 가장자리를 덮는 폭
        pad = s.width - grip
        cv = Image.new("RGBA", (W + pad, H), (0, 0, 0, 0)); cv.alpha_composite(c, (pad, 0))
        y = int((H - sh) * pos); cv.alpha_composite(s, (0, y))
    else:
        sw = int(W * scale); s = s.resize((sw, int(s.height * sw / s.width)), Image.LANCZOS)
        grip = int(s.height * (.16 if kind == "top" else .12))   # 앞발이 카드 윗변을 덮는 높이
        pad = s.height - grip
        cv = Image.new("RGBA", (W, H + pad), (0, 0, 0, 0)); cv.alpha_composite(c, (0, pad))
        x = int((W - sw) * pos); cv.alpha_composite(s, (x, 0))
    out = pathlib.Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    cv.save(out, "WEBP", quality=86, method=6)
    return cv.size


if __name__ == "__main__":
    a = sys.argv[1:]
    print(make(a[0], a[1], a[2], float(a[3]) if len(a) > 3 else .5))
