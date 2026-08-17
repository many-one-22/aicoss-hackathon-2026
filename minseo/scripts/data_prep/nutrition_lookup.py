# -*- coding: utf-8 -*-
"""메뉴 텍스트 → 매칭되는 음식들의 영양정보 (B-A07, 통합 DB nutrition 테이블).

음식명은 공백 제거 상태로 저장돼 있어(build_nutrition), 메뉴도 공백을 제거한 뒤
긴 이름부터 span-consume 방식으로 매칭한다. price_lookup 과 짝을 이루는 조회 유틸.
보조정보 성격(한식 약 44% 커버). 매칭 못 하면 그 메뉴는 영양정보 없음으로 둔다.
"""
import json
import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DB = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "namdo.sqlite"

# food_name 을 제외한 영양 수치 컬럼 — 매칭 결과에 그대로 실어 보낸다.
_NUTRIENT_COLS = ["weight_g", "energy_kcal", "carb_g", "sugar_g", "fat_g", "protein_g",
                  "calcium_mg", "phosphorus_mg", "sodium_mg", "potassium_mg", "magnesium_mg",
                  "iron_mg", "zinc_mg", "cholesterol_mg", "transfat_g"]


def _load_foods():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(f"SELECT food_name, {','.join(_NUTRIENT_COLS)} FROM nutrition").fetchall()
    con.close()
    foods = {r["food_name"]: {c: r[c] for c in _NUTRIENT_COLS} for r in rows}
    names = sorted(foods, key=len, reverse=True)  # 긴 이름 우선(짧은 이름 재매칭 방지)
    return foods, names


_FOODS, _NAMES = _load_foods()


def lookup_nutrition(menu: str) -> list[dict]:
    """메뉴에서 발견된 음식들의 영양정보(메뉴 내 등장순, 중복 제거).
    긴 이름을 먼저 매칭하고 그 구간을 소비해, 짧은 이름이 긴 이름 안에서 다시 걸리는 것을 막는다
    (예: '산채비빔밥'이 먼저 잡히면 '비빔밥'이 그 안에서 또 매칭되지 않음)."""
    work = (menu or "").replace(" ", "")
    hits = []  # (pos, food_name)
    for nm in _NAMES:
        pos = work.find(nm)
        if pos != -1:
            hits.append((pos, nm))
            work = work.replace(nm, " " * len(nm))  # 구간 소비
    hits.sort(key=lambda x: x[0])
    return [{"food_name": nm, **_FOODS[nm]} for _, nm in hits]


if __name__ == "__main__":
    import pprint
    pprint.pprint(lookup_nutrition("산채 비빔밥, 김치찌개, 삼겹살"))
