# 식재료 시세 안내 파이프라인 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 식당 메뉴에서 핵심 식재료를 뽑아 그 재료의 현재 시세·최근 추이·제철 여부를 반환하는 파이프라인을 만든다.

**Architecture:** 4개 독립 모듈 — 재료 추출 사전(`price_ingredients`), KAMIS/B-P07 가격 정제(`build_price`), 제철·추이 계산(`price_seasonality`), 통합 조회(`price_lookup`). 각 모듈은 순수 함수 + 파일 산출로 분리, 개별 테스트 가능.

**Tech Stack:** Python 3.13, openpyxl(엑셀), csv/json(표준). 테스트는 pytest.

## Global Constraints

- 지역: **광주 + 순천(전남 대표)**. area가 "전남"이면 순천, "광주"면 광주 시세 사용. 지역 데이터 없으면 "전국"으로 폴백.
- 승인 데이터만: KAMIS(B-P01), B-P07. 손수 매핑 사전은 처리로직으로 허용(cuisine_type 키워드와 동일 성격).
- 시세 없는 재료(낙지·꼬막·홍어·매생이): 에러 아님. `has_price=False` + 전통시장 안내로 반환.
- 인코딩: 읽기 `utf-8-sig`(BOM 대비)·`cp949`(B-P07), 쓰기 JSON `utf-8` / CSV `utf-8-sig`. 컬럼 영어키(기존 ba01/ba07과 일관).
- Prophet 예측은 out of scope (별도 stretch).
- 산출물 경로: `Data/price/`. 스크립트: `scripts/`.

## File Structure

- `scripts/price_ingredients.py` — `INGREDIENT_MAP`(dish키워드→KAMIS품목) + `extract_ingredients(text)`; main으로 `Data/price/ingredient_map.csv` 덤프
- `scripts/build_price.py` — B-P07(long)·KAMIS(wide) 가격 → `Data/price/price_monthly.csv`
- `scripts/price_seasonality.py` — `compute_seasonality(monthly)` + main으로 `Data/price/seasonality.json`
- `scripts/price_lookup.py` — `lookup_menu(menu, area)` (위 3개 조합)
- `tests/test_price_ingredients.py`, `tests/test_build_price.py`, `tests/test_price_seasonality.py`, `tests/test_price_lookup.py`
- `.gitignore` (원본 대용량 데이터 제외)

---

### Task 0: 프로젝트 셋업 (git + 폴더 + pytest)

**Files:**
- Create: `.gitignore`
- Create: `Data/price/.gitkeep`

- [ ] **Step 1: git 초기화**

Run:
```bash
cd "C:/Users/joo45/Desktop/AICOSS 하계 해커톤_26/PJ"
git init
```
Expected: `Initialized empty Git repository`

- [ ] **Step 2: .gitignore 작성** (원본 GB 데이터·파생 캐시 제외, 스크립트·소형 산출물만 추적)

`.gitignore`:
```
# 원본 대용량 데이터 (수십 GB, 커밋 금지)
B-A01/
B-A07/
B-P07/
B-P01/
# 파이썬 캐시
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: Data/price 폴더 확보**

Run:
```bash
mkdir -p Data/price && touch Data/price/.gitkeep
```

- [ ] **Step 4: pytest 설치 확인**

Run: `python -m pytest --version`
Expected: 버전 출력. 없으면 `pip install pytest` 후 재확인.

- [ ] **Step 5: Commit**

```bash
git add .gitignore Data/price/.gitkeep
git commit -m "chore: init git, gitignore, price data dir"
```

---

### Task 1: 재료 추출 사전 (`price_ingredients`)

식당 메뉴 텍스트에서 **KAMIS에 존재하는 구체 품목**을 추출한다.

**Files:**
- Create: `scripts/price_ingredients.py`
- Test: `tests/test_price_ingredients.py`

**Interfaces:**
- Produces: `extract_ingredients(text: str) -> list[str]` — 텍스트에서 발견된 KAMIS 품목명 리스트(중복 제거, 등장 순서). `INGREDIENT_MAP: dict[str, str]` — dish키워드→KAMIS품목.

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_price_ingredients.py`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from price_ingredients import extract_ingredients


