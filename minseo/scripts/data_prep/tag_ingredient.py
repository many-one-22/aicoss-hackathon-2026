# -*- coding: utf-8 -*-
"""
B-A01 태깅 (2) ingredient_category: 주재료 계열 라벨 (멀티라벨)
- 입력: data/processed/ba01/ba01_{TL,VL}_tagged.json  (cuisine_type 이 이미 붙어있어야 함)
- 방식: 상호+메뉴 텍스트를 재료 사전(해산물/육류/채소)에 대조. 복수 매칭 가능.
- 출력: 같은 tagged.json/.csv 에 ingredient_category 컬럼 추가 (in-place)
- 실행 순서: merge_ba01.py → tag_cuisine.py → tag_ingredient.py

재료 사전은 승인데이터(B-P07/KAMIS 부류)가 메뉴의 37.6%만 커버해서,
cuisine_type 과 동일하게 메뉴 기반 처리사전으로 구성한다.
충돌 방지: 바'회'(육회↔광어회)·바'무'·바'김' 같은 1글자 모호어는 제외.
"""

import json
import csv
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
DATA = SCRIPT_DIR.parent.parent / "data" / "processed" / "ba01"
DEBUG = DATA / "debug"

SEAFOOD = [
    # 생선
    "광어", "우럭", "민어", "농어", "갈치", "고등어", "병어", "전어", "삼치", "도미",
    "조기", "숭어", "참돔", "쏘가리", "메기", "빠가", "생태", "도다리", "미꾸라지",
    "추어", "아귀", "아구", "북어", "황태", "명태", "동태", "꽁치", "가자미", "홍어",
    "짱뚱어", "장어", "붕장어", "아나고", "대구탕", "삼치",
    # 패류·갑각·연체
    "꼬막", "낙지", "문어", "오징어", "쭈꾸미", "주꾸미", "갑오징어", "한치", "전복",
    "새우", "대하", "바지락", "굴", "홍합", "소라", "꽃게", "대게", "킹크랩", "해삼",
    "골뱅이", "가리비", "멍게", "조개",
    # 복합·기타
    "해물", "물회", "활어", "모듬회", "세꼬시", "회무침", "생선", "해산물", "수산",
    "매생이", "굴비", "명란", "알탕", "젓갈", "멸치", "다시마", "미역",
    "연어", "먹태", "어묵", "오뎅", "참치",
]

MEAT = [
    # 소
    "소고기", "쇠고기", "한우", "육회", "육사시미", "육전", "갈비", "설렁탕", "곰탕",
    "도가니", "소머리", "사골", "차돌", "등심", "채끝", "안창", "우삼겹", "생고기",
    # 돼지
    "돼지", "삼겹", "항정", "목살", "앞다리", "보쌈", "수육", "족발", "순대", "곱창",
    "막창", "대창", "내장", "암뽕", "뒷고기", "오겹", "갈매기살", "제육", "두루치기",
    "주물럭", "뼈다귀", "뼈해장", "감자탕",
    # 닭·오리 ('오리'는 오리지날/오리엔탈에 오매칭되어 구체 요리명으로)
    "닭", "삼계", "백숙", "계란",
    "오리탕", "오리불고기", "오리주물럭", "훈제오리", "오리로스", "오리백숙", "오리고기",
    # 총칭·조리
    "불고기", "떡갈비", "육개장", "국밥", "고기",
]

VEGGIE = [
    # 채소 (마늘·양파는 고기집 양념으로 과다매칭되어 제외)
    "배추", "감자전", "고구마", "버섯", "시금치", "오이", "호박",
    "상추", "도라지", "더덕", "산채", "우엉", "열무", "고사리", "취나물", "머위",
    "미나리", "깻잎", "부추", "갓김치",
    # 두부·콩·장
    "두부", "청국장", "된장", "순두부", "비지", "콩나물", "콩국수",
    # 나물·비빔·김치
    "나물", "비빔밥", "쌈밥", "김치", "깍두기", "동치미", "묵",
    # 면(곡물이지만 채소성 한식)
    "모밀", "메밀",
]

