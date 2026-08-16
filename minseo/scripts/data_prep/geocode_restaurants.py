# -*- coding: utf-8 -*-
"""좌표 없는 식당 주소 → Kakao 지오코딩 → geocode_cache.csv (address, lat, lng).
멘토 허용에 따라 승인데이터 외 좌표 보강. Kakao REST API 키는 환경변수 KAKAO_KEY 로 읽는다.

지오코딩 전략(커버리지 ↑): 주소검색(search/address) 먼저 → 0건이면 키워드검색(search/keyword)으로
폴백. 우리 주소엔 상호명이 붙은 경우가 있어(예: '… 지강로 431 시골돼지 담양숯불갈비') 주소검색만으론
실패하므로, 키워드검색이 상호+주소로 장소 좌표를 찾아준다.

재실행 안전: 캐시에 이미 있는 주소는 건너뜀(중단돼도 이어서).
사전 설치: pip install requests

실행(PowerShell):
  $env:KAKAO_KEY="복사한키"; python minseo/scripts/data_prep/geocode_restaurants.py
"""
import csv
import os
import sqlite3
import sys
import time
from pathlib import Path

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent.parent
DB = PROJECT / "data" / "processed" / "namdo.sqlite"
CACHE = PROJECT / "data" / "processed" / "geocode_cache.csv"
KEY = os.environ.get("KAKAO_KEY", "")


def _load_cache():
    done = set()
    if CACHE.exists():
        with open(CACHE, encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                done.add(r["address"])
    return done


def _addresses_to_geocode():
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT DISTINCT address FROM restaurants "
        "WHERE (lat IS NULL OR lat='') AND address IS NOT NULL AND address<>''").fetchall()
    con.close()
    return [r[0] for r in rows]


def _call(kind, addr):
    """Kakao local {kind}(address|keyword) 검색 → (lat, lng) | 'auth' | None."""
    url = f"https://dapi.kakao.com/v2/local/search/{kind}.json"
    try:
        resp = requests.get(url, params={"query": addr},
                            headers={"Authorization": f"KakaoAK {KEY}"}, timeout=5)
    except Exception:
        return None
    if resp.status_code == 401:
        return "auth"          # 키 오류 → 상위에서 즉시 중단
    if resp.status_code == 429:
        time.sleep(1.0)        # rate limit → 잠깐 쉬고 이번 건은 실패 처리
        return None
    docs = resp.json().get("documents", [])
    if docs:
        return docs[0]["y"], docs[0]["x"]   # Kakao: y=위도(lat), x=경도(lng)
    return None


def _geocode(addr):
    """주소검색 → 실패 시 키워드검색 폴백. (lat,lng) | 'auth' | None."""
    for kind in ("address", "keyword"):
        r = _call(kind, addr)
        if r == "auth":
            return "auth"
        if r:
            return r
    return None


def run():
    if not KEY:
        sys.exit("환경변수 KAKAO_KEY 가 비어있어요. 먼저 키를 설정하세요.")
    done = _load_cache()
    addrs = [a for a in _addresses_to_geocode() if a not in done]
    print(f"지오코딩 대상 {len(addrs)}개 (이미 완료 {len(done)}개)")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    write_header = not CACHE.exists()
    ok = fail = 0
    with open(CACHE, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(["address", "lat", "lng"])
        for i, addr in enumerate(addrs, 1):
            r = _geocode(addr)
            if r == "auth":
                sys.exit("❌ Kakao 인증 실패(401). KAKAO_KEY 값이 맞는지 확인하세요.")
            if r:
                w.writerow([addr, r[0], r[1]])
                ok += 1
            else:
                fail += 1
            if i % 200 == 0:
                f.flush()
                print(f"  진행 {i}/{len(addrs)} (성공 {ok}, 실패 {fail})")
            time.sleep(0.05)  # rate limit 여유
    print(f"완료: 성공 {ok}, 실패 {fail} → {CACHE}")


if __name__ == "__main__":
    run()
