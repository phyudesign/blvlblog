# -*- coding: utf-8 -*-
"""blvl 캐릭터 썸네일 생성기 (GitHub Actions에서 실행)

요청 파일: _thumbs/<이름>.json
  {
    "prompt": "장면 설명",              # 필수
    "n": 2,                            # 시안 개수 (기본 2)
    "size": "1024x1024",               # 기본 정사각형
    "quality": "high",                 # low | medium | high
    "character": "gyomyo",             # gyomyo | jangnan | pengson (참고 이미지 = _character/<id>/)
    "mode": "magazine",                # magazine(기본) | scene(본문 삽화, 글자 없음) | thumbnail | poster | emoticon
    "bg": "mint green",                # magazine: 단색 배경 색 (글마다 다르게)
    "eyes": "spiral pupils",           # magazine: 상황별 눈동자
    "title2": "...",                   # magazine: 둘째 줄(빨강) 제목
    "refs": ["_character/front.png"],  # 직접 지정할 때만
    "style_refs": ["_character/style/thumb-style-1.png"],  # 스타일 참고(캐릭터 참고에 추가)
    "title": "...", "subtitle": "...", "badge": "...",     # poster 모드: 이미지 안에 그릴 문구
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
    "poster": ("Square blog thumbnail poster. Match the overall style of the last attached STYLE reference: a dense, energetic "
               "hand-drawn crayon illustration on cream paper, thick black crayon outlines, scribbly pastel crayon fills (pink, yellow, "
               "sky blue, lilac), sparkles and motion lines, the whole frame filled edge to edge. Big hand-lettered crayon title text "
               "near the top, with a black scribbled badge above it and a yellow highlighter ribbon for the subtitle. The character in "
               "the lower half, same face and proportions as its references, drawn in the same crayon style. Write the given Korean text "
               "exactly, letter for letter, with no extra words. "),
    # 기본 썸네일 스타일 (2026-10-31 슨생 확정): 잡지 표지형
    "magazine": ("Square blog thumbnail designed like a bold magazine cover. Match the attached STYLE reference closely. "
                 "Rules: (1) a single flat solid background color: {bg}, with only a few small flying props and sparkles; "
                 "(2) the character drawn very large in the lower two thirds, rough sketchy pencil lines with grainy texture and "
                 "light hand-colored fills, cropped by the frame edges; (3) the character's signature CRAZY EYES: big wide eyes whose "
                 "outer corners are slightly sharp and pointed; the pupils change with the mood of the scene: {eyes}; "
                 "(4) a tiny top label between two thin horizontal rules; (5) a huge title in two lines in the SAME typeface as the "
                 "reference: ultra-heavy, chunky, slightly rough-edged hand-cut bold Korean letters, line 1 in black, line 2 in red; "
                 "(6) the character's head and body overlap IN FRONT of the lower part of the title so some letters are partly hidden, "
                 "like a magazine cover, but every letter must stay readable. Write the given Korean text exactly, letter for letter, "
                 "with no extra words. "),
    # 본문 삽화: 썸네일과 같은 그림체, 글자 없음, 가로형
    "scene": ("A wide blog illustration in the same drawing style as the attached STYLE reference: rough sketchy pencil lines with "
              "grainy texture and light hand-colored fills, on a single flat solid background color: {bg}. The character is the star "
              "of the scene with its signature CRAZY EYES (big wide eyes with slightly sharp pointed outer corners; pupils: {eyes}). "
              "Simple, readable composition with few props. Do not write any text, letters, numbers or logos anywhere. "),
    "emoticon": ("A sticker sheet of the character's emoticons on a pure white background, arranged in an even grid with generous spacing, "
                 "each sticker fully separated with no overlap and nothing touching the edges. Same crayon line style for every sticker, "
                 "black lines only with at most a tiny touch of pink on the cheeks. Do not write any text or letters. "),
}
SAFE = "Do not include any existing franchise characters, brand logos, trademarks or real product packaging artwork. "

def build_prompt(req):
    c = CHARS.get(req.get("character", ""), {})
    who = (f"The attached reference images show {c['name']}, an original mascot of the blvl blog: {c['desc']} " if c else
           "The attached reference image(s) show an original mascot character of the blvl blog. ")
    text = ""
    if req.get("mode", "magazine") == "magazine":
        text = (f'Text to write — top label: "{req.get("badge", "")}"; title line 1 (black): "{req.get("title", "")}"; '
                f'title line 2 (red): "{req.get("title2", "")}". ')
        mode = MODES["magazine"].format(bg=req.get("bg", "warm yellow"), eyes=req.get("eyes", "sparkling yellow stars"))
        return who + LOOK + mode + text + SAFE + "Scene: " + req["prompt"]
    if req.get("mode") == "scene":
        mode = MODES["scene"].format(bg=req.get("bg", "soft cream"), eyes=req.get("eyes", "simple black dots"))
        return who + LOOK + mode + SAFE + "Scene: " + req["prompt"]
    if req.get("mode") == "poster":
        text = (f'Text to write — badge: "{req.get("badge", "")}"; title line(s): "{req.get("title", "")}"; '
                f'subtitle ribbon: "{req.get("subtitle", "")}". ')
    return who + LOOK + MODES.get(req.get("mode", "thumbnail"), "") + text + SAFE + "Scene: " + req["prompt"]

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
    style = req.get("style_refs") or (["_character/style/magazine-1.png"] if req.get("mode", "magazine") in ("magazine", "scene") else [])
    paths += [ROOT / p for p in style]
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
