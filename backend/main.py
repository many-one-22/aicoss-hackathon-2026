"""
main.py

backend/ 평평한 구조로 통일 (app/ 패키지 아님 — 팀 파일도 전부 이 폴더로 이동, import는 flat 방식).

실행:
    pip install fastapi uvicorn
    cd backend
    uvicorn main:app --reload --port 8000

USE_MOCK 스위치로 mock <-> 실데이터 전환. (True: mock, False: 실데이터)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import RecommendRequest, RecommendResponse, HealthResponse, RecommendItem
from mock_data import mock_recommend
from db import get_connection
from restaurant_filter import hard_filter, parking_badge
from sentiment_lookup import get_trend_tags_only
from price_lookup import get_price_info

USE_MOCK = False

app = FastAPI(
    title="남도 식탁 큐레이터 AI API",
    description="향토음식 추천 API",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def live_recommend(req: RecommendRequest) -> dict:
    """실제 namdo.sqlite + restaurant_sentiment 테이블 기반 추천.

    ⚠️ 아직 못 채운 부분 (팀 논의 필요 — restaurant_filter.py 상단 주석 참고):
        - situation(가족식사/혼밥/접대 등): restaurants 테이블에 대응 컬럼 없음 → 현재 필터에서 무시
        - health(저칼로리/고단백): menu ↔ nutrition 매칭 커버율 44.6%라 필터링엔 아직 안 씀
        - 소프트랭킹(KoSBERT 유사도)은 아직 없음 → local_score 내림차순으로만 정렬 (규칙 기반 랭킹)
    """
    conn = get_connection()
    try:
        rows = hard_filter(
            conn,
            ingredient=req.ingredient,
            dish_type=req.food_type,
            region_group=req.region,
            exclude_chain=True,
        )

        fallback_used = False
        message = None
        if not rows and req.region not in (None, "전체"):
            rows = hard_filter(conn, ingredient=req.ingredient, dish_type=req.food_type, region_group=None,
                                exclude_chain=True)
            fallback_used = True
            message = f"'{req.region}'에는 조건에 맞는 향토음식이 없어 지역을 '전체'로 넓혀 재검색했습니다."

        if not rows:
            return {"results": [], "fallback_used": False, "message": "조건에 맞는 향토음식이 없습니다."}

        results = []
        for r in rows[: req.top_k]:
            badges = []
            pb = parking_badge(r)
            if pb:
                badges.append(pb)
            if (r.get("local_score") or 0) >= 3:
                badges.append("#향토색")

            trend_tags = get_trend_tags_only(r["poi_id"])

            results.append(
                RecommendItem(
                    restaurant_id=r["poi_id"],
                    name=r["place"],
                    region=r["region_group"] or "",
                    description=r.get("menu") or "",
                    trend_tags=trend_tags,
                    badges=badges,
                    similarity=None,  # KoSBERT 랭킹 붙기 전까지는 None
                )
            )

        return {"results": results, "fallback_used": fallback_used, "message": message}
    finally:
        conn.close()


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "mode": "mock" if USE_MOCK else "live"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend_endpoint(req: RecommendRequest):
    try:
        if USE_MOCK:
            result = mock_recommend(
                ingredient=req.ingredient,
                food_type=req.food_type,
                situation=req.situation,
                health=req.health,
                region=req.region,
                context=req.context,
                top_k=req.top_k,
            )
        else:
            result = live_recommend(req)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"DB 연결 실패: {e}")

    return result
