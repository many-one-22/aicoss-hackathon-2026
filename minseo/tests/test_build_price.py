import sys, csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
from build_price import parse_bp07


def test_parse_bp07_long(tmp_path):
    # B-P07 형식: 연도(실제 월), 품목명, 품종명, 평균가격, 등급명, 무게, 단위
    f = tmp_path / "bp07.csv"
    rows = [
        ["연도", "품목명", "품종명", "평균가격", "등급명", "유통단계별무게", "유통단계별단위명"],
        ["2024-01", "고등어", "냉동", "8900.5", "상품", "1", "kg"],
        ["2024-02", "고등어", "냉동", "9100", "상품", "1", "kg"],
    ]
    with open(f, "w", newline="", encoding="cp949") as fp:
        csv.writer(fp).writerows(rows)

    recs = parse_bp07(str(f))
    assert len(recs) == 2
    assert recs[0] == {"item": "고등어", "region": "전국",
                       "year_month": "2024-01", "price": 8900.5, "unit": "kg"}
