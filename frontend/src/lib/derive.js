/* 도메인 파생 로직 — 태그/키워드 기반 알레르기·제철 매칭, 찜 기반 추천, 검색. */
import { SEASONAL, DISH_TO_ITEM } from '../data/seasonal.js'

export function haystack(r) {
  return `${(r.tags || []).join(' ')} ${r.key || ''} ${r.name || ''} ${r.desc || ''}`
}

/* 알레르기 자동 감지 (조개류·갑각류·연체류) */
const ALLERGENS = {
  조개류: ['꼬막', '전복', '굴', '조개', '새조개', '키조개', '바지락', '홍합', '멍게'],
  갑각류: ['게장', '간장게장', '양념게장', '꽃게', '새우', '대게', '갑각'],
  연체류: ['낙지', '오징어', '문어', '주꾸미', '갑오징어'],
}
export function allergyInfo(r) {
  const hs = haystack(r)
  const groups = Object.keys(ALLERGENS).filter((g) => ALLERGENS[g].some((a) => hs.includes(a)))
  const items = (r.tags || []).filter((t) => /전복|꼬막|굴|게장|새우|낙지|오징어|홍합|조개/.test(t)).slice(0, 3)
  return { groups, items }
}

/* 제철 시세 연결(실데이터) — 식당 메뉴/태그에서 '지금 제철'인 시세품목을 찾는다.
   ingredient_map(메뉴 키워드 → 시세품목)으로 매칭. 광주 사용자는 광주 시세 우선. */
export function seasonalFor(r, loc = {}) {
  const hs = haystack(r)
  const month = new Date().getMonth() + 1
  const isGwangju = loc.region === '광주'
  // 이 식당 메뉴에 등장하는 시세품목 후보
  const items = new Set()
  for (const [kw, item] of Object.entries(DISH_TO_ITEM)) {
    if (hs.includes(kw)) items.add(item)
  }
  if (!items.size) return null

  // 후보 중 지금 제철인 시세 레코드(광주 우선) 선택
  const cand = SEASONAL.filter(
    (s) => items.has(s.item) && s.peak_months.includes(month) && (isGwangju || s.region === '전국'),
  ).sort((a, b) => {
    const reg = (a.region === '광주' ? 0 : 1) - (b.region === '광주' ? 0 : 1)
    if (reg !== 0 && isGwangju) return reg
    return a.vsAvgPct - b.vsAvgPct
  })
  if (!cand.length) return null
  const s = cand[0]
  const tag = s.region === '광주' ? '광주' : '전국'
  return { id: s.id, label: `${tag} ${s.item} · 지금 제철`, delta: s.vsAvgPct, level: s.level }
}

/* 식당 → 핵심재료 1개 + 현재 시세 레코드(제철 여부 무관).
   seasonalFor 와 달리 peak_months 조건이 없어 '항상' 그 재료를 보여준다.
   반환: { item, record }(record 없으면 null) | null(재료 매칭 실패) */
export function keyIngredientFor(r, loc = {}) {
  const hs = haystack(r)
  const isGwangju = loc.region === '광주'
  const items = new Set()
  for (const [kw, item] of Object.entries(DISH_TO_ITEM)) {
    if (hs.includes(kw)) items.add(item)
  }
  if (!items.size) return null
  // 제철 조건 없이 (광주 우선 →) 연평균比 낮은(저렴) 순으로 시세 레코드 선택
  const cand = SEASONAL.filter(
    (s) => items.has(s.item) && (isGwangju || s.region === '전국'),
  ).sort((a, b) => {
    const reg = (a.region === '광주' ? 0 : 1) - (b.region === '광주' ? 0 : 1)
    if (reg !== 0 && isGwangju) return reg
    return a.vsAvgPct - b.vsAvgPct
  })
  const record = cand[0] || null
  return { item: record ? record.item : [...items][0], record }
}

/* 찜 기반 취향 추천 — 찜한 식당들의 태그·대표키워드·지역 빈도로 유사도 랭킹 */
export function favoriteProfile(favRestaurants) {
  const tagFreq = {}, keyFreq = {}, cityFreq = {}
  favRestaurants.forEach((r) => {
    ;(r.tags || []).forEach((t) => (tagFreq[t] = (tagFreq[t] || 0) + 1))
    if (r.key) keyFreq[r.key] = (keyFreq[r.key] || 0) + 1
    if (r.city) cityFreq[r.city] = (cityFreq[r.city] || 0) + 1
  })
  return { tagFreq, keyFreq, cityFreq, count: favRestaurants.length }
}
export function topTags(favRestaurants, n = 3) {
  const { tagFreq } = favoriteProfile(favRestaurants)
  return Object.keys(tagFreq).sort((a, b) => tagFreq[b] - tagFreq[a]).slice(0, n)
}
export function recommendByFavorites(favRestaurants, allRestaurants, limit = 6) {
  if (!favRestaurants.length) return []
  const favSet = new Set(favRestaurants.map((r) => r.id))
  const p = favoriteProfile(favRestaurants)
  const scored = allRestaurants
    .filter((r) => !favSet.has(r.id))
    .map((r) => {
      let score = 0
      const why = []
      ;(r.tags || []).forEach((t) => {
        if (p.tagFreq[t]) { score += 2 * p.tagFreq[t]; why.push(t) }
      })
      if (r.key && p.keyFreq[r.key]) { score += 1.5 * p.keyFreq[r.key]; why.push(r.key) }
      if (r.city && p.cityFreq[r.city]) score += 0.6 * p.cityFreq[r.city]
      return { r, score, why: [...new Set(why)].slice(0, 2) }
    })
    .filter((x) => x.score > 0)
  scored.sort((a, b) => b.score - a.score)
  // 관련도 상위 후보 풀에서 점수를 가중치로 삼아 무작위 추출 → 로딩할 때마다 다른 추천이 뜬다
  const pool = scored.slice(0, Math.max(limit * 4, 12))
  return weightedSample(pool, limit)
}

/* 점수를 가중치로 삼아 서로 다른 k개를 무작위 추출(높은 점수일수록 더 자주 뽑힘) */
function weightedSample(items, k) {
  const pool = items.slice()
  const out = []
  while (pool.length && out.length < k) {
    const total = pool.reduce((s, x) => s + x.score, 0)
    let r = Math.random() * total
    let idx = 0
    while (idx < pool.length - 1 && (r -= pool[idx].score) > 0) idx++
    out.push(pool.splice(idx, 1)[0])
  }
  return out
}

/* 검색 */
export function searchRestaurants(query, allRestaurants) {
  const toks = (query || '').split(/[\s,?!.]+/).filter((t) => t.length >= 2)
  if (!toks.length) return []
  return allRestaurants
    .map((r) => {
      const hs = `${haystack(r)} ${r.city}`
      let sc = 0
      toks.forEach((t) => {
        if (hs.includes(t)) sc += (r.tags || []).includes(t) || r.name.includes(t) ? 2 : 1
      })
      return { r, sc }
    })
    .filter((x) => x.sc > 0)
    .sort((a, b) => b.sc - a.sc)
    .map((x) => x.r)
}
