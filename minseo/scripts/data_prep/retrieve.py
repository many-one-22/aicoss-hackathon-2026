# -*- coding: utf-8 -*-
"""백엔드(seeun) 검색 진입점.
retrieve(query, filters) → 랭킹된 식당 리스트. 보강(시세·영양·시장)은 백엔드가 별도 부착.
구조화 filters로 하드필터 → query 있으면 임베딩(KoSBERT) 의미순 재정렬.

filters 키(프론트/백엔드 스키마):
  region(str), ingredient_pref(list|str), food_type(list|str), health(list|str),
  situation(현재 미사용 — 검색조건 없음).
반환: list[dict] (hard_filter 컬럼: rowid, place, address, menu, region_group, ...).
※ 시그니처·필터명·exclude_chain 기본값은 seeun과 최종 확정 필요.
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hard_filter import hard_filter
from tag_region import _TN_GROUP

# 프론트가 "여수권"(권역)으로 주든 "여수"·"여수시"(시군)로 주든 안 깨지게 정규화.
_GROUPS = {"여수권", "순천·보성", "목포·신안", "나주·영암", "담양·곡성", "광주 5개구", "기타 전남"}
_CITY_TO_GROUP = {}
for _city, _grp in _TN_GROUP.items():          # 여수시→여수권
    _CITY_TO_GROUP[_city] = _grp
    _CITY_TO_GROUP[_city.rstrip("시군구")] = _grp  # 여수→여수권
_CITY_TO_GROUP["광주"] = "광주 5개구"


def _norm_region(region):
    """region 값을 DB의 권역 표기로 정규화. 이미 권역이면 그대로, 시군명이면 매핑."""
    if not region:
        return None
    if region in _GROUPS:
        return region
    return _CITY_TO_GROUP.get(region.rstrip("시군구"), region)


_ranker = None


def _get_ranker():
    """EmbedRanker 지연 로드(임베딩 81MB + 모델). 서버 시작 시 1회만 로딩됨."""
    global _ranker
    if _ranker is None:
        from embed_rank import EmbedRanker
        _ranker = EmbedRanker()
    return _ranker


def _as_list(v):
    """단일값·None·빈값을 hard_filter가 기대하는 list|None으로 정규화."""
    if v is None or v == "" or v == []:
        return None
    return v if isinstance(v, list) else [v]


def retrieve(query=None, filters=None, top_n=10, exclude_chain=True):
    """구조화 filters로 후보를 좁히고, query 있으면 의미순 재정렬해 상위 top_n 반환.
    query 없으면 hard_filter 기본순(local_score DESC)."""
    f = filters or {}
    cands = hard_filter(
        region=_norm_region(f.get("region")),
        ingredient=_as_list(f.get("ingredient_pref")),
        dish_type=_as_list(f.get("food_type")),
        health=_as_list(f.get("health")),
        exclude_chain=exclude_chain,
    )
    # situation 은 현재 검색조건으로 쓰지 않음(무시)
    if query:
        order = _get_ranker().rank(query, [c["rowid"] for c in cands], top_n)
        pos = {rid: i for i, rid in enumerate(order)}
        cands = sorted((c for c in cands if c["rowid"] in pos), key=lambda c: pos[c["rowid"]])
    return cands[:top_n]


if __name__ == "__main__":
    out = retrieve(query="담백한 조개 해장국",
                   filters={"region": "여수권", "food_type": ["국물요리"]}, top_n=5)
    print(f"검색 결과 {len(out)}곳:")
    for r in out:
        print(f"  - {r['place']} | {(r['menu'] or '')[:35]}")
