/* AI 챗봇 추천 엔진 — minseo/scripts/data_prep 의 retrieve()/hard_filter()/recommend() 를
   프론트(실데이터 번들)로 이식한 것. Python·임베딩 없이 동일한 동작을 재현한다.
   파이프라인: 자연어 질의 → 필터 파싱(지역·재료·음식유형·건강) → 하드필터 →
               랭킹(질의 매칭 + 향토색 local_score + 현재 위치 근접) → 시세·시장 보강.
   ※ 원본 KoSBERT 의미검색 대신 '질의 토큰 매칭 + local_score + 거리' 하이브리드로 랭킹.

   [수정 이력] 대조 표현("A 말고 B", "A 대신 B") 처리 추가.
   기존엔 "감자 말고 전복"에서 "전복"만 재료로 인식해도 부정어 처리가 아예 없어서
   그냥 포함 조건으로 들어갔음(감자는 애초에 인식도 안 됨) → "말고" 뒤의 진짜 원하는
   재료가 아니라 무관한 결과가 섞여 나오는 문제가 있었음. */
import { RESTAURANTS } from '../data/restaurants.js'
import { MARKETS } from '../data/markets.js'
import { DISH_TO_ITEM } from '../data/seasonal.js'
import { distanceKm, cityByName } from '../data/geo.js'
import { haystack, seasonalFor } from './derive.js'

/* 질의어 → dish_type 값(회·생물 / 국물요리 / 구이 / 한상차림 / 면 / 찜) */
const DISH_TYPE_KW = {
  국물요리: ['국물', '탕', '국밥', '찌개', '전골', '해장', '매운탕', '지리', '순댓국', '해장국'],
  구이: ['구이', '고기', '삼겹', '불고기', '갈비', '숯불', '바베큐', 'bbq', '떡갈비'],
  '회·생물': ['회', '물회', '사시미', '활어', '초밥', '스시', '생선'],
  한상차림: ['정식', '한정식', '백반', '상차림', '한상', '집밥', '반찬', '코스'],
  면: ['국수', '칼국수', '냉면', '파스타', '짬뽕', '우동', '수제비'],
  찜: ['찜', '아귀찜', '찜닭'],
}
/* 상황(가족·혼밥·술·해장) — minseo 는 필터로는 안 쓰고 힌트로만 사용 */
const SITUATION_KW = {
  해장: ['해장', '속풀'],
  가족: ['가족', '아이', '부모', '모임'],
  혼밥: ['혼밥', '혼자'],
  술: ['술', '안주', '한잔', '포차', '반주'],
}
/* 알레르기 제외 키워드 — hard_filter.py 의 _CRUSTACEAN / _SHELLFISH 포팅 */
const CRUSTACEAN = ['새우', '꽃게', '대게', '게장', '게살', '게찜', '킹크랩', '크랩', '대하', '가재', '랍스터', '랍스타']
const SHELLFISH = ['조개', '꼬막', '바지락', '홍합', '굴', '소라', '전복', '가리비', '골뱅이', '키조개', '맛조개', '대합', '재첩']
/* 재료 어휘 — ingredient_map 키 + 남도 대표 식재료 (+ 대조 표현에서 흔히 나오는 일반 재료도 포함) */
const INGREDIENTS = [
  ...new Set([
    ...Object.keys(DISH_TO_ITEM),
    ...SHELLFISH,
    ...CRUSTACEAN,
    '낙지', '오징어', '문어', '주꾸미', '갈치', '고등어', '장어', '갯장어', '홍어', '매생이', '김', '병어', '민어',
    '삼겹', '불고기', '떡갈비', '육회', '육전', '한우', '오리', '삼계탕', '추어탕', '곰탕', '떡국', '비빔밥', '국밥',
    '감자', '고구마', '두부', '버섯', '가지', '호박',
  ]),
]