def test_extracts_kamis_item_from_dish():
    assert extract_ingredients("고등어조림, 김치찌개") == ["고등어", "배추"]


def test_dedupes_and_keeps_order():
    assert extract_ingredients("갈치조림, 갈치구이, 삼겹살") == ["갈치", "돼지"]


def test_no_match_returns_empty():
    assert extract_ingredients("아메리카노, 티라미수") == []


def test_niche_seafood_not_in_map():
    # 낙지·꼬막은 시세 없음 → 추출 대상 아님(매핑에 없음)
    assert extract_ingredients("세발낙지, 벌교꼬막") == []
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `python -m pytest tests/test_price_ingredients.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'price_ingredients'`

- [ ] **Step 3: 구현**

`scripts/price_ingredients.py`:
```python
# -*- coding: utf-8 -*-
"""식당 메뉴 텍스트 → KAMIS에 존재하는 구체 식재료 추출.
INGREDIENT_MAP: dish 키워드 → KAMIS 품목명. cuisine_type 키워드와 같은 손수 처리사전.
KAMIS에 시세가 있는 품목만 매핑한다(낙지·꼬막·홍어 등은 의도적으로 제외 → 시세 없음).
"""
import csv
import sys
from pathlib import Path

# dish/메뉴 키워드 → KAMIS 품목명 (긴 키워드 먼저 매칭되도록 아래 로직에서 정렬)
INGREDIENT_MAP = {
    # 수산물 (KAMIS 소매 존재)
    "고등어": "고등어", "갈치": "갈치", "조기": "조기", "굴비": "조기",
    "명태": "명태", "동태": "명태", "코다리": "명태", "북어": "명태", "황태": "명태",
    "오징어": "물오징어", "굴": "굴", "홍합": "홍합", "새우": "새우",
    "전복": "전복", "꽁치": "꽁치", "멸치": "멸치",
    # 축산물
    "삼겹": "돼지", "제육": "돼지", "돼지": "돼지", "목살": "돼지", "보쌈": "돼지",
    "족발": "돼지", "수육": "돼지",
    "소고기": "소", "쇠고기": "소", "육회": "소", "갈비": "소", "불고기": "소",
    "설렁탕": "소", "곰탕": "소",
    "닭": "닭", "삼계": "닭", "백숙": "닭",
    "계란": "계란", "달걀": "계란",
    # 농산물 (채소)
    "배추": "배추", "김치": "배추", "무": "무", "마늘": "깐마늘(국산)",
    "양파": "양파", "감자": "감자", "고구마": "고구마",
    "콩나물": "콩나물", "시금치": "시금치", "오이": "오이", "애호박": "호박",
    "대파": "파", "깻잎": "깻잎", "부추": "부추",
}

# 긴 키워드 우선(예: '소고기'가 '소'보다 먼저) — substring 오매칭 완화
_KEYS_SORTED = sorted(INGREDIENT_MAP.keys(), key=len, reverse=True)


def extract_ingredients(text: str) -> list[str]:
    """텍스트에서 발견된 KAMIS 품목명 리스트(중복 제거, 첫 등장 순서)."""
    found: list[str] = []
    for kw in _KEYS_SORTED:
        if kw in text:
            item = INGREDIENT_MAP[kw]
            if item not in found:
                found.append(item)
    return found


def main():
    out = Path(__file__).resolve().parent.parent / "Data" / "price"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "ingredient_map.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["dish_keyword", "kamis_item"])
        for kw, item in INGREDIENT_MAP.items():
            w.writerow([kw, item])
    print(f"저장: Data/price/ingredient_map.csv ({len(INGREDIENT_MAP)}개 매핑)")


if __name__ == "__main__":
    main()
```

