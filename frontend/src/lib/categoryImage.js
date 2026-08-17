/* 요리 카테고리별 대표 이미지 — restaurants.real.json의 key(대표 dish_type)로 바로 매핑한다.
   실데이터 key는 13종의 넓은 분류(카페/국물요리/한식/면/구이/회·생물/양식/치킨/한상차림/주점/찜/중식/일식)라
   이름 그대로 딕셔너리 조회만 하면 된다. 지금은 Wikimedia Commons의 실제 한식 사진(무료/저작권 문제없음)이고,
   실사 준비되면 CATEGORY_IMAGES/INGREDIENT_IMAGES 값만 바꾸면 전체 화면에 한 번에 반영된다. */

/* Wikimedia Commons 실사진의 CDN 직링크. Special:FilePath 리다이렉트 대신 최종 URL을 써야
   여러 장을 동시에 불러올 때 위키미디어 쪽 속도제한(429)에 걸리지 않는다. */
export const CATEGORY_IMAGES = {
  '카페': 'https://upload.wikimedia.org/wikipedia/commons/7/76/Cup_of_coffee_with_latte_art_2016.jpg',
  '국물요리': 'https://upload.wikimedia.org/wikipedia/commons/b/b4/Korean_stew-Doenjang_jjigae-01.jpg',
  '한식': 'https://upload.wikimedia.org/wikipedia/commons/5/5a/Korean_cuisine-Hoedeopbap-01.jpg',
  '면': 'https://upload.wikimedia.org/wikipedia/commons/7/78/Korean_cold_noodle_soup-Naengmyeon-01.jpg',
  '구이': 'https://upload.wikimedia.org/wikipedia/commons/2/23/Korean.cuisine-Gui_yori-01.jpg',
  '회·생물': 'https://upload.wikimedia.org/wikipedia/commons/4/45/Korean_cuisine-Saengseon_hoe-02.jpg',
  '양식': 'https://upload.wikimedia.org/wikipedia/commons/c/c5/Beef_steak_of_the_set_of_dinner.jpg',
  '치킨': 'https://upload.wikimedia.org/wikipedia/commons/a/aa/Korean_fried_chicken_240206.jpg',
  '한상차림': 'https://upload.wikimedia.org/wikipedia/commons/2/21/0606_hanjeongsik_damyang.jpg',
  '주점': 'https://upload.wikimedia.org/wikipedia/commons/4/4e/Buchimgae_and_makgeolli.jpg',
  '찜': 'https://upload.wikimedia.org/wikipedia/commons/3/30/Jeonbok-jjim.jpg',
  '중식': 'https://upload.wikimedia.org/wikipedia/commons/5/51/Jajangmyeon_1.jpg',
  '일식': 'https://upload.wikimedia.org/wikipedia/commons/d/d5/Japanese_Sushi_platter.jpg',
}

const DEFAULT_IMAGE = CATEGORY_IMAGES['한식']

/* 식당 카드/상세용 이미지 — data 항목에 image 필드(직접 수집한 실사진 경로/URL)가
   있으면 그걸 최우선으로 쓰고, 없으면 key(대표 dish_type) 기준 카테고리 스톡사진으로 대체한다. */
export function imageFor(r) {
  if (r?.image) return r.image
  return CATEGORY_IMAGES[r?.key] || DEFAULT_IMAGE
}

/* 제철 식재료용 이미지 — 실데이터 id(nat-1, gj-3 등)는 화면마다 달라질 수 있어
   식재료 이름(item)으로 매칭한다. 이름에 해당 키워드가 포함되면 매칭. */
const INGREDIENT_KEYWORD_MAP = [
  { kw: '전복', url: 'https://upload.wikimedia.org/wikipedia/commons/1/11/Korean_cuisine-Jeonbok_hoe-01.jpg' },
  { kw: '굴', url: 'https://upload.wikimedia.org/wikipedia/commons/b/b3/Gulhoe_and_jjokpa-ganghoe.jpg' },
  { kw: '갈치', url: 'https://upload.wikimedia.org/wikipedia/commons/4/4d/Galchi-gui.jpg' },
  { kw: '오징어', url: 'https://upload.wikimedia.org/wikipedia/commons/6/61/Korean_cuisine-Ojingeo_bokkeum-01.jpg' },
]

export function imageForIngredient(item) {
  const hit = INGREDIENT_KEYWORD_MAP.find(({ kw }) => (item || '').includes(kw))
  return hit ? hit.url : DEFAULT_IMAGE
}
