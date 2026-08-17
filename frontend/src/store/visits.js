/* 방문 기록 — 식당 상세를 열면 자동 저장(localStorage). 최근 30곳 유지.
   추천(오늘의 추천·찜 취향)에서 '다녀간 곳'의 음식유형·태그를 취향 신호로 쓴다.
   저장 필드는 추천 계산(favoriteProfile)이 쓰는 tags·key·city 만으로 충분. */
const KEY = 'namdo:visits'
const MAX = 30

export function getVisits() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || '[]')
  } catch {
    return []
  }
}

export function recordVisit(r) {
  if (!r || r.id == null) return
  const rec = {
    id: r.id,
    name: r.name,
    tags: r.tags || [],
    key: r.key,
    city: r.city,
    region_group: r.region_group,
    ts: Date.now(),
  }
  // 같은 곳은 앞으로 당김(최근 방문 우선), 최근 MAX개만 보관
  const list = [rec, ...getVisits().filter((v) => v.id !== r.id)].slice(0, MAX)
  localStorage.setItem(KEY, JSON.stringify(list))
}

export function clearVisits() {
  localStorage.removeItem(KEY)
}
