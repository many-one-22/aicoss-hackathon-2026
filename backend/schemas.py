"""
schemas.py

/recommend API 계약(request/response 스키마).
8/13 뼈대 단계에서 이 스키마를 팀 전체(민서/다원/프론트)가 합의하고 고정하는 게 목표.
8/14~16에 mock -> 실데이터로 내용이 바뀌어도, 이 스키마 형태 자체는 최대한 안 바뀌게 유지할 것.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    # 1차 하드필터 조건 (전부 optional — 안 주면 필터 없이 전체 대상)
    ingredient: Optional[str] = Field(None, description="해산물/육류/채소/상관없음")
    food_type: Optional[str] = Field(None, description="국물요리/구이/회·생물/한상차림/면/찜 (namdo.sqlite dish_type 실제 값 기준)")
    situation: Optional[str] = Field(None, description="가족식사/혼밥/접대/간편한 한 끼 (⚠️ DB에 대응 컬럼 없음, 현재 미사용)")
    health: Optional[str] = Field(None, description="저칼로리/고단백/제한없음 (⚠️ 팀 결정으로 현재 필터에서 제외)")
    region: Optional[str] = Field(None, description="광주 5개구/기타 전남/순천·보성/여수권/나주·영암/담양·곡성/목포·신안/전체")

    # 2차 소프트랭킹용 자유 텍스트 (없으면 랭킹 스킵, 하드필터 순서 그대로 반환)
    context: Optional[str] = Field(None, description="자유 텍스트 맥락, 예: '아이랑 갈만한 신선한 회 맛집'")

    top_k: int = Field(3, ge=1, le=10)

    class Config:
        json_schema_extra = {
            "example": {
                "ingredient": "해산물",
                "food_type": "회·생물",
                "situation": "가족식사",
                "health": "제한없음",
                "region": "여수권",
                "context": "아이랑 같이 갈만한 신선한 회 맛집",
                "top_k": 3,
            }
        }


class RecommendItem(BaseModel):
    restaurant_id: str
    name: str
    region: str
    description: str
    trend_tags: List[str] = []
    badges: List[str] = []  # 예: ["#제철", "#향토색", "#주차가능", "#아이동반"]
    similarity: Optional[float] = None  # 소프트랭킹 안 했으면 None


class RecommendResponse(BaseModel):
    results: List[RecommendItem]
    fallback_used: bool = False
    message: Optional[str] = None  # 예: "'광주'에는 조건에 맞는 향토음식이 없어 지역을 '전체'로 넓혀 재검색했습니다."


class HealthResponse(BaseModel):
    status: str
    mode: str  # "mock" | "live"


class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자가 입력한 자유 텍스트 질문")
    session_id: Optional[str] = Field(None, description="대화 맥락 유지용 (선택)")


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list, description="근거로 참조한 문서/식당 등 (근거 표기용)")


class SearchRequest(BaseModel):
    query: str = Field(..., description="자유 텍스트 검색어")
    region: Optional[str] = Field(None, description="선택. 광주 5개구/기타 전남/순천·보성/여수권/나주·영암/담양·곡성/목포·신안/전체")
    top_k: int = Field(10, ge=1, le=20)