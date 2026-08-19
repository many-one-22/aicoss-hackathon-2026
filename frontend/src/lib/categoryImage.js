/* 요리 카테고리별 대표 이미지 — restaurants.real.json의 key(대표 dish_type)로 바로 매핑한다.
   실데이터 key는 13종의 넓은 분류(카페/국물요리/한식/면/구이/회·생물/양식/치킨/한상차림/주점/찜/중식/일식)라
   이름 그대로 딕셔너리 조회만 하면 된다. 지금은 Wikimedia Commons의 실제 한식 사진(무료/저작권 문제없음)이고,
   실사 준비되면 CATEGORY_IMAGES/INGREDIENT_IMAGES 값만 바꾸면 전체 화면에 한 번에 반영된다.
   카테고리마다 사진을 여러 장 두고 가게 id 기준으로 골고루 분산시켜서, 같은 카테고리 가게들이
   전부 똑같은 사진을 쓰지 않도록 한다. */

/* Wikimedia Commons 실사진의 CDN 직링크. Special:FilePath 리다이렉트 대신 최종 URL을 써야
   여러 장을 동시에 불러올 때 위키미디어 쪽 속도제한(429)에 걸리지 않는다. */
export const CATEGORY_IMAGES = {
  '카페': [
    'https://upload.wikimedia.org/wikipedia/commons/7/76/Cup_of_coffee_with_latte_art_2016.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/b/be/Iced_Americano_1.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/c/c2/Cold_brew_for_Terra.jpg',
  ],
  '국물요리': [
    'https://upload.wikimedia.org/wikipedia/commons/b/b4/Korean_stew-Doenjang_jjigae-01.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/a/a6/Budae-jjigae_1.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/3/3c/Korean_stew-Budae_jjigae-01.jpg',
  ],
  '한식': [
    'https://upload.wikimedia.org/wikipedia/commons/5/5a/Korean_cuisine-Hoedeopbap-01.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/f/fe/Bibimbap_with_egg.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/3/33/Stone_bowl_Bibimbap_(29938996780).jpg',
  ],
  '면': [
    'https://upload.wikimedia.org/wikipedia/commons/7/78/Korean_cold_noodle_soup-Naengmyeon-01.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/b/b8/Korean.noodle-Kalguksu-01.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/e/e2/Kal-guksu_4.jpg',
  ],
  '구이': [
    'https://upload.wikimedia.org/wikipedia/commons/2/23/Korean.cuisine-Gui_yori-01.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/f/fd/Korean.cuisine-Bulgogi-01.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/7/76/Bulgogi_3.jpg',
  ],
  '회·생물': [
    'https://upload.wikimedia.org/wikipedia/commons/4/45/Korean_cuisine-Saengseon_hoe-02.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/7/79/Sashimi_plate.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/1/11/Korean_cuisine-Jeonbok_hoe-01.jpg',
  ],
  '양식': [
    'https://upload.wikimedia.org/wikipedia/commons/c/c5/Beef_steak_of_the_set_of_dinner.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/e/e2/Plate_of_Pasta_(Unsplash).jpg',
    'https://upload.wikimedia.org/wikipedia/commons/b/bc/Two_pizza_slices.jpg',
  ],
  '치킨': [
    'https://upload.wikimedia.org/wikipedia/commons/a/aa/Korean_fried_chicken_240206.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/6/6a/Yangnyeom_Chicken_Korean_fried_chicken.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/1/1e/Korean.cuisine-Yangnyeom_chicken-01.jpg',
  ],
  '한상차림': [
    'https://upload.wikimedia.org/wikipedia/commons/2/21/0606_hanjeongsik_damyang.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/8/87/Korean_cuisine-Kimchi_and_banchan-01.jpg',
  ],
  '주점': [
    'https://upload.wikimedia.org/wikipedia/commons/4/4e/Buchimgae_and_makgeolli.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/8/84/Soju.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/9/97/Pajeon.jpg',
  ],
  '찜': [
    'https://upload.wikimedia.org/wikipedia/commons/3/30/Jeonbok-jjim.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/d/df/Korean_steamed_food-Agujjim-01.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/9/96/Korean_braised_beef_short_ribs-Galbijjim.jpg',
  ],
  '중식': [
    'https://upload.wikimedia.org/wikipedia/commons/5/51/Jajangmyeon_1.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/3/3e/Jjamppong_1.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/1/12/Jjamppong_2.jpg',
  ],
  '일식': [
    'https://upload.wikimedia.org/wikipedia/commons/d/d5/Japanese_Sushi_platter.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/9/97/A_bowl_of_ramen_in_Osaka%2C_Japan.jpg',
    'https://upload.wikimedia.org/wikipedia/commons/a/a4/Bowl_of_shio_ramen_with_pork.jpg',
  ],
}

