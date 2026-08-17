import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
import price_lookup


def _seed(tmp_path, monkeypatch):
    data = {"고등어|전국": {"current_price": 8900.0, "trend_12m": [["2024-01", 8900.0]],
                          "level": "저렴", "peak_months": [1], "in_season": True}}
    f = tmp_path / "seasonality.json"
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(price_lookup, "SEASONALITY_PATH", f)


def test_priced_ingredient(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    out = price_lookup.lookup_menu("고등어조림", "광주")
    assert len(out) == 1
    assert out[0]["ingredient"] == "고등어"
    assert out[0]["has_price"] is True
    assert out[0]["level"] == "저렴"


def test_niche_ingredient_fallback(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    # 낙지는 매핑에 없음 → 재료 추출 자체가 안 됨 → 결과 없음
    assert price_lookup.lookup_menu("세발낙지탕탕이", "전남") == []


def test_priced_but_no_region_data_uses_fallback_region(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    # 광주 데이터 없고 전국만 있음 → 전국으로 폴백
    out = price_lookup.lookup_menu("고등어구이", "광주")
    assert out[0]["region"] == "전국"
