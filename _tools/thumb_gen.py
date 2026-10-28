# -*- coding: utf-8 -*-
"""blvl 캐릭터 썸네일 생성기 (GitHub Actions에서 실행)

요청 파일: _thumbs/<이름>.json
  {
    "prompt": "장면 설명",              # 필수
    "n": 2,                            # 시안 개수 (기본 2)
    "size": "1024x1024",               # 기본 정사각형
    "quality": "high",                 # low | medium | high
    "character": "gyomyo",             # gyomyo | jangnan | pengson (참고 이미지 = _character/<id>/)
    "mode": "thumbnail",               # thumbnail | emoticon
    "refs": ["_character/front.png"],  # 직접 지정할 때만
    "regenerate": false                # true면 이미 만든 결과가 있어도 다시 생성
  }
결과: _thumbs/out/<이름>-1.png, -2.png …  (요청 파일 옆 기록: _thumbs/out/<이름>.log.json)

필요한 것: 저장소 Secret OPENAI_API_KEY
선택: 저장소 Variable OPENAI_IMAGE_MODEL (기본 gpt-image-2)
"""
import os, sys, json, base64, time, pathlib, requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQ_DIR, OUT_DIR, CHAR_DIR = ROOT / "_thumbs", ROOT / "_thumbs" / "out", ROOT / "_character"
MODEL = os.environ.get("OPENAI_IMAGE_MODEL") or "gpt-image-2"
KEY = os.environ.get("OPENAI_API_KEY")
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}

CHARS = json.loads((CHAR_DIR / "characters.json").read_text(encoding="utf-8")) if (CHAR_DIR / "characters.json").exists() else {}

LOOK = ("Keep the exact hand-drawn look of the references: rough black crayon/pencil line art with grainy texture, "
        "simple shapes, minimal detail, the same face and proportions. ")
MODES = {
    "thumbnail": ("Square blog thumbnail. The character keeps its black crayon line art; the background is a soft pastel colored-paper "
                  "texture with a few simple crayon doodles. Bright, cute and funny. Keep the top 35% of the image empty and calm for a title "
                  "that will be added later. Do not write any text or letters. "),
    "emoticon": ("A sticker sheet of the character's emoticons on a pure white background, arranged in an even grid with generous spacing, "
                 "each sticker fully separated with no overlap and nothing touching the edges. Same crayon line style for every sticker, "
                 "black lines only with at most a tiny touch of pink on the cheeks. Do not write any text or letters. "),
}
SAFE = "Do not include any existing franchise characters, brand logos, trademarks or real product packaging artwork. "

def build_prompt(req):
    c = CHARS.get(req.get("character", ""), {})
    who = (f"The attached reference images show {c['name']}, an original mascot of the blvl blog: {c['desc']} " if c else
           "The attached reference image(s) show an original mascot character of the blvl blog. ")
    return who + LOOK + MODES.get(req.get("mode", "thumbnail"), "") + SAFE + "Scene: " + req["prompt"]

STYLE_LEGACY = (
    "The attached reference image(s) show 'blvl', the original mascot character of the blvl blog. "
    "Draw this exact character: keep its face, proportions, colors, outfit and line style identical to the references. "
    "Square blog thumbnail, bright and cute, clean composition, leave clear empty space for a title. "
    "Do not include any existing franchise characters, brand logos, trademarks or real product packaging artwork. "
    "Scene: "
)

def todo(only):
    for f in sorted(REQ_DIR.glob("*.json")):
        if only and f.stem not in only: continue
        req = json.loads(f.read_text(encoding="utf-8"))
        done = (OUT_DIR / f"{f.stem}-1.png").exists()
        if done and not req.get("regenerate"): continue
        yield f.stem, req

def refs_for(req):
    folder = CHAR_DIR / req["character"] if req.get("character") else CHAR_DIR
    paths = [ROOT / p for p in req.get("refs", [])] or sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT)
    return [p for p in paths if p.exists()][:16]

def generate(name, req):
    refs = refs_for(req)
    data = {"model": MODEL, "prompt": build_prompt(req), "n": str(req.get("n", 2)),
            "size": req.get("size", "1024x1024"), "quality": req.get("quality", "high")}
    headers = {"Authorization": f"Bearer {KEY}"}
    if refs:
        files = [("image[]", (p.name, p.read_bytes())) for p in refs]
        r = requests.post("https://api.openai.com/v1/images/edits", headers=headers, data=data, files=files, timeout=600)
    else:
        data["n"] = int(data["n"])
        r = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=data, timeout=600)
    if r.status_code != 200:
        raise RuntimeError(f"{name}: OpenAI {r.status_code} {r.text[:500]}")
    res = r.json(); imgs = res["data"]; usage = res.get("usage") or {}
    det = usage.get("input_tokens_details") or {}
    # gpt-image-2 공시 단가(1M 토큰당): 텍스트 입력 $5, 이미지 입력 $8, 이미지 출력 $30
    cost = (det.get("text_tokens", 0) * 5 + det.get("image_tokens", 0) * 8 + usage.get("output_tokens", 0) * 30) / 1e6
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outs = []
    for i, d in enumerate(imgs, 1):
        p = OUT_DIR / f"{name}-{i}.png"
        p.write_bytes(base64.b64decode(d["b64_json"]))
        outs.append(str(p.relative_to(ROOT)))
    log = {"model": MODEL, "prompt": req["prompt"], "refs": [str(p.relative_to(ROOT)) for p in refs],
           "outputs": outs, "usage": usage, "est_cost_usd": round(cost, 4), "created": time.strftime("%Y-%m-%d %H:%M:%S")}
    (OUT_DIR / f"{name}.log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{name}: {len(outs)}장 생성 → {', '.join(outs)} · 예상 비용 ${cost:.4f}")

if __name__ == "__main__":
    if not KEY:
        sys.exit("OPENAI_API_KEY Secret이 등록되지 않았어요.")
    only = set(a for a in sys.argv[1:] if a)
    jobs = list(todo(only))
    if not jobs: print("새로 만들 썸네일이 없어요.")
    failed = 0
    for name, req in jobs:
        try: generate(name, req)
        except Exception as e:
            failed += 1; print("실패:", e)
    sys.exit(1 if failed else 0)