const DEFAULT_IMAGE = CATEGORY_IMAGES['한식'][0]

/* 가게 id를 시드로 카테고리 사진 풀에서 하나를 고정 선택 — 새로고침해도 같은 가게는 항상
   같은 사진, 같은 카테고리 안의 다른 가게는 다른 사진이 나온다. */
function pickFromPool(pool, seed) {
  if (!pool || pool.length === 0) return DEFAULT_IMAGE
  const n = Number(seed)
  const idx = Number.isFinite(n) ? Math.abs(n) % pool.length : 0
  return pool[idx]
}

/* 식당 카드/상세용 이미지 — data 항목에 image 필드(직접 수집한 실사진 경로/URL)가
   있으면 그걸 최우선으로 쓰고, 없으면 key(대표 dish_type) 카테고리 풀에서 id 기준으로 하나 골라 쓴다. */
export function imageFor(r) {
  if (r?.image) return r.image
  const pool = CATEGORY_IMAGES[r?.key]
  return pool ? pickFromPool(pool, r?.id) : DEFAULT_IMAGE
}

/* 제철 식재료용 이미지 — seasonal.real.json에 등장하는 각 품목에 실제 그 재료 사진을 매칭.
   실데이터 id(nat-1, gj-3 등)는 화면마다 달라질 수 있어 식재료 이름(item)으로 매칭한다.
   값이 '/images/...' 로 시작하면 직접 넣은 로컬 사진(frontend/public/ 아래)을 쓴다. */
