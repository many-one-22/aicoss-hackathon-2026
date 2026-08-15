/* 제철 특산물 (KAMIS 시세 연동 가정). delta = 평년 대비 %(음수=저렴/구매적기) */
export const SEASONAL = [
  { id: 'jeonbok', name: '완도 전복', short: '전복', origin: '완도', season: '가을~겨울 성수기', delta: -8, flag: '구매 적기' },
  { id: 'gul', name: '고흥·여수 굴', short: '굴', origin: '고흥·여수', season: '11~2월', delta: -5 },
  { id: 'galchi', name: '여수 갈치', short: '갈치', origin: '여수', season: '가을~겨울', delta: 6 },
  { id: 'mulojingeo', name: '여수 물오징어', short: '오징어', origin: '여수', season: '가을철', delta: 0 },
]
