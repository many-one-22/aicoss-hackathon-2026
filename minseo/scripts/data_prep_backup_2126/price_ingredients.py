# -*- coding: utf-8 -*-
"""식당 메뉴 텍스트 → KAMIS에 존재하는 구체 식재료 추출.
INGREDIENT_MAP: dish 키워드 → KAMIS 품목명. cuisine_type 키워드와 같은 손수 처리사전.
KAMIS에 시세가 있는 품목만 매핑한다(낙지·꼬막·홍어 등은 의도적으로 제외 → 시세 없음).
"""
import csv
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# dish/메뉴 키워드 → KAMIS 품목명 (긴 키워드 먼저 매칭되도록 아래 로직에서 정렬)
INGREDIENT_MAP = {
    # 수산물 (KAMIS 소매 존재)
    "고등어": "고등어", "갈치": "갈치", "조기": "조기", "굴비": "조기",
    "명태": "명태", "동태": "명태", "코다리": "명태", "북어": "명태", "황태": "명태",
    "오징어": "물오징어", "굴": "굴", "홍합": "홍합", "새우": "새우",
    "전복": "전복", "꽁치": "꽁치", "멸치": "건멸치",  # 데이터 품목명은 건멸치
    # 축산물
    "삼겹": "돼지", "제육": "돼지", "돼지": "돼지", "목살": "돼지", "보쌈": "돼지",
    "족발": "돼지", "수육": "돼지",
    "소고기": "소", "쇠고기": "소", "육회": "소", "갈비": "소", "불고기": "소",
    "설렁탕": "소", "곰탕": "소",
    "닭": "닭", "삼계": "닭", "백숙": "닭",
    "계란": "계란", "달걀": "계란",
    # 농산물 (채소)
    # '무'(radish)는 바로 쓰면 스무디·무침·무한리필·열무 등에 대량 오매칭(84%) → 확실한 무요리만
    "배추": "배추", "김치": "배추", "깍두기": "무", "동치미": "무", "마늘": "깐마늘",
    "양파": "양파", "감자": "감자", "고구마": "고구마",
    "콩나물": "콩나물", "시금치": "시금치", "오이": "오이", "애호박": "호박",
    "대파": "파", "깻잎": "깻잎", "부추": "부추",
}

# 긴 키워드 우선(예: '소고기'가 '소'보다 먼저) — substring 오매칭 완화
_KEYS_SORTED = sorted(INGREDIENT_MAP.keys(), key=len, reverse=True)


def extract_ingredients(text: str) -> list[str]:
    """텍스트에서 발견된 KAMIS 품목명(중복 제거), 텍스트 내 첫 등장 위치 순.
    긴 키워드부터 매칭하고 매칭 구간을 '소비'(공백 치환)해, 짧은 키워드가 긴 것 안에서
    재매칭되는 것을 막는다. (예: '굴비'가 먼저 '조기'로 잡히고 구간을 먹어 '굴'이 안 걸림)"""
    work = text
    hits = []  # (pos, item)
    seen = set()
    for kw in _KEYS_SORTED:  # 긴 키워드 우선
        pos = work.find(kw)
        if pos == -1:
            continue
        item = INGREDIENT_MAP[kw]
        if item not in seen:
            seen.add(item)
            hits.append((pos, item))
        work = work.replace(kw, " " * len(kw))  # 모든 occurrence 소비(중복 등장 대비)
    hits.sort(key=lambda x: x[0])
    return [item for _, item in hits]


def main():
    out = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "bp01_p07"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "ingredient_map.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["dish_keyword", "kamis_item"])
        for kw, item in INGREDIENT_MAP.items():
            w.writerow([kw, item])
    print(f"저장: data/processed/bp01_p07/ingredient_map.csv ({len(INGREDIENT_MAP)}개 매핑)")


if __name__ == "__main__":
    main()
