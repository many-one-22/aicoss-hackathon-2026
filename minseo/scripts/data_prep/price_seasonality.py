# -*- coding: utf-8 -*-
"""품목·지역별 제철·추이 계산 → data/processed/bp01_p07/seasonality.json.
현재수준 = 현재가 vs 전체 과거 분포 백분위(하위33 저렴/상위33 비쌈).
제철 = 캘린더 달별 과거 중앙값 최저 3개월.
"""
import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OUT = Path(__file__).resolve().parents[3] / "data" / "processed" / "bp01_p07"


def compute_seasonality(monthly: list[tuple[str, float]]) -> dict:
    if not monthly:
        return {"current_price": None, "trend_12m": [], "level": None,
                "peak_months": [], "in_season": False}
    ordered = sorted(monthly, key=lambda x: x[0])  # year_month 오름차순
    prices = [p for _, p in ordered]
    current = ordered[-1][1]  # 최신 월 가격

    # 현재수준: 전체 과거 대비 백분위
    below = sum(1 for p in prices if p < current)
    pct = below / len(prices)
    level = "저렴" if pct <= 0.33 else ("비쌈" if pct >= 0.67 else "평균")

    # 제철: 캘린더 달별 중앙값 최저 3개월. (in_season 판정은 '오늘 달'이 필요하므로
    #  여기서 고정하지 않고 peak_months만 저장 → 조회 시점에 price_lookup이 현재 달로 판정)
    by_month = defaultdict(list)
    for ym, p in ordered:
        by_month[int(ym.split("-")[1])].append(p)
    month_med = {m: statistics.median(v) for m, v in by_month.items()}
    peak_months = sorted(sorted(month_med, key=lambda m: month_med[m])[:3])

    return {
        "current_price": current,
        "trend_12m": ordered[-12:],
        "level": level,
        "peak_months": peak_months,
    }


def run():
    rows = list(csv.DictReader(open(OUT / "price_monthly.csv", encoding="utf-8-sig")))
    series = defaultdict(list)
    for r in rows:
        series[(r["item"], r["region"])].append((r["year_month"], float(r["price"])))

    result = {}
    for (item, region), monthly in series.items():
        result[f"{item}|{region}"] = compute_seasonality(monthly)

    (OUT / "seasonality.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: data/processed/bp01_p07/seasonality.json ({len(result)}개 품목·지역)")


if __name__ == "__main__":
    run()
