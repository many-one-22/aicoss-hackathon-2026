/* 식재료 산지·시세 상세 (화면 ⑤). series = 최근 시세 추이(원/kg)
   기간 탭(4주/3개월/1년)별 시리즈와 요약값을 함께 제공 → 탭 전환 시 dynamic 렌더 */
export const INGREDIENTS = {
  jeonbok: {
    id: 'jeonbok', name: '전복', origin: '완도군', season: '사계절(가을~겨울 성수기)',
    buyNow: true,
    dishes: ['전복죽', '전복회', '전복찜', '전복버터구이'],
    markets: ['완도종합시장', '여수수산시장'],
    ranges: {
      '4주': { current: 32400, avg: 35200, wowPct: -2, vsAvgPct: -8, series: [35600, 34800, 34100, 33600, 33000, 32700, 32400] },
      '3개월': { current: 32400, avg: 35800, wowPct: -1, vsAvgPct: -9, series: [38200, 37400, 36600, 35200, 34100, 33200, 32400] },
      '1년': { current: 32400, avg: 34600, wowPct: 0, vsAvgPct: -6, series: [30100, 31200, 33400, 36800, 38200, 35200, 32400] },
    },
  },
  gul: {
    id: 'gul', name: '굴', origin: '고흥·여수', season: '11~2월',
    buyNow: true,
    dishes: ['굴국밥', '굴전', '석화구이', '굴무침'],
    markets: ['여수수산시장', '고흥시장'],
    ranges: {
      '4주': { current: 9800, avg: 10300, wowPct: -3, vsAvgPct: -5, series: [10600, 10400, 10200, 10000, 9900, 9850, 9800] },
      '3개월': { current: 9800, avg: 11200, wowPct: -2, vsAvgPct: -12, series: [12800, 12200, 11400, 10800, 10200, 9900, 9800] },
      '1년': { current: 9800, avg: 10600, wowPct: 1, vsAvgPct: -8, series: [8600, 9200, 10400, 12800, 11400, 10200, 9800] },
    },
  },
  galchi: {
    id: 'galchi', name: '갈치', origin: '여수', season: '가을~겨울',
    buyNow: false,
    dishes: ['갈치조림', '갈치구이', '갈치회'],
    markets: ['여수수산시장', '여수돌산전통시장'],
    ranges: {
      '4주': { current: 28600, avg: 27000, wowPct: 3, vsAvgPct: 6, series: [26800, 27200, 27600, 28000, 28300, 28500, 28600] },
      '3개월': { current: 28600, avg: 26200, wowPct: 2, vsAvgPct: 9, series: [24200, 24800, 25600, 26200, 27200, 28000, 28600] },
      '1년': { current: 28600, avg: 26800, wowPct: 1, vsAvgPct: 7, series: [22400, 24600, 26800, 25200, 27000, 27800, 28600] },
    },
  },
  mulojingeo: {
    id: 'mulojingeo', name: '물오징어', origin: '여수', season: '가을철',
    buyNow: false,
    dishes: ['오징어물회', '오징어볶음', '오징어숙회'],
    markets: ['여수수산시장'],
    ranges: {
      '4주': { current: 6400, avg: 6300, wowPct: 0, vsAvgPct: 2, series: [6300, 6350, 6400, 6380, 6420, 6400, 6400] },
      '3개월': { current: 6400, avg: 6100, wowPct: 1, vsAvgPct: 5, series: [5800, 5900, 6000, 6100, 6250, 6350, 6400] },
      '1년': { current: 6400, avg: 6200, wowPct: 0, vsAvgPct: 3, series: [5600, 5900, 6400, 6800, 6200, 6300, 6400] },
    },
  },
}
