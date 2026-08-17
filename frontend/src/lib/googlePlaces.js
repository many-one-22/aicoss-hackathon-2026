/* Google Places API (New) 연동 — 가게 이름+주소로 실제 등록 사진을 가져온다.
   .env.local 의 VITE_GOOGLE_PLACES_API_KEY 가 없으면 조용히 null 반환(호출부가 스톡 이미지로 폴백).
   결과는 localStorage에 캐시해서 같은 가게를 재조회하지 않는다. */
const API_KEY = import.meta.env.VITE_GOOGLE_PLACES_API_KEY
const CACHE_KEY = 'namdo:placePhotoCache:v1'

function readCache() {
  try {
    return JSON.parse(localStorage.getItem(CACHE_KEY)) || {}
  } catch {
    return {}
  }
}
function writeCache(cache) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache))
  } catch {
    /* storage 접근 불가 시 무시 */
  }
}

const memo = readCache()

/* 성공하면 실제 사진 URL, 실패/키없음이면 null */
export async function fetchRestaurantPhoto(r) {
  if (!API_KEY || !r) return null
  const key = String(r.id)
  if (key in memo) return memo[key]

  try {
    const res = await fetch('https://places.googleapis.com/v1/places:searchText', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.photos',
      },
      body: JSON.stringify({ textQuery: `${r.name} ${r.addr || ''}`, languageCode: 'ko' }),
    })
    if (!res.ok) throw new Error(`places search failed: ${res.status}`)
    const data = await res.json()
    const photoName = data?.places?.[0]?.photos?.[0]?.name
    const url = photoName
      ? `https://places.googleapis.com/v1/${photoName}/media?maxWidthPx=480&key=${API_KEY}`
      : null
    memo[key] = url
    writeCache(memo)
    return url
  } catch {
    memo[key] = null
    writeCache(memo)
    return null
  }
}