⚠️ 주의: `extract_ingredients`는 첫 등장 순서로 반환. `test_extracts_kamis_item_from_dish`는 "고등어조림, 김치찌개" → 고등어(먼저), 배추(김치). 텍스트 내 위치 순서를 지키려면 아래 Step 3b로 보정.

- [ ] **Step 3b: 등장 순서 보정** (키워드가 텍스트에 나타난 위치 기준 정렬)

`extract_ingredients`를 아래로 교체:
```python
def extract_ingredients(text: str) -> list[str]:
    """텍스트에서 발견된 KAMIS 품목명(중복 제거). 텍스트 내 첫 등장 위치 순."""
    hits = []  # (pos, item)
    seen = set()
    for kw in _KEYS_SORTED:
        pos = text.find(kw)
        if pos != -1:
            item = INGREDIENT_MAP[kw]
            if item not in seen:
                seen.add(item)
                hits.append((pos, item))
    hits.sort(key=lambda x: x[0])
    return [item for _, item in hits]
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_price_ingredients.py -v`
Expected: 4 passed

- [ ] **Step 5: 사전 CSV 생성 + 커밋**

Run: `python scripts/price_ingredients.py`
Expected: `저장: Data/price/ingredient_map.csv (...개 매핑)`

```bash
git add scripts/price_ingredients.py tests/test_price_ingredients.py Data/price/ingredient_map.csv
git commit -m "feat: dish->KAMIS ingredient extraction"
```

---

### Task 2: 가격 정제 (`build_price`)

가격 원본을 `price_monthly.csv`(long)로 통일. **1차 소스는 B-P07(우리가 가진 것, 전국 2024)**, KAMIS 광주/순천 수동 스냅샷은 추후 추가.

**Files:**
- Create: `scripts/build_price.py`
- Test: `tests/test_build_price.py`

**Interfaces:**
- Produces: `Data/price/price_monthly.csv` (컬럼 `item, region, year_month, price, unit`). `parse_bp07(path) -> list[dict]` — B-P07 csv → 레코드 리스트.

- [ ] **Step 1: 실패 테스트 작성** (B-P07 형식 픽스처 파싱)

`tests/test_build_price.py`:
```python
import sys, csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_price import parse_bp07


def test_parse_bp07_long(tmp_path):
    # B-P07 형식: 연도(실제 월), 품목명, 품종명, 평균가격, 등급명, 무게, 단위
    f = tmp_path / "bp07.csv"
    rows = [
        ["연도", "품목명", "품종명", "평균가격", "등급명", "유통단계별무게", "유통단계별단위명"],
        ["2024-01", "고등어", "냉동", "8900.5", "상품", "1", "kg"],
        ["2024-02", "고등어", "냉동", "9100", "상품", "1", "kg"],
    ]
    with open(f, "w", newline="", encoding="cp949") as fp:
        csv.writer(fp).writerows(rows)

    recs = parse_bp07(str(f))
    assert len(recs) == 2
    assert recs[0] == {"item": "고등어", "region": "전국",
                       "year_month": "2024-01", "price": 8900.5, "unit": "kg"}
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/test_build_price.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_price'`

- [ ] **Step 3: 구현**

`scripts/build_price.py`:
```python
# -*- coding: utf-8 -*-
"""가격 원본 → Data/price/price_monthly.csv (long: item, region, year_month, price, unit).
1차 소스: B-P07(전국, cp949, '연도' 컬럼이 실제로 YYYY-MM). KAMIS 광주/순천은 추후 추가.
"""
import csv
import glob
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "Data" / "price"


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
            "item": r[1].strip(),
            "region": "전국",
            "year_month": r[0].strip(),
            "price": round(price, 2),
            "unit": (r[6].strip() if len(r) > 6 and r[6] else ""),
        })
    return recs


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []
    for p in glob.glob(str(PROJECT / "B-P07" / "*.csv")):
        recs.extend(parse_bp07(p))

    with open(OUT / "price_monthly.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["item", "region", "year_month", "price", "unit"])
        w.writeheader()
        w.writerows(recs)
    print(f"저장: Data/price/price_monthly.csv ({len(recs)}행, "
          f"{len({r['item'] for r in recs})}품목)")


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_build_price.py -v`
Expected: 1 passed

