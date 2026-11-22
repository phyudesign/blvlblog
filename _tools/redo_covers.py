"""표지 다시 만들기 (2026-11-22): 시리즈 콘셉트 배경 + 교묘 위치(A 오른쪽 아래 · B 왼쪽 아래 · C 제목 옆 위 · D 오른쪽 가운데)에 맞춰 상품 배치
    python3 _tools/redo_covers.py            # 전부
    python3 _tools/redo_covers.py 20261107   # 하나만
이전 표지 파일은 지우지 않고 새 이름(-v2)으로 만들어 글의 thumb 만 바꿔요 (되돌리기 쉽게).
"""
import json, sys, subprocess, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
POSJ = json.loads((ROOT / "_thumbs" / "cover_positions.json").read_text())
FRONT = {"A": [[58, 50, 100, 100]], "B": [[0, 50, 42, 100]], "C": [[64, 0, 100, 50]], "D": [[62, 30, 100, 84]]}
STAMP = {"A": {"x": 66, "y": 4, "r": 6}, "B": {"x": 66, "y": 4, "r": 6}, "C": {"x": 74, "y": 90, "r": -6}, "D": {"x": 66, "y": 4, "r": 6}}
BGKEY = {"A": [300, 620], "B": [700, 620], "C": [500, 640], "D": [300, 640]}


def layout(items, pos):
    items = [dict(i) for i in items]
    if pos == "B":
        for i in items: i["x"] = 100 - i["x"]; i["r"] = -i.get("r", 0)
    elif pos == "C":
        n = len(items); xs = [20 + 60 * k / max(1, n - 1) for k in range(n)] if n > 1 else [50]
        order = sorted(range(n), key=lambda k: items[k].get("x", 50))
        for xi, k in zip(xs, order):
            items[k]["x"] = round(xi); items[k]["y"] = 74 + (4 if items[k].get("z", 1) % 2 else 0)
            items[k]["h"] = round(items[k]["h"] * .95)
    elif pos == "D":
        for i in items: i["x"] = min(i["x"], 56)
    return items


def build(cfg_path, bg, out, pos, stamp_text=None):
    c = json.loads((ROOT / cfg_path).read_text())
    c["bgimg"] = bg; c["out"] = out; c["front"] = FRONT[pos]; c["bgkey"] = BGKEY[pos]; c["tol"] = 70
    c["items"] = layout(c["items"], pos)
    if stamp_text: c["stamp"] = dict(STAMP[pos], text=stamp_text)
    else: c.pop("stamp", None)
    tmp = ROOT / "_thumbs" / "cards" / (pathlib.Path(cfg_path).stem + "-v2.json")
    tmp.write_text(json.dumps(c, ensure_ascii=False, indent=1))
    subprocess.run([sys.executable, str(ROOT / "_tools" / "thumbcard" / "make.py"), str(tmp)], check=True, capture_output=True)
    return "/" + out


def set_thumb(post, url):
    p = ROOT / "_posts" / f"{post}.html"; s = p.read_text(encoding="utf-8")
    s = re.sub(r'"thumb": "[^"]*"', f'"thumb": "{url}"', s, count=1); p.write_text(s, encoding="utf-8")


def main(only=None):
    for d, pos in POSJ["daily"].items():
        if only and only != d: continue
        bg = f"_thumbs/out/gyomyo-news-{d}-1.png"
        if not (ROOT / bg).exists(): print("배경 없음", d); continue
        m, dd = int(d[4:6]), int(d[6:])
        url = build(f"_thumbs/cards/daily-{d}.json", bg, f"wp-content/uploads/2026/11/blvl-tcg-daily-{d}-news.jpg", pos, f"{m}월 {dd}일")
        set_thumb(f"tcg-데일리-{d}", url); print("ok", d, pos)
    G = {"amazon": ("_thumbs/cards/amazon.json", "아마존-응모-포켓몬카드-원피스카드"),
         "japan-shops": ("_thumbs/cards/japan-shops.json", "일본-카드-쇼핑몰-추첨-총정리"),
         "hadou-lottery": ("_thumbs/cards/hadou.json", "파동시커-응모-총정리")}
    for k, pos in POSJ["guides"].items():
        if only and only != k: continue
        bg = f"_thumbs/out/gyomyo-cover-{k}-1.png"
        if not (ROOT / bg).exists(): print("배경 없음", k); continue
        cfg, post = G[k]
        url = build(cfg, bg, f"wp-content/uploads/2026/11/blvl-tcg-{k}-cover-v2.jpg", pos)
        set_thumb(post, url); print("ok", k, pos)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
