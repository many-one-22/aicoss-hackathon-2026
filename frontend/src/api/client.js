/* Mock API 클라이언트
   ─ 모든 화면은 이 모듈만 호출한다. 백엔드가 준비되면 각 함수 내부를
     fetch('/api/...') 로 바꾸기만 하면 UI 변경 없이 실 API 연동이 된다.
   ─ 지금은 src/data 의 로컬 데이터를 Promise 로 감싸 async 흐름을 흉내낸다. */
import { RESTAURANTS } from '../data/restaurants.js'
import { SEASONAL } from '../data/seasonal.js'
import { MARKETS } from '../data/markets.js'
import { INGREDIENTS } from '../data/ingredients.js'
import { allergyInfo, seasonalFor, searchRestaurants } from '../lib/derive.js'

const delay = (ms = 220) => new Promise((res) => setTimeout(res, ms))

export async function getRestaurants() {
  await delay()
  return RESTAURANTS
}

export async function getRestaurant(id) {
  await delay(120)
  return RESTAURANTS.find((r) => r.id === Number(id)) || null
}

export async function getSeasonal() {
  await delay(120)
  return SEASONAL
}

export async function getMarkets() {
  await delay(160)
  return MARKETS
}

export async function getIngredient(id) {
  await delay(120)
  return INGREDIENTS[id] || INGREDIENTS.jeonbok
}

/* 위치 자동 감지 — 실제로는 브라우저 Geolocation + 역지오코딩.
   데모에서는 권한 여부와 무관하게 광역 도시명을 반환한다. */
export async function detectLocation() {
  const fallback = { city: '여수시', label: '여수시 · 자동감지' }
  if (!('geolocation' in navigator)) return fallback
  try {
    await new Promise((resolve, reject) =>
      navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 2500, maximumAge: 600000 }),
    )
    // 좌표→도시 역지오코딩 API 자리(추후 연동). 지금은 데모 도시 유지.
    return fallback
  } catch {
    return fallback
  }
}

/* 오늘의 추천 — 위치/기록 기반. 데모에서는 위치 도시의 대표 식당(전복 우선) */
export async function getTodayRecommendation(city = '여수시') {
  await delay(180)
  const pool = RESTAURANTS.filter((r) => r.city === city)
  const base = pool.length ? pool : RESTAURANTS
  const pick = base.find((r) => /전복/.test(`${r.tags.join('')}${r.key}`)) || base[0]
  return { restaurant: pick, allergy: allergyInfo(pick), seasonal: seasonalFor(pick) }
}

export async function search(query) {
  await delay(240)
  return searchRestaurants(query, RESTAURANTS)
}

/* 챗봇 응답 (RAG 흉내) — 질의에서 지역/메뉴 토큰을 뽑아 매칭 식당 카드를 반환 */
export async function chatReply(text, city = '여수시') {
  await delay(650)
  const hits = searchRestaurants(text, RESTAURANTS)
  if (hits.length) {
    const r = hits[0]
    return {
      messages: [
        { who: 'bot', text: `${r.city}에서 조건에 맞는 곳으로 ${hits.length}곳을 찾았어요. 대표로 한 곳 보여드릴게요.` },
        { who: 'card', restaurant: r },
        ...(hits.length > 1 ? [{ who: 'bot', text: '“비슷한 3곳”을 눌러 맞춤 추천으로 이어갈 수 있어요.' }] : []),
      ],
      hits,
    }
  }
  return {
    messages: [
      { who: 'bot', text: '아직 딱 맞는 향토음식점을 못 찾았어요. 지역(예: 여수·보성)이나 메뉴(예: 꼬막·게장)를 함께 말해주시면 더 정확해집니다.' },
    ],
    hits: [],
  }
}
