# -*- coding: utf-8 -*-
"""백엔드 검색 진입점.
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


# 부정어 처리 — "전복 싫은데"처럼 재료 뒤에 부정어가 오면 그 재료를 결과에서 뺀다.
# (KoSBERT 임베딩은 부정을 못 잡아 오히려 '전복'을 상위로 올리므로 명시적으로 제외한다.)
_NEG_CUES = ("싫", "말고", "빼고", "제외", "별로", "아니", "못 먹", "못먹")
_EXCLUDABLE = (
    "전복", "꼬막", "조개", "굴", "홍합", "바지락", "소라", "골뱅이", "새우", "꽃게", "게장",
    "낙지", "오징어", "문어", "주꾸미", "장어", "갈치", "고등어", "홍어", "매생이",
    "삼겹", "돼지", "오리", "한우", "회",
)


def _parse_exclude(query):
    """query에서 '재료 뒤 부정어'(전복 싫은데) 패턴을 찾아 제외할 재료 리스트를 반환."""
    if not query:
        return []
    neg_pos = [query.find(c) for c in _NEG_CUES if c in query]
    if not neg_pos:
        return []
    return [ing for ing in _EXCLUDABLE
            if query.find(ing) >= 0 and any(np > query.find(ing) for np in neg_pos)]


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
    # 사용자가 싫다고 한 재료가 든 곳은 제외한다("전복 싫은데" → 전복집 제외)
    exclude = _parse_exclude(query)
    if exclude:
        cands = [c for c in cands
                 if not any(ing in ((c.get("menu") or "") + (c.get("place") or "")) for ing in exclude)]
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
