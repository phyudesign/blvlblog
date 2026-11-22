"""기존 글 본문 이미지에 교묘 연출을 넣는 일괄 작업 (2026-11-22, 슨생 요청 "전부 수정")
한 줄 = (글 slug, 원본 이미지 주소에 들어 있는 글자, 연출, 옵션, 덧붙일 alt)
아마존 상품 사진(m.media-amazon.com)은 assets/products/ASIN.webp 누끼로 합성해요.
"""
import re, sys, pathlib, shutil
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gyocard

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_thumbs" / "peek-src"
OUTD = ROOT / "wp-content" / "uploads" / "2026" / "11" / "gyo"
AMZ = {"715oCiYpb-L": "B0H4PQ6LR5", "61FmZOBIZlL": "B0HFVPJF4Q", "711dPI8FndL": "B0GXCRBL5J", "715FaccxhwL": "B0GP928YDZ",
       "61UK9XZctYL": "B0HB3JQ6P4", "61DEiJm305L": "B0H43ZX8LK", "61fcPWlRwhL": "B0HMZ9WLVZ", "81tO30I8gwL": "B0FX7X71KK",
       "61EvBG8mJ-L": "B0G2VKBZML", "71RQY+K9JzL": "B0GXCM4BCZ", "71I7EZSM4DL": "B0HPRX138T"}
ACT = {"peek": "카드 뒤에서 빼꼼 고개를 내민 교묘", "wave": "카드 뒤에서 손 흔드는 교묘", "hold": "카드를 머리 위로 들고 자랑하는 교묘",
       "hug": "끌어안고 볼 비비는 교묘", "pack": "앞에 앉아 팩을 뜯는 교묘", "loupe": "돋보기로 감정하는 교묘",
       "sleep": "기대어 낮잠 자는 교묘", "photo": "휴대폰으로 사진 찍는 교묘", "aura": "파동 포즈를 따라 하는 교묘",
       "flex": "레슬러처럼 근육 자랑하는 교묘", "sit": "박스 위에 걸터앉은 교묘", "push": "박스를 영차 미는 교묘",
       "pray": "추첨권 들고 당첨을 비는 교묘"}

PLAN = [
 ("tcg-데일리-20261107", "blvl-pk-maxi-sar.jpg", "hold", {}),
 ("tcg-데일리-20261107", "61FmZOBIZlL", "sit", {}),
 ("tcg-데일리-20261107", "blvl-pk-iruka-sar.jpg", "photo", {"side": "right"}),
 ("tcg-데일리-20261109", "blvl-pk-m7-riolu.jpg", "aura", {"side": "right"}),
 ("tcg-데일리-20261109", "blvl-pk-m7-machamp.jpg", "peek", {"pos": .2}),
 ("tcg-데일리-20261110", "715oCiYpb-L", "pray", {"side": "right"}),
 ("tcg-데일리-20261110", "711dPI8FndL", "push", {}),
 ("tcg-데일리-20261112", "blvl-pk-mg-ferali.jpg", "hug", {}),
 ("tcg-데일리-20261112", "blvl-pk-mg-gengar.jpg", "sleep", {}),
 ("tcg-데일리-20261112", "61UK9XZctYL", "sit", {"pos": .8}),
 ("tcg-데일리-20261113", "blvl-tcg-daily-20261113-scam.jpg", "loupe", {"side": "left"}),
 ("tcg-데일리-20261113", "blvl-pk-m7-absol.jpg", "wave", {"pos": .75}),
 ("tcg-데일리-20261113", "61fcPWlRwhL", "photo", {"side": "right"}),
 ("tcg-데일리-20261114", "blvl-pk-m7-hawlucha.jpg", "flex", {"side": "right"}),
 ("tcg-데일리-20261114", "blvl-naruto-c-001.jpg", "peek", {"pos": .7}),
 ("tcg-데일리-20261114", "711dPI8FndL", "pray", {"side": "right"}),
 ("tcg-데일리-20261116", "blvl-op-st37.jpg", "sit", {"pos": .3}),
 ("tcg-데일리-20261116", "blvl-op-st38.jpg", "push", {}),
 ("tcg-데일리-20261116", "blvl-pk-m7-garchomp.jpg", "loupe", {"side": "left"}),
 ("tcg-데일리-20261117", "61DEiJm305L", "pray", {"side": "right"}),
 ("tcg-데일리-20261117", "blvl-pk-m7-hawlucha.jpg", "peek", {"pos": .8}),
 ("tcg-데일리-20261118", "715FaccxhwL", "sit", {"pos": .6}),
 ("tcg-데일리-20261118", "71RQY+K9JzL", "photo", {"side": "right"}),
 ("tcg-데일리-20261119", "61EvBG8mJ-L", "push", {}),
 ("tcg-데일리-20261119", "715oCiYpb-L", "loupe", {"side": "left"}),
 ("tcg-데일리-20261120", "711dPI8FndL", "photo", {"side": "right"}),
 ("tcg-데일리-20261120", "op-eb06.webp", "sit", {"pos": .4}),
 ("tcg-데일리-20261120", "op-op19.webp", "pack", {"side": "right"}),
 ("tcg-데일리-20261121", "m7/m7-113.jpg", "wave", {"pos": .2}),
 ("tcg-데일리-20261121", "715FaccxhwL", "push", {}),
 ("tcg-데일리-20261121", "blvl-pk-30th-cardset-kr.jpg", "loupe", {"side": "left"}),
 ("아마존-응모-포켓몬카드-원피스카드", "715oCiYpb-L", "pray", {"side": "right"}),
 ("아마존-응모-포켓몬카드-원피스카드", "61FmZOBIZlL", "sit", {}),
 ("일본-카드-쇼핑몰-추첨-총정리", "711dPI8FndL", "push", {}),
 ("일본-카드-쇼핑몰-추첨-총정리", "715FaccxhwL", "loupe", {"side": "left"}),
 ("파동시커-응모-총정리", "blvl-pk-m7-lucario.jpg", "peek", {"pos": .3}),
 ("파동시커-응모-총정리", "blvl-pk-m7-korrina.jpg", "aura", {"side": "right"}),
 ("파동시커-응모-총정리", "blvl-pk-maxi-sar.jpg", "flex", {"side": "right"}),
 ("포켓몬카드-30주년-박스-시세", "blvl-pk-30th-charizard.jpg", "hug", {}),
 ("포켓몬카드-30주년-박스-시세", "blvl-pk-30th-lugia.jpg", "photo", {"side": "right"}),
 ("포켓몬카드-30주년-박스-시세", "blvl-pk-30th-pikachu-day.jpg", "wave", {"pos": .7}),
 ("포켓몬카드-30주년-박스-시세", "711dPI8FndL", "loupe", {"side": "left"}),
]


