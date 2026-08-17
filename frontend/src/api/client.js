/* API 클라이언트 — 모든 화면은 이 모듈만 호출한다.
   데이터는 namdo.sqlite 에서 추출한 실데이터 JSON(src/data/*.real.json)을 사용한다.
   위치는 브라우저 Geolocation 좌표를 광주·전남 도시로 오프라인 매핑(geo.js)해 얻고,
   식당/시장/추천/제철을 모두 '현재 위치' 기준으로 필터·정렬한다. */
import { RESTAURANTS } from '../data/restaurants.js'
import { SEASONAL, DISH_TO_ITEM } from '../data/seasonal.js'
import { MARKETS } from '../data/markets.js'
import { CITIES, nearestCity, cityByName, distanceKm } from '../data/geo.js'
import { allergyInfo, seasonalFor, searchRestaurants } from '../lib/derive.js'
import { retrieveLocal, enrich } from '../lib/chatbot.js'

const delay = (ms = 200) => new Promise((res) => setTimeout(res, ms))
const LEVEL_ORDER = { 저렴: 0, 평균: 1, 비쌈: 2 }

/* loc 에서 정렬 기준 좌표를 얻는다(없으면 null). */
function originOf(loc = {}) {
  if (loc.lat != null && loc.lng != null) return { lat: loc.lat, lng: loc.lng }
  const c = loc.city ? cityByName(loc.city) : loc.region === '광주' ? cityByName('광주') : null
  return c ? { lat: c.lat, lng: c.lng } : null
}
/* 좌표가 있는 항목을 사용자와 가까운 순으로 정렬(사본 반환). */
function byDistance(list, origin) {
  if (!origin) return list.slice()
  return list
    .map((x) => ({ x, d: x.lat != null && x.lng != null ? distanceKm(origin, x) : Infinity }))
    .sort((a, b) => a.d - b.d)
    .map((o) => ({ ...o.x, _distKm: Math.round(o.d) }))
}

export async function getRestaurants() {
  await delay()
  return RESTAURANTS
}

export async function getRestaurant(id) {
  await delay(120)
  return RESTAURANTS.find((r) => r.id === Number(id)) || null
}

/* 현재 위치에서 가까운 순 식당(같은 권역 우선). 각 항목에 _distKm 포함. */
export async function getRestaurantsNear(loc = {}, { region = true } = {}) {
  await delay(160)
  const origin = originOf(loc)
  const reg = typeof loc === 'string' ? null : loc.region
  const pool = region && reg ? RESTAURANTS.filter((r) => r.region === reg) : RESTAURANTS
  return byDistance(pool.length ? pool : RESTAURANTS, origin)
}

/* ── 위치 자동 감지 ── */
function locFromCity(c, auto = true) {
  return { city: c.name, region: c.region, lat: c.lat, lng: c.lng, label: `${c.name} · ${auto ? '자동감지' : '선택'}` }
}
export async function detectLocation() {
  const fallback = locFromCity(cityByName('광주'))
  if (!('geolocation' in navigator)) return fallback
  try {
    const pos = await new Promise((resolve, reject) =>
      navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 4000, maximumAge: 600000 }),
    )
    const { latitude, longitude } = pos.coords
    const c = nearestCity(latitude, longitude)
    return { city: c.name, region: c.region, lat: latitude, lng: longitude, label: `${c.name} · 자동감지` }
  } catch {
    return fallback
  }
}
export function locationChoices() {
  return CITIES.map((c) => c.name)
}
export function locationByName(name) {
  const c = cityByName(name)
  return c ? locFromCity(c, false) : null
}

/* ── 제철 시세 (실데이터) ──
   현재 월에 성수기(peak_months)인 품목만. 광주 사용자는 광주 시세 우선 + 전국 보완.
   정렬: 광주 지역 우선 → 구매적기(저렴) → 평년比 낮은 순. */
export async function getSeasonal(ctx = {}) {
  await delay(120)
  const month = ctx.month || new Date().getMonth() + 1
  const isGwangju = ctx.region === '광주'
  const inMonth = (s) => s.peak_months.includes(month)

  let list
  if (isGwangju) {
    const gj = SEASONAL.filter((s) => s.region === '광주' && inMonth(s))
    const names = new Set(gj.map((s) => s.item))
    const nat = SEASONAL.filter((s) => s.region === '전국' && inMonth(s) && !names.has(s.item))
    list = [...gj, ...nat]
  } else {
    list = SEASONAL.filter((s) => s.region === '전국' && inMonth(s))
  }
  return list
    .map((s) => ({ ...s, month, _regionRank: s.region === '광주' ? 0 : 1 }))
    .sort((a, b) => {
      if (a._regionRank !== b._regionRank) return a._regionRank - b._regionRank
      const lv = (LEVEL_ORDER[a.level] ?? 1) - (LEVEL_ORDER[b.level] ?? 1)
      if (lv !== 0) return lv
      return a.vsAvgPct - b.vsAvgPct
    })
}

export async function getMarkets(loc) {
  await delay(160)
  return loc ? byDistance(MARKETS, originOf(loc)) : MARKETS
}

/* 시세품목이 들어가는 향토음식(메뉴 키워드) — ingredient_map 역방향. */
function dishesForItem(item) {
  const ks = Object.entries(DISH_TO_ITEM).filter(([, v]) => v === item).map(([k]) => k)
  return [...new Set([item, ...ks])].slice(0, 6)
}

