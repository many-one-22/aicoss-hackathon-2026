"""
build_seasonal_json.py

원래 seasonal.real.json을 만들던 스크립트를 못 찾아서, seasonal.js 상단 주석에 적힌
필드 스펙(id, item, region, unit, current, avg12, level, vsAvgPct, wowPct, peak_months, trend)
그대로 namdo.sqlite에서 다시 뽑아낸다.

DB의 seasonality 테이블엔 id/unit/avg12/vsAvgPct/wowPct가 없어서, 여기서 직접 계산한다:
    - unit: prices 테이블에서 같은 item의 unit을 찾아옴
    - avg12: trend_12m(그 품목의 최근 최대 12개월 가격) 평균
    - vsAvgPct: (현재가 - avg12) / avg12 * 100
    - wowPct: trend_12m의 마지막 두 시점 간 변화율(%)
    - id: "품목_지역" slug (프론트가 라우팅에 쓰는 값이라 안정적으로 고정)

사용법:
    python build_seasonal_json.py --db data/processed/namdo.sqlite \
        --out frontend/src/data/seasonal.real.json
"""

import argparse
import json
import re
import sqlite3
import statistics
from pathlib import Path


def slugify(item):
    return re.sub(r"[^0-9A-Za-z가-힣]+", "-", item).strip("-")


def unit_for_item(conn, item):
    row = conn.execute("SELECT unit FROM prices WHERE item = ? LIMIT 1", (item,)).fetchone()
    return row[0] if row else None


def forecasts_by_item_region(conn):
    """(item, region) → {"forecast": [...], "forecastMape": n} (price_forecast 테이블 없으면 {})."""
    try:
        rows = conn.execute(
            "SELECT item, region, year_month, yhat, yhat_lower, yhat_upper, mape "
            "FROM price_forecast ORDER BY item, region, year_month"
        ).fetchall()
    except sqlite3.OperationalError:
        return {}

    out = {}
    for item, region, ym, yhat, yhat_lower, yhat_upper, mape in rows:
        key = (item, region)
        entry = out.setdefault(key, {"forecast": [], "forecastMape": mape})
        entry["forecast"].append({"ym": ym, "yhat": yhat, "lo": yhat_lower, "hi": yhat_upper})
    return out


def build(db_path, out_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT item, region, current_price, level, peak_months, trend_12m FROM seasonality").fetchall()
    forecasts = forecasts_by_item_region(conn)

    result = []
    for item, region, current_price, level, peak_months_raw, trend_raw in rows:
        peak_months = json.loads(peak_months_raw) if peak_months_raw else []
        trend = json.loads(trend_raw) if trend_raw else []
        prices_only = [p for _, p in trend]
        avg12 = round(statistics.mean(prices_only), 2) if prices_only else current_price

        vs_avg_pct = round((current_price - avg12) / avg12 * 100, 1) if avg12 else 0
        wow_pct = 0
        if len(trend) >= 2:
            prev = trend[-2][1]
            wow_pct = round((trend[-1][1] - prev) / prev * 100, 1) if prev else 0

        fc = forecasts.get((item, region))

        result.append(
            {
                "id": f"{slugify(item)}-{region}",
                "item": item,
                "region": region,
                "unit": unit_for_item(conn, item),
                "current": current_price,
                "avg12": avg12,
                "level": level,
                "vsAvgPct": vs_avg_pct,
                "wowPct": wow_pct,
                "peak_months": peak_months,
                "trend": trend,
                "forecast": fc["forecast"] if fc else None,
                "forecastMape": fc["forecastMape"] if fc else None,
            }
        )

    conn.close()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"[정보] {len(result)}건 저장 → {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    build(Path(args.db), Path(args.out))


if __name__ == "__main__":
    main()
