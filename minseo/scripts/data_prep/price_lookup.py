# -*- coding: utf-8 -*-
"""메뉴 텍스트 + area → 재료별 시세 정보 또는 전통시장 안내.
시세는 통합 DB(namdo.sqlite)의 seasonality 테이블에서 읽는다(단일 소스)."""
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from price_ingredients import extract_ingredients

DB = Path(__file__).resolve().parents[3] / "data" / "processed" / "namdo.sqlite"


def _load():
    """seasonality 테이블 → {'품목|지역': {current_price, level, peak_months, trend_12m}}.
    peak_months/trend_12m 은 DB에 JSON 문자열로 저장돼 있어 리스트로 복원한다."""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    out = {}
    for r in con.execute("SELECT item, region, current_price, level, peak_months, trend_12m FROM seasonality"):
        out[f'{r["item"]}|{r["region"]}'] = {
            "current_price": r["current_price"],
            "level": r["level"],
            "peak_months": json.loads(r["peak_months"]) if r["peak_months"] else [],
            "trend_12m": json.loads(r["trend_12m"]) if r["trend_12m"] else [],
        }
    con.close()
    return out


def _region_for(area: str) -> str:
    # 순천 데이터는 미확보 → 전남도 인접 광역인 광주를 지역가로 사용, 없으면 전국 폴백.
    # (품목별 지역 시세차는 작고, 우리가 보여주는 수준/제철은 전국 계절성이 지배해 무해)
    return "광주"


def lookup_menu(menu: str, area: str) -> list[dict]:
    season = _load()
    region = _region_for(area)
    this_month = datetime.now().month  # 제철 판정은 조회 시점의 실제 달 기준
    out = []
    for ing in extract_ingredients(menu):
        # 지역 우선, 없으면 전국 폴백
        entry = season.get(f"{ing}|{region}") or season.get(f"{ing}|전국")
        used_region = region if f"{ing}|{region}" in season else "전국"
        if entry and entry.get("current_price") is not None:
            peak = entry.get("peak_months", [])
            out.append({
                "ingredient": ing, "has_price": True, "region": used_region,
                "current_price": entry["current_price"], "level": entry["level"],
                "peak_months": peak, "in_season": this_month in peak,
                "trend_12m": entry["trend_12m"],
            })
        else:
            out.append({
                "ingredient": ing, "has_price": False,
                "note": f"{ing} 시세 데이터 없음 - 인근 전통시장 안내",
            })
    return out


if __name__ == "__main__":
    import pprint
    pprint.pprint(lookup_menu("고등어조림, 김치찌개, 삼겹살", "광주"))
