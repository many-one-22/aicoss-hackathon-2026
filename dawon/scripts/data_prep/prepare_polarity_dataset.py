"""
prepare_polarity_dataset.py

B-A06 (한국어 SNS 속성기반 감성분석) 라벨 JSON 파일들을
KcELECTRA 문서 단위 3-class 감성분류 학습용 데이터셋으로 변환한다.

입력 JSON 레코드 예시 (AI Hub 속성기반 감성분석 포맷):
{
    "Index": "1024338",
    "RawText": "...",
    "Domain": "패션",
    "MainCategory": "여성의류",
    "ProductName": "...",
    "GeneralPolarity": "1",   # -1(부정) / 0(중립) / 1(긍정)
    "Aspects": [...]          # 이번 단계에서는 사용하지 않음 (문서 단위 극성만 사용)
}

사용법:
    python prepare_polarity_dataset.py --input_dir /path/to/jsons --output_dir ./data
    python prepare_polarity_dataset.py --input_dir /path/to/jsons --pattern "1-1_*" --val_ratio 0.1

출력:
    output_dir/train.jsonl
    output_dir/val.jsonl
    output_dir/label_map.json
    콘솔에 도메인별/라벨별 분포 요약 출력
"""

import argparse
import json
import os
import random
import sys
import unicodedata
from collections import Counter, defaultdict

# GeneralPolarity 원본 값 -> 학습용 정수 라벨
# HuggingFace Trainer 등에서 바로 쓰기 좋게 0/1/2로 정렬 (부정/중립/긍정)
LABEL_MAP = {"-1": 0, "0": 1, "1": 2}
LABEL_NAMES = {0: "부정", 1: "중립", 2: "긍정"}


def normalize_name(name: str) -> str:
    """macOS 등에서 저장된 파일명이 NFD로 분해되어 있는 경우가 있어 NFC로 통일."""
    return unicodedata.normalize("NFC", name)


def find_json_files(input_dir: str, pattern_prefix: str, recursive: bool = True):
    """input_dir 안에서 pattern_prefix로 시작하는 .json 파일을 모두 찾는다.
    유니코드 정규화(NFC/NFD) 차이로 인한 매칭 누락을 방지한다.
    recursive=True면 하위 폴더(도메인별 TL_SNS_xx.도메인명 폴더 등)까지 전부 훑는다."""
    files = []
    if recursive:
        for root, _dirs, fnames in os.walk(input_dir):
            for fname in fnames:
                norm = normalize_name(fname)
                if norm.endswith(".json") and norm.startswith(pattern_prefix):
                    files.append(os.path.join(root, fname))
    else:
        for fname in os.listdir(input_dir):
            norm = normalize_name(fname)
            if norm.endswith(".json") and norm.startswith(pattern_prefix):
                files.append(os.path.join(input_dir, fname))
    return sorted(files)


def load_records(json_paths, base_dir=None):
    records = []
    skipped_no_polarity = 0
    skipped_empty_text = 0

    for path in json_paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print(f"[경고] {path}: 최상위가 list가 아님 — 건너뜀", file=sys.stderr)
            continue

        for rec in data:
            polarity_raw = rec.get("GeneralPolarity")
            text = (rec.get("RawText") or "").strip()

            if polarity_raw not in LABEL_MAP:
                skipped_no_polarity += 1
                continue
            if not text:
                skipped_empty_text += 1
                continue

            records.append(
                {
                    "index": rec.get("Index"),
                    "text": text,
                    "label": LABEL_MAP[polarity_raw],
                    "label_name": LABEL_NAMES[LABEL_MAP[polarity_raw]],
                    "domain": rec.get("Domain"),
                    "main_category": rec.get("MainCategory"),
                    "product_name": rec.get("ProductName"),
                    "source_file": normalize_name(
                        os.path.relpath(path, base_dir) if base_dir else os.path.basename(path)
                    ),
                }
            )

    if skipped_no_polarity:
        print(f"[정보] GeneralPolarity 누락/이상값으로 제외된 레코드: {skipped_no_polarity}건")
    if skipped_empty_text:
        print(f"[정보] 본문(RawText)이 비어있어 제외된 레코드: {skipped_empty_text}건")

    return records


