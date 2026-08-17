# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
import forecast_price as fp


def test_short_series_returns_none(monkeypatch):
    # 이력이 min_months 미만이면 예측하지 않고 None (엉터리 예측 방지)
    monkeypatch.setattr(fp, "_load_series", lambda item, region: [("2024-%02d" % (i + 1), 100) for i in range(10)])
    assert fp.forecast("배추", "광주", min_months=24) is None


def test_enough_series_calls_prophet(monkeypatch):
    # 이력 충분하면 _fit_predict가 호출되고 그 결과를 그대로 반환
    monkeypatch.setattr(fp, "_load_series", lambda item, region: [("2023-01", 100)] * 30)
    monkeypatch.setattr(fp, "_fit_predict",
                        lambda series, periods: [{"year_month": "2026-08", "yhat": 120.0,
                                                  "yhat_lower": 110.0, "yhat_upper": 130.0}])
    out = fp.forecast("배추", "광주", periods=1, min_months=24)
    assert out == [{"year_month": "2026-08", "yhat": 120.0, "yhat_lower": 110.0, "yhat_upper": 130.0}]
