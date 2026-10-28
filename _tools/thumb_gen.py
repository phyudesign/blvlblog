# -*- coding: utf-8 -*-
"""blvl 캐릭터 썸네일 생성기 (GitHub Actions에서 실행)

요청 파일: _thumbs/<이름>.json
  {
    "prompt": "장면 설명",              # 필수
    "n": 2,                            # 시안 개수 (기본 2)
    "size": "1024x1024",               # 기본 정사각형
    "quality": "high",                 # low | medium | high
    "refs": ["_character/front.png"],  # 생략하면 _character/ 안의 이미지 전부 사용
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

STYLE = (
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
    paths = [ROOT / p for p in req.get("refs", [])] or sorted(p for p in CHAR_DIR.iterdir() if p.suffix.lower() in IMG_EXT)
    return [p for p in paths if p.exists()][:16]

def generate(name, req):
    refs = refs_for(req)
    data = {"model": MODEL, "prompt": STYLE + req["prompt"], "n": str(req.get("n", 2)),
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
    imgs = r.json()["data"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outs = []
    for i, d in enumerate(imgs, 1):
        p = OUT_DIR / f"{name}-{i}.png"
        p.write_bytes(base64.b64decode(d["b64_json"]))
        outs.append(str(p.relative_to(ROOT)))
    log = {"model": MODEL, "prompt": req["prompt"], "refs": [str(p.relative_to(ROOT)) for p in refs],
           "outputs": outs, "created": time.strftime("%Y-%m-%d %H:%M:%S")}
    (OUT_DIR / f"{name}.log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{name}: {len(outs)}장 생성 → {', '.join(outs)}")

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