const ITEM_IMAGES = {
  가리비: 'https://upload.wikimedia.org/wikipedia/commons/3/3b/Scallops.jpg',
  간장: 'https://upload.wikimedia.org/wikipedia/commons/1/12/Soy_sauce.jpg',
  갈치: 'https://upload.wikimedia.org/wikipedia/commons/4/4d/Galchi-gui.jpg',
  감귤: 'https://upload.wikimedia.org/wikipedia/commons/5/55/Mandarin_orange.jpg',
  감자: '/images/seasonal/potato.jpg',
  갓: 'https://upload.wikimedia.org/wikipedia/commons/4/4c/Starr-150403-0144-Brassica_juncea-leaf-Southeast_Eastern_Island-Midway_Atoll_(24648901563).jpg',
  건고추: 'https://upload.wikimedia.org/wikipedia/commons/b/b2/Inle_Lake,_Dried_red_chili_(chilli)_pepper,_Capsicum_annuum,_Myanmar.jpg',
  건다시마: 'https://upload.wikimedia.org/wikipedia/commons/3/3e/Japan,_Hokkaido,_drying_kelp_2.jpg',
  건멸치: 'https://upload.wikimedia.org/wikipedia/commons/5/59/Dried_anchovies_in_Yeosu2.jpg',
  건미역: 'https://upload.wikimedia.org/wikipedia/commons/f/f8/Dried_miyeok.jpg',
  건오징어: 'https://upload.wikimedia.org/wikipedia/commons/6/61/Korean_cuisine-Ojingeo_bokkeum-01.jpg',
  고구마: 'https://upload.wikimedia.org/wikipedia/commons/4/42/Sweet_potato.jpg',
  고등어: 'https://upload.wikimedia.org/wikipedia/commons/8/8e/Mackerel.jpg',
  고추장: 'https://upload.wikimedia.org/wikipedia/commons/e/e5/Fruit_tea,_mayonnaise,_and_gochujang_on_display_in_Lotte_Plaza_Market,_Tampa,_Florida,_on_15_January_2025.jpg',
  고춧가루: 'https://upload.wikimedia.org/wikipedia/commons/e/e0/Gochugaru.jpg',
  굴: 'https://upload.wikimedia.org/wikipedia/commons/b/b3/Gulhoe_and_jjokpa-ganghoe.jpg',
  굵은소금: 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Sea_salt.jpg',
  김: 'https://upload.wikimedia.org/wikipedia/commons/b/be/Nori.jpg',
  김치: 'https://upload.wikimedia.org/wikipedia/commons/8/87/Korean_cuisine-Kimchi_and_banchan-01.jpg',
  깐마늘: 'https://upload.wikimedia.org/wikipedia/commons/f/f1/Garlic_cloves.jpg',
  깻잎: 'https://upload.wikimedia.org/wikipedia/commons/8/8b/Perilla_frutescens.jpg',
  꽁치: 'https://upload.wikimedia.org/wikipedia/commons/8/80/Sanma01.jpg',
  녹두: 'https://upload.wikimedia.org/wikipedia/commons/5/5e/Mung_beans.jpg',
  느타리버섯: 'https://upload.wikimedia.org/wikipedia/commons/d/d7/Oyster_mushroom.jpg',
  단감: 'https://upload.wikimedia.org/wikipedia/commons/c/c7/Persimmon.jpg',
  당근: 'https://upload.wikimedia.org/wikipedia/commons/d/d2/Carrots_with_stems.jpg',
  된장: 'https://upload.wikimedia.org/wikipedia/commons/8/87/Doenjang.jpg',
  두부: 'https://upload.wikimedia.org/wikipedia/commons/5/5d/Tofu.jpg',
  딸기: 'https://upload.wikimedia.org/wikipedia/commons/0/0f/Strawberry.jpg',
  땅콩: 'https://upload.wikimedia.org/wikipedia/commons/8/82/Peanut.jpg',
  레몬: 'https://upload.wikimedia.org/wikipedia/commons/2/21/Tangerine.jpg',
  마른멸치: 'https://upload.wikimedia.org/wikipedia/commons/5/59/Dried_anchovies_in_Yeosu2.jpg',
  마른미역: 'https://upload.wikimedia.org/wikipedia/commons/f/f8/Dried_miyeok.jpg',
  마른오징어: 'https://upload.wikimedia.org/wikipedia/commons/6/61/Korean_cuisine-Ojingeo_bokkeum-01.jpg',
  맛김: 'https://upload.wikimedia.org/wikipedia/commons/b/be/Nori.jpg',
  망고: 'https://upload.wikimedia.org/wikipedia/commons/f/fe/Mango.jpg',
  멜론: 'https://upload.wikimedia.org/wikipedia/commons/b/b6/Melon.jpg',
  멸치액젓: 'https://upload.wikimedia.org/wikipedia/commons/d/d1/Fish_soy_sauce_bottle_(37082990452).jpg',
  명태: 'https://upload.wikimedia.org/wikipedia/commons/9/9b/Alaska_pollock_2.jpg',
  무: 'https://upload.wikimedia.org/wikipedia/commons/a/a8/Daikon.jpg',
  물오징어: 'https://upload.wikimedia.org/wikipedia/commons/6/61/Korean_cuisine-Ojingeo_bokkeum-01.jpg',
  미나리: 'https://upload.wikimedia.org/wikipedia/commons/a/a0/Oenanthe_javanica1.jpg',
  바나나: 'https://upload.wikimedia.org/wikipedia/commons/c/c7/Banana.jpg',
  바지락: 'https://upload.wikimedia.org/wikipedia/commons/8/86/Fresh_clam_soup.jpg',
  방울토마토: 'https://upload.wikimedia.org/wikipedia/commons/b/b5/Cherry_tomatoes.jpg',
  배: 'https://upload.wikimedia.org/wikipedia/commons/4/46/Korean_pear.jpg',
  배추: 'https://upload.wikimedia.org/wikipedia/commons/6/6c/Napa_cabbage.jpg',
  복숭아: 'https://upload.wikimedia.org/wikipedia/commons/d/d5/Peaches.jpg',
  붉은고추: 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Red_chili.jpg',
  브로콜리: 'https://upload.wikimedia.org/wikipedia/commons/4/41/Broccoli.jpg',
  사과: 'https://upload.wikimedia.org/wikipedia/commons/2/2b/Apple.jpg',
  상추: 'https://upload.wikimedia.org/wikipedia/commons/7/74/Lettuce.jpg',
  새송이버섯: '/images/seasonal/king-oyster-mushroom.jpg',
  새우: 'https://upload.wikimedia.org/wikipedia/commons/a/a6/Shrimp.jpg',
  새우젓: 'https://upload.wikimedia.org/wikipedia/commons/b/b9/Saeu-jeot_1.jpg',
  생강: 'https://upload.wikimedia.org/wikipedia/commons/2/23/Ginger.jpg',
  수박: 'https://upload.wikimedia.org/wikipedia/commons/b/b9/Watermelon.jpg',
  수입조기: 'https://upload.wikimedia.org/wikipedia/commons/0/0f/Dried_yellow_croaker_(20241102).jpg',
  시금치: 'https://upload.wikimedia.org/wikipedia/commons/c/cd/Spinach.jpg',
  쌀: 'https://upload.wikimedia.org/wikipedia/commons/a/a3/White_rice.jpg',
  아몬드: 'https://upload.wikimedia.org/wikipedia/commons/a/a5/Almond.jpg',
  아보카도: 'https://upload.wikimedia.org/wikipedia/commons/8/81/Avocado.jpg',
  알배기배추: 'https://upload.wikimedia.org/wikipedia/commons/6/6c/Napa_cabbage.jpg',
  양배추: 'https://upload.wikimedia.org/wikipedia/commons/7/70/Cabbage.jpg',
  양파: 'https://upload.wikimedia.org/wikipedia/commons/9/93/Onion.jpg',
  얼갈이배추: 'https://upload.wikimedia.org/wikipedia/commons/6/6c/Napa_cabbage.jpg',
  열무: 'https://upload.wikimedia.org/wikipedia/commons/1/1f/Yeolmu_Kimchi.jpg',
  오렌지: 'https://upload.wikimedia.org/wikipedia/commons/8/83/Oranges.jpg',
  오이: 'https://upload.wikimedia.org/wikipedia/commons/0/0a/Cucumber.jpg',
  전복: 'https://upload.wikimedia.org/wikipedia/commons/1/11/Korean_cuisine-Jeonbok_hoe-01.jpg',
  절임배추: 'https://upload.wikimedia.org/wikipedia/commons/6/6c/Napa_cabbage.jpg',
  조기: 'https://upload.wikimedia.org/wikipedia/commons/d/d2/Frozen-fresh_yellow_croaker.jpg',
  참깨: 'https://upload.wikimedia.org/wikipedia/commons/d/d9/Sesame_seed.jpg',
  참다래: 'https://upload.wikimedia.org/wikipedia/commons/3/38/Kiwifruit.jpg',
  참외: 'https://upload.wikimedia.org/wikipedia/commons/0/0c/Korean_melon-Chamoe-01.jpg',
  찹쌀: 'https://upload.wikimedia.org/wikipedia/commons/a/a7/Sticky_rice.jpg',
  천일염: 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Sea_salt.jpg',
  체리: 'https://upload.wikimedia.org/wikipedia/commons/0/0e/Cherries.jpg',
  콩: 'https://upload.wikimedia.org/wikipedia/commons/3/33/Soybean.jpg',
  콩나물: 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Soybean_sprouts.jpg',
  토마토: 'https://upload.wikimedia.org/wikipedia/commons/a/a2/Tomato.jpg',
  파: 'https://upload.wikimedia.org/wikipedia/commons/b/bc/Spring_onions.jpg',
  파인애플: 'https://upload.wikimedia.org/wikipedia/commons/a/a1/Pineapple.jpg',
  파프리카: 'https://upload.wikimedia.org/wikipedia/commons/9/95/Paprika.jpg',
  팥: 'https://upload.wikimedia.org/wikipedia/commons/3/32/Adzuki_beans.jpg',
  팽이버섯: 'https://upload.wikimedia.org/wikipedia/commons/9/90/Enoki_mushroom.jpg',
  포도: 'https://upload.wikimedia.org/wikipedia/commons/6/6b/Grapes.jpg',
  풋고추: 'https://upload.wikimedia.org/wikipedia/commons/9/9d/Green_chili_pepper.jpg',
  피망: 'https://upload.wikimedia.org/wikipedia/commons/c/c0/Bell_pepper.jpg',
  호두: 'https://upload.wikimedia.org/wikipedia/commons/0/0a/Walnut.jpg',
  호박: 'https://upload.wikimedia.org/wikipedia/commons/f/f7/Pumpkin.jpg',
  홍합: 'https://upload.wikimedia.org/wikipedia/commons/f/f0/Mussel.jpg',
}

export function imageForIngredient(item) {
  return ITEM_IMAGES[item] || DEFAULT_IMAGE
}
