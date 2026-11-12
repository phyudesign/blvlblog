"""재고 감시기가 모아 둔 텔레그램 알림(_monitor/tg_queue.json)을 블로그 배포가 끝난 뒤 보내요."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import monitor as m
q = m.TG_QUEUE_FILE
if q.exists():
    for msg in json.loads(q.read_text(encoding="utf-8")):
        print("텔레그램:", m.telegram(msg))
    q.unlink()
