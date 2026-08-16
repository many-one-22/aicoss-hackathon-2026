# -*- coding: utf-8 -*-
"""
seeun 쪽에서 minseo/scripts/data_prep/hard_filter.py 의 hard_filter() 함수를
직접 불러와(import) 실행해보는 테스트 스크립트.

[왜 import 경로 문제가 생기나?]
hard_filter.py는 minseo/scripts/data_prep/ 폴더 안에 있고,
이 파일은 seeun/app/ 폴더 안에 있다. 서로 폴더 트리가 다르다.

파이썬은 `import 이름`을 실행할 때 아래 두 곳에서만 그 이름을 찾는다.
  1) 지금 실행 중인 스크립트가 들어있는 폴더 (여기서는 seeun/app)
  2) sys.path 리스트에 등록된 폴더들

hard_filter.py가 있는 minseo/scripts/data_prep 폴더는 이 목록에
없기 때문에, 그냥 `from hard_filter import hard_filter` 라고 쓰면

    ModuleNotFoundError: No module named 'hard_filter'

가 난다. 해결 방법은 hard_filter.py가 있는 폴더 경로를 실행 시점에
sys.path에 직접 추가해주는 것. 그러면 파이썬이 그 폴더도 뒤져서
찾아낼 수 있게 된다. (minseo 쪽에 __init__.py로 패키지를 만들어
설치하는 정식 방법도 있지만, 지금처럼 팀원 폴더가 분리된 해커톤
구조에서는 sys.path를 임시로 넓혀주는 방식이 제일 간단하다.)
"""
import sys
from pathlib import Path

# 이 파일(seeun/app/test_hard_filter.py) 기준으로 상위 폴더를 거슬러 올라가
# minseo/scripts/data_prep 경로를 계산한다.
#   parents[0] = seeun/app
#   parents[1] = seeun
#   parents[2] = aicoss-hackathon-2026  (레포 루트, seeun과 minseo가 둘 다 이 아래 있음)
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_PREP_DIR = REPO_ROOT / "minseo" / "scripts" / "data_prep"

if not DATA_PREP_DIR.exists():
    raise FileNotFoundError(f"hard_filter.py가 있어야 할 폴더를 못 찾음: {DATA_PREP_DIR}")

sys.path.insert(0, str(DATA_PREP_DIR))

from hard_filter import hard_filter  # noqa: E402  (sys.path 추가 뒤에 import해야 해서 위치가 파일 맨 위가 아님)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def run(title, **kwargs):
    print(f"\n=== {title} ===")
    print("조건:", kwargs)
    results = hard_filter(**kwargs)
    print(f"결과 {len(results)}건")
    for r in results[:5]:
        print(" -", r["place"], "|", r["region_group"], "|", r["ingredient_category"])
    return results


if __name__ == "__main__":
    # 요청받은 조건 그대로 실행
    run("region=광주, ingredient=[해산물]", region="광주", ingredient=["해산물"])

    # 위 결과가 0건으로 나온다면 DB 값 자체가 다른 것이 원인이다.
    # region_group 컬럼은 '광주'가 아니라 '광주 5개구' 처럼 정확한 전체 문자열로
    # 저장돼 있고, hard_filter()는 region을 "완전히 같은 값"으로만 비교한다
    # (WHERE region_group = ?, LIKE가 아님). 그래서 실제 값으로 다시 확인해본다.
    run("실제 DB 값으로 재확인: region=광주 5개구, ingredient=[해산물]",
        region="광주 5개구", ingredient=["해산물"])
