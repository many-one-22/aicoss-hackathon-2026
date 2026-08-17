# -*- coding: utf-8 -*-
"""하이브리드 추천엔진 1차 SQL 하드필터.
프론트 필터 선택 → namdo.sqlite 에서 후보 식당을 좁힌다(임베딩 랭커의 입력).

필터 결합 규칙: 필터 '내부' 복수선택 = OR, 필터 '간' = AND.
건강필터의 제외 키워드는 손수 처리사전(생물분류 기반). 알레르기는 과다제외가 안전한 방향이라
모호한 1글자('굴' 등)도 포함해 놓친 것보다 넉넉히 거른다.

[수정 이력] DB 경로를 minseo/ 개인 폴더가 아니라 레포 루트 data/processed/ 기준으로 통일.
(namdo.sqlite가 폴더별로 따로 있어서 rowid가 어긋나는 사고가 있었음 — build_embeddings.py와
반드시 같은 DB를 봐야 함.)
"""
import sqlite3
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 이 파일이 minseo/scripts/data_prep/hard_filter.py에 있다는 가정:
#   parents[0]=data_prep, parents[1]=scripts, parents[2]=minseo, parents[3]=레포 루트
DB = Path(__file__).resolve().parents[3] / "data" / "processed" / "namdo.sqlite"

# 응답에 실을 컬럼(임베딩 랭커·프론트 카드용). rowid = 임베딩 후보 매칭 키
COLS = ["rowid", "place", "region_group", "cuisine_type", "dish_type", "ingredient_category",
        "local_score", "is_chain", "address", "lat", "lng", "menu", "phone", "parking", "hours"]

# 알레르기 제외 키워드 (생물분류 기반 손수사전)
_CRUSTACEAN = ["새우", "꽃게", "대게", "게장", "게살", "게찜", "킹크랩", "크랩", "대하", "가재", "랍스터", "랍스타"]
_SHELLFISH = ["조개", "꼬막", "바지락", "홍합", "굴", "소라", "전복", "가리비", "골뱅이", "키조개", "맛조개", "대합", "재첩"]


def hard_filter(region=None, ingredient=None, dish_type=None, health=None, exclude_chain=True):
    """필터 조건 → 후보 식당 dict 리스트 (기본 정렬 local_score DESC).
    region: str 1개 / ingredient·dish_type·health: list / exclude_chain: bool."""
    where, params = [], []

    if region:
        where.append("region_group = ?")
        params.append(region)

    if ingredient:  # 식재료 (선택된 것 OR)
        where.append("(" + " OR ".join(["ingredient_category LIKE ?"] * len(ingredient)) + ")")
        params += [f"%{x}%" for x in ingredient]

    if dish_type:  # 음식유형 (OR)
        where.append("(" + " OR ".join(["dish_type LIKE ?"] * len(dish_type)) + ")")
        params += [f"%{x}%" for x in dish_type]

    if exclude_chain:
        where.append("is_chain = 0")

    for h in (health or []):
        if h == "채식":  # 채소 O, 육류·해산물 X (태그 기반 근사)
            where.append("(ingredient_category LIKE '%채소%' "
                         "AND ingredient_category NOT LIKE '%육류%' "
                         "AND ingredient_category NOT LIKE '%해산물%')")
        elif h == "갑각류 제외":
            for kw in _CRUSTACEAN:
                where.append("menu NOT LIKE ?")
                params.append(f"%{kw}%")
        elif h == "조개류 제외":
            for kw in _SHELLFISH:
                where.append("menu NOT LIKE ?")
                params.append(f"%{kw}%")

    sql = f"SELECT {', '.join(COLS)} FROM restaurants"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY local_score DESC"

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, params).fetchall()
    con.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    print(f"[정보] DB: {DB} (존재: {DB.exists()})")

    def viol(rows, field, kws):
        return [r["place"] for r in rows if any(k in (r[field] or "") for k in kws)]

    r1 = hard_filter(region="여수권", dish_type=["국물요리"])
    print(f"[1] 여수권+국물요리+비체인: {len(r1)}곳 (탕수육 오탐 정정 후 ~97)")
    print("    상위:", [x["place"] for x in r1[:4]])

    r2 = hard_filter(health=["갑각류 제외"])
    print(f"[2] 갑각류 제외: {len(r2)}곳, 새우/게 메뉴 잔존: {len(viol(r2,'menu',['새우','꽃게','대게']))} (0이어야)")

    r3 = hard_filter(health=["조개류 제외"])
    print(f"[3] 조개류 제외: {len(r3)}곳, 꼬막/바지락 잔존: {len(viol(r3,'menu',['꼬막','바지락']))} (0이어야)")

    r4 = hard_filter(health=["채식"])
    print(f"[4] 채식: {len(r4)}곳, 육류 태그 잔존: {len(viol(r4,'ingredient_category',['육류']))} (0이어야)")

    r5 = hard_filter(region="광주 5개구", ingredient=["해산물", "육류"])
    both = sum(1 for x in r5 if "해산물" not in x["ingredient_category"] and "육류" not in x["ingredient_category"])
    print(f"[5] 광주+({{해산물 OR 육류}}): {len(r5)}곳, 둘 다 없는 위반: {both} (0이어야)")

    r6 = hard_filter(region="여수권", dish_type=["국물요리"], health=["조개류 제외"])
    print(f"[6] 여수권+국물요리+조개류제외: {len(r6)}곳 (r1보다 작아야: {len(r1)})")