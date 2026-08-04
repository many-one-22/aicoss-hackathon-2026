import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
from price_ingredients import extract_ingredients


def test_extracts_kamis_item_from_dish():
    assert extract_ingredients("고등어조림, 김치찌개") == ["고등어", "배추"]


def test_dedupes_and_keeps_order():
    assert extract_ingredients("갈치조림, 갈치구이, 삼겹살") == ["갈치", "돼지"]


def test_no_match_returns_empty():
    assert extract_ingredients("아메리카노, 티라미수") == []


def test_niche_seafood_not_in_map():
    # 낙지·꼬막은 시세 없음 → 추출 대상 아님(매핑에 없음)
    assert extract_ingredients("세발낙지, 벌교꼬막") == []
