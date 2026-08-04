# -*- coding: utf-8 -*-
"""
B-A01 태깅 (1) cuisine_type: 요리 계열 라벨 부여
- 입력: data/processed/ba01/ba01_{TL,VL}_merged.json
- 방식: 상호명 + 메뉴 텍스트를 우선순위 키워드로 분류 (삭제 없음, 라벨만 추가)
- 우선순위: 카페 > 중식 > 일식 > 양식 > 치킨 > 주점 > 한식(기본값)
- 출력: ba01_{TL,VL}_tagged.json/.csv + debug/cuisine_distribution.txt

주의(코드리뷰 #1): 이 스크립트는 merged.json 에서 tagged.json 을 새로 쓴다.
따라서 단독 재실행하면 뒤 단계가 넣은 ingredient_category/local_score 가 사라진다.
키워드 튜닝 후에는 반드시 scripts/run_tags.py 로 3개를 순서대로 다시 실행할 것.
"""

import json
import csv
import sys
from pathlib import Path

# Windows cp949 콘솔에서 한글 print 시 UnicodeEncodeError 방지
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parent.parent
DATA = PROJECT / "data" / "processed" / "ba01"
DEBUG = DATA / "debug"

# 강한 한식 메인 메뉴 — 이게 있으면 상호에 cafe 가 있어도 한식으로 본다.
# (곰탕·칼국수류 추가: 이런 메뉴는 진짜 카페엔 안 나와서 안전. '커피 파는 한식당' 유출 방지)
STRONG_KOREAN = ["비빔밥", "죽", "국밥", "백반", "한정식",
                 "곰탕", "설렁탕", "칼국수", "곱창", "전골", "백숙", "수제비"]

# 카페 신호 — 음료(커피류)/디저트/카페성 상호. 이 중 하나라도 있고 강한한식메인이 없으면 카페.
# (에이드/스무디/주스 등은 치킨·분식집도 팔아서 제외, 커피·베이커리류만.)
CAFE_SIGNAL = [
    "카페", "cafe", "커피", "coffee", "아메리카노", "라떼", "에스프레소", "카푸치노",
    "베이커리", "제과", "빵집", "케이크", "디저트", "빙수", "마카롱", "와플", "도넛",
    "donut", "아이스크림", "젤라또", "티라미수", "쿠키", "크로플", "스콘", "브런치",
    # 프랜차이즈 브랜드명 (메뉴에 표기 오타/자체명칭이라 키워드 회피하는 경우 대비)
    "스타벅스", "투썸", "빽다방", "할리스", "이디야", "메가커피", "컴포즈", "폴바셋",
    "엔제리너스", "커피빈", "파스쿠찌", "탐앤탐스", "드롭탑", "할리치노", "프라푸치노",
]

# (카테고리, 키워드) — 카페 판정 이후, 위에서부터 매칭. 어디에도 안 걸리면 '한식'.
# 버거는 '밥버거'(분식) 오매칭 때문에 별도 처리(아래) 하므로 양식 목록에서 뺌.
CUISINE_RULES = [
    ("중식", ["짜장", "자장", "짬뽕", "탕수육", "중화요리", "중국집", "반점", "양꼬치",
             "마라탕", "마라샹", "마라상", "마라향", "훠궈", "깐풍", "팔보채", "멘보샤",
             "유산슬", "동파육"]),
    ("일식", ["초밥", "스시", "sushi", "사시미", "라멘", "오마카세", "이자카야", "텐동",
             "규동", "소바", "낫또", "가이센"]),
    ("양식", ["파스타", "스파게티", "피자", "pizza", "스테이크", "리조또", "라자냐",
             "그라탱", "파니니", "감바스"]),
    ("치킨", ["치킨", "통닭", "후라이드", "양념치킨", "bbq", "교촌", "굽네", "닭강정"]),
    ("주점", ["포차", "포장마차", "호프", "술집", "맥주", "와인", "위스키", "하이볼",
             "칵테일", "펍", "pub", "bar", "요리주점", "실내포차"]),
]


def classify_cuisine(place, menu):
    text = f"{place} {menu}".lower()

    # 1) 카페: 카페 신호 있고 + 강한 한식 메인 없을 때 (본죽&비빔밥cafe 같은 건 한식으로)
    # STRONG_KOREAN 은 '메뉴에서만' 검사 — 상호명의 '죽림/죽녹원/가죽' 부분매칭으로
    # 진짜 카페(투썸 죽림점 등)를 한식으로 밀어내는 것 방지.
    if not any(k in menu for k in STRONG_KOREAN):
        for kw in CAFE_SIGNAL:
            if kw.lower() in text:
                return "카페", kw

    # 2) 나머지 카테고리 우선순위 매칭
    for cat, keywords in CUISINE_RULES:
        for kw in keywords:
            if kw.lower() in text:
                return cat, kw
        # 양식 단계에서 버거 별도 처리: '버거' 있고 '밥버거'(분식) 아니면 양식
        if cat == "양식" and "버거" in text and "밥버거" not in text:
            return "양식", "버거"

    return "한식", ""


def run():
    DEBUG.mkdir(parents=True, exist_ok=True)
    report = []

    for tag in ("TL", "VL"):
        src = DATA / f"ba01_{tag}_merged.json"
        if not src.exists():
            print(f"[스킵] {src} 없음")
            continue

        recs = json.loads(src.read_text(encoding="utf-8"))
        dist = {}
        samples = {}   # 카테고리별 샘플 (검수용)

        for r in recs:
            cat, kw = classify_cuisine(r.get("place", ""), r.get("menu", ""))
            r["cuisine_type"] = cat
            dist[cat] = dist.get(cat, 0) + 1
            samples.setdefault(cat, [])
            if len(samples[cat]) < 20:
                samples[cat].append((r.get("place", ""), kw, r.get("menu", "")[:40]))

        # 저장 (기존 필드 + cuisine_type)
        fields = list(recs[0].keys())
        (DATA / f"ba01_{tag}_tagged.json").write_text(
            json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
        with open(DATA / f"ba01_{tag}_tagged.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(recs)

        # 리포트
        report.append(f"\n{'='*50}\n[{tag}] cuisine_type 분포 (총 {len(recs)})\n{'='*50}")
        for cat, cnt in sorted(dist.items(), key=lambda x: -x[1]):
            report.append(f"  {cat:4s} : {cnt:6d} ({cnt/len(recs)*100:5.1f}%)")
        for cat in [c for c, _ in CUISINE_RULES] + ["한식"]:
            if cat in samples:
                report.append(f"\n--- [{tag}] {cat} 샘플 (상호 | 매칭키워드 | 메뉴) ---")
                for place, kw, menu in samples[cat]:
                    report.append(f"  {place} | {kw} | {menu}")

    (DEBUG / "cuisine_distribution.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\n저장: data/processed/ba01/ba01_*_tagged.json/.csv")
    print(f"리포트: data/processed/ba01/debug/cuisine_distribution.txt")


if __name__ == "__main__":
    run()
