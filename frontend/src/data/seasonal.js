/* 실데이터 — namdo.sqlite seasonality 테이블(광주 14 + 전국 92).
   필드: id, item, region('광주'|'전국'), unit, current, avg12, level('저렴'|'평균'|'비쌈'),
   vsAvgPct(현재가 vs 12개월 평균 %), wowPct(전월 대비 %), peak_months[], trend[[ym,price]...]
   모든 값은 KAMIS 실측 기반(합성값 아님). */
import SEASONAL_REAL from './seasonal.real.json'
import INGREDIENT_MAP from './ingredient_map.real.json'

export const SEASONAL = SEASONAL_REAL
export const DISH_TO_ITEM = INGREDIENT_MAP // 메뉴 키워드 → 시세품목명
