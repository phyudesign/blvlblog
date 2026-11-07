"""제품 중심 표지(1024x1024) 만들기: python3 _tools/thumbcard/make.py 설정.json
설정: {"out": "wp-content/uploads/…jpg", "bg": "#3aa0ff", "bg2": "#0d5fd6", "ink": "#fff",
       "kicker": "교묘의 TCG 정보통", "title": ["파동시커", "응모 총정리"], "accent": "#FFE14D",
       "items": [{"src": "assets/products/B0H4PQ6LR5.webp", "x": 50, "y": 70, "h": 46, "r": -4, "z": 3, "card": false}],
       "emo": "kyaa", "say": "꼭 뽑고 싶다냥!"}
 x·y = 이미지 중심 위치(%), h = 높이(%), r = 기울기(도), card = 흰 테두리·그림자 카드 효과."""
import json, sys, pathlib, subprocess, html
ROOT = pathlib.Path(__file__).resolve().parents[2]
cfg = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
def u(p): return (ROOT / p).as_uri()
items = ""
for it in cfg["items"]:
    cls = ("it card" if it.get("card") else "it") + (" ink" if it.get("ink", cfg.get("ink_all")) else "")
    items += (f'<img class="{cls}" src="{u(it["src"])}" style="left:{it["x"]}%;top:{it["y"]}%;height:{it["h"]}%;'
              f'transform:translate(-50%,-50%) rotate({it.get("r",0)}deg);z-index:{it.get("z",1)}">')
t = cfg.get("title", [])
title = "".join(f'<div class="t{i}">{html.escape(x)}</div>' for i, x in enumerate(t))
emo = cfg.get("emo")
emo_html = (f'<div class="emo"><img src="{u("wp-content/uploads/emoticons/gyomyo/"+emo+".webp")}"></div>'
            + (f'<div class="say">{html.escape(cfg["say"])}</div>' if cfg.get("say") else "")) if emo else ""
bgcss = (f"url('{u(cfg['bgimg'])}') center/cover no-repeat" if cfg.get("bgimg")
         else f"radial-gradient(circle at 50% 72%,{cfg.get('bg','#3aa0ff')} 0%,{cfg.get('bg2','#0d5fd6')} 78%)")
head = "" if cfg.get("bgimg") else f'<div class="head"><div class="kick">{cfg.get("kicker","<b>blvl.</b> TCG 정보통")}</div>{title}</div>'
dots = "" if cfg.get("bgimg") else "dots"
page = f"""<html><head><style>
*{{margin:0;box-sizing:border-box}}
body{{width:1024px;height:1024px;overflow:hidden;font-family:"Noto Sans CJK KR",sans-serif;position:relative;
 background:{bgcss}}}
body.dots:before{{content:"";position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.13) 2px,transparent 2.4px);background-size:22px 22px;
 -webkit-mask:linear-gradient(180deg,#000 0,transparent 55%);mask:linear-gradient(180deg,#000 0,transparent 55%)}}
.head{{position:absolute;left:0;right:0;top:46px;text-align:center;z-index:20;color:{cfg.get('ink',"#fff")}}}
.kick{{display:inline-block;font-size:26px;font-weight:800;padding:8px 22px;border-radius:999px;background:rgba(0,0,0,.28);color:#fff;letter-spacing:.5px}}
.kick b{{font-weight:900;color:{cfg.get('accent',"#FFE14D")}}}
.t0{{font-size:{cfg.get('size0',112)}px;font-weight:900;letter-spacing:-4px;line-height:1.02;margin-top:18px;text-shadow:0 6px 0 rgba(0,0,0,.18)}}
.t1{{font-size:{cfg.get('size1',96)}px;font-weight:900;letter-spacing:-3px;line-height:1.05;color:{cfg.get('accent',"#FFE14D")};text-shadow:0 6px 0 rgba(0,0,0,.22)}}
.it{{position:absolute;filter:drop-shadow(0 18px 24px rgba(0,0,0,.35))}}
.it.card{{border-radius:16px;filter:none;box-shadow:0 18px 34px rgba(0,0,0,.4)}}
.it.ink{{filter:drop-shadow(4px 0 0 #1b1b1f) drop-shadow(-4px 0 0 #1b1b1f) drop-shadow(0 4px 0 #1b1b1f) drop-shadow(0 -4px 0 #1b1b1f) drop-shadow(0 18px 22px rgba(0,0,0,.28));box-shadow:none;border-radius:14px}}
.emo{{position:absolute;right:30px;bottom:28px;width:190px;height:190px;border-radius:50%;background:#fff;z-index:30;padding:14px;box-shadow:0 10px 24px rgba(0,0,0,.25)}}
.emo img{{width:100%;height:100%;object-fit:contain}}
.say{{position:absolute;right:200px;bottom:150px;z-index:31;background:#fff;color:#16171b;font-size:25px;font-weight:900;padding:12px 20px;border-radius:22px 22px 4px 22px;box-shadow:0 8px 18px rgba(0,0,0,.2)}}
.logo{{position:absolute;left:34px;bottom:30px;height:34px;z-index:30;filter:brightness(0) invert(1);opacity:.9}}
</style></head><body class="{dots}">
{head}
{items}{emo_html}{'' if cfg.get('bgimg') else '<img class="logo" src="'+u('assets/logo-blvl.png')+'">'}
</body></html>"""
tmp = pathlib.Path("/tmp") / "blvl_thumb.html"; tmp.write_text(page, encoding="utf-8")
js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage({{viewport:{{width:1024,height:1024}}}});
await p.goto('file://{tmp}');await p.waitForTimeout(500);await p.screenshot({{path:'{ROOT / cfg["out"]}',type:'jpeg',quality:88}});await b.close()}})()"""
subprocess.run(["node", "-e", js], check=True)
print("saved", cfg["out"])
