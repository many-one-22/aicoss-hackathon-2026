/* 전통시장 (전국 전통시장 표준데이터 가정). category = 필터 칩 매칭용 */
export const MARKETS = [
  { id: 'beolgyo', name: '벌교전통시장', city: '보성군', addr: '전남 보성군 벌교읍', stores: 120, parking: '무료', onnuri: true, marketDays: '4·9일', items: ['꼬막', '수산물', '농산물', '건어물', '반찬'], tag: '꼬막 제철', note: '상설 + 4·9일 장날', category: '전통시장', lat: 34.83, lng: 127.34 },
  { id: 'dolsan', name: '여수돌산전통시장', city: '여수시', addr: '전남 여수시 돌산읍', stores: 86, parking: '가능', onnuri: true, marketDays: '3·8일', items: ['돌산갓', '수산물', '반찬'], tag: '돌산갓 제철', note: '점포 86 · 장날 3·8일', category: '전통시장', lat: 34.72, lng: 127.75 },
  { id: 'suncheon', name: '순천아랫장', city: '순천시', addr: '전남 순천시', stores: 210, parking: '가능', onnuri: true, marketDays: '2·7일', items: ['농산물', '수산물', '반찬', '건어물'], note: '점포 210 · 주차 가능', category: '전통시장', lat: 34.95, lng: 127.49 },
  { id: 'yeosususan', name: '여수수산시장', city: '여수시', addr: '전남 여수시 교동', stores: 86, parking: '가능', onnuri: false, marketDays: '상설', items: ['수산물', '건어물', '활어'], tag: '활어·제철 산지', note: '점포 86 · 상설', category: '제철 산지', lat: 34.74, lng: 127.74 },
  { id: 'wando', name: '완도종합시장', city: '완도군', addr: '전남 완도군 완도읍', stores: 140, parking: '가능', onnuri: true, marketDays: '5·10일', items: ['전복', '해조류', '건어물', '수산물'], tag: '전복 산지', note: '5·10일 장날', category: '제철 산지', lat: 34.31, lng: 126.75 },
]
