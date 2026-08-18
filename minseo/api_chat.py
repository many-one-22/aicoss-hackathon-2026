# -*- coding: utf-8 -*-
from __future__ import annotations
"""KoSBERT 의미검색 챗봇 백엔드 엔드포인트 (민서).
자연어 질의 → retrieve()(하드필터 + KoSBERT 임베딩) → 식당 결과(JSON).
프론트 챗봇이 이걸 호출하면 토큰매칭 대신 '진짜 의미검색'이 된다.
(예: '전복요리' → 장어집이 아니라 진짜 전복 전문점)
- 전체 27,573개 식당을 검색(프론트 번들 3,500개 한계 없음 — 백엔드가 다 가짐).
- 서버 시작 후 첫 질의 때 임베딩(81MB)+KoSBERT 모델 1회 로드(수 초).
- seeun 백엔드(FastAPI)에 이 로직을 통합 예정. CORS 열려 있어 프론트가 바로 호출 가능.
- 응답은 프론트 restaurants.real.json 과 동일한 카드 객체(전체정보) → 프론트가 번들에
  없는 식당도 이 정보만으로 카드·상세를 바로 렌더(id로 재조회 안 함).

[수정 이력] DB 경로를 minseo/ 자기 자신 기준이 아니라 레포 루트 data/processed/ 기준으로 통일.
(레포 루트 namdo.sqlite가 팀 공식 기준 — build_embeddings.py/hard_filter.py와 반드시 같은
파일을 봐야 rowid가 안 어긋남. minseo/의 옛날 사본은 삭제됨.)

실행:
    pip install fastapi uvicorn
    cd minseo
    uvicorn api_chat:app --port 8001
    # 확인: http://localhost:8001/chat?q=전복요리&region=광주
"""
import sqlite3
import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

HERE = Path(__file__).resolve().parent  # minseo/
sys.path.insert(0, str(HERE / "scripts" / "data_prep"))
from retrieve import retrieve

# minseo/의 한 단계 위 = 레포 루트
DB = HERE.parent / "data" / "processed" / "namdo.sqlite"

# 검색어 안에서 의미를 흐리는 흔한 단어들. 이런 단어가 붙으면 임베딩이 핵심 명사(예: "전복")보다
# "일반적인 음식/요리"라는 방향으로 쏠려서 변별력이 떨어짐 — 문장 임베딩 모델의 알려진 특성.
# 검색 전에 미리 제거해서 핵심 단어에 신호를 집중시킨다.
_FILLER_WORDS = [
    "요리", "음식점", "음식", "맛집", "맛있는 곳", "맛있는곳",
    "먹고 싶어", "먹고싶어", "먹고 싶은", "먹고싶은",
    "추천해줘", "추천해주세요", "추천", "알려줘", "알려주세요",
    "해줘", "찾아줘", "좋은 곳", "좋은곳", "괜찮은 곳", "괜찮은곳",
    "먹을 만한", "먹을만한", "곳",
]


# "A 말고 B", "A 대신 B" 같은 대조 표현. KoSBERT는 문장 임베딩 특성상 이런 부정/대조 표현을
# 잘 구분 못 해서, "감자 말고 전복"처럼 두 명사가 점수상 박빙이 되면 컴퓨터/실행마다
# 미세한 부동소수점 차이로 순위가 뒤집히는 불안정한 상황이 생길 수 있다(실제로 재현됨).
# 검색어 자체에서 부정된 앞부분(A)을 아예 잘라내, 뒷부분(B)만 KoSBERT에 넘겨서 이 문제를 없앤다.
_CONTRASTIVE_WORDS = ["말고", "대신"]


def _clean_query(q: str) -> str:
    """대조 표현 처리 + 필러 단어 제거.
    다 지워서 빈 문자열이 되면 원본 그대로 반환 (안전장치)."""
    cleaned = q

    # 1) "A 말고 B" / "A 대신 B" → A는 버리고 B만 남긴다
    for w in _CONTRASTIVE_WORDS:
        idx = cleaned.find(w)
        if idx != -1:
            cleaned = cleaned[idx + len(w):]
            break  # 여러 개 겹치는 경우는 드물어서 첫 번째만 처리

    # 2) 필러 단어 제거
    for w in _FILLER_WORDS:
        cleaned = cleaned.replace(w, " ")
    cleaned = " ".join(cleaned.split())
    return cleaned if cleaned else q

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


@app.get("/health")
def health():
    return {"status": "ok", "db": str(DB), "db_exists": DB.exists()}


@app.get("/chat")
def chat(q: str, region: Optional[str] = None, top_n: int = 4):
    """자연어 q(+선택 region) → KoSBERT 의미검색 상위 top_n 식당(카드 전체정보)."""
    cleaned_q = _clean_query(q)
    res = retrieve(query=cleaned_q, filters={"region": region} if region else None, top_n=top_n)
    poi = _poi_map([r["rowid"] for r in res])
    return {
        "query": q,
        "cleaned_query": cleaned_q,
        "engine": "KoSBERT",
        "results": [_card(r, poi.get(r["rowid"])) for r in res],
    }