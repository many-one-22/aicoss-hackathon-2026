# -*- coding: utf-8 -*-
"""B-A01 태깅: dish_type — 메뉴로 음식 유형 분류 (프론트 '음식 유형' 필터, 멀티라벨).
값(복수 가능): 국물요리 / 구이 / 찜 / 회·생물 / 한상차림 / 면  (없으면 '미분류')
cuisine_type(한/중/일…)과 직교하는 축. 상호+메뉴 텍스트를 유형 사전에 대조.
build_db 가 이 함수로 restaurants.dish_type 컬럼을 채운다.
"""
import sqlite3
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# (유형, 키워드) — 멀티라벨이라 우선순위 없이 '존재하면 부여'. 모호어는 배제.
DISH_RULES = [
    ("국물요리", ["찌개", "전골", "매운탕", "해장국", "곰탕", "설렁탕", "육개장", "추어탕",
               "감자탕", "국밥", "순대국", "뼈해장", "우거지", "시래기", "떡국", "만둣국",
               "떡만두", "지리", "알탕", "대구탕", "동태탕", "갈비탕", "삼계", "백숙", "탕"]),
    ("면", ["국수", "냉면", "칼국수", "막국수", "짜장", "짬뽕", "파스타", "스파게티", "우동",
          "소바", "라멘", "쫄면", "라면", "밀면", "비빔면", "잔치국수", "콩국수", "메밀", "당면"]),
    ("구이", ["구이", "숯불", "직화", "석쇠", "삼겹", "목살", "항정", "갈매기살", "바베큐",
           "연탄", "떡갈비", "불백", "로스구이", "곱창구이", "장어구이"]),
    ("찜", ["아구찜", "아귀찜", "갈비찜", "해물찜", "코다리", "찜닭", "찜"]),
    # 바 '회'는 상회(상호)·육회(고기)·회춘탕에 오매칭 → 배제. 어패류 회 신호만.
    ("회·생물", ["횟집", "회센터", "물회", "막회", "사시미", "세꼬시", "활어", "숙성회",
             "모둠회", "모듬회", "생선회", "회무침", "회덮밥", "초밥", "대게", "킹크랩"]),
    ("한상차림", ["한정식", "백반", "한상", "쌈밥", "밥상", "보리밥"]),
]


def classify_dishtype(place, menu):
    """상호+메뉴에서 발견된 음식 유형(멀티라벨) 리스트. 없으면 빈 리스트.
    '탕수육'(튀김)·'탕후루'의 '탕'이 국물요리로 오매칭되므로 사전에 제거."""
    text = f"{place} {menu}".replace("탕수육", "").replace("탕후루", "")
    return [name for name, kws in DISH_RULES if any(k in text for k in kws)]


def run():
    db = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "namdo.sqlite"
    con = sqlite3.connect(db)
    dist = Counter()
    unclassified = 0
    n = 0
    samples = {name: [] for name, _ in DISH_RULES}
    for place, menu, cuisine in con.execute("SELECT place, menu, cuisine_type FROM restaurants"):
        n += 1
        hits = classify_dishtype(place or "", menu or "")
        if not hits:
            unclassified += 1
        for h in hits:
            dist[h] += 1
            if len(samples[h]) < 6:
                samples[h].append((place or "", (menu or "")[:30]))
    print(f"dish_type 분포 (총 {n}, 미분류 {unclassified} = {unclassified/n*100:.1f}%):")
    for name, _ in DISH_RULES:
        print(f"   {name:6s}: {dist[name]:6d} ({dist[name]/n*100:4.1f}%)")
    for name, _ in DISH_RULES:
        print(f"\n--- {name} 샘플 ---")
        for pl, mn in samples[name]:
            print(f"   {pl[:16]} | {mn}")


if __name__ == "__main__":
    run()
