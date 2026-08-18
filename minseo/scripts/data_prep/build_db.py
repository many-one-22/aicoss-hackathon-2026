# -*- coding: utf-8 -*-
"""통합 DB 적재: 처리된 데이터셋 전부 → data/processed/namdo.sqlite.
하이브리드 추천엔진의 1차 SQL 하드필터가 조회하는 '음식 DB + 가격 시계열 DB'.
재적재는 idempotent (테이블 drop 후 재생성).

테이블: restaurants, nutrition, prices, seasonality, markets, ingredient_map
"""
import json
import csv
import sqlite3
import sys
from collections import Counter
from pathlib import Path

# 태그 로직은 재구현하지 않고 태깅 스크립트의 함수를 그대로 재사용(중복 방지).
from tag_cuisine import classify_cuisine
from tag_ingredient import classify_ingredient
from tag_local import local_score as local_score_fn
from tag_region import region_group
from tag_dishtype import classify_dishtype

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROC = Path(__file__).resolve().parents[3] / "data" / "processed"
DB = PROC / "namdo.sqlite"

# 지점명 뗀 브랜드가 이 개수 이상 반복되면 체인으로 본다(승인데이터 내 등장수만 사용).
CHAIN_MIN = 3

# 병합 시 첫 non-empty 로 채울 기본 필드(menu 는 union, 태그는 재계산으로 별도 처리).
BASE_FIELDS = ["poi_id", "place", "area", "lat", "lng", "address", "phone",
               "hours", "closed_days", "parking"]


def _union_menu(menus):
    # 여러 메뉴 문자열을 콤마 기준으로 합쳐 중복 없이 등장순으로 이어붙인다.
    seen, out = set(), []
    for m in menus:
        for item in str(m or "").split(","):
            item = item.strip()
            if item and item not in seen:
                seen.add(item)
                out.append(item)
    return ", ".join(out)


def _brand(place):
    # 상호에서 끝 토큰이 '점'으로 끝나면(지점명) 떼어 브랜드만 남긴다.
    # 공백으로 구분된 지점명만 보수적으로 제거('행복정육점' 같은 붙은 이름은 유지).
    toks = str(place or "").split()
    if len(toks) >= 2 and toks[-1].endswith("점"):
        return " ".join(toks[:-1])
    return str(place or "")


def load_restaurants(con):
    # 1) TL+VL 로드 (서비스 DB는 학습용이 아니므로 둘 다 필요)
    raw = []
    for split in ("TL", "VL"):
        recs = json.loads((PROC / "ba01" / f"ba01_{split}_tagged.json").read_text(encoding="utf-8"))
        for r in recs:
            r["_split"] = split
            raw.append(r)

    # 2) (place,address) 교차중복 병합: 같은 식당의 TL판·VL판 메뉴가 다르므로(정보 손실 방지)
    #    메뉴는 union, 나머지 기본필드는 첫 non-empty. place/address 결측은 병합 불가 → 단독 유지.
    groups, singles = {}, []
    for r in raw:
        place, addr = (r.get("place") or "").strip(), (r.get("address") or "").strip()
        if place and addr:
            groups.setdefault((place, addr), []).append(r)
        else:
            singles.append([r])

    merged = []
    for recs in list(groups.values()) + singles:
        rec = {f: next((r.get(f) for r in recs
                        if r.get(f) not in (None, "", "없음")), recs[0].get(f))
               for f in BASE_FIELDS}
        rec["menu"] = _union_menu(r.get("menu") for r in recs)
        rec["split"] = "+".join(sorted({r["_split"] for r in recs}))
        # 3) 합친 메뉴 기준 태그 재계산 (부분 메뉴로 계산된 기존 태그 대체)
        cat, _ = classify_cuisine(rec["place"] or "", rec["menu"])
        cats, _ = classify_ingredient(rec["place"] or "", rec["menu"])
        s, _ = local_score_fn(cat, rec["place"] or "", rec["menu"])
        rec["cuisine_type"] = cat
        rec["ingredient_category"] = "|".join(cats) if cats else "미분류"
        rec["local_score"] = s
        # 프론트 필터용 파생 태그: 지역 권역(주소), 음식 유형(메뉴, 멀티라벨)
        rec["region_group"] = region_group(rec["address"] or "", rec["area"] or "")
        rec["dish_type"] = "|".join(classify_dishtype(rec["place"] or "", rec["menu"])) or "미분류"
        merged.append(rec)

    # 4) is_chain: 브랜드(지점명 제거) 등장수 >= CHAIN_MIN
    brand_count = Counter(_brand(m["place"]) for m in merged if (m.get("place") or "").strip())
    for m in merged:
        b = _brand(m["place"])
        m["is_chain"] = 1 if b and brand_count[b] >= CHAIN_MIN else 0

    cols = ["split", "poi_id", "place", "area", "lat", "lng", "menu", "address",
            "phone", "hours", "closed_days", "parking",
            "cuisine_type", "ingredient_category", "local_score", "is_chain",
            "region_group", "dish_type"]
    con.execute("DROP TABLE IF EXISTS restaurants")
    coldefs = ", ".join((c + " INTEGER" if c in ("local_score", "is_chain") else c + " TEXT")
                        for c in cols)
    con.execute(f"CREATE TABLE restaurants ({coldefs})")
    con.executemany(
        f"INSERT INTO restaurants ({','.join(cols)}) VALUES ({','.join('?'*len(cols))})",
        [[m.get(c) for c in cols] for m in merged])

    n_merged = sum(1 for m in merged if "+" in m["split"])
    n_chain = sum(m["is_chain"] for m in merged)
    print(f"  restaurants: 원본 {len(raw)} → 병합 {len(merged)} "
          f"(교차중복 병합 {n_merged}쌍, 체인 {n_chain})")
    return len(merged)