/* ── 산지·시세 상세 (실데이터 12개월 추이) ── */
export async function getIngredient(id) {
  await delay(120)
  const s = SEASONAL.find((x) => x.id === id)
  if (!s) return null
  const monthNames = { 1: '1월', 2: '2월', 3: '3월', 4: '4월', 5: '5월', 6: '6월', 7: '7월', 8: '8월', 9: '9월', 10: '10월', 11: '11월', 12: '12월' }
  return {
    id: s.id,
    name: s.item,
    region: s.region,
    unit: s.unit,
    level: s.level,
    season: s.peak_months.map((m) => monthNames[m]).join('·'),
    current: s.current,
    avg: s.avg12,
    vsAvgPct: s.vsAvgPct,
    wowPct: s.wowPct,
    dishes: dishesForItem(s.item),
    trend: s.trend, // [[ 'YYYY-MM', price ], ...]
    forecast: s.forecast ?? null, // [{ym,yhat,lo,hi}] Prophet 6개월 예측 (있는 재료만)
    forecastMape: s.forecastMape ?? null, // 백테스트 오차율(%) — 정확도 표시용
    inSeason: s.peak_months.includes(new Date().getMonth() + 1),
  }
}

/* ── 오늘의 추천 — 현재 위치 근처 향토색 식당 중 매번 랜덤 ──
   새로고침(재호출)할 때마다 '가까운 후보군'에서 무작위로 골라 그때그때 바뀐다. */
export async function getTodayRecommendation(loc = {}) {
  await delay(180)
  const origin = originOf(loc)
  const region = typeof loc === 'string' ? null : loc.region
  const pool = region ? RESTAURANTS.filter((r) => r.region === region) : RESTAURANTS
  const base = pool.length ? pool : RESTAURANTS
  const near = byDistance(base, origin).slice(0, 12) // 사용자와 가장 가까운 12곳
  const local = near.filter((r) => (r.local_score || 0) >= 1) // 그 안에서 향토색 있는 곳 우선
  const cands = local.length >= 4 ? local : near
  const pick = cands[Math.floor(Math.random() * cands.length)] || base[0]
  return { restaurant: pick, allergy: allergyInfo(pick), seasonal: seasonalFor(pick, loc) }
}

export async function search(query, loc) {
  try {
    const res = await fetch('http://localhost:8000/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, region: loc?.region, top_k: 10 }),
    })
    if (!res.ok) throw new Error('backend error')
    const data = await res.json()

    const byId = new Map(RESTAURANTS.map((r) => [String(r.poi_id), r]))
    const hits = data.results.map((item) => byId.get(String(item.restaurant_id))).filter(Boolean)

    return loc ? byDistance(hits, originOf(loc)) : hits
  } catch (e) {
    // 백엔드 실패 시 로컬 검색으로 자동 전환
    await delay(220)
    const hits = searchRestaurants(query, RESTAURANTS)
    return loc ? byDistance(hits, originOf(loc)) : hits
  }
}

export async function chatReply(text, loc = {}) {
  const cityLabel = loc.city || '현재 위치'

  try {
    const params = new URLSearchParams({ q: text, top_n: 4 })
    if (loc?.region) params.set('region', loc.region)
    const res = await fetch(`http://localhost:8001/chat?${params}`)
    if (!res.ok) throw new Error('backend error')
    const data = await res.json()

    if (!data.results.length) {
      return {
        messages: [
          { who: 'bot', text: `아직 ${cityLabel} 근처에서 딱 맞는 곳을 못 찾았어요. 메뉴(예: 꼬막·게장·백반)나 상황(예: 가족·해장)을 함께 말해주시면 더 정확해집니다.` },
        ],
        hits: [],
      }
    }

    const top = data.results[0]
    const bits = enrich(top, loc)
    const messages = [
      { who: 'bot', text: `${cityLabel} 근처 향토음식점으로 이곳을 추천해요.` },
      { who: 'card', restaurant: top },
    ]
    if (bits.length) messages.push({ who: 'bot', text: `👍 ${top.name} — ${bits.join(' · ')}` })
    return { messages, hits: data.results }
  } catch (e) {
    // 백엔드(KoSBERT 의미검색) 실패 시 로컬 토큰매칭 챗봇으로 자동 전환
    await delay(500)
    const { filters, fallback, results } = retrieveLocal(text, loc, 4)

    if (!results.length) {
      return {
        messages: [
          { who: 'bot', text: `아직 ${cityLabel} 근처에서 딱 맞는 곳을 못 찾았어요. 메뉴(예: 꼬막·게장·백반)나 상황(예: 가족·해장)을 함께 말해주시면 더 정확해집니다.` },
        ],
        hits: [],
      }
    }

    const chips = [...filters.ingredients, ...filters.dishType, ...filters.health]
    const cond = chips.length ? `'${chips.slice(0, 3).join(', ')}' ` : ''
    const top = results[0]
    const bits = enrich(top, loc)

    const messages = [
      {
        who: 'bot',
        text: fallback
          ? `${cityLabel} 근처엔 딱 맞는 곳이 적어 조건을 넓혀 골랐어요. 가장 가까운 이곳을 추천해요.`
          : `${cityLabel} 근처 ${cond}향토음식점으로 이곳을 추천해요.`,
      },
      { who: 'card', restaurant: top },
    ]
    if (bits.length) messages.push({ who: 'bot', text: `👍 ${top.name} — ${bits.join(' · ')}` })
    return { messages, hits: results }
  }
}