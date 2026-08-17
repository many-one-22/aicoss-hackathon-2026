/* AI 챗봇 추천 엔진 — minseo/scripts/data_prep 의 retrieve()/hard_filter()/recommend() 를
   프론트(실데이터 번들)로 이식한 것. Python·임베딩 없이 동일한 동작을 재현한다.
   파이프라인: 자연어 질의 → 필터 파싱(지역·재료·음식유형·건강) → 하드필터 →
               랭킹(질의 매칭 + 향토색 local_score + 현재 위치 근접) → 시세·시장 보강.
   ※ 원본 KoSBERT 의미검색 대신 '질의 토큰 매칭 + local_score + 거리' 하이브리드로 랭킹. */
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
/* 재료 어휘 — ingredient_map 키 + 남도 대표 식재료 */
const INGREDIENTS = [
  ...new Set([
    ...Object.keys(DISH_TO_ITEM),
    ...SHELLFISH,
    ...CRUSTACEAN,
    '낙지', '오징어', '문어', '주꾸미', '갈치', '고등어', '장어', '갯장어', '홍어', '매생이', '김', '병어', '민어',
    '삼겹', '불고기', '떡갈비', '육회', '육전', '한우', '오리', '삼계탕', '추어탕', '곰탕', '떡국', '비빔밥', '국밥',
  ]),
]

export function parseQuery(text) {
  const t = text || ''
  const dishType = Object.entries(DISH_TYPE_KW)
    .filter(([, kws]) => kws.some((k) => t.toLowerCase().includes(k)))
    .map(([dt]) => dt)
  const ingredients = [...new Set(INGREDIENTS.filter((ing) => t.includes(ing)))]
  const situation = Object.entries(SITUATION_KW)
    .filter(([, kws]) => kws.some((k) => t.includes(k)))
    .map(([s]) => s)
  const health = []
  if (t.includes('갑각류') && t.includes('제외')) health.push('갑각류 제외')
  if (t.includes('조개') && t.includes('제외')) health.push('조개류 제외')
  if (t.includes('채식') || t.includes('비건')) health.push('채식')
  // 해장이면 국물요리 성향으로(원본 recommend 의 상황→유형 근사)
  if (situation.includes('해장') && !dishType.includes('국물요리')) dishType.push('국물요리')
  const tokens = t.split(/[\s,?!.]+/).filter((x) => x.length >= 2)
  return { dishType, ingredients, situation, health, tokens }
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
export function retrieveLocal(text, loc = {}, topN = 6) {
  const f = parseQuery(text)
  const region = typeof loc === 'string' ? null : loc.region
  const origin =
    loc.lat != null && loc.lng != null
      ? { lat: loc.lat, lng: loc.lng }
      : region === '광주'
        ? cityByName('광주')
        : null

  const match = (r) => {
    if (region && r.region !== region) return false // 같은 권역(지역 필터)
    if (!passesHealth(r, f.health)) return false
    if (f.dishType.length && !f.dishType.some((dt) => (r.key || '').includes(dt) || (r.tags || []).some((tg) => tg.includes(dt))))
      return false
    if (f.ingredients.length) {
      const hs = haystack(r)
      if (!f.ingredients.some((ing) => hs.includes(ing))) return false
    }
    return true
  }

  let cands = RESTAURANTS.filter(match)
  let fallback = false
  // 조건이 너무 좁아 0곳이면 지역·건강만 유지하고 재검색(원본의 지역 폴백과 같은 취지)
  if (!cands.length) {
    fallback = true
    cands = RESTAURANTS.filter((r) => (!region || r.region === region) && passesHealth(r, f.health))
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
