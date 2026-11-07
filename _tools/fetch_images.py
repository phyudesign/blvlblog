"""_fetch/images.json 의 {"저장경로": "원본 주소"} 를 받아 jpg 로 저장 (공식 상품 이미지 등). 받은 뒤 목록을 비워요."""
import io, json, pathlib, requests
from PIL import Image
ROOT = pathlib.Path(__file__).resolve().parent.parent
LIST = ROOT / "_fetch" / "images.json"
jobs = json.loads(LIST.read_text(encoding="utf-8")) if LIST.exists() else {}
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"}
for dest, src in jobs.items():
    r = requests.get(src, headers=UA, timeout=30); r.raise_for_status()
    im = Image.open(io.BytesIO(r.content)).convert("RGBA")
    bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[3])
    out = ROOT / dest; out.parent.mkdir(parents=True, exist_ok=True)
    bg.save(out, "JPEG", quality=86, optimize=True); print("saved", dest, bg.size)
LIST.write_text("{}\n", encoding="utf-8")
