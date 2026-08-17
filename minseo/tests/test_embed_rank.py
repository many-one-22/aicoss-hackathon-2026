# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
from embed_rank import _rank_by_vector


def test_rank_orders_by_cosine():
    q = np.array([1.0, 0.0], dtype=np.float32)
    cand_vecs = np.array([[0.0, 1.0], [1.0, 0.0], [0.7, 0.7]], dtype=np.float32)
    out = _rank_by_vector(q, cand_vecs, [10, 20, 30], top_n=3)
    assert [cid for cid, _ in out] == [20, 30, 10]  # 20이 q와 가장 유사


def test_rank_respects_top_n():
    q = np.array([1.0, 0.0], dtype=np.float32)
    cand_vecs = np.array([[1.0, 0.0], [0.9, 0.1], [0.0, 1.0]], dtype=np.float32)
    out = _rank_by_vector(q, cand_vecs, [1, 2, 3], top_n=2)
    assert [cid for cid, _ in out] == [1, 2]


def test_rank_empty_candidates():
    q = np.array([1.0, 0.0], dtype=np.float32)
    assert _rank_by_vector(q, np.zeros((0, 2), dtype=np.float32), [], top_n=5) == []


def test_build_creates_artifacts(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
    from build_embeddings import build
    out = build(limit=20, out_dir=tmp_path)
    emb = np.load(out / "embeddings.npy")
    rowids = np.load(out / "rowids.npy")
    assert emb.shape[0] == rowids.shape[0] == 20
    assert emb.dtype == np.float32 and emb.shape[1] > 0
    assert (out / "index.faiss").exists()


def test_ranker_rank_orders_and_filters(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
    import embed_rank as er
    # 합성 산출물: rowid 100,200,300 / 2차원 정규화 벡터
    np.save(tmp_path / "embeddings.npy",
            np.array([[1, 0], [0, 1], [0.7, 0.7]], dtype=np.float32))
    np.save(tmp_path / "rowids.npy", np.array([100, 200, 300], dtype=np.int64))
    ranker = er.EmbedRanker(artifacts_dir=tmp_path)
    ranker._encode = lambda q: np.array([1.0, 0.0], dtype=np.float32)  # 스텁
    # 후보에 존재하지 않는 999는 무시되어야 함
    out = ranker.rank("아무거나", candidate_rowids=[300, 200, 999], top_n=2)
    assert out == [300, 200]  # q=[1,0]에 300(0.7)이 200(0)보다 유사


def test_recommend_query_reorders(monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "data_prep"))
    import recommend as rc

    # 하드필터 후보 3개(스텁, top_n보다 많게), 랭커는 상위 2개만 뒤집어 반환
    def _rec(rid, place, menu):
        return {"rowid": rid, "place": place, "region_group": "여수권", "cuisine_type": "한식",
                "dish_type": "국물요리", "ingredient_category": "해산물", "local_score": 0,
                "address": "전남 여수시 x", "phone": "", "parking": "", "hours": "", "menu": menu}
    fake = [_rec(1, "A", "해물탕"), _rec(2, "B", "생선탕"), _rec(3, "C", "매운탕")]
    monkeypatch.setattr(rc, "hard_filter", lambda *a, **k: fake)

    class FakeRanker:
        def rank(self, query, candidate_rowids, top_n):
            return [2, 1]  # 3개 중 상위 2개, 순서를 2,1로
    monkeypatch.setattr(rc, "_get_ranker", lambda: FakeRanker())

    out = rc.recommend(region="여수권", dish_type=["국물요리"], query="해산물 탕", top_n=2)
    assert [r["place"] for r in out["results"]] == ["B", "A"]  # 랭커 순서 반영
    assert out["total_candidates"] == 3  # 재정렬로 줄기 전 하드필터 통과 수 유지
