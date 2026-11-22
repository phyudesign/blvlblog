"""본문 교묘 연출 계획 v2 (2026-11-22 슨생: 카드·상품마다 특징을 살려, 블로그 전체에서 포즈 중복 없이)
(글 slug, 원본 이미지 주소에 들어 있는 글자, 배치, 스티커 이름, 옵션, alt 끝에 붙일 행동 설명)
배치: side(옆에 서서) · front(앞에 앉아서) · top(박스 위에 앉아서) · lean(기대서) · push(밀기) · hold/hug(초록 카드 자리) · peek(뒤에서 빼꼼)
스티커 이름이 NEW 에 있으면 새로 그려요(_thumbs/gyomyo-card-이름.json → _thumbs/out/gyomyo-card-이름-1.png).
"""
GREEN = ("filled with flat solid pure green color #00FF00 (no texture, crisp black crayon outline around the rectangle)")
FLAT = ("The image ends in a perfectly straight horizontal cut just below its front paws, which grip a straight horizontal edge "
        "(the rest of the body is hidden behind a wall that is not drawn).")

NEW = {
 # 11/7
 "manga-fist": "standing with one clenched fist raised high, surrounded by dramatic heavy manga speed lines and bold ink hatching, intense heroic face, wind blowing its fur, a single sweat drop.",
 "dolphin-hero": "wearing a blue inflatable dolphin swim ring around its waist and a tiny red cape, striking a superhero pose with one paw pointing to the sky.",
 "king-sit": "sitting proudly like a king, the bottom of its round body cut perfectly flat and horizontal (as if sitting on a flat edge that is not drawn), tiny hind legs dangling in front, wearing a small golden crown and a red royal cape, holding a little scepter, smug face.",
 "empty-wallet": "sitting on the floor crying big tears while shaking an empty coin purse upside down, one small coin falling out.",
 # 11/9
 "meditate": "sitting cross-legged meditating with eyes closed and a calm smile, small blue aura wisps rising from its paws, sensing the air.",
 "four-arms": "flexing proudly with two extra arms made of cardboard taped to its sides (four arms total, all flexing), big grin.",
 "headspin": "spinning upside down on its head like a breakdancer, legs in the air, swirl motion lines around it.",
 "flying-press": "leaping through the air like a pro wrestler doing a flying body press from the top rope, arms and legs spread wide, determined face.",
 "popup-go": "wearing a tiny backpack, holding a folded paper map in one paw and pointing forward excitedly with the other, ready to go out.",
 # 11/10
 "party": "wearing a striped party hat and blowing a party horn, colorful confetti falling around it, celebrating.",
 "gummy": "sitting and happily munching a gummy candy with puffed cheeks, a few colorful gummy candies scattered beside it.",
 # 11/12
 "croc-jaws": "pretending to be a crocodile: both front paws stretched forward one above the other like big snapping jaws, fierce toothy grin.",
 "mail-wings": "flying with small paper wings strapped to its back, carrying a letter in its mouth, dotted flight path behind it.",
 "ghost-sheet": "hiding under a white bedsheet like a ghost, only its crazy eyes showing through two holes, wiggly spooky pose.",
 "bouquet": "standing shyly holding a bouquet of flowers behind its back, blushing, little hearts.",
 # 11/13
 "detective-stop": "wearing a deerstalker detective hat, holding one paw out flat like a STOP sign and the other paw shaking a finger 'no no', serious warning face.",
 "peek-worry": "peeking up with a worried face, ears down, two small red exclamation marks above its head. " + FLAT,
 "rowboat": "rowing a tiny wooden rowboat with one oar, wearing a small sailor hat, splashes of sea water.",
 # 11/14
 "queue": "standing patiently in line holding a small numbered paper ticket and a tiny lunch box, looking ahead.",
 "ninja-run": "running fast in a forward-leaning sprint with both arms stretched straight back, speed lines and a dust cloud.",
 "cake": "holding a birthday cake with lit candles, cheeks puffed about to blow them out, sparkles.",
 "belly-mat": "lying on its belly on the floor, chin resting on its front paws, legs kicking in the air happily, looking forward.",
 # 11/16
 "camel": "riding a small wooden toy camel, wearing a light desert scarf, a little sun doodle.",
 "agent": "dressed as a secret agent in a small black trench coat and dark sunglasses, sneaking on tiptoes with one paw to its lips 'shh'.",
 "sonic-dash": "dashing super fast with a jet-like dust trail behind it, mouth open with excitement, motion streaks.",
 "storm": "holding a little umbrella that is flipping inside out in strong wind, ears blown back, leaves flying.",
 # 11/17
 "champion": "wearing red boxing gloves and a big champion belt, raising one glove high in victory, proud.",
 "torch": "holding a lit torch high above its head with both paws, flame flickering, solemn determined face.",
 "form": "sitting at a tiny desk filling in an application form with a giant pencil, tongue out in concentration.",
 # 11/18
 "gem": "holding a big sparkling green emerald gem up to the light with both paws, eyes reflecting sparkles.",
 "app-tap": "sitting and tapping furiously on a smartphone with both thumbs, sweat drops, speed lines on its paws.",
 "sun-moon": "half sleepy and half awake: a small sun doodle on one side and a crescent moon on the other, one eye open and one eye closed, yawning.",
 "win-paper": "jumping for joy holding up a paper with a big red circle mark on it, confetti.",
 # 11/19
 "laptop": "sitting in front of a small laptop clicking a mouse with intense focus, glowing screen light on its face.",
 "flag-cheer": "waving a small flag with a paw print on it, cheering loudly with mouth wide open.",
 # 11/20
 "shopping": "walking happily holding a shopping bag in one paw and a long store receipt in the other.",
 "treasure": "kneeling and opening a small wooden treasure chest, golden light and coins spilling out, amazed face.",
 "map-draw": "sitting and drawing a treasure map on paper with a red crayon, an X mark on the map.",
 # 11/21
 "figure-pose": "standing perfectly still on a small round display base like a collectible figure, one paw raised in a cute pose, a tiny label tag on the base.",
 "balloons": "holding three small balloons on strings, one green, one orange and one blue, floating up, happy.",
 # 가이드·정리 글
 "invite-letter": "holding up a big envelope sealed with a red wax seal, eyes shining with excitement, tiny sparkles.",
 "press-button": "standing on tiptoes, reaching up to press a big round button with one paw, the other paw crossed for luck.",
 "traveler": "wearing a small backpack and holding a passport and a train ticket, cheerful traveler pose.",
 "ticket-fan": "holding a stack of lottery tickets fanned out like playing cards, grinning slyly.",
 "skates": "gliding on roller skates with arms spread out for balance, one leg lifted, wind lines.",
 "peek-salute": "peeking up and giving a crisp salute with one paw, cheeky grin. " + FLAT,
 "fire-breath": "puffing out its cheeks and blowing a tiny puff of orange fire like a small dragon, proud.",
 "surf": "surfing on a small blue wave with a tiny surfboard, arms out for balance.",
 "cheek-spark": "rubbing both of its round cheeks with its paws, tiny yellow electric sparks crackling from its cheeks.",
 "calculator": "holding a calculator and a pencil tucked behind its ear, frowning while calculating, a few numbers doodled in the air.",
 "coin-cat": "lying elegantly on its side with a small gold coin balanced on its forehead, sly half-closed eyes.",
}