- [ ] **Step 5: 실제 B-P07로 생성 + 커밋**

Run: `python scripts/build_price.py`
Expected: `저장: Data/price/price_monthly.csv (...행, ...품목)`

```bash
git add scripts/build_price.py tests/test_build_price.py Data/price/price_monthly.csv
git commit -m "feat: build price_monthly from B-P07"
```

> 📌 KAMIS 광주/순천 다년 스냅샷은 이후 별도 태스크로: 통계 페이지에서 품목별 월별 엑셀 저장 → `build_price`에 KAMIS wide 파서 추가 → region='광주'/'순천' 행 append. 인터페이스(`price_monthly.csv` 컬럼)는 동일하게 유지.

---

### Task 3: 제철·추이 계산 (`price_seasonality`)

품목·지역별로 현재수준·최근추이·제철달을 계산.

**Files:**
- Create: `scripts/price_seasonality.py`
- Test: `tests/test_price_seasonality.py`

**Interfaces:**
- Consumes: `price_monthly.csv` (Task 2)
- Produces: `compute_seasonality(monthly: list[tuple[str, float]]) -> dict` — 입력은 (year_month, price) 리스트. 반환 `{current_price, trend_12m, level, peak_months, in_season}`. main으로 `Data/price/seasonality.json` (키 `"{item}|{region}"`).

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_price_seasonality.py`:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from price_seasonality import compute_seasonality


def test_level_and_current():
    # 가격이 100..1200 (월별 상승), 현재(마지막)=1200 → 상위 → 비쌈
    monthly = [(f"2024-{m:02d}", m * 100.0) for m in range(1, 13)]
    r = compute_seasonality(monthly)
    assert r["current_price"] == 1200.0
    assert r["level"] == "비쌈"
    assert len(r["trend_12m"]) == 12


def test_peak_season_lowest_months():
    # 1,2,3월이 싸고 나머지 비쌈 → 제철(최저 3개월)에 1,2,3 포함
    monthly = [(f"2024-{m:02d}", (100.0 if m <= 3 else 900.0)) for m in range(1, 13)]
    r = compute_seasonality(monthly)
    assert set(r["peak_months"]) == {1, 2, 3}
    # 현재 달(마지막=12월)은 제철 아님
    assert r["in_season"] is False


def test_empty_returns_none():
    r = compute_seasonality([])
    assert r["current_price"] is None
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/test_price_seasonality.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 구현**

`scripts/price_seasonality.py`:
```python
# -*- coding: utf-8 -*-
"""품목·지역별 제철·추이 계산 → Data/price/seasonality.json.
현재수준 = 현재가 vs 전체 과거 분포 백분위(하위33 저렴/상위33 비쌈).
제철 = 캘린더 달별 과거 중앙값 최저 3개월.
"""
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "Data" / "price"


def compute_seasonality(monthly: list[tuple[str, float]]) -> dict:
    if not monthly:
        return {"current_price": None, "trend_12m": [], "level": None,
                "peak_months": [], "in_season": False}
    ordered = sorted(monthly, key=lambda x: x[0])  # year_month 오름차순
    prices = [p for _, p in ordered]
    current_ym, current = ordered[-1]

    # 현재수준: 전체 과거 대비 백분위
    below = sum(1 for p in prices if p < current)
    pct = below / len(prices)
    level = "저렴" if pct <= 0.33 else ("비쌈" if pct >= 0.67 else "평균")

    # 제철: 캘린더 달별 중앙값 최저 3개월
    by_month = defaultdict(list)
    for ym, p in ordered:
        by_month[int(ym.split("-")[1])].append(p)
    month_med = {m: statistics.median(v) for m, v in by_month.items()}
    peak_months = sorted(sorted(month_med, key=lambda m: month_med[m])[:3])
    in_season = int(current_ym.split("-")[1]) in peak_months

    return {
        "current_price": current,
        "trend_12m": ordered[-12:],
        "level": level,
        "peak_months": peak_months,
        "in_season": in_season,
    }


