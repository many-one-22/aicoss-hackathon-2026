# -*- coding: utf-8 -*-
"""임베딩 기반 후보 재정렬. 순수 함수(_rank_by_vector) + EmbedRanker(런타임).

[수정 이력] OUT 경로를 minseo/ 개인 폴더가 아니라 레포 루트 data/processed/embeddings 기준으로 통일.
build_embeddings.py가 저장하는 위치와 반드시 같아야 함 (다르면 임베딩 파일을 못 찾거나,
옛날 임베딩을 읽어서 rowid가 어긋난 결과가 나옴).
"""
import sys
from pathlib import Path
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 이 파일이 minseo/scripts/data_prep/embed_rank.py에 있다는 가정:
#   parents[0]=data_prep, parents[1]=scripts, parents[2]=minseo, parents[3]=레포 루트
PROJECT = Path(__file__).resolve().parents[3]
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
        if not (self._dir / "embeddings.npy").exists():
            raise FileNotFoundError(
                f"임베딩 파일을 찾을 수 없습니다: {self._dir}\n"
                f"build_embeddings.py를 먼저 실행하세요 (같은 레포 루트 DB 기준으로)."
            )
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