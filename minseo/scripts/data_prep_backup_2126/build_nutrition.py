# -*- coding: utf-8 -*-
"""
B-A07 전처리: 400 외식·한식 메뉴의 영양성분 테이블 정제
- 입력: B-A07/음식분류_AI_데이터_영양DB.xlsx (시트 '400외식메뉴')
- 처리: 컬럼명 영어키, 음식명 공백 정리, '-'(결측)→null, 긴 소수 반올림(2자리)
- 출력: data/processed/ba07/nutrition.json / .csv (400행)
- 건강 플래그는 만들지 않음(근거 없는 임의 기준 회피). 원본 수치만 저장.

역할: B-A01 식당 메뉴와 음식명으로 매칭하여 '건강조건(영양) 보조정보' 제공.
매칭 커버리지는 한식의 약 44%(검증 완료) — 보조 기능.
"""

import json
import csv
from pathlib import Path
import openpyxl

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parent.parent
SRC = PROJECT / "data" / "raw" / "B-A07" / "음식분류_AI_데이터_영양DB.xlsx"
OUT = PROJECT / "data" / "processed" / "ba07"

# 원본 컬럼(순서대로) → 영어키
COLS = [
    "food_name", "weight_g", "energy_kcal", "carb_g", "sugar_g", "fat_g",
    "protein_g", "calcium_mg", "phosphorus_mg", "sodium_mg", "potassium_mg",
    "magnesium_mg", "iron_mg", "zinc_mg", "cholesterol_mg", "transfat_g",
]


def clean_val(v):
    """'-'/빈값 → None, 숫자는 2자리 반올림."""
    if v is None or v == "-" or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, (int, float)):
        return round(float(v), 2)
    # 문자로 온 숫자
    try:
        return round(float(str(v).replace(",", "").strip()), 2)
    except ValueError:
        return str(v).strip()


def run():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["400외식메뉴"]

    records = []
    seen = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        # 음식명 공백 전부 제거 = 조인 키. "산채비빔밥 "/"음 식 명" 정리.
        # ⚠️ 나중에 B-A01 메뉴와 매칭할 때는 메뉴 쪽도 동일하게 공백 제거해야 함
        #    (메뉴 '산채 비빔밥' vs 키 '산채비빔밥' → 정규화 안 하면 놓침)
        name = str(row[0]).replace(" ", "").strip()
        rec = {"food_name": name}
        for i, key in enumerate(COLS[1:], start=1):
            rec[key] = clean_val(row[i]) if i < len(row) else None
        records.append(rec)
        seen[name] = seen.get(name, 0) + 1

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "nutrition.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(OUT / "nutrition.csv", "w", newline="", encoding="utf-8-sig") as f:
        wtr = csv.DictWriter(f, fieldnames=COLS)
        wtr.writeheader()
        wtr.writerows(records)

    dups = {k: c for k, c in seen.items() if c > 1}
    nulls = sum(1 for r in records for k in COLS[1:] if r[k] is None)
    print(f"음식 수: {len(records)}")
    print(f"중복 음식명: {len(dups)}  {dups if dups else ''}")
    print(f"null(결측) 셀: {nulls}")
    print(f"저장: data/processed/ba07/nutrition.json / .csv")


if __name__ == "__main__":
    run()
