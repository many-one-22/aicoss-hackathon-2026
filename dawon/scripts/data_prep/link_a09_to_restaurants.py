"""
link_a09_to_restaurants.py

B-A09(광주전남_향토음식점_후보_체인제외.csv)에는 poi_id가 없고,
namdo.sqlite의 restaurants 테이블에는 있다. 이름+주소로 매칭해서 진짜 poi_id를 붙인다.
(1차: 이름+주소 완전일치, 2차: 이름만 일치 — 약 91%까지 매칭됨. 실제 실행 시 회전 확인.)

매칭 안 된 건은 poi_id가 비어있는 채로 남기고 --keep_unmatched로 포함 여부를 정할 수 있다.
(build_restaurant_sentiment.py는 poi_id가 없으면 자동으로 이름+주소 해시 ID를 대신 만든다.)

사용법:
    python scripts/data_prep/link_a09_to_restaurants.py \
  --a09 data/raw/광주전남_향토음식점_후보_체인제외.csv \
  --db data/raw/namdo.sqlite \
  --output data/processed/a09_linked.csv
"""

import argparse
import sqlite3

import pandas as pd


def norm(s):
    return str(s).replace(" ", "").strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a09", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--output", default="a09_linked.csv")
    args = ap.parse_args()

    a09 = pd.read_csv(args.a09)
    conn = sqlite3.connect(args.db)
    rest = pd.read_sql(
        "SELECT poi_id, place, address, region_group, dish_type, ingredient_category, local_score, is_chain FROM restaurants",
        conn,
    )
    conn.close()

    a09["name_key"] = a09["음식점명"].map(norm)
    a09["addr_key"] = a09["주소"].map(norm)
    rest["name_key"] = rest["place"].map(norm)
    rest["addr_key"] = rest["address"].map(norm)

    # 1차: 이름+주소 완전일치
    merged = a09.merge(
        rest.drop_duplicates(["name_key", "addr_key"]),
        on=["name_key", "addr_key"],
        how="left",
        suffixes=("", "_r"),
    )
    merged["match_method"] = merged["poi_id"].notna().map({True: "name+address", False: None})

    # 2차: 이름만 일치 (1차에서 못 찾은 것만 대상)
    name_lookup = rest.drop_duplicates("name_key").set_index("name_key")[
        ["poi_id", "region_group", "dish_type", "ingredient_category", "local_score", "is_chain"]
    ]
    unmatched_mask = merged["poi_id"].isna()
    for col in ["poi_id", "region_group", "dish_type", "ingredient_category", "local_score", "is_chain"]:
        fallback = merged.loc[unmatched_mask, "name_key"].map(name_lookup[col])
        merged.loc[unmatched_mask, col] = fallback
    merged.loc[unmatched_mask & merged["poi_id"].notna(), "match_method"] = "name_only"
    merged["match_method"] = merged["match_method"].fillna("unmatched")

    out_cols = [
        "지역", "시군구", "음식점명", "주소", "전화번호", "설명",
        "poi_id", "region_group", "dish_type", "ingredient_category", "local_score", "is_chain", "match_method",
    ]
    result = merged[out_cols]
    result.to_csv(args.output, index=False, encoding="utf-8-sig")

    counts = result["match_method"].value_counts()
    print("[정보] 매칭 결과:")
    for method, n in counts.items():
        print(f"  {method}: {n}건 ({n/len(result)*100:.1f}%)")
    print(f"[정보] 저장 완료: {args.output}")


if __name__ == "__main__":
    main()