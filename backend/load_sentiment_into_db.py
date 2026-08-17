"""
load_sentiment_into_db.py

build_restaurant_sentiment.py로 만든 restaurant_sentiment.csv를 SQLite 테이블로 적재.

사용법:
    cp namdo.sqlite namdo_local_test.sqlite
    python load_sentiment_into_db.py \
        --csv restaurant_sentiment.csv \
        --db namdo_local_test.sqlite
"""

import argparse
import sqlite3

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--table", default="restaurant_sentiment")
    args = ap.parse_args()

    df = pd.read_csv(args.csv, dtype={"restaurant_id": str})
    conn = sqlite3.connect(args.db)
    df.to_sql(args.table, conn, if_exists="replace", index=False)

    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{args.table}_rid ON {args.table}(restaurant_id)")
    conn.commit()

    n = conn.execute(f"SELECT COUNT(*) FROM {args.table}").fetchone()[0]
    print(f"[정보] {args.db}의 {args.table} 테이블에 {n}행 적재 완료 (restaurant_id 인덱스 생성됨)")
    conn.close()


if __name__ == "__main__":
    main()
