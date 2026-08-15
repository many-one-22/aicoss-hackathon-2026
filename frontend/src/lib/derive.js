/* 도메인 파생 로직 — 태그/키워드 기반 알레르기·제철 매칭, 찜 기반 추천, 검색.
   백엔드 감정분석/트렌드태그 모델이 준비되면 이 함수들을 API 호출로 대체 가능. */
import { SEASONAL } from '../data/seasonal.js'

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

/* 제철 식재료 연결 */
const SEASON_MAP = [
  { kw: ['전복'], id: 'jeonbok', label: '완도 전복 · 제철 (가을~겨울)' },
  { kw: ['굴'], id: 'gul', label: '고흥·여수 굴 · 제철 (11~2월)' },
  { kw: ['갈치'], id: 'galchi', label: '여수 갈치 · 가을~겨울' },
  { kw: ['오징어', '물오징어'], id: 'mulojingeo', label: '여수 물오징어 · 가을철' },
]
export function seasonalFor(r) {
  const hs = haystack(r)
  for (const m of SEASON_MAP) {
    if (m.kw.some((k) => hs.includes(k))) {
      const s = SEASONAL.find((x) => x.id === m.id)
      return { id: m.id, label: m.label, delta: s ? s.delta : 0 }
    }
  }
  return null
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
  return scored.slice(0, limit)
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