/* 대조 표현("A 말고 B", "A 대신 B", "A보다는 B") — A는 제외, B는 포함으로 정확히 나눠 해석한다.
   순수 부정어("싫어/안 먹어/빼고/제외" 등)만 있는 경우엔 대조 대상이 없으니
   언급된 재료 전부를 제외 조건으로 처리한다. */
const CONTRASTIVE_WORDS = ['말고', '대신', '아니라', '아니고', '보다는']

// 순수 거부/제외 표현. 띄어쓰기 유무가 갈리는 건 둘 다 넣어둠(안 먹어요 / 안먹어요 등).
// '싫'/'별로'/'극혐'처럼 어간만 넣은 건 뒤에 어미가 뭐가 붙어도(싫어/싫은데/싫고 등) 다 잡히게 하려는 의도.
const NEGATION_WORDS = [
  '싫',
  '안 먹', '안먹',
  '못 먹', '못먹',
  '빼고', '빼줘', '빼주세요',
  '제외',
  '알레르기',
  '비추',
  '안돼', '안 돼',
  '별로',
  '극혐',
  '안 좋아', '안좋아',
  '꺼려',
  '기피',
]

/* 카테고리 단어("해산물"/"육류"/"채소") — INGREDIENTS(구체적 재료명)와 별도로 관리한다.
   메뉴 텍스트엔 "해산물"이란 단어 자체가 거의 안 나오고(예: "낙지볶음"이라고 쓰지
   "해산물"이라고 안 씀) 대신 r.tags 배열에 분류값으로 들어있어서, 매칭 방식이 달라야 한다
   (haystack 텍스트 검색이 아니라 tags 배열 포함 여부로 체크).
   [수정 이력] "해산물 싫어"가 INGREDIENTS에 없어서 아예 필터링 자체가 안 걸리던 버그 수정
   (retrieve.py에서 먼저 발견된 것과 동일한 종류의 문제). */
const CATEGORY_WORDS = ['해산물', '육류', '채소']

// 사람들이 정식 카테고리명 대신 흔히 쓰는 구어체 → 카테고리 매핑.
// [수정 이력] "고기 싫어"가 CATEGORY_WORDS엔 "육류"만 있어서 안 걸리던 버그 수정
// (실제로 "고기 싫어"라고 했는데 "남도한우"(구이)를 추천하는 문제가 있었음).
const CATEGORY_SYNONYMS = {
  고기: '육류',
  생선: '해산물',
  야채: '채소',
  나물: '채소',
}

function findCategories(text) {
  const found = new Set()
  for (const c of CATEGORY_WORDS) if (text.includes(c)) found.add(c)
  for (const [syn, cat] of Object.entries(CATEGORY_SYNONYMS)) if (text.includes(syn)) found.add(cat)
  return [...found]
}

/* 대조 표현("A 말고 B") 기준으로 텍스트를 앞/뒤로 쪼갠다. 재료뿐 아니라 음식유형·상황·건강
   조건도 전부 이 쪼갠 텍스트를 기준으로 판단해야 한다.
   [수정 이력] "떡갈비 말고 회"에서 dishType은 원문 전체를 훑어서 "떡갈비"(구이 키워드)랑
   "회"(회·생물 키워드)가 둘 다 걸려버리는 버그가 있었음 — 제외하겠다는 "떡갈비"까지
   긍정 조건으로 잡혀서, 회 대신 구이(떡갈비) 집이 추천되는 문제. 재료 필터만 대조표현을
   이해하고 나머지(dishType 등)는 원문 전체를 그대로 쓰던 게 원인 — 전부 통일함. */
function splitByContrastive(text) {
  for (const w of CONTRASTIVE_WORDS) {
    const idx = text.indexOf(w)
    if (idx !== -1) {
      return { before: text.slice(0, idx), after: text.slice(idx + w.length), hasContrastive: true }
    }
  }
  return { before: '', after: text, hasContrastive: false }
}

