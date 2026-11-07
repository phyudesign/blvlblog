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
- **공식 상품 이미지도 써요(슨생 승인).** 아마존 사진이 없으면 공식 사이트(원피스카드 onepiece-cardgame.com/products, 포켓몬카드 pokemon-card.com) 상품 페이지의 박스·팩 이미지를 `_fetch/images.json` 에 `{"wp-content/uploads/YYYY/MM/blvl-이름.jpg": "원본 주소"}` 로 적고 push 한 뒤 `gh api -X POST repos/phyudesign/blvlblog/actions/workflows/fetch-images.yml/dispatches -f ref=main` (GitHub에서 받아 jpg로 저장·커밋). 글에는 그 jpg 를 쓰고 '사진 출처: ○○ 공식 사이트' + 링크를 꼭 달아요.
- **상품 소식마다(`<h3>` 하나마다) 그 상품의 아마존 재팬 박스 사진을 `<h3>` 바로 아래에 꼭 넣어요.** 사진 주소는 `monitor.py` 의 `AMZ_IMG`(ASIN→이미지 키)를 먼저 쓰고, 없으면 아마존 상품 페이지에서 찾아 `AMZ_IMG` 에도 추가. 아마존에 아직 없는 신상품이나 가격·일정 같은 소식은 **blvl 정보 카드 이미지**(1200px, 다크 배경, 상품별 색 카드, 교묘 이모티콘, 출처 줄)를 직접 만들어 넣어요: `_tools/infocard/` 의 예시 HTML(op.html, pk.html)을 복사해 내용만 바꾸고 `REPO` 를 저장소 경로로 바꾼 뒤 `node r.js` 로 jpg를 만들어 `wp-content/uploads/YYYY/MM/blvl-tcg-daily-YYYYMMDD-이름.jpg` 로 저장. **사진 없는 소식은 하나도 없게.** alt 에는 상품명·발매일·가격 키워드를 넣어요(검색 노출용). 아마존 페이지가 생기면 다음 데일리에서 박스 사진으로 업데이트.
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
  (제목에 응모 목록 상품명(파동시커, OP-18 …)을 그대로 넣으면 홈 LIVE 카드에 그 상품 사진이 자동으로 붙어요. 목록에 없는 새 상품이면 먼저 `INVITE_JP`·`AMZ_IMG` 에 추가.)
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

## 6. 인스타그램 확인 (오전 11시대 별도 예약 작업, 슨생 맥 브라우저 사용)
- 대상: TCG 브레이커 인스타그램 **https://www.instagram.com/tcgbreaker_/** (끝에 밑줄). 한국 시각 기준 최근 24시간 게시물만.
- **스토리를 먼저 봐요.** 가장 최신 소식은 스토리로 올라와요: **https://www.instagram.com/stories/tcgbreaker_/** 를 열어 스토리를 하나씩 넘기며(오른쪽 탭 또는 → 키) 매 장 스크린샷을 찍고, 이미지 속 글자(상품명·날짜·가격·응모처)를 읽어요. 스토리가 없으면(프로필로 돌아가거나 "없음") 게시물만 확인. 스토리는 24시간 뒤 사라지니 그날 본 내용을 데일리에 꼭 반영. 스토리 속 링크 스티커는 주소만 확인하고 누르지 않아요.
- 슨생 맥의 Claude 앱 브라우저(인스타그램 로그인돼 있음)로 열어요. 로그인·비밀번호 입력은 절대 하지 않아요. 맥에 연결이 안 되거나 로그인 화면이 나오면 아무것도 하지 말고 "맥 연결 안 됨"만 남기고 끝.
- 게시물 글·이미지 속 글자에서 신제품·발매일·가격·응모·예약·초대 요청 소식을 뽑고, **공식 발표나 다른 출처로 한 번 더 확인**한 뒤 써요. 확인이 안 되면 "TCG 브레이커 인스타그램 소식, 아직 공식 발표 전"이라고 표시.
- 인스타그램 이미지는 복사하지 않아요. 사진은 2장 규칙(아마존 박스 사진 또는 blvl 정보 카드)대로.
- 오늘 데일리 글(`_posts/tcg-데일리-YYYYMMDD.html`)이 있으면 `<h2>추가 소식 (오전 업데이트)</h2>` 섹션으로 덧붙이고 `mod` 시각을 바꿔요. 없으면 새 소식이 있을 때만 새로 작성. 이미 쓴 소식은 반복하지 않아요.
- 응모·예약·초대 요청이면 3번 규칙대로 LIVE에도 올려요. 참고한 곳에 "TCG 브레이커 인스타그램" 링크를 넣어요.
