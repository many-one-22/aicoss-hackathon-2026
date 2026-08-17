# -*- coding: utf-8 -*-
"""KoSBERT 의미검색 챗봇 백엔드 엔드포인트 (민서).
자연어 질의 → retrieve()(하드필터 + KoSBERT 임베딩) → 식당 결과(JSON).
프론트 챗봇이 이걸 호출하면 토큰매칭 대신 '진짜 의미검색'이 된다.
(예: '전복요리' → 장어집이 아니라 진짜 전복 전문점)

- 전체 27,573개 식당을 검색(프론트 번들 3,500개 한계 없음 — 백엔드가 다 가짐).
- 서버 시작 후 첫 질의 때 임베딩(81MB)+KoSBERT 모델 1회 로드(수 초).
- seeun 백엔드(FastAPI)에 이 로직을 통합 예정. CORS 열려 있어 프론트가 바로 호출 가능.
- 응답은 프론트 restaurants.real.json 과 동일한 카드 객체(전체정보) → 프론트가 번들에
  없는 식당도 이 정보만으로 카드·상세를 바로 렌더(id로 재조회 안 함).

실행:
    pip install fastapi uvicorn
    cd minseo
    uvicorn api_chat:app --port 8001
    # 확인: http://localhost:8001/chat?q=전복요리&region=광주
"""
import sqlite3
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts" / "data_prep"))
from retrieve import retrieve

DB = HERE / "data" / "processed" / "namdo.sqlite"

app = FastAPI(title="남도식탁 KoSBERT 챗봇")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _poi_map(rowids):
    """rowid → poi_id (식당 고유키)."""
    if not rowids:
        return {}
    con = sqlite3.connect(DB)
    q = f"SELECT rowid, poi_id FROM restaurants WHERE rowid IN ({','.join('?' * len(rowids))})"
    m = {row[0]: row[1] for row in con.execute(q, rowids)}
    con.close()
    return m


def _to_float(v):
    """DB의 문자열 좌표('' 포함) → float | None."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _card(r, poi_id):
    """retrieve 결과 1건 → 프론트 restaurants.real.json 과 동일한 카드 객체.
    프론트가 번들에 없는 식당도 이 정보만으로 카드·상세를 렌더할 수 있다."""
    toks = (r["address"] or "").split()
    tags = [t for t in (r["ingredient_category"] or "").split("|") if t and t != "미분류"]
    dts = [t for t in (r["dish_type"] or "").split("|") if t and t != "미분류"]
    for t in dts:                       # 태그 = 식재료 + 음식유형(중복 제외)
        if t not in tags:
            tags.append(t)
    return {
        "id": poi_id,                   # 백엔드 결과 고유키(프론트 정수 id와 충돌 안 나게 poi_id 사용)
        "poi_id": poi_id,
        "name": r["place"],
        "region": "광주" if r["region_group"] == "광주 5개구" else "전남",
        "city": toks[1] if len(toks) >= 2 else "",
        "region_group": r["region_group"],
        "key": dts[0] if dts else (r["cuisine_type"] or "한식"),
        "tags": tags,
        "addr": r["address"],
        "tel": r["phone"],
        "desc": r["menu"],
        "lat": _to_float(r["lat"]),
        "lng": _to_float(r["lng"]),
        "parking": r["parking"] == "있음",
        "local_score": r["local_score"],
    }


@app.get("/chat")
def chat(q: str, region: str | None = None, top_n: int = 4):
    """자연어 q(+선택 region) → KoSBERT 의미검색 상위 top_n 식당(카드 전체정보)."""
    res = retrieve(query=q, filters={"region": region} if region else None, top_n=top_n)
    poi = _poi_map([r["rowid"] for r in res])
    return {
        "query": q,
        "engine": "KoSBERT",
        "results": [_card(r, poi.get(r["rowid"])) for r in res],
    }
