import sys, re; sys.path.insert(0, "_tools")
import monitor as m
h = m.get("https://torecaplaza55.com/")
blks = re.split(r'<li class="c-item-list__item"', h)[1:]
print("blocks", len(blks))
n=0
for blk in blks:
    tm = re.search(r'c-item-list__ttl">\s*<a href="\?pid=(\d+)"[^>]*>(.*?)</a>', blk, re.S)
    if not tm: continue
    t = m.text_of(tm.group(2)); n+=1
    if any(w in t for w in m.WATCH_WORDS): print(m.relevant(t), "SOLD" if "is-soldout" in blk else "ok", t[:70])
print("titled", n, "kept", len(m.scan_shoppro(h, "torecaplaza55", "https://torecaplaza55.com/")))