def dedupe(records):
    """같은 Index가 여러 파일에 중복 등장하는 경우 첫 번째만 남긴다."""
    seen = set()
    out = []
    dup_count = 0
    for r in records:
        key = r["index"]
        if key in seen:
            dup_count += 1
            continue
        seen.add(key)
        out.append(r)
    if dup_count:
        print(f"[정보] 중복 Index {dup_count}건 제거")
    return out


def stratified_split(records, val_ratio, seed):
    """라벨 비율을 유지하며 train/val로 분할."""
    random.seed(seed)
    by_label = defaultdict(list)
    for r in records:
        by_label[r["label"]].append(r)

    train, val = [], []
    for label, items in by_label.items():
        items = items[:]
        random.shuffle(items)
        n_val = max(1, round(len(items) * val_ratio)) if len(items) > 1 else 0
        val.extend(items[:n_val])
        train.extend(items[n_val:])

    random.shuffle(train)
    random.shuffle(val)
    return train, val


def write_jsonl(records, path):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def print_distribution(records, title):
    print(f"\n=== {title} (총 {len(records)}건) ===")

    label_counts = Counter(r["label_name"] for r in records)
    print("라벨 분포:")
    for name in ["긍정", "중립", "부정"]:
        c = label_counts.get(name, 0)
        pct = (c / len(records) * 100) if records else 0
        print(f"  {name}: {c}건 ({pct:.1f}%)")

    domain_counts = Counter(r["domain"] for r in records)
    print("도메인 분포:")
    for domain, c in domain_counts.most_common():
        print(f"  {domain}: {c}건")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input_dir", required=True, help="B-A06 라벨 JSON 파일들이 있는 디렉토리")
    ap.add_argument("--pattern", default="", help="파일명 접두어 필터 (예: '1-1_'). 기본값은 전체 .json")
    ap.add_argument("--output_dir", default="./data", help="train.jsonl / val.jsonl 저장 위치")
    ap.add_argument("--val_ratio", type=float, default=0.1, help="검증셋 비율 (기본 0.1)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument(
        "--no_recursive",
        action="store_true",
        help="지정하면 하위 폴더는 훑지 않고 input_dir 바로 안의 파일만 찾음 (기본은 하위 폴더까지 재귀 탐색)",
    )
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    if not os.path.isdir(args.input_dir):
        print(f"[오류] input_dir 경로가 존재하지 않습니다: '{args.input_dir}'", file=sys.stderr)
        print(f"[안내] 현재 작업 디렉토리(pwd): {os.getcwd()}", file=sys.stderr)
        print("[안내] 상대경로(../ 등)를 쓰셨다면, 지금 터미널이 어디 있는지부터 `pwd`로 확인해보세요.", file=sys.stderr)
        sys.exit(1)

    json_paths = find_json_files(args.input_dir, args.pattern, recursive=not args.no_recursive)
    if not json_paths:
        print(f"[오류] '{args.input_dir}'에서 패턴 '{args.pattern}*.json'에 맞는 파일을 찾지 못했습니다.", file=sys.stderr)
        try:
            top_level = os.listdir(args.input_dir)
        except OSError as e:
            top_level = [f"(목록을 읽을 수 없음: {e})"]
        print(f"[안내] input_dir 바로 안에 있는 항목 ({len(top_level)}개):", file=sys.stderr)
        for item in sorted(top_level)[:20]:
            print(f"    - {item}", file=sys.stderr)
        if len(top_level) > 20:
            print(f"    ... 외 {len(top_level) - 20}개", file=sys.stderr)
        sys.exit(1)
    print(f"[정보] 입력 파일 {len(json_paths)}개 발견")

    records = load_records(json_paths, base_dir=args.input_dir)
    records = dedupe(records)

    if not records:
        print("[오류] 유효한 레코드가 없습니다.", file=sys.stderr)
        sys.exit(1)

    print_distribution(records, "전체 데이터")

    train, val = stratified_split(records, args.val_ratio, args.seed)
    print_distribution(train, "Train")
    print_distribution(val, "Validation")

    write_jsonl(train, os.path.join(args.output_dir, "train.jsonl"))
    write_jsonl(val, os.path.join(args.output_dir, "val.jsonl"))
    with open(os.path.join(args.output_dir, "label_map.json"), "w", encoding="utf-8") as f:
        json.dump({"label_map": LABEL_MAP, "label_names": LABEL_NAMES}, f, ensure_ascii=False, indent=2)

    print(f"\n저장 완료: {args.output_dir}/train.jsonl, val.jsonl, label_map.json")


if __name__ == "__main__":
    main()