# -*- coding: utf-8 -*-
"""가격 원본 → data/processed/bp01_p07/price_monthly.csv (long: item, region, year_month, price, unit).
1차 소스: B-P07(전국, cp949, '연도' 컬럼이 실제로 YYYY-MM). KAMIS 광주/순천은 추후 추가.

⚠️ B-P07은 한 품목에 품종·등급·단위가 여러 행(월별 최대 7행). 그대로 두면 단위가 섞이고
   (고등어=마리+손, 명태=마리+kg) 계절 품종(배추 월동/봄/여름)이 각각 5~6개월만 남는다.
   → aggregate_canonical: 품목별 '대표 단위'(행 수 최다)만 남기고, 그 단위 안에서 품종을
   월별 중앙값으로 집계 → (item, region, year_month) 당 한 값. 단위 통일 + 연중 연속.
"""
import csv
import glob
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT = Path(__file__).resolve().parent.parent.parent
OUT = PROJECT / "data" / "processed" / "bp01_p07"


def _norm_item(s: str) -> str:
    """품목명 정규화: 괄호 수식어 제거로 소스 간 이름 통일.
    (B-P07 '깐마늘(국산)' vs KAMIS 파일명 '깐마늘' → 둘 다 '깐마늘')."""
    return re.sub(r"\s*\(.*?\)", "", str(s)).strip()


def parse_bp07(path: str) -> list[dict]:
    """B-P07 csv(cp949) → 레코드 리스트. region은 '전국' 고정."""
    recs = []
    with open(path, encoding="cp949", newline="") as f:
        rows = list(csv.reader(f))
    for r in rows[1:]:
        if len(r) < 4 or not r[0] or not r[1]:
            continue
        try:
            price = float(str(r[3]).replace(",", "").strip())
        except ValueError:
            continue
        recs.append({
            "item": _norm_item(r[1]),
            "region": "전국",
            "year_month": r[0].strip(),
            "price": round(price, 2),
            "unit": (r[6].strip() if len(r) > 6 and r[6] else ""),
        })
    return recs


def parse_kamis(path: str, default_region: str = "광주") -> list[dict]:
    """KAMIS 기간별 다운로드(.xls 지만 실제 HTML) → 레코드.
    파일명 '가격정보_[지역_]{품목}[_등급/크기]_단위{단위}.xls' 에서 지역·품목·단위 추출,
    HTML 표(연도행 × 1~12월)에서 가격. '-'(결측) 스킵. B-P07과 같은 스키마."""
    toks = Path(path).stem.replace("가격정보_", "").split("_")
    region = default_region
    if toks and toks[0] in ("광주", "순천", "전국"):
        region, toks = toks[0], toks[1:]
    item = _norm_item(toks[0]) if toks else ""
    unit = next((t.replace("단위", "") for t in toks if t.startswith("단위")), "")

    html = re.sub(r"<style.*?</style>", "", open(path, encoding="utf-8").read(), flags=re.S | re.I)
    recs = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.S | re.I):
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, flags=re.S | re.I)]
        if len(cells) >= 13 and re.fullmatch(r"\d{4}", cells[0]):
            for m in range(1, 13):
                v = cells[m].replace(",", "").strip()
                if v and v != "-":
                    recs.append({"item": item, "region": region,
                                 "year_month": f"{cells[0]}-{m:02d}",
                                 "price": round(float(v), 2), "unit": unit})
    return recs


def aggregate_canonical(recs: list[dict]) -> list[dict]:
    """품목·지역별로 대표 단위(행 수 최다)만 남기고, 그 단위 안에서 품종을 월별 중앙값으로 집계.
    → (item, region, year_month) 당 한 행. 단위 섞임 제거 + 계절 품종 합쳐 연중 연속."""
    by_ir = defaultdict(list)
    for r in recs:
        by_ir[(r["item"], r["region"])].append(r)

    out = []
    for (item, region), rs in by_ir.items():
        dom_unit = Counter(r["unit"] for r in rs).most_common(1)[0][0]
        rs_u = [r for r in rs if r["unit"] == dom_unit]
        by_month = defaultdict(list)
        for r in rs_u:
            by_month[r["year_month"]].append(r["price"])
        for ym, prices in by_month.items():
            out.append({
                "item": item, "region": region, "year_month": ym,
                "price": round(statistics.median(prices), 2), "unit": dom_unit,
            })
    out.sort(key=lambda r: (r["item"], r["region"], r["year_month"]))
    return out


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = []
    for p in glob.glob(str(PROJECT / "data" / "raw" / "B-P07" / "*.csv")):   # 전국 (B-P07)
        raw.extend(parse_bp07(p))
    for p in glob.glob(str(PROJECT / "data" / "raw" / "B-P01" / "*.xls")):   # 광주 (KAMIS)
        raw.extend(parse_kamis(p))
    recs = aggregate_canonical(raw)

    with open(OUT / "price_monthly.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["item", "region", "year_month", "price", "unit"])
        w.writeheader()
        w.writerows(recs)
    print(f"저장: data/processed/bp01_p07/price_monthly.csv (원본 {len(raw)}행 → 집계 {len(recs)}행, "
          f"{len({r['item'] for r in recs})}품목)")


if __name__ == "__main__":
    run()
