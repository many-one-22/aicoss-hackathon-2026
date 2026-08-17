# -*- coding: utf-8 -*-
"""restaurants 텍스트 → KoSBERT 임베딩 + FAISS 인덱스 사전계산.
출력: data/processed/embeddings/{embeddings.npy, rowids.npy, index.faiss}

⚠️ 정합성: 임베딩은 restaurants.rowid 를 매칭키로 쓴다. build_db.py 가 DROP+재생성하며
rowid 를 재할당할 수 있으므로, DB 재빌드(build_db.py) 후에는 이 스크립트를 반드시 재실행해
임베딩을 재생성해야 한다(안 하면 rowid 어긋나 엉뚱한 식당이 랭킹됨).
"""
import sqlite3
import sys
from pathlib import Path
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent.parent
DB = PROJECT / "data" / "processed" / "namdo.sqlite"
OUT = PROJECT / "data" / "processed" / "embeddings"
MODEL_NAME = "jhgan/ko-sroberta-multitask"


def _load_texts(limit=None):
    con = sqlite3.connect(DB)
    sql = "SELECT rowid, place, menu FROM restaurants"
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = con.execute(sql).fetchall()
    con.close()
    rowids = [r[0] for r in rows]
    texts = [f"{r[1] or ''} {r[2] or ''}".strip() for r in rows]
    return rowids, texts


def build(limit=None, out_dir=None):
    from sentence_transformers import SentenceTransformer
    import faiss
    out_dir = Path(out_dir) if out_dir else OUT
    rowids, texts = _load_texts(limit)
    model = SentenceTransformer(MODEL_NAME)
    emb = model.encode(texts, batch_size=64, show_progress_bar=True,
                       normalize_embeddings=True).astype("float32")
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / "embeddings.npy", emb)
    np.save(out_dir / "rowids.npy", np.array(rowids, dtype=np.int64))
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    faiss.write_index(index, str(out_dir / "index.faiss"))
    print(f"임베딩 {emb.shape} 저장 → {out_dir}")
    return out_dir


if __name__ == "__main__":
    build()
