/* 실데이터 — namdo.sqlite restaurants 테이블에서 권역별(좌표 보유·비체인 우선) 추출.
   추출 스크립트: (repo)/scripts 참고. 필드: id, poi_id, name, region, city, region_group,
   key(대표 dish_type), tags[], addr, tel, desc(메뉴), lat, lng, parking, local_score */
import RESTAURANTS_REAL from './restaurants.real.json'

export const RESTAURANTS = RESTAURANTS_REAL
