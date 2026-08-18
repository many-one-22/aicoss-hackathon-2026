# -*- coding: utf-8 -*-
"""월별 시세(prices) → Prophet 으로 다음 몇 달 시세 예측(신뢰구간 포함).
배치로 미리 예측해 price_forecast 테이블에 저장(런타임은 조회만).

⚠️ 데이터 한계: 이력 >= min_months(기본 24개월) 인 재료만 예측(계절성 필요).
   1년치뿐인 재료는 계절 패턴을 못 잡아 엉터리 예측 → 건너뜀(정직).
   시세는 KAMIS 광주 위주라 남도 수산물(꼬막·홍어 등)은 예측 대상 아님.

사전 설치: pip install prophet
재빌드: python scripts/data_prep/forecast_price.py
"""
import logging
import sqlite3
import sys
import warnings
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

warnings.filterwarnings("ignore")
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)

DB = Path(__file__).resolve().parent.parent.parent.parent / "data" / "processed" / "namdo.sqlite"


def _load_series(item, region):
    """(item, region)의 월별 (year_month, price) 오름차순."""
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT year_month, price FROM prices WHERE item=? AND region=? "
                       "ORDER BY year_month", (item, region)).fetchall()
    con.close()
    return rows


def _fit_predict(series, periods):
    """Prophet 학습 → 다음 periods개월 예측. 시세라 하한은 0으로 클립."""
    import pandas as pd
    from prophet import Prophet
    df = pd.DataFrame({"ds": pd.to_datetime([ym + "-01" for ym, _ in series]),
                       "y": [p for _, p in series]})
    m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    m.fit(df)
    fc = m.predict(m.make_future_dataframe(periods=periods, freq="MS")).tail(periods)
    out = []
    for row in fc.itertuples(index=False):
        out.append({"year_month": row.ds.strftime("%Y-%m"),
                    "yhat": round(max(row.yhat, 0), 2),
                    "yhat_lower": round(max(row.yhat_lower, 0), 2),
                    "yhat_upper": round(max(row.yhat_upper, 0), 2)})
    return out


def forecast(item, region, periods=6, min_months=24):
    """이력 충분하면 다음 periods개월 예측 리스트, 부족하면 None."""
    series = _load_series(item, region)
    if len(series) < min_months:
        return None
    return _fit_predict(series, periods)


def _backtest_mape(series, holdout=6):
    """최근 holdout개월을 빼고 학습→예측, 실제와 비교한 평균절대오차율(%)."""
    train, test = series[:-holdout], series[-holdout:]
    fc = _fit_predict(train, holdout)
    ape = [abs(f["yhat"] - actual) / actual * 100
           for (_, actual), f in zip(test, fc) if actual]
    return sum(ape) / len(ape) if ape else 999.0


def build_forecasts(periods=6, min_months=24, max_mape=20.0):
    """이력 >= min_months 인 재료를 백테스트→MAPE < max_mape 인 것만 예측 저장.
    부정확한 예측(변동성 큰 채소 등)은 제외해 서비스가 믿을 값만 제공한다.
    mape 컬럼도 저장(정확도 공개용)."""
    con = sqlite3.connect(DB)
    pairs = con.execute("SELECT item, region FROM prices GROUP BY item, region "
                        "HAVING COUNT(*) >= ?", (min_months,)).fetchall()
    con.execute("DROP TABLE IF EXISTS price_forecast")
    con.execute("CREATE TABLE price_forecast "
                "(item TEXT, region TEXT, year_month TEXT, yhat REAL, "
                "yhat_lower REAL, yhat_upper REAL, mape REAL)")
    kept, dropped = 0, []
    for item, region in pairs:
        series = _load_series(item, region)
        mape = _backtest_mape(series, periods)
        if mape >= max_mape:  # 부정확 → 서비스에서 제외
            dropped.append((item, round(mape, 1)))
            continue
        for r in _fit_predict(series, periods):
            con.execute("INSERT INTO price_forecast VALUES (?,?,?,?,?,?,?)",
                        (item, region, r["year_month"], r["yhat"],
                         r["yhat_lower"], r["yhat_upper"], round(mape, 1)))
        kept += 1
    con.commit()
    con.close()
    print(f"예측 저장: {kept}/{len(pairs)}개 재료 (MAPE<{max_mape}%) × {periods}개월")
    if dropped:
        print(f"제외(부정확): {', '.join(f'{i}({m}%)' for i, m in dropped)}")
    return kept


def lookup_forecast(item, region):
    """런타임 조회: price_forecast 에서 (item, region) 예측 리스트."""
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT year_month, yhat, yhat_lower, yhat_upper, mape FROM price_forecast "
                       "WHERE item=? AND region=? ORDER BY year_month", (item, region)).fetchall()
    con.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    build_forecasts()
