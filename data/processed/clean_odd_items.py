"""
clean_odd_items.py

prices/seasonality 테이블에서 "제철"이라는 개념 자체가 안 맞는 가공식품/조미료류를 제거한다.
(즉석밥이 "지금 제철이라 저렴해요"로 뜨는 것처럼, 신선식품이 아닌 것들이 섞여있던 문제)

이 목록은 다원 님이 직접 검토해서 빼거나 추가하시면 됩니다 — 실행 전에 꼭 한 번 확인하세요.

사용법:
    python clean_odd_items.py --db namdo.sqlite            # 미리보기만 (삭제 안 함)
    python clean_odd_items.py --db namdo.sqlite --apply     # 실제로 삭제 (자동 백업 생성)
"""

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# 검토해서 조정하세요 — ①가공식품/조미료류(제철 개념 안 맞음), ②생과일류(향토음식 재료로 안 쓰임)
ODD_ITEMS = [
    # 가공식품/조미료
    "즉석밥",
    "고추장",
    "된장",
    "간장",
    "김치",
    "두부",
    "맛김",
    "멸치액젓",
    "새우젓",
    "굵은소금",
    "천일염",
    # 생과일 (향토음식 요리 재료로 쓰이지 않고 그냥 먹는 과일)
    "감귤",
    "단감",
    "딸기",
    "레몬",
    "망고",
    "멜론",
    "바나나",
    "배",
    "복숭아",
    "사과",
    "수박",
    "아보카도",
    "오렌지",
    "참다래",
    "참외",
    "체리",
    "파인애플",
    "포도",
    # 견과류 (그냥 먹는 것, 향토음식 조리 재료로 안 씀)
    "땅콩",
    "호두",
    "아몬드",
]


def preview(conn, items):
    print("=== 삭제 예정 행 수 ===")
    total = 0
    for table in ["prices", "seasonality"]:
        for item in items:
            n = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE item = ?", (item,)).fetchone()[0]
            if n:
                print(f"  {table}.{item}: {n}행")
                total += n
    print(f"\n총 {total}행이 삭제됩니다.")


def apply(db_path, items):
    backup_path = db_path.with_name(f"{db_path.stem}_backup_{datetime.now():%m%d_%H%M}{db_path.suffix}")
    shutil.copy(db_path, backup_path)
    print(f"[정보] 백업 생성: {backup_path}")

    conn = sqlite3.connect(db_path)
    for table in ["prices", "seasonality"]:
        placeholders = ",".join("?" * len(items))
        cur = conn.execute(f"DELETE FROM {table} WHERE item IN ({placeholders})", items)
        print(f"[정보] {table}에서 {cur.rowcount}행 삭제")
    conn.commit()
    conn.close()
    print("[정보] 완료")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", required=True)
    ap.add_argument("--apply", action="store_true", help="지정하지 않으면 미리보기만 하고 실제로 삭제하지 않음")
    args = ap.parse_args()

    db_path = Path(args.db)
    conn = sqlite3.connect(db_path)
    preview(conn, ODD_ITEMS)
    conn.close()

    if args.apply:
        apply(db_path, ODD_ITEMS)
    else:
        print("\n[안내] 미리보기만 실행됐습니다. 실제로 삭제하려면 --apply 옵션을 추가하세요.")


if __name__ == "__main__":
    main()