function parseIngredientPreference(before, after, hasContrastive) {
  if (hasContrastive) {
    return {
      excludeIngredients: [...new Set(INGREDIENTS.filter((ing) => before.includes(ing)))],
      excludeCategories: findCategories(before),
      ingredients: [...new Set(INGREDIENTS.filter((ing) => after.includes(ing)))],
      categories: findCategories(after),
    }
  }
  const mentionedIngredients = [...new Set(INGREDIENTS.filter((ing) => after.includes(ing)))]
  const mentionedCategories = findCategories(after)
  const negated = NEGATION_WORDS.some((w) => after.includes(w))
  return negated
    ? { excludeIngredients: mentionedIngredients, excludeCategories: mentionedCategories, ingredients: [], categories: [] }
    : { excludeIngredients: [], excludeCategories: [], ingredients: mentionedIngredients, categories: mentionedCategories }
}

export function parseQuery(text) {
  const t = text || ''
  const { before, after, hasContrastive } = splitByContrastive(t)
  // 대조 표현이 있으면 "after"(진짜 원하는 것)만 보고, 없으면 원문 전체(after=t)를 본다.
  const positive = after

  const { ingredients, excludeIngredients, categories, excludeCategories } = parseIngredientPreference(before, after, hasContrastive)

  const dishType = Object.entries(DISH_TYPE_KW)
    .filter(([, kws]) => kws.some((k) => positive.toLowerCase().includes(k)))
    .map(([dt]) => dt)

  const situation = Object.entries(SITUATION_KW)
    .filter(([, kws]) => kws.some((k) => positive.includes(k)))
    .map(([s]) => s)
  const health = []
  if (positive.includes('갑각류') && positive.includes('제외')) health.push('갑각류 제외')
  if (positive.includes('조개') && positive.includes('제외')) health.push('조개류 제외')
  if (positive.includes('채식') || positive.includes('비건')) health.push('채식')
  // 해장이면 국물요리 성향으로(원본 recommend 의 상황→유형 근사)
  if (situation.includes('해장') && !dishType.includes('국물요리')) dishType.push('국물요리')
  const tokens = positive.split(/[\s,?!.]+/).filter((x) => x.length >= 2)
  return { dishType, ingredients, excludeIngredients, categories, excludeCategories, situation, health, tokens }
}

function passesHealth(r, health) {
  if (!health.length) return true
  const hs = haystack(r)
  if (health.includes('갑각류 제외') && CRUSTACEAN.some((k) => hs.includes(k))) return false
  if (health.includes('조개류 제외') && SHELLFISH.some((k) => hs.includes(k))) return false
  if (health.includes('채식')) {
    const tags = r.tags || []
    if (!tags.includes('채소')) return false
    if (tags.includes('육류') || tags.includes('해산물')) return false
  }
  return true
}

/* hard_filter + 랭킹 — 현재 위치(권역·거리) 반영. 반환: {filters, fallback, results[]} */
/* 질의에서 아무 신호도 못 뽑았는지 판단한다("노트북" 같은 무관한 단어).
   조건(음식유형/재료/카테고리/건강/상황)이 하나도 안 걸렸고, 토큰 중 어떤 것도
   식당 메뉴·이름에 문자 그대로 등장하지 않으면 "이해 못 함"으로 본다.
   [수정 이력] 예전엔 이 경우도 그냥 local_score 1등 식당을 자신 있게 추천해버려서,
   마치 "노트북"을 이해하고 골라준 것처럼 보이는 문제가 있었음. */
function isUnderstood(f) {
  const hasFilter =
    f.dishType.length || f.ingredients.length || f.excludeIngredients.length ||
    f.categories.length || f.excludeCategories.length || f.health.length || f.situation.length
  if (hasFilter) return true
  if (!f.tokens.length) return false
  return f.tokens.some((tk) => RESTAURANTS.some((r) => haystack(r).includes(tk)))
}

