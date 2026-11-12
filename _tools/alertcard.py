"""속보 표지 만들기 (Pillow만 사용 — 재고 감시기 GitHub 작업에서 바로 돌아가요)

교묘 배경(_thumbs/out/gyomyo-alert-*-1.png, 포즈가 모두 다름) 위에 실제 상품 사진을 크게 얹고,
교묘와 카드 더미는 상품 앞으로 다시 올려요. 배경은 종류별로 돌아가며 써서 연속으로 같은 포즈가 나오지 않게 해요.

    from alertcard import make_alert_thumb
    make_alert_thumb(kind, product_img_url_or_path, out_path, last_bg="")
"""
import io, random, pathlib
from collections import deque
from PIL import Image, ImageFilter, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "_thumbs" / "out"
POOLS = {"stock": ["stock-a", "stock-b", "stock-c", "stock-d", "stock-e", "stock-f"],
         "invite": ["invite-a", "invite-b"], "krnews": ["kr-a", "kr-b"],
         "lottery": ["lottery-a", "lottery-b", "lottery-c"]}
SIZE = 1024


def pick_bg(kind, last=""):
    pool = [k for k in POOLS.get(kind, POOLS["stock"]) if (OUT / f"gyomyo-alert-{k}-1.png").exists()]
    if not pool and kind == "lottery":
        pool = [k for k in POOLS["stock"] if (OUT / f"gyomyo-alert-{k}-1.png").exists()]
    if not pool: return ""
    choices = [k for k in pool if k != last] or pool
    return random.choice(choices)


def _load(src):
    if str(src).startswith("http"):
        import requests
        r = requests.get(src, timeout=20, headers={"User-Agent": "Mozilla/5.0"}); r.raise_for_status()
        return Image.open(io.BytesIO(r.content))
    return Image.open(src)


def _cutout(im):
    """흰 배경 상품 사진이면 가장자리에서 이어진 흰색을 지워요(투명 PNG는 그대로)."""
    im = im.convert("RGBA")
    if im.getextrema()[3][0] < 250:  # 이미 투명 영역이 있음
        return im.crop(im.getbbox())
    w, h = im.size; px = im.load(); seen = bytearray(w * h); q = deque()
    for x in range(w): q.append((x, 0)); q.append((x, h - 1))
    for y in range(h): q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or seen[y * w + x]: continue
        r, g, b, a = px[x, y]
        if min(r, g, b) < 238: continue
        seen[y * w + x] = 1; px[x, y] = (r, g, b, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def _ink(im, width=7):
    """검은 크레용 테두리 + 그림자"""
    im = ImageOps.expand(im, border=width + 2, fill=(0, 0, 0, 0))
    a = im.split()[3]
    grow = a.filter(ImageFilter.MaxFilter(width * 2 + 1))
    pad = width + 24
    canvas = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("L", canvas.size, 0); sh.paste(grow.point(lambda v: v * 90 // 255), (pad, pad + 16))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 255)); shadow.putalpha(sh.filter(ImageFilter.GaussianBlur(10)))
    canvas.alpha_composite(shadow)
    line = Image.new("RGBA", grow.size, (27, 27, 31, 255)); line.putalpha(grow)
    canvas.alpha_composite(line, (pad, pad))
    canvas.alpha_composite(im, (pad, pad))
    return canvas


def _front_mask(bg, regions=((48, 50, 100, 100), (0, 82, 46, 100)), key_xy=(400, 600), tol=70):
    px = bg.load(); key = px[key_xy]
    near = lambda c: abs(c[0] - key[0]) + abs(c[1] - key[1]) + abs(c[2] - key[2]) <= tol
    mask = Image.new("L", bg.size, 0); mp = mask.load(); S = bg.size[0] / 100
    for x0, y0, x1, y1 in regions:
        X0, Y0, X1, Y1 = int(x0 * S), int(y0 * S), min(bg.size[0], int(x1 * S)), min(bg.size[1], int(y1 * S))
        bgset = set(); q = deque()
        for x in range(X0, X1): q.append((x, Y0)); q.append((x, Y1 - 1))
        for y in range(Y0, Y1): q.append((X0, y)); q.append((X1 - 1, y))
        while q:
            x, y = q.popleft()
            if (x, y) in bgset or not (X0 <= x < X1 and Y0 <= y < Y1) or not near(px[x, y]): continue
            bgset.add((x, y)); q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        for y in range(Y0, Y1):
            for x in range(X0, X1):
                if (x, y) not in bgset: mp[x, y] = 255
    return mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1))


def make_alert_thumb(kind, product, out_path, last_bg=""):
    """만든 배경 키를 돌려줘요(다음 번에 같은 포즈를 피하려고 저장). 배경이 없으면 ""."""
    key = pick_bg(kind, last_bg)
    if not key: return ""
    bg = Image.open(OUT / f"gyomyo-alert-{key}-1.png").convert("RGB").resize((SIZE, SIZE))
    out = bg.copy().convert("RGBA")
    if product:
        try:
            p = _cutout(_load(product))
            box_w, box_h = int(SIZE * .52), int(SIZE * .46)
            scale = min(box_w / p.width, box_h / p.height)
            p = p.resize((max(1, int(p.width * scale)), max(1, int(p.height * scale))), Image.LANCZOS)
            p = _ink(p).rotate(random.choice((-5, -3, 3, 4)), expand=True, resample=Image.BICUBIC)
            cx, cy = int(SIZE * .33), int(SIZE * .72)
            out.alpha_composite(p, (max(0, cx - p.width // 2), min(SIZE - p.height, max(int(SIZE * .40), cy - p.height // 2))))
        except Exception as e:
            print("속보 표지: 상품 사진 실패", e)
    out = out.convert("RGB")
    out.paste(bg, (0, 0), _front_mask(bg))
    out_path = pathlib.Path(out_path); out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path, "JPEG", quality=86, optimize=True)
    return key
