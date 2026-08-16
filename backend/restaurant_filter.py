"""
restaurant_filter.py

지난번 hybrid_recommend.py의 하드필터는 제가 임의로 만든 toy `foods` 테이블(food.db) 기준이었다.
이제 민서님이 진짜 namdo.sqlite 연결 코드(app/db.py, app/*_lookup.py)를 공유해주셨으니,
그 실제 restaurants 테이블 스키마에 맞춰 하드필터를 다시 짠다.

실제 스키마에서 중요한 차이점 (SCHEMA_NOTES.md + 직접 조회 결과):
    - dish_type, ingredient_category: "국물요리|구이|찜"처럼 파이프로 합쳐진 멀티라벨.
      정확일치(=)가 아니라 LIKE '%값%'으로 부분일치 검색해야 함.
    - local_score: INTEGER (0~5).
    - is_chain: INTEGER (0/1).
    - region_group: 7종 (광주 5개구/기타 전남/순천·보성/여수권/나주·영암/담양·곡성/목포·신안), 빈 문자열 24건 존재.
    - parking: restaurants 테이블은 "있음"/"없음" 텍스트 (markets 테이블의 parking_p02/p03는 "Y"/"N"이라 형식 다름 — 주의).

⚠️ 아직 못 푼 문제 (팀 논의 필요):
    - `situation`(가족식사/혼밥/접대/간편한 한 끼) — restaurants 테이블에 대응 컬럼이 전혀 없음.
      데모 시나리오 필터 조건에서 이 항목을 빼거나, 다른 방식(예: 메뉴 텍스트 키워드 추론)으로 대체해야 함.
    - `health_condition`(저칼로리/고단백) — nutrition 테이블은 400개 "표준 메뉴명" 기준이라
      restaurants.menu 텍스트와 직접 매칭이 안 됨. 팀 문서에 이미 "메뉴↔영양 매칭 커버율 44.6%"로
      기록되어 있는 그 문제. 여기서는 필터에서 제외하고, 매칭 성공한 것만 보조 정보로 보여주는 정도로 타협.

사용법 (app/db.py의 get_connection 재사용 가정):
    from app.db import get_connection
    from restaurant_filter import hard_filter

    conn = get_connection()
    candidates = hard_filter(conn, ingredient="해산물", dish_type="회·생물", region_group="여수권")
"""

from typing import Optional


def hard_filter(
    conn,
    ingredient: Optional[str] = None,        # 해산물/육류/채소/발효·젓갈 중 하나 (부분일치)
    dish_type: Optional[str] = None,          # 국물요리/구이/찜/회·생물/한상차림/면 중 하나 (부분일치)
    region_group: Optional[str] = None,       # 7종 region_group 값 중 하나 (완전일치)
    exclude_chain: bool = True,               # is_chain=1 제외 여부
    min_local_score: int = 0,                 # local_score 이 값 이상만
):
    where = []
    params = []

    if ingredient and ingredient != "상관없음":
        where.append("ingredient_category LIKE ?")
        params.append(f"%{ingredient}%")

    if dish_type and dish_type != "전체":
        where.append("dish_type LIKE ?")
        params.append(f"%{dish_type}%")

    if region_group and region_group != "전체":
        where.append("region_group = ?")
        params.append(region_group)

    if exclude_chain:
        where.append("is_chain = 0")

    if min_local_score:
        where.append("local_score >= ?")
        params.append(min_local_score)

    sql = "SELECT * FROM restaurants"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY local_score DESC"

    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def parking_badge(restaurant_row: dict) -> Optional[str]:
    """restaurants.parking은 '있음'/'없음' 텍스트. markets 테이블(parking_p02/p03, 'Y'/'N')과
    형식이 다르니 절대 같은 함수로 처리하지 말 것 — SCHEMA_NOTES.md 참고."""
    if restaurant_row.get("parking") == "있음":
        return "#주차가능"
    return None
