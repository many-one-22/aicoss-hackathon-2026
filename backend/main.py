"""
main.py

backend/ 평평한 구조로 통일 (app/ 패키지 아님 — 팀 파일도 전부 이 폴더로 이동, import는 flat 방식).

실행:
    pip install fastapi uvicorn
    cd backend
    uvicorn main:app --reload --port 8000

USE_MOCK 스위치로 mock <-> 실데이터 전환.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from schemas import RecommendRequest, RecommendResponse, HealthResponse, RecommendItem, ChatRequest, ChatResponse
from mock_data import mock_recommend
from db import get_connection
from sentiment_lookup import get_trend_tags_only
from price_lookup import get_price_info

# retrieve.py는 minseo/scripts/data_prep에 있음 (backend/로 옮기지 않음 —
# hard_filter.py/tag_region.py/embed_rank.py 같은 폴더에 있어서 옮기면 서로 import 깨짐).
# 대신 backend/ 기준 상대경로로 그 폴더를 찾아서 sys.path에 추가.
_RETRIEVE_DIR = Path(__file__).resolve().parent.parent / "minseo" / "scripts" / "data_prep"
if str(_RETRIEVE_DIR) not in sys.path:
    sys.path.insert(0, str(_RETRIEVE_DIR))

USE_MOCK = False  # 실데이터/실DB 연동 검증 끝나면 False로 전환


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 서버 시작 시 랭커 미리 워밍업 ---
    # 세은님 retrieve.py는 load_index()/load_model() 같은 별도 프리로드 함수가 없고,
    # retrieve() 안의 _get_ranker()가 "첫 호출 때 자동 로드 + 이후 캐시" 방식으로 되어있음.
    # 그래서 첫 실제 요청이 로딩 시간(81MB+400MB)을 떠안지 않도록, 더미 쿼리로 한 번 미리 불러둔다.
    if not USE_MOCK:
        try:
            from retrieve import retrieve as _warmup_retrieve

            print("[정보] 검색 랭커 워밍업 중... (81MB+400MB, 시간 좀 걸릴 수 있음)")
            _warmup_retrieve(query="워밍업", filters={}, top_n=1)
            print("[정보] 워밍업 완료")
        except Exception as e:
            print(f"[경고] 랭커 워밍업 실패 (첫 요청이 느릴 수 있음): {e}")
    yield


app = FastAPI(
    title="남도 식탁 큐레이터 AI API",
    description="향토음식 추천 API",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def live_recommend(req: RecommendRequest) -> dict:
    """seeun님의 retrieve.py(hard_filter + KoSBERT 임베딩 재정렬)를 그대로 사용.

    ⚠️ 확인 필요 (세은님과 맞춰야 함):
        - retrieve()가 반환하는 dict에 'poi_id' 키가 있는지, 아니면 'rowid'만 있는지.
          다르면 restaurant_sentiment 조인이 조용히 실패함 — 아래 _get_restaurant_id()에서
          우선순위를 두고 방어적으로 처리하되, 실제로 뭐가 맞는지는 검증 필요.
        - health 필터: 팀은 빼기로 했는데 retrieve()엔 아직 파라미터가 살아있음.
          여기서는 넘기지 않음 (None 고정) — 세은님 쪽 hard_filter 기본값과 맞는지 확인.
        - situation: retrieve() 내부에서 이미 무시하도록 되어 있어 여기서도 안 넘김.
    """
    from retrieve import retrieve as seeun_retrieve

    filters = {
        "region": req.region,
        "ingredient_pref": req.ingredient,
        "food_type": req.food_type,
        # "health": 팀 결정에 따라 미전달 (세은님 쪽 기본값 확인 필요)
    }

    cands = seeun_retrieve(query=req.context, filters=filters, top_n=req.top_k)
    # print(f"[디버그] query={req.context!r} filters={filters} -> 후보 {len(cands)}건", flush=True)
    # for c in cands[:3]:
    #     print(f"[디버그]   place={c.get('place')!r} poi_id={c.get('poi_id')!r} rowid={c.get('rowid')!r} keys={list(c.keys())}", flush=True)

    fallback_used = False
    message = None
    if not cands and req.region:
        cands = seeun_retrieve(query=req.context, filters={**filters, "region": None}, top_n=req.top_k)
        fallback_used = True
        message = f"'{req.region}'에는 조건에 맞는 향토음식이 없어 지역을 '전체'로 넓혀 재검색했습니다."

    if not cands:
        return {"results": [], "fallback_used": False, "message": "조건에 맞는 향토음식이 없습니다."}

    conn = get_connection()
    try:
        results = []
        for c in cands:
            poi_id = _rowid_to_poi_id(conn, c.get("rowid"))
            trend_tags = get_trend_tags_only(poi_id) if poi_id else []

            badges = []
            if (c.get("local_score") or 0) >= 3:
                badges.append("#향토색")

            results.append(
                RecommendItem(
                    restaurant_id=str(poi_id) if poi_id else f"rowid-{c.get('rowid')}",
                    name=c.get("place", ""),
                    region=c.get("region_group") or "",
                    description=c.get("menu") or "",
                    trend_tags=trend_tags,
                    badges=badges,
                    similarity=None,
                )
            )
        return {"results": results, "fallback_used": fallback_used, "message": message}
    finally:
        conn.close()


def _rowid_to_poi_id(conn, rowid) -> str | None:
    """세은님 hard_filter.py가 poi_id를 안 돌려주고 rowid만 줘서, DB에서 직접 역조회한다.
    rowid는 DB 재빌드 시 바뀔 수 있으니(build_embeddings.py 경고 참고),
    API 응답/감성 조인에는 안정적인 poi_id를 쓰는 게 맞다."""
    row = conn.execute("SELECT poi_id FROM restaurants WHERE rowid = ?", (rowid,)).fetchone()
    return row["poi_id"] if row and row["poi_id"] else None


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "mode": "mock" if USE_MOCK else "live"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    if USE_MOCK:
        return {"answer": f"(mock) '{req.message}'에 대한 답변입니다.", "sources": ["mock-source"]}

    # ⚠️ 아직 연결 불가: 세은님 retrieve.py는 검색+랭킹만 하고 LLM 답변 생성 기능이 없음.
    # RAG 답변 생성(retrieve 결과 + LLM 프롬프트 구성) 코드를 담당자한테 받아야 이 자리를 채울 수 있음.
    raise HTTPException(
        status_code=501,
        detail="RAG 답변 생성 코드 미연결 — retrieve.py는 검색/랭킹만 지원. 답변 생성 함수 확인 필요.",
    )


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