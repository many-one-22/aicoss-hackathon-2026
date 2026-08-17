# -*- coding: utf-8 -*-
"""임베딩 기반 후보 재정렬. 순수 함수(_rank_by_vector) + EmbedRanker(런타임)."""
import sys
from pathlib import Path
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent.parent
OUT = PROJECT / "data" / "processed" / "embeddings"
MODEL_NAME = "jhgan/ko-sroberta-multitask"


def _rank_by_vector(query_vec, cand_vecs, cand_ids, top_n):
    """정규화된 query_vec(1D)와 cand_vecs(2D, 행=후보)의 내적(=코사인)으로 내림차순 정렬.
    반환: [(cand_id, score)] 상위 top_n."""
    if len(cand_ids) == 0:
        return []
    scores = cand_vecs @ query_vec
    order = np.argsort(-scores)[:top_n]
    return [(cand_ids[int(i)], float(scores[int(i)])) for i in order]


class EmbedRanker:
    """사전계산 임베딩을 로드해 후보 rowid를 질의 유사도로 정렬."""

    def __init__(self, artifacts_dir=OUT, model_name=MODEL_NAME):
        self._dir = Path(artifacts_dir)
        self.emb = np.load(self._dir / "embeddings.npy")
        self.rowids = np.load(self._dir / "rowids.npy")
        self._pos = {int(r): i for i, r in enumerate(self.rowids)}
        self._model_name = model_name
        self._model = None

    def _encode(self, query):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        return self._model.encode([query], normalize_embeddings=True).astype("float32")[0]

    def rank(self, query, candidate_rowids, top_n=10):
        ids = [int(r) for r in candidate_rowids if int(r) in self._pos]
        if not ids:
            return []
        cand_vecs = self.emb[[self._pos[r] for r in ids]]
        qv = self._encode(query)
        ranked = _rank_by_vector(qv, cand_vecs, ids, top_n)
        return [rid for rid, _ in ranked]

    def semantic_search(self, query, top_n=10):
        import faiss
        index = faiss.read_index(str(self._dir / "index.faiss"))
        qv = self._encode(query).reshape(1, -1)
        _, idx = index.search(qv, top_n)
        return [int(self.rowids[i]) for i in idx[0] if i != -1]
