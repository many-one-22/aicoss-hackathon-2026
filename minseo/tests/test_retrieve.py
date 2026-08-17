# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
import retrieve as rt


def test_filters_map_to_hard_filter(monkeypatch):
    # seeun 필터명(ingredient_pref/food_type/health) → 민서 hard_filter 인자로 매핑되는지
    captured = {}

    def fake_hard_filter(region=None, ingredient=None, dish_type=None, health=None, exclude_chain=True):
        captured.update(region=region, ingredient=ingredient, dish_type=dish_type,
                        health=health, exclude_chain=exclude_chain)
        return []
    monkeypatch.setattr(rt, "hard_filter", fake_hard_filter)

    rt.retrieve(filters={"region": "여수권", "ingredient_pref": "해산물",
                         "food_type": ["국물요리"], "health": "채식",
                         "situation": "데이트"})  # situation은 무시돼야 함
    assert captured["region"] == "여수권"
    assert captured["ingredient"] == ["해산물"]   # 단일값도 리스트로
    assert captured["dish_type"] == ["국물요리"]
    assert captured["health"] == ["채식"]
    assert captured["exclude_chain"] is True       # 기본 True(향토)


def test_query_reorders_by_ranker(monkeypatch):
    fake = [{"rowid": 1, "place": "A"}, {"rowid": 2, "place": "B"}, {"rowid": 3, "place": "C"}]
    monkeypatch.setattr(rt, "hard_filter", lambda *a, **k: fake)

    class FakeRanker:
        def rank(self, query, candidate_rowids, top_n):
            return [3, 1]  # 상위 2개, 순서 3,1
    monkeypatch.setattr(rt, "_get_ranker", lambda: FakeRanker())

    out = rt.retrieve(query="해물탕", filters={"region": "여수권"}, top_n=2)
    assert [r["place"] for r in out] == ["C", "A"]  # 랭커 순서 반영


def test_no_query_keeps_hard_filter_order(monkeypatch):
    fake = [{"rowid": 1, "place": "A"}, {"rowid": 2, "place": "B"}]
    monkeypatch.setattr(rt, "hard_filter", lambda *a, **k: fake)
    out = rt.retrieve(filters={"region": "여수권"}, top_n=5)  # query 없음
    assert [r["place"] for r in out] == ["A", "B"]  # hard_filter 순서 그대로


def test_region_normalized(monkeypatch):
    # 프론트가 "여수"/"여수시"로 줘도 DB 권역 "여수권"으로 정규화되는지
    captured = {}
    monkeypatch.setattr(rt, "hard_filter",
                        lambda region=None, **k: captured.setdefault("region", region) or [])
    rt.retrieve(filters={"region": "여수"})
    assert captured["region"] == "여수권"
    assert rt._norm_region("여수시") == "여수권"
    assert rt._norm_region("광주") == "광주 5개구"
    assert rt._norm_region("여수권") == "여수권"   # 이미 권역이면 그대로