def load_nutrition(con):
    recs = json.loads((PROC / "ba07" / "nutrition.json").read_text(encoding="utf-8"))
    cols = list(recs[0].keys())
    con.execute("DROP TABLE IF EXISTS nutrition")
    con.execute(f"CREATE TABLE nutrition ({', '.join(c+(' TEXT' if c=='food_name' else ' REAL') for c in cols)})")
    con.executemany(f"INSERT INTO nutrition VALUES ({','.join('?'*len(cols))})",
                    [[r.get(c) for c in cols] for r in recs])
    return con.execute("SELECT COUNT(*) FROM nutrition").fetchone()[0]


def load_prices(con):
    rows = list(csv.DictReader(open(PROC / "bp01_p07" / "price_monthly.csv", encoding="utf-8-sig")))
    con.execute("DROP TABLE IF EXISTS prices")
    con.execute("CREATE TABLE prices (item TEXT, region TEXT, year_month TEXT, price REAL, unit TEXT)")
    con.executemany("INSERT INTO prices VALUES (?,?,?,?,?)",
                    [(r["item"], r["region"], r["year_month"], float(r["price"]), r["unit"]) for r in rows])
    return con.execute("SELECT COUNT(*) FROM prices").fetchone()[0]


def load_seasonality(con):
    data = json.loads((PROC / "bp01_p07" / "seasonality.json").read_text(encoding="utf-8"))
    con.execute("DROP TABLE IF EXISTS seasonality")
    con.execute("""CREATE TABLE seasonality
        (item TEXT, region TEXT, current_price REAL, level TEXT,
         peak_months TEXT, trend_12m TEXT)""")
    rows = []
    for key, s in data.items():
        item, region = key.split("|", 1)
        rows.append((item, region, s.get("current_price"), s.get("level"),
                     json.dumps(s.get("peak_months", []), ensure_ascii=False),
                     json.dumps(s.get("trend_12m", []), ensure_ascii=False)))
    con.executemany("INSERT INTO seasonality VALUES (?,?,?,?,?,?)", rows)
    return con.execute("SELECT COUNT(*) FROM seasonality").fetchone()[0]


def load_markets(con):
    recs = json.loads((PROC / "bp02_p03" / "markets.json").read_text(encoding="utf-8"))
    cols = list(recs[0].keys())
    con.execute("DROP TABLE IF EXISTS markets")
    con.execute(f"CREATE TABLE markets ({', '.join(c+' TEXT' for c in cols)})")
    con.executemany(f"INSERT INTO markets VALUES ({','.join('?'*len(cols))})",
                    [[r.get(c) for c in cols] for r in recs])
    return con.execute("SELECT COUNT(*) FROM markets").fetchone()[0]


def load_ingredient_map(con):
    rows = list(csv.DictReader(open(PROC / "bp01_p07" / "ingredient_map.csv", encoding="utf-8-sig")))
    con.execute("DROP TABLE IF EXISTS ingredient_map")
    con.execute("CREATE TABLE ingredient_map (dish_keyword TEXT, kamis_item TEXT)")
    con.executemany("INSERT INTO ingredient_map VALUES (?,?)",
                    [(r["dish_keyword"], r["kamis_item"]) for r in rows])
    return con.execute("SELECT COUNT(*) FROM ingredient_map").fetchone()[0]


def run():
    con = sqlite3.connect(DB)
    counts = {
        "restaurants": load_restaurants(con),
        "nutrition": load_nutrition(con),
        "prices": load_prices(con),
        "seasonality": load_seasonality(con),
        "markets": load_markets(con),
        "ingredient_map": load_ingredient_map(con),
    }
    # 조회 성능용 인덱스
    con.execute("CREATE INDEX ix_rest_filter ON restaurants(region_group, cuisine_type, is_chain)")
    con.execute("CREATE INDEX ix_price ON prices(item, region)")
    con.commit()
    con.close()
    print(f"적재 완료: data/processed/namdo.sqlite")
    for t, n in counts.items():
        print(f"  {t}: {n}")


if __name__ == "__main__":
    run()
