# -*- coding: utf-8 -*-
"""end-to-end 추천: 하드필터 → 랭킹 → 시세·영양·지역 전통시장 보강.
앱/API가 부르는 지휘자 함수. Figma 'AI 추천 결과' 화면의 데이터 소스.
임시 랭킹은 local_score(향토색) — 임베딩(KoSBERT/FAISS) 도입 시 이 부분만 교체.

전통시장은 좌표(식당의 35%만 보유)가 아니라 '시·군' 행정구역으로 매칭한다:
식당 주소의 시·군 == 시장 sigungu → 같은 지역 시장. 좌표 불필요, 100% 커버.
"""
import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hard_filter import hard_filter
from price_lookup import lookup_menu
from nutrition_lookup import lookup_nutrition

DB = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "namdo.sqlite"


def _load_markets():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT market_name, sigungu, num_stores, items, open_cycle, "
                       "kids_room, rest_area, parking_p02, lat, lng FROM markets").fetchall()
    con.close()
    return [dict(r) for r in rows]


_MARKETS = _load_markets()


def _sigungu_of(address):
    """주소 두 번째 토큰(시·군·구). '전남 여수시 …'→여수시, '광주 북구 …'→북구."""
    toks = str(address or "").split()
    return toks[1] if len(toks) >= 2 else ""


def _num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _region_markets(address, k=3):
    """같은 시·군의 전통시장 k곳(점포수 많은 순). 주소만 사용 → 좌표 없어도 100% 매칭.
    lat/lng 도 함께 반환(시장은 98% 좌표 보유 → 프론트 지도 핀용)."""
    sg = _sigungu_of(address)
    if not sg:
        return []
    ms = sorted((m for m in _MARKETS if m["sigungu"] == sg),
                key=lambda m: _num(m["num_stores"]), reverse=True)
    return [{"market_name": m["market_name"], "sigungu": m["sigungu"],
             "num_stores": m["num_stores"], "items": m["items"], "open_cycle": m["open_cycle"],
             "parking": m["parking_p02"], "kids_room": m["kids_room"], "rest_area": m["rest_area"],
             "lat": m["lat"], "lng": m["lng"]} for m in ms[:k]]


def recommend(region=None, ingredient=None, dish_type=None, health=None,
              exclude_chain=True, top_n=10):
    """필터 → 후보(하드필터) → local_score 상위 top_n → 시세·영양·지역시장 보강.
    반환: {total_candidates, returned, results:[식당+보강정보]}."""
    cands = hard_filter(region, ingredient, dish_type, health, exclude_chain)
    results = []
    for r in cands[:top_n]:  # hard_filter가 local_score DESC 정렬 → 그대로 상위 N
        area = "광주" if r["region_group"] == "광주 5개구" else "전남"
        results.append({
            "place": r["place"], "region_group": r["region_group"],
            "cuisine_type": r["cuisine_type"], "dish_type": r["dish_type"],
            "ingredient_category": r["ingredient_category"], "local_score": r["local_score"],
            "address": r["address"], "phone": r["phone"], "parking": r["parking"],
            "hours": r["hours"], "menu": r["menu"],
            "prices": lookup_menu(r["menu"], area),          # 재료 시세·제철
            "nutrition": lookup_nutrition(r["menu"]),        # 음식 영양
            "region_markets": _region_markets(r["address"]),  # 같은 시·군 전통시장
        })
    return {"total_candidates": len(cands), "returned": len(results), "results": results}


if __name__ == "__main__":
    out = recommend(region="광주 5개구", dish_type=["한상차림"], top_n=3)
    print(f"후보 {out['total_candidates']}건 중 상위 {out['returned']}건\n")
    for r in out["results"]:
        print(f"■ {r['place']} ({r['region_group']} / {r['dish_type']} / 향토{r['local_score']})")
        print(f"   메뉴: {r['menu'][:45]}")
        pr = [(p['ingredient'], p['current_price'] if p.get('has_price') else '시세없음') for p in r['prices']]
        print(f"   시세: {pr}")
        print(f"   영양: {[n['food_name'] for n in r['nutrition']]}")
        mk = [m['market_name'] + "(점포" + str(m['num_stores']) + ")" for m in r['region_markets']]
        print(f"   지역시장: {mk}")
        print()
