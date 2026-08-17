"""
build_restaurant_sentiment.py

B-A09(광주전남 맛집 코퍼스)의 '설명' 텍스트를 감성분석 파이프라인(extract_trend_tags.py)에 돌려서,
민서님 팀에 넘길 restaurant_sentiment 테이블을 만든다.

주의: '설명'은 실제 SNS 리뷰가 아니라 약 120자로 잘린 업체소개 텍스트라 아스펙트 언급이 적을 수 있음.
      임시 리뷰 소스로 쓰고, 실제 리뷰(네이버플레이스/카카오맵 등) 확보되면 --input만 교체하면 됨.
      (컬럼명이 지역/시군구/음식점명/주소/전화번호/설명 이라고 가정. 다르면 --col_* 옵션으로 매핑)

설치:
    pip install pandas transformers torch   # --model_dir 쓸 경우에만 transformers/torch 필요

사용법 (placeholder 극성판정, 빠른 테스트용):
    python build_restaurant_sentiment.py \
        --input 광주전남_향토음식점_후보_체인제외.csv \
        --output restaurant_sentiment.csv --limit 200

사용법 (실제 KcELECTRA 모델, 정식 실행):
    python scripts/inference/build_restaurant_sentiment.py \
  --input data/processed/a09_linked.csv \
  --model_dir models/kcelectra-polarity/best_model \
  --output data/processed/restaurant_sentiment.csv
"""

import argparse
import hashlib
import sys

import pandas as pd

from extract_trend_tags import (
    load_keywords,
    load_kcelectra_polarity_fn,
    placeholder_polarity_fn,
    split_sentences,
    match_aspects,
    LABEL_NAMES,
)


def make_restaurant_id(name: str, address: str) -> str:
    """이름+주소 기반 안정적 ID. 민서님 DB의 식당 PK와 이름/주소로 매칭 조인 가능."""
    key = f"{name}|{address}".strip()
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:12]


def summarize_tag(pos, neu, neg, aspect):
    total = pos + neu + neg
    if total == 0:
        return None
    if pos > neg * 2 and pos > 0:
        return f"{aspect} 호평 다수 ({pos}건)"
    if neg > pos:
        return f"{aspect} 불만 존재 ({neg}건)"
    if pos > 0:
        return f"{aspect} 언급 ({total}건, 대체로 긍정)"
    return f"{aspect} 언급 ({total}건)"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, help="B-A09 맛집 코퍼스 CSV")
    ap.add_argument("--output", default="restaurant_sentiment.csv")
    ap.add_argument("--keywords", default="data/resources/food_aspect_keywords.json")
    ap.add_argument("--model_dir", default=None, help="실제 KcELECTRA 모델 경로. 없으면 placeholder 사전 기반 사용")
    ap.add_argument("--limit", type=int, default=None, help="테스트용 상위 N개만 처리")
    ap.add_argument("--col_name", default="음식점명")
    ap.add_argument("--col_address", default="주소")
    ap.add_argument("--col_region", default="지역")
    ap.add_argument("--col_sigungu", default="시군구")
    ap.add_argument("--col_text", default="설명")
    ap.add_argument("--col_poi_id", default="poi_id",
                     help="namdo.sqlite의 restaurants.poi_id와 매칭된 컬럼명 (link_a09_to_restaurants.py 출력 기준). "
                          "값이 없거나 컬럼 자체가 없으면 이름+주소 해시로 대체")
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    if args.limit:
        df = df.head(args.limit)

    required = [args.col_name, args.col_address, args.col_region, args.col_sigungu, args.col_text]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"[오류] 입력 파일에 없는 컬럼: {missing}. --col_* 옵션으로 실제 컬럼명을 지정하세요.", file=sys.stderr)
        sys.exit(1)

    keywords = load_keywords(args.keywords)

    if args.model_dir:
        print(f"[정보] 실제 모델 사용: {args.model_dir}")
        polarity_fn = load_kcelectra_polarity_fn(args.model_dir)
    else:
        print("[정보] placeholder(사전 기반) 극성 판정 사용 중 — 정식 산출물은 --model_dir로 실제 모델을 지정하세요.")
        polarity_fn = placeholder_polarity_fn

    rows_out = []
    n_no_mention = 0

    for i, row in df.iterrows():
        text = str(row[args.col_text]) if pd.notna(row[args.col_text]) else ""
        aspect_counts = {}  # aspect -> {"긍정": n, "중립": n, "부정": n}

        for sentence in split_sentences(text):
            aspects = match_aspects(sentence, keywords)
            if not aspects:
                continue
            polarity = polarity_fn(sentence)
            for aspect in aspects:
                d = aspect_counts.setdefault(aspect, {"긍정": 0, "중립": 0, "부정": 0})
                d[LABEL_NAMES[polarity]] += 1

        if not aspect_counts:
            n_no_mention += 1
            continue

        poi_id = row[args.col_poi_id] if args.col_poi_id in df.columns else None
        if pd.notna(poi_id) and str(poi_id).strip():
            rid = str(int(poi_id)) if isinstance(poi_id, float) and poi_id.is_integer() else str(poi_id)
        else:
            rid = make_restaurant_id(row[args.col_name], row[args.col_address])
        for aspect, d in aspect_counts.items():
            tag = summarize_tag(d["긍정"], d["중립"], d["부정"], aspect)
            rows_out.append(
                {
                    "restaurant_id": rid,
                    "restaurant_name": row[args.col_name],
                    "region": row[args.col_region],
                    "sigungu": row[args.col_sigungu],
                    "aspect": aspect,
                    "positive_count": d["긍정"],
                    "neutral_count": d["중립"],
                    "negative_count": d["부정"],
                    "trend_tag": tag,
                }
            )

        if (i + 1) % 500 == 0:
            print(f"[진행] {i + 1}/{len(df)}건 처리")

    out_df = pd.DataFrame(rows_out)
    out_df.to_csv(args.output, index=False, encoding="utf-8-sig")

    print(f"\n[정보] 처리 완료: 전체 {len(df)}건 중 아스펙트 언급 있는 식당 {len(df) - n_no_mention}건")
    print(f"[정보] 언급 없어 제외된 식당 {n_no_mention}건 (설명이 120자로 잘려있어 아스펙트 키워드 자체가 안 걸린 경우가 많음)")
    print(f"[정보] restaurant_sentiment 행 수: {len(out_df)}")
    print(f"[정보] 저장 완료: {args.output}")
    if not out_df.empty:
        print("\n아스펙트별 총 언급 건수:")
        print(out_df.groupby("aspect")[["positive_count", "neutral_count", "negative_count"]].sum())


if __name__ == "__main__":
    main()