PLAN = [
 ("tcg-데일리-20261107", "blvl-pk-maxi-sar.jpg", "side", "manga-fist", {"side": "right"}, "열혈 만화 주인공처럼 주먹을 치켜든 교묘"),
 ("tcg-데일리-20261107", "blvl-pk-iruka-sar.jpg", "side", "dolphin-hero", {"side": "left"}, "돌고래 튜브를 끼고 히어로 포즈를 잡은 교묘"),
 ("tcg-데일리-20261107", "61FmZOBIZlL", "top", "king-sit", {"pos": .5}, "신의 지배 박스 위에 왕관 쓰고 앉은 교묘"),
 ("tcg-데일리-20261107", "blvl-tcg-daily-20261107-price.jpg", "front", "empty-wallet", {"side": "right"}, "빈 지갑을 털며 우는 교묘"),
 ("tcg-데일리-20261109", "blvl-pk-m7-riolu.jpg", "side", "meditate", {"side": "right"}, "리오르처럼 파동을 느끼며 명상하는 교묘"),
 ("tcg-데일리-20261109", "blvl-pk-m7-machamp.jpg", "side", "four-arms", {"side": "right"}, "골판지 팔 두 개를 더 붙이고 근육 자랑하는 교묘"),
 ("tcg-데일리-20261109", "blvl-pk-m7-hitmontop.jpg", "side", "headspin", {"side": "left"}, "카포에라처럼 머리로 도는 교묘"),
 ("tcg-데일리-20261109", "blvl-pk-m7-hawlucha.jpg", "side", "flying-press", {"side": "right"}, "루차불처럼 플라잉 프레스를 하는 교묘"),
 ("tcg-데일리-20261109", "blvl-tcg-daily-20261109-popup.jpg", "front", "popup-go", {"side": "right"}, "지도를 들고 팝업에 가자고 외치는 교묘"),
 ("tcg-데일리-20261110", "715oCiYpb-L", "side", "pray", {"side": "right"}, "추첨권 들고 당첨을 비는 교묘"),
 ("tcg-데일리-20261110", "711dPI8FndL", "side", "party", {"side": "left"}, "고깔모자 쓰고 30주년을 축하하는 교묘"),
 ("tcg-데일리-20261110", "61FmZOBIZlL", "push", "push", {}, "박스를 영차 미는 교묘"),
 ("tcg-데일리-20261110", "71I7EZSM4DL", "front", "gummy", {"side": "right"}, "젤리를 오물오물 먹는 교묘"),
 ("tcg-데일리-20261112", "blvl-pk-mg-ferali.jpg", "side", "croc-jaws", {"side": "right"}, "장크로다일처럼 앞발로 악어 입을 흉내 내는 교묘"),
 ("tcg-데일리-20261112", "blvl-pk-mg-dragonite.jpg", "side", "mail-wings", {"side": "left"}, "망나뇽처럼 편지를 물고 나는 교묘"),
 ("tcg-데일리-20261112", "blvl-pk-mg-gengar.jpg", "side", "ghost-sheet", {"side": "right"}, "이불을 뒤집어쓰고 유령 흉내 내는 교묘"),
 ("tcg-데일리-20261112", "61UK9XZctYL", "side", "bouquet", {"side": "right"}, "꽃다발을 들고 수줍어하는 교묘"),
 ("tcg-데일리-20261113", "blvl-tcg-daily-20261113-scam.jpg", "front", "detective-stop", {"side": "left"}, "탐정 모자 쓰고 사칭 메일을 막는 교묘"),
 ("tcg-데일리-20261113", "blvl-pk-m7-absol.jpg", "peek", "peek-worry", {"pos": .7}, "앱솔 카드 뒤에서 불길한 예감에 빼꼼한 교묘"),
 ("tcg-데일리-20261113", "61fcPWlRwhL", "side", "rowboat", {"side": "right"}, "작은 나룻배를 젓는 교묘"),
 ("tcg-데일리-20261114", "blvl-pokemon-card-store-202611.jpg", "front", "queue", {"side": "right"}, "번호표 들고 줄 서 있는 교묘"),
 ("tcg-데일리-20261114", "blvl-naruto-c-001.jpg", "side", "ninja-run", {"side": "right"}, "팔을 뒤로 뻗고 달리는 교묘"),
 ("tcg-데일리-20261114", "711dPI8FndL", "side", "cake", {"side": "left"}, "생일 케이크 촛불을 끄려는 교묘"),
 ("tcg-데일리-20261114", "blvl-naruto-playmat-naruto-vs-sasuke.jpg", "front", "belly-mat", {"side": "left"}, "매트 앞에 엎드려 구경하는 교묘"),
 ("tcg-데일리-20261116", "blvl-op-st37.jpg", "side", "camel", {"side": "right"}, "장난감 낙타를 탄 교묘"),
 ("tcg-데일리-20261116", "blvl-op-st38.jpg", "side", "agent", {"side": "left"}, "선글라스 낀 비밀요원 교묘"),
 ("tcg-데일리-20261116", "blvl-pk-m7-garchomp.jpg", "side", "sonic-dash", {"side": "right"}, "한카리아스처럼 쌩 달리는 교묘"),
 ("tcg-데일리-20261116", "715FaccxhwL", "side", "storm", {"side": "left"}, "폭풍에 우산이 뒤집힌 교묘"),
 ("tcg-데일리-20261117", "61DEiJm305L", "side", "champion", {"side": "right"}, "챔피언 벨트를 차고 승리 포즈를 취한 교묘"),
 ("tcg-데일리-20261117", "81tO30I8gwL", "side", "torch", {"side": "left"}, "횃불을 높이 든 교묘"),
 ("tcg-데일리-20261117", "715oCiYpb-L", "front", "form", {"side": "right"}, "추첨 신청서를 쓰는 교묘"),
 ("tcg-데일리-20261118", "715FaccxhwL", "side", "gem", {"side": "right"}, "에메랄드를 빛에 비춰 보는 교묘"),
 ("tcg-데일리-20261118", "711dPI8FndL", "front", "app-tap", {"side": "left"}, "앱으로 추첨 신청하느라 바쁜 교묘"),
 ("tcg-데일리-20261118", "71RQY+K9JzL", "side", "sun-moon", {"side": "right"}, "낮과 밤 사이에서 졸린 교묘"),
 ("tcg-데일리-20261118", "715oCiYpb-L", "side", "win-paper", {"side": "left"}, "동그라미 표시 종이를 들고 뛰는 교묘"),
 ("tcg-데일리-20261119", "61FmZOBIZlL", "top", "sit", {"pos": .5}, "박스 위에 걸터앉은 교묘"),
 ("tcg-데일리-20261119", "61EvBG8mJ-L", "front", "laptop", {"side": "left"}, "노트북으로 응모하는 교묘"),
 ("tcg-데일리-20261119", "715oCiYpb-L", "side", "flag-cheer", {"side": "right"}, "깃발 흔들며 응원하는 교묘"),
 ("tcg-데일리-20261120", "715oCiYpb-L", "side", "shopping", {"side": "right"}, "쇼핑백과 영수증을 들고 가는 교묘"),
 ("tcg-데일리-20261120", "71RQY+K9JzL", "side", "photo", {"side": "right"}, "휴대폰으로 사진 찍는 교묘"),
 ("tcg-데일리-20261120", "61FmZOBIZlL", "front", "treasure", {"side": "right"}, "보물 상자를 여는 교묘"),
 ("tcg-데일리-20261120", "op-eb06.webp", "front", "map-draw", {"side": "left"}, "보물 지도를 그리는 교묘"),
 ("tcg-데일리-20261121", "blvl-pk-30th-figure-kv.jpg", "side", "figure-pose", {"side": "right"}, "피규어처럼 받침 위에서 포즈 잡은 교묘"),
 ("tcg-데일리-20261121", "blvl-pk-30th-cardset-kr.jpg", "side", "balloons", {"side": "left"}, "풍선 세 개를 든 교묘"),
 ("아마존-응모-포켓몬카드-원피스카드", "715oCiYpb-L", "side", "invite-letter", {"side": "right"}, "초대장 봉투를 든 교묘"),
 ("아마존-응모-포켓몬카드-원피스카드", "61FmZOBIZlL", "side", "press-button", {"side": "left"}, "까치발로 버튼을 누르는 교묘"),
 ("일본-카드-쇼핑몰-추첨-총정리", "711dPI8FndL", "side", "traveler", {"side": "right"}, "여권과 기차표를 든 여행자 교묘"),
 ("일본-카드-쇼핑몰-추첨-총정리", "715FaccxhwL", "side", "ticket-fan", {"side": "left"}, "추첨권을 부채처럼 펼친 교묘"),
 ("파동시커-응모-총정리", "blvl-pk-m7-lucario.jpg", "peek", "peek-salute", {"pos": .3}, "카드 뒤에서 경례하며 빼꼼한 교묘"),
 ("파동시커-응모-총정리", "blvl-pk-m7-korrina.jpg", "side", "skates", {"side": "right"}, "코르니처럼 롤러스케이트를 타는 교묘"),
 ("파동시커-응모-총정리", "blvl-pk-maxi-sar.jpg", "peek", "wave", {"pos": .75}, "카드 뒤에서 손 흔드는 교묘"),
 ("포켓몬카드-30주년-박스-시세", "blvl-pk-30th-charizard.jpg", "side", "fire-breath", {"side": "right"}, "리자몽처럼 작은 불을 뿜는 교묘"),
 ("포켓몬카드-30주년-박스-시세", "blvl-pk-30th-lugia.jpg", "side", "surf", {"side": "left"}, "파도를 타는 교묘"),
 ("포켓몬카드-30주년-박스-시세", "blvl-pk-30th-pikachu-day.jpg", "side", "cheek-spark", {"side": "right"}, "피카츄처럼 볼에서 찌릿 불꽃을 내는 교묘"),
 ("포켓몬카드-30주년-박스-시세", "711dPI8FndL", "side", "calculator", {"side": "left"}, "계산기 두드리며 시세를 따지는 교묘"),
]
# 파동시커 총정리(이미 적용): aura(메가루카리오), hug(메가한카리아스), hold(마키시 SAR), flex(마키시 일반), sleep(리오르), loupe(심보러ex), pack(메가앱솔), peek(메가루카리오 ①) — 070 페르시온만 coin-cat 으로 바꿔요
PLAN_HADOU = [("파동시커-총정리", "peek-070.webp", "side", "coin-cat", {"side": "right"}, "페르시온처럼 이마에 동전을 얹고 누운 교묘")]
