import sys, re; sys.path.insert(0, "_tools")
import monitor as m, requests
u = "https://pokemonkorea.co.kr/news/2/21508"
r = requests.get(u, headers=m.UA, timeout=30); print("monitor UA", r.status_code, len(r.text), r.url)
print(re.findall(r'<img[^>]+src="([^"]+)"', r.text)[:8])
