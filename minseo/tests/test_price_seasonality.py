import csv
import sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
from price_seasonality import compute_seasonality


def test_level_and_current():
    # 가격이 100..1200 (월별 상승), 현재(마지막)=1200 → 상위 → 비쌈
    monthly = [(f"2024-{m:02d}", m * 100.0) for m in range(1, 13)]
    r = compute_seasonality(monthly)
    assert r["current_price"] == 1200.0
    assert r["level"] == "비쌈"
    assert len(r["trend_12m"]) == 12


def test_peak_season_lowest_months():
    # 1,2,3월이 싸고 나머지 비쌈 → 제철(최저 3개월)에 1,2,3 포함
    monthly = [(f"2024-{m:02d}", (100.0 if m <= 3 else 900.0)) for m in range(1, 13)]
    r = compute_seasonality(monthly)
    assert set(r["peak_months"]) == {1, 2, 3}


def test_empty_returns_none():
    r = compute_seasonality([])
    assert r["current_price"] is None


def test_real_price_monthly_trend_no_duplicate_months():
    """실제 집계 산출물을 통과시켜 C1 회귀 방지: build_price 집계가 월별 1값이므로
    trend_12m에 같은 달 중복·13개월 이상이 나오면 안 된다."""
    path = Path(__file__).resolve().parent.parent / "data" / "processed" / "bp01_p07" / "price_monthly.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    series = defaultdict(list)
    for r in rows:
        series[(r["item"], r["region"])].append((r["year_month"], float(r["price"])))
    checked = 0
    for key, monthly in series.items():
        months = [ym for ym, _ in compute_seasonality(monthly)["trend_12m"]]
        assert len(months) == len(set(months)), f"{key} trend has duplicate months"
        assert len(months) <= 12
        checked += 1
    assert checked > 50
