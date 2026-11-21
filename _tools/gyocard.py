"""본문 카드·상품 이미지에 교묘를 섞는 여러 연출 (한 글 안에서 연출을 섞어 써요 — 똑같은 합성만 반복하지 않기)

    python3 _tools/gyocard.py 연출 원본이미지 저장.webp [옵션 side=left|right pos=0.5]

연출:
  peek / wave   카드 뒤에 숨어 윗변을 잡고 빼꼼 (peek.py)
  hold          자기보다 큰 카드를 머리 위로 들어 올려 자랑  (스티커 gyomyo-card-hold-up: 초록 사각형 자리에 카드)
  hug           큰 카드를 옆에서 끌어안고 볼 비비기        (gyomyo-card-hug)
  pack          카드 앞에 앉아 팩 뜯기                       (gyomyo-card-open-pack)
  loupe         카드 앞에 앉아 돋보기로 감정                  (gyomyo-card-magnifier)
  sleep         카드에 등을 기대고 낮잠                       (gyomyo-card-sleep)
  photo         카드 옆에서 휴대폰으로 사진 찍기              (gyomyo-card-photo)
  aura / flex   카드 옆에서 카드 속 포즈 따라 하기 (파동 / 레슬러) (gyomyo-card-mimic-*)
원본 스티커: _thumbs/out/gyomyo-card-*-1.png (흰 배경 → 투명). 결과는 투명 배경 webp.
"""
import sys, pathlib
from PIL import Image, ImageFilter, ImageDraw
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import peek

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "_thumbs" / "out"
STICK = {"hold": "hold-up", "hug": "hug", "pack": "open-pack", "loupe": "magnifier", "sleep": "sleep",
         "photo": "photo", "aura": "mimic-aura", "flex": "mimic-flex"}


def _sticker(name, green=False):
    im = peek._cut_white(Image.open(OUT / f"gyomyo-card-{name}-1.png"))
    box = None
    if green:   # 초록 사각형(카드 자리)을 찾아 투명하게
        px = im.load(); w, h = im.size; xs = []; ys = []
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if a and g > 150 and g > r + 50 and g > b + 50:
                    px[x, y] = (r, g, b, 0); xs.append(x); ys.append(y)
        if xs:
            xs.sort(); ys.sort(); n = len(xs)
            box = (xs[n // 100], ys[n // 100], xs[-n // 100 - 1], ys[-n // 100 - 1])   # 튀는 점 몇 개 무시
    bb = im.getbbox(); im = im.crop(bb)
    if box: box = (box[0] - bb[0], box[1] - bb[1], box[2] - bb[0], box[3] - bb[1])
    return im, box


def _shadow(size, w, h):
    sh = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    return sh, d


def _fit(im, h):
    return im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)


def make(kind, src, out, side="right", pos=.5):
    if kind in ("peek", "top", "wave"):
        return peek.make(src, "wave" if kind == "wave" else "top", out, pos)
    card = Image.open(src).convert("RGBA"); H = 900
    card = _fit(card, H); W = card.width
    if kind in ("hold", "hug"):
        s, box = _sticker(STICK[kind], green=True)
        if not box: raise SystemExit("초록 카드 자리를 못 찾았어요")
        bw, bh = box[2] - box[0], box[3] - box[1]
        k = H * 1.0 / bh                                   # 카드가 원래 크기(900px)로 들어가게 스티커를 키워요
        s = s.resize((int(s.width * k), int(s.height * k)), Image.LANCZOS)
        box = tuple(int(v * k) for v in box); bw, bh = box[2] - box[0], box[3] - box[1]
        c = Image.open(src).convert("RGBA").resize((bw + 6, bh + 6), Image.LANCZOS)
        cv = Image.new("RGBA", s.size, (0, 0, 0, 0))
        cv.alpha_composite(c, (box[0] - 3, box[1] - 3))   # 카드는 교묘 뒤(앞발·테두리가 카드 위에 얹혀요)
        cv.alpha_composite(s)
    elif kind in ("pack", "loupe", "photo", "aura", "flex"):
        s, _ = _sticker(STICK[kind]); s = _fit(s, int(H * (.5 if kind in ("pack", "loupe") else .62)))
        if kind in ("pack", "loupe"):                      # 카드 앞에 앉아서 — 카드 아래쪽을 조금 가려요
            pad = int(s.width * .45)
            cv = Image.new("RGBA", (W + pad, H + int(s.height * .12)), (0, 0, 0, 0))
            cx = pad if side == "left" else 0
            cv.alpha_composite(card, (cx, 0))
            sx = 0 if side == "left" else cv.width - s.width
            cv.alpha_composite(s, (sx, cv.height - s.height))
        else:                                              # 카드 옆에 서서 (사진 찍기·포즈 따라 하기)
            gap = int(W * .04)
            cv = Image.new("RGBA", (W + gap + s.width, H), (0, 0, 0, 0))
            if side == "left":
                cv.alpha_composite(s, (0, H - s.height)); cv.alpha_composite(card, (s.width + gap, 0))
            else:
                cv.alpha_composite(card, (0, 0)); cv.alpha_composite(s, (W + gap, H - s.height))
    elif kind == "sleep":                                  # 카드 왼쪽 아래에 등을 기대고 낮잠
        s, _ = _sticker(STICK[kind]); s = _fit(s, int(H * .45))
        over = int(s.width * .12)
        cv = Image.new("RGBA", (W + s.width - over, H), (0, 0, 0, 0))
        cv.alpha_composite(card, (s.width - over, 0)); cv.alpha_composite(s, (0, H - s.height))
    else:
        raise SystemExit("연출 이름을 확인해 주세요: " + kind)
    out = pathlib.Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    cv.thumbnail((1000, 1000), Image.LANCZOS)
    cv.save(out, "WEBP", quality=86, method=6)
    return cv.size


if __name__ == "__main__":
    a = sys.argv[1:]; opt = dict(x.split("=", 1) for x in a[3:])
    print(make(a[0], a[1], a[2], opt.get("side", "right"), float(opt.get("pos", .5))))
