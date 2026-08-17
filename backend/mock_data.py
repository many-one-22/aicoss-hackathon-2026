"""
mock_data.py

실제 DB가 없을 경우 사용.
"""

import random
from typing import Optional

MOCK_FOODS = [
    {
        "restaurant_id": "mock-001",
        "name": "여수 전복탕 맛집",
        "region": "여수권",
        "food_type": "국물요리",
        "ingredient": "해산물",
        "situation": "가족식사",
        "health": "제한없음",
        "description": "싱싱한 전복으로 끓인 진한 전복탕. 가족 식사로 인기 많은 여수 향토음식.",
        "trend_tags": ["신선도 호평 다수", "가격 호평"],
        "badges": ["#제철", "#향토색", "#주차가능"],
    },
    {
        "restaurant_id": "mock-002",
        "name": "순천 콩나물국밥",
        "region": "순천권",
        "food_type": "국물요리",
        "ingredient": "채소",
        "situation": "혼밥",
        "health": "저칼로리",
        "description": "얼큰하고 시원한 순천식 콩나물국밥. 혼자 가볍게 먹기 좋은 저칼로리 메뉴.",
        "trend_tags": ["가격 호평 다수"],
        "badges": ["#향토색"],
    },
    {
        "restaurant_id": "mock-003",
        "name": "광주 양동시장 한정식",
        "region": "광주",
        "food_type": "밥류",
        "ingredient": "육류",
        "situation": "접대",
        "health": "제한없음",
        "description": "정갈한 반찬이 함께 나오는 한정식. 접대 자리에 어울리는 광주 대표 향토음식.",
        "trend_tags": ["맛 호평 다수", "재방문의사 높음"],
        "badges": ["#향토색", "#주차가능"],
    },
    {
        "restaurant_id": "mock-004",
        "name": "목포 홍어삼합집",
        "region": "목포권",
        "food_type": "회·날것",
        "ingredient": "해산물",
        "situation": "접대",
        "health": "제한없음",
        "description": "삭힌 홍어와 삶은 돼지고기, 묵은지를 함께 내는 목포 대표 향토음식.",
        "trend_tags": ["호불호 뚜렷"],
        "badges": ["#향토색"],
    },
]


def mock_recommend(
    ingredient: Optional[str],
    food_type: Optional[str],
    situation: Optional[str],
    health: Optional[str],
    region: Optional[str],
    context: Optional[str],
    top_k: int,
):
    """hybrid_recommend.recommend()와 동일한 반환 형태(dict)를 흉내내는 목 함수.
    실제 SQL 필터링/임베딩 랭킹 없이, 조건에 맞는 것만 골라 유사도 대신 랜덤 점수를 붙인다."""

    def matches(food, region_filter):
        if ingredient and ingredient not in ("상관없음",) and food["ingredient"] != ingredient:
            return False
        if food_type and food_type not in ("전체",) and food["food_type"] != food_type:
            return False
        if situation and food["situation"] != situation:
            return False
        if health and health not in ("제한없음",) and food["health"] != health:
            return False
        if region_filter and region_filter not in ("전체",) and food["region"] != region_filter:
            return False
        return True

    candidates = [f for f in MOCK_FOODS if matches(f, region)]
    fallback_used = False
    message = None

    if not candidates and region not in (None, "전체"):
        # 실패 대응: 지역 조건을 '전체'로 완화해서 재검색 (다른 조건은 그대로 유지)
        candidates = [f for f in MOCK_FOODS if matches(f, "전체")]
        fallback_used = True
        message = f"'{region}'에는 조건에 맞는 향토음식이 없어 지역을 '전체'로 넓혀 재검색했습니다. (mock)"

    if not candidates:
        return {"results": [], "fallback_used": False, "message": "조건에 맞는 향토음식이 없습니다. (mock)"}

    random.seed(hash(context) if context else 0)
    results = []
    for f in candidates[:top_k]:
        results.append(
            {
                "restaurant_id": f["restaurant_id"],
                "name": f["name"],
                "region": f["region"],
                "description": f["description"],
                "trend_tags": f["trend_tags"],
                "badges": f["badges"],
                "similarity": round(random.uniform(0.6, 0.95), 3) if context else None,
            }
        )
    if context:
        results.sort(key=lambda r: r["similarity"], reverse=True)

    return {"results": results, "fallback_used": fallback_used, "message": message}
