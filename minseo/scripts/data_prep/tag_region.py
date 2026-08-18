# -*- coding: utf-8 -*-
"""B-A01 태깅: region_group — 주소로 지역 권역 분류 (프론트 '지역' 필터).
값: 여수권 / 순천·보성 / 목포·신안 / 나주·영암 / 담양·곡성 / 광주 5개구 / 기타 전남 / (빈값=주소불명)
주소 문자열만 사용(승인데이터 내 처리). build_db 가 이 함수로 restaurants.region_group 컬럼을 채운다.

주의: area 컬럼(광주/전남)은 원본에 오분류가 섞여있어(전남 영광군인데 area=광주 등),
      권역 판정은 area 가 아니라 address 를 우선 신뢰한다.
"""
import sqlite3
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# 전남 시·군 → 권역 (그 외 전남 시·군은 '기타 전남')
_TN_GROUP = {
    "여수시": "여수권",
    "순천시": "순천·보성", "보성군": "순천·보성",
    "목포시": "목포·신안", "신안군": "목포·신안",
    "나주시": "나주·영암", "영암군": "나주·영암",
    "담양군": "담양·곡성", "곡성군": "담양·곡성",
}


def region_group(address, area=""):
    """주소의 시·도(toks[0])·시·군(toks[1]) 토큰만으로 권역 판정.
    substring 이 아니라 토큰을 봐서, 도로명·상호명에 시군명이 섞여도 오분류되지 않는다
    (예: '전남 화순군 … 담양숯불갈비' → 담양이 아니라 화순=기타 전남)."""
    toks = str(address or "").split()
    if not toks:
        return ""
    sido = toks[0]
    city = toks[1] if len(toks) >= 2 else ""
    if sido.startswith("광주"):
        return "광주 5개구"
    if sido.startswith("전남") or sido.startswith("전라남"):
        return _TN_GROUP.get(city, "기타 전남")
    return ""  # 주소 없음/불명


def run():
    db = Path(__file__).resolve().parents[3] / "data" / "processed" / "namdo.sqlite"
    con = sqlite3.connect(db)
    c = Counter()
    for addr, area in con.execute("SELECT address, area FROM restaurants"):
        c[region_group(addr, area)] += 1
    tot = sum(c.values())
    print(f"region_group 분포 (총 {tot}):")
    for k, v in c.most_common():
        print(f"   {(k or '(불명)'):10s}: {v:6d} ({v/tot*100:4.1f}%)")


if __name__ == "__main__":
    run()