export function retrieveLocal(text, loc = {}, topN = 6) {
  const f = parseQuery(text)
  const region = typeof loc === 'string' ? null : loc.region
  const origin =
    loc.lat != null && loc.lng != null
      ? { lat: loc.lat, lng: loc.lng }
      : region === '광주'
        ? cityByName('광주')
        : null

  // 아무 신호도 없으면 자신 있게 추천하지 말고 정직하게 "결과 없음"으로 반환
  // (client.js의 기존 "못 찾았어요" 안내 메시지로 자연스럽게 이어짐)
  if (!isUnderstood(f)) {
    return { filters: f, fallback: false, understood: false, results: [] }
  }

  const match = (r) => {
    if (region && r.region !== region) return false // 같은 권역(지역 필터)
    if (!passesHealth(r, f.health)) return false
    // 대조 표현으로 걸린 재료(예: "감자 말고 전복"의 감자)는 무조건 제외
    if (f.excludeIngredients.length) {
      const hs = haystack(r)
      if (f.excludeIngredients.some((ing) => hs.includes(ing))) return false
    }
    // 카테고리 제외("해산물 싫어") — tags 배열로 체크 (메뉴 텍스트엔 "해산물"이란 말 자체가 잘 안 나옴)
    if (f.excludeCategories.length) {
      const tags = r.tags || []
      if (f.excludeCategories.some((c) => tags.includes(c))) return false
    }
    if (f.dishType.length && !f.dishType.some((dt) => (r.key || '').includes(dt) || (r.tags || []).some((tg) => tg.includes(dt))))
      return false
    if (f.ingredients.length) {
      const hs = haystack(r)
      if (!f.ingredients.some((ing) => hs.includes(ing))) return false
    }
    if (f.categories.length) {
      const tags = r.tags || []
      if (!f.categories.some((c) => tags.includes(c))) return false
    }
    return true
  }

  let cands = RESTAURANTS.filter(match)
  let fallback = false
  // 조건이 너무 좁아 0곳이면 지역·건강·제외조건만 유지하고 재검색(원본의 지역 폴백과 같은 취지)
  if (!cands.length) {
    fallback = true
    cands = RESTAURANTS.filter((r) => {
      if (region && r.region !== region) return false
      if (!passesHealth(r, f.health)) return false
      if (f.excludeIngredients.length) {
        const hs = haystack(r)
        if (f.excludeIngredients.some((ing) => hs.includes(ing))) return false
      }
      if (f.excludeCategories.length) {
        const tags = r.tags || []
        if (f.excludeCategories.some((c) => tags.includes(c))) return false
      }
      return true
    })
  }

  const scored = cands
    .map((r) => {
      const hs = haystack(r)
      let rel = 0
      f.ingredients.forEach((ing) => hs.includes(ing) && (rel += 3))
      f.dishType.forEach((dt) => (r.key || '').includes(dt) && (rel += 2))
      f.tokens.forEach((tk) => hs.includes(tk) && (rel += 1))
      const dist = origin && r.lat != null ? distanceKm(origin, r) : 999
      return { r, dist, score: rel * 10 + (r.local_score || 0) * 2 - Math.min(dist, 50) / 10 }
    })
    .sort((a, b) => b.score - a.score)

  return {
    filters: f,
    fallback,
    understood: true,
    results: scored.slice(0, topN).map((s) => ({ ...s.r, _distKm: Math.round(s.dist) })),
  }
}

/* 같은 시·군 전통시장 — recommend.py 의 _region_markets 포팅(점포수 많은 순) */
export function regionMarkets(city, k = 2) {
  if (!city) return []
  return MARKETS.filter((m) => m.city === city)
    .sort((a, b) => (b.stores || 0) - (a.stores || 0))
    .slice(0, k)
}

/* 추천 근거 한 줄 — 제철 시세 + 지역 시장 보강(recommend 의 prices/region_markets 역할) */
export function enrich(r, loc) {
  const bits = []
  const season = seasonalFor(r, loc)
  if (season) bits.push(`${season.label.replace(' · 지금 제철', '')} 제철${season.level === '저렴' ? '·시세 저렴' : ''}`)
  const mk = regionMarkets(r.city, 1)[0]
  if (mk) bits.push(`근처 ${mk.name}(점포 ${mk.stores || '-'})`)
  return bits
}