def source(key, src_url):
    if key in AMZ: return ROOT / "assets" / "products" / f"{AMZ[key]}.webp"
    if key.endswith(".webp") and (ROOT / "assets" / "products" / key).exists(): return ROOT / "assets" / "products" / key
    loc = ROOT / src_url.lstrip("/")
    keep = SRC / loc.name
    if not keep.exists(): shutil.copy(loc, keep)       # 원본은 지워지지 않는 곳에 보관
    return keep


def run(plan=None):
    """plan: gyo_plan.PLAN 형식 (slug, key, 배치, 스티커, 옵션, 행동 설명)"""
    import gyo_plan
    plan = plan or gyo_plan.PLAN
    OUTD.mkdir(parents=True, exist_ok=True)
    for slug, key, lay, stk, opt, act in plan:
        p = ROOT / "_posts" / f"{slug}.html"; s = p.read_text(encoding="utf-8")
        m = None
        for mm in re.finditer(r'<img\b[^>]*>', s):
            src = re.search(r'src="([^"]+)"', mm.group(0)).group(1)
            if key in src and "/gyo/" not in src and "gc-" not in src: m = mm; break
        if not m: print("못 찾음", slug, key); continue
        tag = m.group(0); src = re.search(r'src="([^"]+)"', tag).group(1)
        name = f"{slug[:24]}-{re.sub(r'[^A-Za-z0-9]', '', key)[:18]}-{stk}.webp"
        out = OUTD / name
        if stk in gyo_plan.NEW:
            size = gyocard.make(lay, source(key, src), out, opt.get("side", "right"), opt.get("pos", .5), sticker=stk)
        else:   # 처음 만든 공용 스티커(pray·push·sit·photo·wave …)는 블로그 전체에서 한 번씩만
            size = gyocard.make(stk, source(key, src), out, opt.get("side", "right"), opt.get("pos", .5))
        alt = re.search(r'alt="([^"]*)"', tag); alt = alt.group(1) if alt else ""
        new = re.sub(r'src="[^"]+"', f'src="/wp-content/uploads/2026/11/gyo/{name}"', tag)
        new = re.sub(r'\s(width|height|referrerpolicy)="[^"]*"', "", new)
        new = re.sub(r'alt="[^"]*"', f'alt="{alt} — {act}"', new) if 'alt="' in new else new.replace("<img", f'<img alt="{act}"', 1)
        new = new.replace('background:#fff', 'background:transparent')
        s = s[:m.start()] + new + s[m.end():]
        p.write_text(s, encoding="utf-8")
        print("ok", slug, stk, size)


if __name__ == "__main__":
    run()