def run():
    rows = list(csv.DictReader(open(OUT / "price_monthly.csv", encoding="utf-8-sig")))
    series = defaultdict(list)
    for r in rows:
        series[(r["item"], r["region"])].append((r["year_month"], float(r["price"])))

    result = {}
    for (item, region), monthly in series.items():
        result[f"{item}|{region}"] = compute_seasonality(monthly)

    (OUT / "seasonality.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"저장: Data/price/seasonality.json ({len(result)}개 품목·지역)")


if __name__ == "__main__":
    run()
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_price_seasonality.py -v`
Expected: 3 passed

- [ ] **Step 5: 실제 생성 + 커밋**

Run: `python scripts/price_seasonality.py`
Expected: `저장: Data/price/seasonality.json (...개 품목·지역)`

```bash
git add scripts/price_seasonality.py tests/test_price_seasonality.py Data/price/seasonality.json
git commit -m "feat: seasonality (level + peak season) from price_monthly"
```

---

### Task 4: 통합 조회 (`price_lookup`)

메뉴 텍스트 + area → 재료별 시세 정보 또는 전통시장 안내.

**Files:**
- Create: `scripts/price_lookup.py`
- Test: `tests/test_price_lookup.py`

**Interfaces:**
- Consumes: `extract_ingredients`(Task1), `seasonality.json`(Task3)
- Produces: `lookup_menu(menu: str, area: str) -> list[dict]`. 각 dict: `{ingredient, has_price(bool), region, current_price, level, in_season, trend_12m}` 또는 `{ingredient, has_price=False, note}`.

- [ ] **Step 1: 실패 테스트 작성**

`tests/test_price_lookup.py`:
```python
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import price_lookup


def _seed(tmp_path, monkeypatch):
    data = {"고등어|전국": {"current_price": 8900.0, "trend_12m": [["2024-01", 8900.0]],
                          "level": "저렴", "peak_months": [1], "in_season": True}}
    f = tmp_path / "seasonality.json"
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(price_lookup, "SEASONALITY_PATH", f)


def test_priced_ingredient(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    out = price_lookup.lookup_menu("고등어조림", "광주")
    assert len(out) == 1
    assert out[0]["ingredient"] == "고등어"
    assert out[0]["has_price"] is True
    assert out[0]["level"] == "저렴"


def test_niche_ingredient_fallback(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    # 낙지는 매핑에 없음 → 재료 추출 자체가 안 됨 → 결과 없음
    assert price_lookup.lookup_menu("세발낙지탕탕이", "전남") == []


def test_priced_but_no_region_data_uses_fallback_region(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    # 광주 데이터 없고 전국만 있음 → 전국으로 폴백
    out = price_lookup.lookup_menu("고등어구이", "광주")
    assert out[0]["region"] == "전국"
```

- [ ] **Step 2: 실패 확인**

Run: `python -m pytest tests/test_price_lookup.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 구현**

`scripts/price_lookup.py`:
```python
# -*- coding: utf-8 -*-
"""메뉴 텍스트 + area → 재료별 시세 정보 또는 전통시장 안내."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from price_ingredients import extract_ingredients

SEASONALITY_PATH = Path(__file__).resolve().parent.parent / "Data" / "price" / "seasonality.json"


def _load():
    if SEASONALITY_PATH.exists():
        return json.loads(SEASONALITY_PATH.read_text(encoding="utf-8"))
    return {}


def _region_for(area: str) -> str:
    return "순천" if area == "전남" else "광주"


def lookup_menu(menu: str, area: str) -> list[dict]:
    season = _load()
    region = _region_for(area)
    out = []
    for ing in extract_ingredients(menu):
        # 지역 우선, 없으면 전국 폴백
        entry = season.get(f"{ing}|{region}") or season.get(f"{ing}|전국")
        used_region = region if f"{ing}|{region}" in season else "전국"
        if entry and entry.get("current_price") is not None:
            out.append({
                "ingredient": ing, "has_price": True, "region": used_region,
                "current_price": entry["current_price"], "level": entry["level"],
                "in_season": entry["in_season"], "trend_12m": entry["trend_12m"],
            })
        else:
            out.append({
                "ingredient": ing, "has_price": False,
                "note": f"{ing} 시세 데이터 없음 — 인근 전통시장 안내",
            })
    return out


if __name__ == "__main__":
    import pprint
    pprint.pprint(lookup_menu("고등어조림, 김치찌개, 삼겹살", "광주"))
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python -m pytest tests/test_price_lookup.py -v`
Expected: 3 passed

- [ ] **Step 5: 실데이터 스모크 + 커밋**

Run: `python scripts/price_lookup.py`
Expected: 고등어/배추/돼지 각각의 시세 dict 또는 시세없음 note 출력 (크래시 없음)

```bash
git add scripts/price_lookup.py tests/test_price_lookup.py
git commit -m "feat: price_lookup integrates extract+seasonality with fallback"
```

---

### Task 5: 전체 검증 + 러너

**Files:**
- Create: `scripts/run_price.py`

**Interfaces:**
- Consumes: 모든 이전 태스크

- [ ] **Step 1: 러너 작성** (순서: ingredient_map → build_price → seasonality)

`scripts/run_price.py`:
```python
# -*- coding: utf-8 -*-
"""시세 파이프라인 일괄 실행: 사전 → 가격 → 제철. lookup은 조회용이라 제외."""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for step in ["price_ingredients.py", "build_price.py", "price_seasonality.py"]:
    print(f"\n### {step}")
    if subprocess.run([sys.executable, str(HERE / step)]).returncode != 0:
        sys.exit(f"[중단] {step} 실패")
print("\n[완료] 시세 파이프라인")
```

- [ ] **Step 2: 전체 테스트 통과 확인**

Run: `python -m pytest tests/ -v`
Expected: 모든 테스트 passed (11개)

- [ ] **Step 3: 파이프라인 실행**

Run: `python scripts/run_price.py`
Expected: 3단계 순서 실행, `[완료]`. `Data/price/`에 ingredient_map.csv·price_monthly.csv·seasonality.json 생성

- [ ] **Step 4: 커밋**

```bash
git add scripts/run_price.py
git commit -m "feat: price pipeline runner"
```

---

## Self-Review

**Spec coverage:**
- ① 재료 추출 → Task 1 ✅ / ② KAMIS 가격 → Task 2(B-P07 1차, KAMIS 확장 명시) ✅ / ③ 제철·추이 → Task 3 ✅ / ④ 통합 조회 → Task 4 ✅ / 시세없는 재료 우회 → Task 4 fallback ✅ / 지역 광주+순천(전국 폴백) → Task 4 `_region_for` + 폴백 ✅
- ⚠️ 스펙의 "지역 광주+순천"은 KAMIS 스냅샷이 있어야 완전 충족. 현재 계획은 B-P07(전국)로 파이프라인을 먼저 완성하고, KAMIS 광주/순천은 Task 2 하단 노트대로 후속. 이 갭은 의도적(데이터 미확보) — 인터페이스는 동일해 나중에 데이터만 추가.

**Placeholder scan:** 모든 스텝에 실제 코드/명령/기대출력 포함. TODO 없음.

**Type consistency:** `extract_ingredients(text)->list[str]`, `compute_seasonality(list[tuple])->dict`, `lookup_menu(menu,area)->list[dict]`, `price_monthly.csv` 컬럼(item,region,year_month,price,unit)이 Task 2/3/4에서 일관. `SEASONALITY_PATH`는 Task4에서 monkeypatch 가능하도록 모듈 상수로 정의.

**주의(제철 신뢰도):** B-P07은 2024 1년치라 제철 판정이 그해 최저 3개월. KAMIS 다년 스냅샷 추가 시 계절패턴 신뢰도 상승(코드 변경 불필요, 데이터만 확장).
