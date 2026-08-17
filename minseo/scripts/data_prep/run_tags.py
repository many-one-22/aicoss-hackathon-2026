# -*- coding: utf-8 -*-
"""
B-A01 태깅 파이프라인 러너 — 반드시 이 순서로 실행해야 함.

주의(코드리뷰 #1): tag_cuisine 은 merged.json 에서 새로 tagged.json 을 쓰므로,
단독 재실행하면 ingredient_category / local_score 컬럼이 사라진다.
키워드를 튜닝한 뒤에는 항상 이 러너로 3개를 순서대로 다시 돌릴 것.

  merge_ba01.py  (선행: 무거워서 여기 포함 안 함. 원본 바뀌었을 때만 따로 실행)
   → tag_cuisine.py    (cuisine_type)
   → tag_ingredient.py (ingredient_category)
   → tag_local.py      (local_score, cuisine_type 게이트 사용)
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = ["tag_cuisine.py", "tag_ingredient.py", "tag_local.py"]


def main():
    for step in STEPS:
        print(f"\n{'#'*60}\n# 실행: {step}\n{'#'*60}")
        r = subprocess.run([sys.executable, str(HERE / step)])
        if r.returncode != 0:
            sys.exit(f"[중단] {step} 실패 (코드 {r.returncode})")
    print("\n[완료] 태깅 3종 순서대로 실행됨.")


if __name__ == "__main__":
    main()
