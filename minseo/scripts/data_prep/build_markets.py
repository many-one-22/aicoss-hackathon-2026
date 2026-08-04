# -*- coding: utf-8 -*-
"""B-P02/B-P03 전통시장 통합 xlsx → data/processed/bp02_p03/markets.{json,csv}.
이미 잘 결합된 파일(광주전남_전통시장_통합)을 영어키로 정리만 한다. 결측은 null.
용도: 통합 DB의 markets 테이블. 좌표로 식당↔시장 거리, 취급품목으로 재료-시장 연계.
"""
import json
import csv
import sys
from pathlib import Path
import openpyxl

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent.parent
SRC = PROJECT / "data" / "raw" / "B-P02_P03" / "광주전남_전통시장_통합데이터(B-P02,B-P03).xlsx"
OUT = PROJECT / "data" / "processed" / "bp02_p03"

# 원본 컬럼(순서) → 영어키
KEYS = ["market_name", "sido", "sigungu", "address", "lat", "lng",
        "num_stores", "items", "open_cycle", "parking_p02", "parking_p03",
        "rest_area", "kids_room", "match_status"]


def clean(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v.strip() if isinstance(v, str) else v


def run():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["광주전남_전통시장_통합"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))

    records = []
    for r in rows:
        if not r or not r[0]:
            continue
        records.append({k: clean(r[i]) if i < len(r) else None for i, k in enumerate(KEYS)})

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "markets.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(OUT / "markets.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=KEYS)
        w.writeheader()
        w.writerows(records)

    with_coord = sum(1 for r in records if r["lat"] is not None)
    print(f"저장: data/processed/bp02_p03/markets.{{json,csv}} ({len(records)}개 시장, 좌표 {with_coord})")


if __name__ == "__main__":
    run()
