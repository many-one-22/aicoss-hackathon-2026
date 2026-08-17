/* 요리 카테고리별 대표 이미지 — key/tags로 카테고리를 판별해 같은 카테고리 식당끼리 이미지를 공유한다.
   지금은 Wikimedia Commons의 실제 한식 사진(무료/저작권 문제없음)이고, 실사 준비되면
   CATEGORY_IMAGES/INGREDIENT_IMAGES 값만 바꾸면 전체 화면에 한 번에 반영된다. */

const KEYWORD_MAP = [
  { cat: 'hoe', kw: ['횟집', '준치', '육회', '육전'] },
  { cat: 'gui', kw: ['떡갈비', '한우', '불고기', '갈치구이'] },
  { cat: 'jjim', kw: ['아귀찜', '추어탕', '곰탕', '국밥', '연포탕', '해장국'] },
  { cat: 'gejang', kw: ['게장', '간장게장', '양념게장'] },
  { cat: 'jeonbok', kw: ['전복', '꼬막', '굴', '조개'] },
  { cat: 'jeongsik', kw: ['정식', '한정식', '삼합'] },
  { cat: 'myeon', kw: ['냉면'] },
  { cat: 'samgyetang', kw: ['삼계탕'] },
  { cat: 'banchan', kw: ['갓김치', '굴비'] },
]

/* Wikimedia Commons 실사진(무료/저작권 문제없음)의 CDN 직링크.
   Special:FilePath 리다이렉트 경유 대신 최종 URL을 직접 써야 여러 장을 동시에 불러올 때
   위키미디어 쪽 속도제한(429)에 걸리지 않는다. */
export const CATEGORY_IMAGES = {
  hoe: 'https://upload.wikimedia.org/wikipedia/commons/4/45/Korean_cuisine-Saengseon_hoe-02.jpg', // 생선회
  gui: 'https://upload.wikimedia.org/wikipedia/commons/2/23/Korean.cuisine-Gui_yori-01.jpg', // 구이요리
  jjim: 'https://upload.wikimedia.org/wikipedia/commons/b/b4/Korean_stew-Doenjang_jjigae-01.jpg', // 된장찌개
  gejang: 'https://upload.wikimedia.org/wikipedia/commons/c/c4/Korean_seafood-ganjang_gejang_Yeosu_2015-08-15.jpg', // 간장게장(여수)
  jeonbok: 'https://upload.wikimedia.org/wikipedia/commons/3/30/Jeonbok-jjim.jpg', // 전복찜
  jeongsik: 'https://upload.wikimedia.org/wikipedia/commons/2/21/0606_hanjeongsik_damyang.jpg', // 담양 한정식
  myeon: 'https://upload.wikimedia.org/wikipedia/commons/7/78/Korean_cold_noodle_soup-Naengmyeon-01.jpg', // 냉면
  samgyetang: 'https://upload.wikimedia.org/wikipedia/commons/4/40/Samgyetang_Chicken_Ginseng_Soup.jpg', // 삼계탕
  banchan: 'https://upload.wikimedia.org/wikipedia/commons/8/87/Korean_cuisine-Kimchi_and_banchan-01.jpg', // 김치·반찬
}

const DEFAULT_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/5/5a/Korean_cuisine-Hoedeopbap-01.jpg'

export function categoryOf(r) {
  const hs = `${r.key || ''} ${(r.tags || []).join(' ')}`
  const hit = KEYWORD_MAP.find(({ kw }) => kw.some((k) => hs.includes(k)))
  return hit ? hit.cat : null
}

/* 식당 카드/상세용 이미지 — data/restaurants.js 항목에 image 필드(직접 수집한 실사진 경로/URL)가
   있으면 그걸 최우선으로 쓰고, 없으면 카테고리 스톡사진으로 대체한다. */
export function imageFor(r) {
  if (r?.image) return r.image
  const cat = categoryOf(r)
  return cat ? CATEGORY_IMAGES[cat] : DEFAULT_IMAGE
}

/* 제철 식재료용 이미지 (id 직접 매핑, 종류가 적어 카테고리 없이 바로 매핑) */
export const INGREDIENT_IMAGES = {
  jeonbok: 'https://upload.wikimedia.org/wikipedia/commons/1/11/Korean_cuisine-Jeonbok_hoe-01.jpg', // 전복회
  gul: 'https://upload.wikimedia.org/wikipedia/commons/b/b3/Gulhoe_and_jjokpa-ganghoe.jpg', // 굴회
  galchi: 'https://upload.wikimedia.org/wikipedia/commons/4/4d/Galchi-gui.jpg', // 갈치구이
  mulojingeo: 'https://upload.wikimedia.org/wikipedia/commons/6/61/Korean_cuisine-Ojingeo_bokkeum-01.jpg', // 오징어볶음
}

export function imageForIngredient(id) {
  return INGREDIENT_IMAGES[id] || DEFAULT_IMAGE
}
