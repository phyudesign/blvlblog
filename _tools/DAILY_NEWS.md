# TCG 데일리 뉴스 작성 가이드 (매일 실행되는 예약 작업용)

블로그: https://blvlblog.com (저장소 phyudesign/blvlblog, GitHub Pages, `main`에 올리면 배포)
운영자: 슨생. 글은 한국어, 쉬운 말(응모, 당첨 메일, 한국 공식 상품명)로 써요.

## 1. 조사 (최근 24~48시간 새 소식만)
포켓몬카드·원피스카드의 **신제품 발표, 발매일, 예약·추첨·응모, 아마존 초대 요청(招待リクエスト), 재판매, 한글판 소식**을 찾아요.
- 공식: 포켓몬카드 공식(pokemon-card.com), 【公式】ポケモンカードチャンネル, 원피스카드 공식(onepiece-cardgame.com, en.onepiece-cardgame.com/products), 포켓몬코리아(pokemonkorea.co.kr/news/2), 포켓몬카드 한국(pokemoncard.co.kr)
- 일본 정리: 게임피디아 프리미엄(premium.gamepedia.jp/pokeca, /toreca), 스니덩 매거진(snkrdunk.com/articles), 트레카맵, アルテマ, 전격온라인·인사이드·GAME Watch
- 영어권 유통(원피스 신상 날짜가 가장 먼저 뜸): ICv2(icv2.com), 해외 판매점 발매 일정표
- 이미 블로그에 쓴 소식(최근 데일리 뉴스, `_posts/`)은 반복하지 말고 "업데이트"로만 짧게.
- 확인 안 된 루머는 쓰지 않거나 "아직 공식 발표 전"이라고 분명히 표시.

## 2. 데일리 뉴스 글
- 파일: `_posts/tcg-데일리-YYYYMMDD.html` (한국 날짜). 맨 위 JSON 앞머리는 기존 글과 같은 형식:
  - title: `TCG 데일리 뉴스 M월 D일 — {가장 큰 소식 한 줄}`
  - slug: `tcg-데일리-YYYYMMDD`, date/mod: `YYYY-MM-DD HH:MM:SS`(한국 시간), category: `tcg`
  - thumb: `/wp-content/uploads/2026/11/blvl-tcg-daily.jpg`, tags: 포켓몬카드/원피스카드 등
  - desc: 오늘 소식 요약 1~2문장
- 본문 구성: 짧은 인사 → `<h2>오늘의 핵심</h2>` 3줄 요약 → `<h2>포켓몬카드</h2>` / `<h2>원피스카드</h2>` 소식별 `<h3>` + 2~4문장(날짜·가격·구성·한국에서 응모 가능 여부) → `<h2>응모·예약 일정</h2>` 표(마감 빠른 순) → 교묘 말풍선 1~2개 → 맨 아래 `참고한 곳:` 링크.
- 교묘 말풍선 형식(기존 글 참고): `<div class="emo"><img src="/wp-content/uploads/emoticons/gyomyo/{이름}.webp" ...><div class="bubble"><b>미친고양이 교묘</b>…냥</div></div>`
  이모티콘 이름: great heok happy-cards hmm-question good kyaa sob watching hmm price-check rare too-many hoho angry nyamnyam flat mine happy-sleep sounds-good lets-go blank what-now best sigh
- 이미지: 박스 사진은 아마존 상품 사진만, 출처·링크 표기(기존 `파동시커-응모-총정리.html` 의 figure 형식). 공식 유튜브는 youtube-nocookie 임베드 + 출처. 다른 사이트 이미지 복사 금지.
- **새 소식이 거의 없는 날은 글을 쓰지 않아요.** (같은 내용 반복 금지 — 애드센스 품질)

## 3. LIVE(응모 판·속보)에 올리기 — 초대 요청·예약·추첨·응모가 있을 때
- **아마존 재팬 초대 요청 상품**: `_tools/monitor.py` 의 `INVITE_JP` 맨 위에 `("ASIN", "한글 상품명", "포켓몬|원피스", "")` 추가, `AMZ_IMG` 에 대표 사진 키(가능하면) 추가. 미국 아마존은 `INVITE_US`.
- **그 밖의 추첨·예약·응모(포켓몬센터, 국내판 등)**: 속보 글을 만들어요.
  ```
  cd 저장소 && python3 - <<'PY'
  import sys, json; sys.path.insert(0, "_tools"); import monitor as m
  st = json.loads(m.STATE.read_text(encoding="utf-8"))
  m.write_alert_post({"key": "daily:고유키", "kind": "page", "shop_kr": "포켓몬센터 온라인", "title": "상품명 추첨 접수 (마감 11/11)",
                      "url": "공식 공지 주소", "status": "krnews 또는 invite", "price": ""}, st)
  m.STATE.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
  PY
  ```
  (status: 국내판이면 `krnews`, 그 밖은 `invite`. 같은 key로 24시간 안이면 기존 글에 기록만 추가돼요.)

## 4. 빌드·올리기
```
python3 _tools/site.py
git add -A
git -c user.name=phyudesign -c user.email=phyudesign@users.noreply.github.com commit -m "데일리 뉴스: M월 D일

Co-Authored-By: Claude <noreply@anthropic.com>"
for i in 1 2 3; do git pull --rebase origin main && git push origin main && break; sleep 5; done
```
- 재고 감시기(10분마다)가 같은 저장소에 커밋하므로 push 전 항상 pull --rebase.
- `_monitor/state.json` 충돌 시 원격 것을 받아들이고 3번 작업만 다시.

## 5. 끝나면
몇 줄 요약(쓴 글 제목, LIVE에 올린 것)을 남겨요. 새 소식이 없어서 안 썼으면 그렇다고만.
