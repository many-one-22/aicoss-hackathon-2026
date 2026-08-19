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
    return _CITY_TO_GROUP.get(region.rstrip("시군구"))  # 못 찾으면(광역 '전남' 등) None → 전체에서 거리순


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
_NEG_CUES = ("싫", "말고", "빼고", "빼줘", "빼주", "빼서", "뺀", "없이",
             "제외", "별로", "아니", "못 먹", "못먹", "알레르기", "알러지",
             "대신", "보다는", "극혐", "꺼려", "기피", "안 좋아", "안좋아", "안돼", "안 돼")

# 구체적인 재료명(메뉴 텍스트에 실제로 등장하는 단어들) — menu+place 문자열에서 직접 찾아 제외.
_EXCLUDABLE = (
    "전복", "꼬막", "조개", "굴", "홍합", "바지락", "소라", "골뱅이", "새우", "꽃게", "게장",
    "낙지", "오징어", "문어", "주꾸미", "장어", "갈치", "고등어", "홍어", "매생이",
    "삼겹", "돼지", "오리", "한우", "회",
    "감자", "고구마", "두부", "버섯", "가지", "호박",  # 해산물·육류 외 일반 재료 (예: "감자 말고 전복")
)

# 카테고리 단어("해산물"/"육류"/"채소") — 메뉴 텍스트엔 이 단어 자체가 거의 안 나와서
# (예: 메뉴에 "해산물"이라 안 쓰고 "전복죽"이라고 씀) _EXCLUDABLE 방식(문자열 포함 검색)으론
# 못 걸러진다. ingredient_category 필드(DB에 미리 분류되어 있는 컬럼)로 따로 걸러야 함.
_CATEGORY_EXCLUDABLE = ("해산물", "육류", "채소")

# 정식 카테고리명 대신 흔히 쓰는 구어체 → 카테고리 매핑.
_CATEGORY_SYNONYMS = {"고기": "육류", "생선": "해산물", "야채": "채소", "나물": "채소"}

# 한 글자지만 의미 있는 음식 키워드(탕·국 등) — lex 매칭에서 살린다(짧은 단어 보정).
_FOOD1CHAR = ("탕", "국", "회", "면", "죽", "찜")


def _parse_exclude(query):
    """query에서 '재료 뒤 부정어'(전복 싫은데) 패턴을 찾아 제외할 재료 리스트를 반환.
    (item, category) 두 리스트로 나눠 반환 — 필터링 방식이 서로 다르기 때문.

    카테고리 판정에 쓰인 단어(해산물 자체 또는 "생선" 같은 동의어)는 item_exclude에도
    같이 넣는다 — ingredient_category 태그가 불완전한 식당(약 47.7% 미분류)도
    메뉴 텍스트 리터럴 매칭으로 이중 방어하기 위함."""
    if not query:
        return [], []
    neg_pos = [query.find(c) for c in _NEG_CUES if c in query]
    if not neg_pos:
        return [], []
    item_exclude = [ing for ing in _EXCLUDABLE
                     if query.find(ing) >= 0 and any(np > query.find(ing) for np in neg_pos)]
    category_exclude = {cat for cat in _CATEGORY_EXCLUDABLE
                         if query.find(cat) >= 0 and any(np > query.find(cat) for np in neg_pos)}
    for cat in list(category_exclude):
        item_exclude.append(cat)
    for syn, cat in _CATEGORY_SYNONYMS.items():
        if query.find(syn) >= 0 and any(np > query.find(syn) for np in neg_pos):
            category_exclude.add(cat)
            item_exclude.append(syn)
    return list(set(item_exclude)), list(category_exclude)


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
    # 향토음식점(한식)만 추천 — 카페·주점·양식 등은 컨셉에 안 맞아 제외
    cands = [c for c in cands if c.get("cuisine_type") == "한식"]
    # 사용자가 싫다고 한 재료/카테고리가 든 곳은 제외한다
    # ("전복 싫은데" → 전복집 제외, "생선/해산물 싫은데" → 해산물 카테고리 전체 제외)
    item_exclude, category_exclude = _parse_exclude(query)
    if item_exclude:
        cands = [c for c in cands
                 if not any(ing in ((c.get("menu") or "") + (c.get("place") or "")) for ing in item_exclude)]
    if category_exclude:
        cands = [c for c in cands
                 if not any(cat in (c.get("ingredient_category") or "") for cat in category_exclude)]
    # 같은 집이 두 POI_id로 중복될 수 있어 1곳만 남긴다.
    # 주소 끝에 상호가 덧붙거나 공백이 달라도 같은 곳으로 보게 정규화(상호·공백 제거).
    seen, uniq = set(), []
    for c in cands:
        place = c["place"] or ""
        norm_addr = (c.get("address") or "").replace(place, "").replace(" ", "")
        key = (place, norm_addr)
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    cands = uniq
    # situation 은 현재 검색조건으로 쓰지 않음(무시)
    if query:
        ids = [c["rowid"] for c in cands]
        print(f"[디버그] 랭킹 전 후보: {len(ids)}건, query={query!r}", flush=True)
        order = _get_ranker().rank(query, ids, len(ids))   # 전체 임베딩 순위
        print(f"[디버그] rank() 반환 order 길이: {len(order)}", flush=True)
        pos = {rid: i for i, rid in enumerate(order)}
        print(f"[디버그] pos 딕셔너리 크기: {len(pos)}", flush=True)
        # 짧은 단어 질의 보정 — KoSBERT는 단어 1개면 임베딩이 약해 랭킹이 흐려진다.
        # 질의어가 메뉴·상호에 직접 있으면 임베딩보다 우선(리터럴 신호로 보완).
        # 부정어(_NEG_CUES)는 키워드 매칭에서 빼야 함 — 안 그러면 메뉴에 우연히 "싫어" 같은
        # 글자가 들어간 식당(예: "양념 싫어 세트")이 리터럴 매칭 보너스로 엉뚱하게 1등이 됨.
        kws = [t for t in query.split()
               if (len(t) >= 2 or t in _FOOD1CHAR) and not any(neg in t for neg in _NEG_CUES)]

        def _lex_hit(c):
            hay = (c.get("menu") or "") + (c.get("place") or "")
            return any(k in hay for k in kws)

        cands = sorted(
            (c for c in cands if c["rowid"] in pos),
            key=lambda c: (0 if _lex_hit(c) else 1, pos[c["rowid"]]),
        )
    return cands[:top_n]


if __name__ == "__main__":
    out = retrieve(query="담백한 조개 해장국",
                   filters={"region": "여수권", "food_type": ["국물요리"]}, top_n=5)
    print(f"검색 결과 {len(out)}곳:")
    for r in out:
        print(f"  - {r['place']} | {(r['menu'] or '')[:35]}")
