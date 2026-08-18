# -*- coding: utf-8 -*-
"""
B-A01 태깅 (3) local_score: 남도 향토 점수 (0 이상 정수)
- 입력: data/processed/ba01/ba01_{TL,VL}_tagged.json (cuisine_type 필요)
- 동작:
    1) cuisine_type != "한식"  →  local_score = 0 (외국음식·카페는 향토 대상 아님)
    2) 한식이면: 상호+메뉴에 등장하는 '남도 향토 신호' 키워드의 '서로 다른 개수'가 점수
- 출력: 같은 tagged.json/.csv 에 local_score 컬럼 추가 (in-place)
- 실행 순서: merge → tag_cuisine → tag_ingredient → tag_local

주의(설계상 인정): 향토 기준은 주관적. 데이터 근거 없는 손수 키워드(cuisine/ingredient과 동일 처리로직).
흔한 백반·국밥은 제외하고 '구별력 있는 남도 특색'만 넣음. score 0(일반 한식)이 다수인 게 정상.
키워드는 겹치지 않게 어근으로 구성(홍어무침→'홍어'로 흡수), 한 집당 키워드는 중복 없이 1회만 카운트.
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

# 남도 향토 신호 (어근, 서로 substring 중첩 안 되게)
LOCAL_KEYWORDS = [
    # 수산 특색
    "홍어", "홍탁", "낙지", "갈낙", "꼬막", "매생이", "짱뚱어", "병어", "민어",
    "굴비", "장어",
    # 육류·상차림
    "떡갈비", "육전", "한정식", "오리탕",
    # 김치·기타
    "갓김치", "추어",
    # 남도 지향 표현·지역명(상호)
    "남도", "전라도", "무안", "벌교", "영광", "담양", "여수", "순천",
]


# 향토 점수 대상 업종: 한식 + 주점(남도 포차 문화 = 향토의 일부. 홍어삼합 포차 등)
# 일반 맥주집은 향토 키워드가 없어 어차피 0.
LOCAL_ELIGIBLE = ("한식", "주점")


def local_score(cuisine_type, place, menu):
    if cuisine_type not in LOCAL_ELIGIBLE:
        return 0, []
    text = f"{place} {menu}"
    hit = [k for k in LOCAL_KEYWORDS if k in text]
    return len(hit), hit


def run():
    DEBUG.mkdir(parents=True, exist_ok=True)
    report = []

    for tag in ("TL", "VL"):
        src = DATA / f"ba01_{tag}_tagged.json"
        if not src.exists():
            print(f"[스킵] {src} 없음")
            continue
        recs = json.loads(src.read_text(encoding="utf-8"))
        # 가드: cuisine_type 게이트를 쓰므로 선행 단계(tag_cuisine)가 반드시 돌아야 함
        if recs and "cuisine_type" not in recs[0]:
            sys.exit(f"[중단] {src} 에 cuisine_type 없음 — run_tags.py 로 순서대로 실행할 것")

        score_dist = {}
        kw_count = {}
        samples = {}   # score대별 샘플
        for r in recs:
            s, hit = local_score(r.get("cuisine_type", ""), r.get("place", ""), r.get("menu", ""))
            r["local_score"] = s
            score_dist[s] = score_dist.get(s, 0) + 1
            for k in hit:
                kw_count[k] = kw_count.get(k, 0) + 1
            samples.setdefault(s, [])
            if s >= 1 and len(samples[s]) < 15:
                samples[s].append((r["place"], "+".join(hit), r["menu"][:35]))

        fields = list(recs[0].keys())
        src.write_text(json.dumps(recs, ensure_ascii=False, indent=2), encoding="utf-8")
        with open(DATA / f"ba01_{tag}_tagged.csv", "w", newline="", encoding="utf-8-sig") as f:
            wtr = csv.DictWriter(f, fieldnames=fields)
            wtr.writeheader()
            wtr.writerows(recs)

        n = len(recs)
        eligible = sum(1 for r in recs if r["cuisine_type"] in LOCAL_ELIGIBLE)
        local1 = sum(v for k, v in score_dist.items() if k >= 1)
        report.append(f"\n{'='*50}\n[{tag}] local_score (총 {n}, 대상 한식+주점 {eligible})\n{'='*50}")
        report.append("점수분포: " + ", ".join(f"{k}점={v}" for k, v in sorted(score_dist.items())))
        report.append(f"향토(score>=1): {local1} ({local1/eligible*100:.1f}% of 한식+주점)")
        report.append("키워드별 매칭수: " + ", ".join(f"{k} {v}" for k, v in sorted(kw_count.items(), key=lambda x: -x[1])))
        for s in sorted(samples, reverse=True):
            if samples[s]:
                report.append(f"\n--- [{tag}] score={s} 샘플 (상호 | 매칭 | 메뉴) ---")
                for pl, kw, mn in samples[s]:
                    report.append(f"  {pl[:16]} | {kw} | {mn}")

    (DEBUG / "local_distribution.txt").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    print(f"\n저장: data/processed/ba01/ba01_*_tagged.json/.csv (local_score 추가)")
    print(f"리포트: data/processed/ba01/debug/local_distribution.txt")


if __name__ == "__main__":
    run()
