/* 지역 좌표 테이블 — 위치 자동감지(역지오코딩 대체)와 제철 '지역순 정렬'에 공용 사용.
   API 키 없이 오프라인으로 GPS 좌표를 앱이 다루는 광주·전남 도시로 매핑한다.
   name  = 화면 표기명, region = 권역('광주'|'전남'),
   matchCity = restaurants/markets 데이터의 city 값(표기명과 다를 수 있음). */
export const CITIES = [
  { name: '광주', region: '광주', lat: 35.16, lng: 126.85, matchCity: '광주' },
  { name: '여수시', region: '전남', lat: 34.76, lng: 127.66, matchCity: '여수시' },
  { name: '순천시', region: '전남', lat: 34.95, lng: 127.49, matchCity: '순천시' },
  { name: '보성군', region: '전남', lat: 34.77, lng: 127.08, matchCity: '보성군' },
  { name: '목포시', region: '전남', lat: 34.81, lng: 126.39, matchCity: '목포시' },
  { name: '나주시', region: '전남', lat: 35.02, lng: 126.71, matchCity: '나주시' },
  { name: '광양시', region: '전남', lat: 34.94, lng: 127.70, matchCity: '광양시' },
  { name: '담양군', region: '전남', lat: 35.32, lng: 126.99, matchCity: '담양군' },
  { name: '강진군', region: '전남', lat: 34.64, lng: 126.77, matchCity: '강진군' },
  { name: '진도군', region: '전남', lat: 34.49, lng: 126.26, matchCity: '진도군' },
  { name: '완도군', region: '전남', lat: 34.31, lng: 126.75, matchCity: '완도군' },
  { name: '장흥군', region: '전남', lat: 34.68, lng: 126.91, matchCity: '장흥군' },
  { name: '영광군', region: '전남', lat: 35.28, lng: 126.51, matchCity: '영광군' },
  { name: '고흥군', region: '전남', lat: 34.61, lng: 127.28, matchCity: '고흥군' },
  { name: '무안군', region: '전남', lat: 34.99, lng: 126.48, matchCity: '무안군' },
  { name: '신안군', region: '전남', lat: 34.83, lng: 126.11, matchCity: '신안군' },
  { name: '해남군', region: '전남', lat: 34.57, lng: 126.60, matchCity: '해남군' },
  { name: '영암군', region: '전남', lat: 34.80, lng: 126.70, matchCity: '영암군' },
  { name: '곡성군', region: '전남', lat: 35.28, lng: 127.29, matchCity: '곡성군' },
  { name: '화순군', region: '전남', lat: 35.06, lng: 126.99, matchCity: '화순군' },
  { name: '함평군', region: '전남', lat: 35.07, lng: 126.52, matchCity: '함평군' },
]

/* 두 좌표 간 근사 거리(km) — 이 지역 스케일에선 등거리 근사로 충분. */
export function distanceKm(a, b) {
  const R = 6371
  const dLat = ((b.lat - a.lat) * Math.PI) / 180
  const meanLat = (((a.lat + b.lat) / 2) * Math.PI) / 180
  const dLng = (((b.lng - a.lng) * Math.PI) / 180) * Math.cos(meanLat)
  return R * Math.sqrt(dLat * dLat + dLng * dLng)
}

/* GPS 좌표 → 가장 가까운 등록 도시. */
export function nearestCity(lat, lng) {
  let best = CITIES[0]
  let bestD = Infinity
  for (const c of CITIES) {
    const d = distanceKm({ lat, lng }, c)
    if (d < bestD) { bestD = d; best = c }
  }
  return best
}

export function cityByName(name) {
  return CITIES.find((c) => c.name === name || c.matchCity === name) || null
}