# 발효·젓갈 (프론트 식재료 필터 4번째). 김치·된장 등 기존 채소/해산물과 겹치되(멀티라벨),
# 발효 요리를 별도로 집계. '식해'(젓갈)≠'식혜'(음료)라 오매칭 없음.
FERMENTED = [
    # 김치류 (메뉴에 김치 '요리'로 등장)
    "김치", "묵은지", "깍두기", "동치미", "갓김치", "총각김치", "열무김치", "백김치", "파김치",
    # 젓갈·염장 어패
    "젓갈", "명란", "새우젓", "어리굴젓", "갈치속젓", "창란", "낙지젓", "밴댕이젓", "식해",
    # 장류
    "된장", "청국장",
    # 삭힘·홍탁 (남도 발효 특색). '삼합'은 키조개·불삼합 등 비발효도 잡혀 제외,
    # 남도 홍어(대개 삭힌홍어)로 홍어삼합·홍탁을 포괄.
    "홍어", "홍탁", "삭힌", "삭혀", "장아찌",
]

CATS = [("해산물", SEAFOOD), ("육류", MEAT), ("채소", VEGGIE), ("발효·젓갈", FERMENTED)]


def classify_ingredient(place, menu):
    text = f"{place} {menu}"
    cats = []
    hits = {}
    for name, seed in CATS:
        matched = [k for k in seed if k in text]
        if matched:
            cats.append(name)
            hits[name] = matched[0]
    return cats, hits


def run():
    DEBUG.mkdir(parents=True, exist_ok=True)
    report = []

    for tag in ("TL", "VL"):
        src = DATA / f"ba01_{tag}_tagged.json"
        if not src.exists():
            print(f"[스킵] {src} 없음 (tag_cuisine.py 먼저 실행)")
            continue
        recs = json.loads(src.read_text(encoding="utf-8"))

        dist = {}
        combo = {}
        samples = {}
        unclassified = []
        for r in recs:
            cats, hits = classify_ingredient(r.get("place", ""), r.get("menu", ""))
            r["ingredient_category"] = "|".join(cats) if cats else "미분류"
            key = r["ingredient_category"]
            combo[key] = combo.get(key, 0) + 1
            for c in cats:
                dist[c] = dist.get(c, 0) + 1
                samples.setdefault(c, [])
                if len(samples[c]) < 15:
                    samples[c].append((r["place"], hits[c], r["menu"][:35]))
            if not cats:
                unclassified.append(r)

        # in-place 저장 (컬럼 추가)
        fields = list(recs[0].keys())
        src.write_text(json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
        with open(DATA / f"ba01_{tag}_tagged.csv", "w", newline="", encoding="utf-8-sig") as f:
            wtr = csv.DictWriter(f, fieldnames=fields)
            wtr.writeheader()
            wtr.writerows(recs)

        n = len(recs)
        classified = n - len(unclassified)
        report.append(f"\n{'='*50}\n[{tag}] ingredient_category (총 {n})\n{'='*50}")
        report.append(f"최소1개 분류: {classified} ({classified/n*100:.1f}%) / 미분류 {len(unclassified)} ({len(unclassified)/n*100:.1f}%)")
        report.append(f"카테고리별: " + ", ".join(f"{k} {v}" for k, v in sorted(dist.items(), key=lambda x: -x[1])))
        report.append(f"조합분포: " + ", ".join(f"{k}={v}" for k, v in sorted(combo.items(), key=lambda x: -x[1])[:10]))
        for c, _ in CATS:
            if c in samples:
                report.append(f"\n--- [{tag}] {c} 샘플 (상호 | 매칭 | 메뉴) ---")
                for pl, kw, mn in samples[c]:
                    report.append(f"  {pl[:14]} | {kw} | {mn}")
        report.append(f"\n--- [{tag}] 미분류 샘플 20 ---")
        for r in unclassified[:20]:
            report.append(f"  {r['place'][:14]} | {r['menu'][:45]}")

    (DEBUG / "ingredient_distribution.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\n저장: data/processed/ba01/ba01_*_tagged.json/.csv (ingredient_category 추가)")
    print(f"리포트: data/processed/ba01/debug/ingredient_distribution.txt")


if __name__ == "__main__":
    run()
