# -*- coding: utf-8 -*-
"""
B-A01 병합 스크립트: 트리플(기본정보) + QA(좌표) 를 병합
- 뼈대 = 트리플 (식당 대다수가 트리플에만 존재)
- QA = 좌표(lat/lng) 채우기 + 빠진 정보 보완
- TL / VL 은 절대 합치지 않고 각각 산출 (모델 학습/평가 분리)
- 같은 식당이 두 POI_id(18xxxx/42xxxx 등)로 존재 → (place, address)로 최종 병합

방어코드:
  1) utf-8-sig 로 읽어 BOM 처리
  2) 파일별 try/except
  3) triple 길이 != 3 이면 스킵 (상호명 쉼표로 깨진 원본 줄)
  4) 관계 화이트리스트만 사용 ('인접' 등 불필요/깨진 관계 무시)
  5) 값의 잔여 따옴표/공백 제거
  6) "알수없음"/빈값 스킵
  7) glob 정렬로 재현성 확보, 빈 split ZeroDivision 가드
  8) 좌표: 유효값 나올 때까지 imageInfo 순회 (None 방지)
  9) (place, address) 기준 중복 식당 병합 (좌표/메뉴/정보 union)

좌표 주의: 원본 imageInfo 의 mapx≈35(위도), mapy≈126(경도) 로 통상 규약과 반대.
그래서 출력은 명시적으로 lat(=mapx), lng(=mapy) 컬럼으로 낸다.

출력:
  PJ/data/processed/ba01/ba01_TL_merged.json / .csv
  PJ/data/processed/ba01/ba01_VL_merged.json / .csv
  PJ/data/processed/ba01/debug/merge_report.txt
"""

import json
import csv
import glob
import re
from pathlib import Path

# 경로 설정 ----------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT = SCRIPT_DIR.parent.parent           # PJ/ (scripts/data_prep/ 기준)
RAW = PROJECT / "data" / "raw" / "B-A01"      # 원본
OUT = PROJECT / "data" / "processed" / "ba01" # 산출물
DEBUG = OUT / "debug"

# 트리플 관계 -> 우리 필드명 (화이트리스트)
FACT_RELATIONS = {
    "메뉴": "menu",
    "주소": "address",
    "연락처": "phone",
    "영업시간": "hours",
    "휴무일": "closed_days",
    "주차시설": "parking",
}

# QA 질문 텍스트 키워드 -> 필드명
QA_QUESTION_MAP = [
    ("메뉴", "menu"),
    ("주소", "address"),
    ("연락처", "phone"),
    ("영업시간", "hours"),
    ("휴무", "closed_days"),
    ("주차", "parking"),
]

# "없음"은 살린다: 주차시설=없음(주차불가) 17,780건, 휴무일=없음(연중무휴) 11,623건은 유효 정보.
# 진짜 모름인 "알수없음"만 스킵.
SKIP_VALUES = {"", "알수없음", "알 수 없음"}

# 분할별 폴더 접두사
SPLITS = {"TL": "Train", "VL": "Validation"}


def load_json(path):
    """utf-8-sig 로 읽어 BOM 처리. 실패 시 None."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        return None


def clean(v):
    """값의 잔여 따옴표/공백 제거."""
    if v is None:
        return ""
    return str(v).strip().strip('"').strip()


def area_from_folder(folder_name):
    """폴더명에서 지역 추출 (…_광주_… / …_전남_…)."""
    if "광주" in folder_name:
        return "광주"
    if "전남" in folder_name:
        return "전남"
    return ""


def place_from_filename(path):
    """트리플 파일명에서 상호명 추출.
    파일명 형식: tp_{poi}_{d}_{area}_{d}_{상호명}_{seq}.json
    트리플 subject 는 쉼표 상호명에서 깨지지만, 파일명은 온전하므로 여기서 뽑는다."""
    name = Path(path).stem                 # .json 제거
    parts = name.split("_", 5)             # 앞 5토큰만 분리, 나머지는 통째로
    if len(parts) < 6:
        return ""
    rest = parts[5]                        # "{상호명}_{seq}"
    # 뒤의 _{seq} 는 seq 가 숫자일 때만 제거 (상호명 끝 토큰 훼손 방지)
    head, sep, tail = rest.rpartition("_")
    place = head if (sep and tail.isdigit()) else rest
    return place.strip()


def pass_triples(tag):
    """트리플 스캔 -> {poi: {필드...}} 반환 + 스킵 통계."""
    store = {}
    stats = {"files": 0, "file_fail": 0, "triple_total": 0,
             "skip_len": 0, "skip_relation": 0, "skip_value": 0, "used": 0}

    folders = sorted(glob.glob(str(RAW / SPLITS[tag] / f"{tag}_트리플*")))
    for fol in folders:
        area = area_from_folder(Path(fol).name)
        for path in sorted(glob.glob(fol + "/*.json")):
            stats["files"] += 1
            d = load_json(path)
            if d is None:
                stats["file_fail"] += 1
                continue

            place_fn = place_from_filename(path)   # 파일명에서 상호명 (쉼표 상호도 온전)

            for t in d.get("triples", []):
                stats["triple_total"] += 1
                poi = t.get("POI_id")
                tr = t.get("triple", [])

                # 방어 3) 길이 != 3 스킵 (쉼표 상호명으로 깨진 줄)
                if not poi or len(tr) != 3:
                    stats["skip_len"] += 1
                    continue

                rel, val = tr[1].strip(), clean(tr[2])

                rec = store.setdefault(poi, {"area": area, "place": ""})
                # place: 파일명에서 뽑은 상호명을 최초 1회 채움
                if not rec["place"] and place_fn:
                    rec["place"] = place_fn

                # 방어 4) 관계 화이트리스트
                field = FACT_RELATIONS.get(rel)
                if field is None:
                    stats["skip_relation"] += 1
                    continue
                # 방어 6) 빈값/알수없음 스킵
                if val in SKIP_VALUES:
                    stats["skip_value"] += 1
                    continue

                if field == "menu":
                    # 메뉴만 여러 값 누적 (식당당 서로 다른 메뉴 트리플 존재, 0.4%).
                    # 재료 태깅에 쓸 텍스트라 최대한 모은다. 중복은 제거.
                    bucket = rec.setdefault("_menu_set", [])
                    if val not in bucket:
                        bucket.append(val)
                        stats["used"] += 1
                elif field not in rec:    # 그 외는 첫 값만 (dedup)
                    rec[field] = val
                    stats["used"] += 1

    # 누적된 메뉴를 아이템 단위로 중복 제거하며 합침
    for rec in store.values():
        if "_menu_set" in rec:
            items = []
            for val in rec.pop("_menu_set"):
                for m in val.split(", "):
                    m = m.strip()
                    if m and m not in items:
                        items.append(m)
            rec["menu"] = ", ".join(items)

    return store, stats


def extract_qa_facts(d):
    """QA annotations 에서 필드별 첫 유효답변 추출."""
    facts = {}
    for ann in d.get("annotations", []):
        for q in ann.get("question", []):
            qt = q.get("question", "")
            ans = clean(q.get("answer", ""))
            if ans in SKIP_VALUES:
                continue
            # 복합질문 방어: 주제어가 2개 이상이면 어느 필드 답인지 모호 → 스킵
            hits = [field for kw, field in QA_QUESTION_MAP if kw in qt]
            if len(set(hits)) != 1:
                continue
            field = hits[0]
            if field not in facts:
                facts[field] = ans
    return facts


def pass_qa(tag, store):
    """QA 스캔 -> store 에 좌표/place/area 채우고 빠진 필드 보완."""
    stats = {"files": 0, "file_fail": 0, "qa_only_new": 0, "coords_filled": 0}

    folders = sorted(glob.glob(str(RAW / SPLITS[tag] / f"{tag}_QA*")))
    for fol in folders:
        for path in sorted(glob.glob(fol + "/*.json")):
            stats["files"] += 1
            d = load_json(path)
            if d is None:
                stats["file_fail"] += 1
                continue

            meta = d.get("data", {})
            poi = meta.get("POI_id")
            if not poi:
                continue

            rec = store.get(poi)
            if rec is None:                       # QA 에만 있는 식당
                rec = {"area": "", "place": ""}
                store[poi] = rec
                stats["qa_only_new"] += 1

            # place / area 는 QA 값이 깨끗하므로 우선 반영
            if meta.get("place"):
                rec["place"] = clean(meta["place"])
            if meta.get("area"):
                rec["area"] = clean(meta["area"])

            # 좌표 (QA 에만 존재). 유효한 mapx/mapy 나올 때까지 imageInfo 순회.
            # 원본 mapx=위도, mapy=경도 → lat/lng 로 저장.
            # 무효값 방어: 0/비수치 제외, 한국 범위(위도 33~39, 경도 124~132) 안만 채택.
            if "lat" not in rec:
                for img in d.get("imageInfo", []):
                    x, y = img.get("mapx"), img.get("mapy")
                    if (isinstance(x, (int, float)) and isinstance(y, (int, float))
                            and 33 <= x <= 39 and 124 <= y <= 132):
                        rec["lat"] = x
                        rec["lng"] = y
                        stats["coords_filled"] += 1
                        break

            # 트리플에서 못 채운 필드 보완
            for field, val in extract_qa_facts(d).items():
                if field not in rec:
                    rec[field] = val

    return stats


FIELDS = ["poi_id", "place", "area", "lat", "lng",
          "menu", "address", "phone", "hours", "closed_days", "parking"]


def build_records(store):
    records = []
    for poi, rec in store.items():
        records.append({
            "poi_id": poi,
            "place": rec.get("place", ""),
            "area": rec.get("area", ""),
            "lat": rec.get("lat", ""),
            "lng": rec.get("lng", ""),
            "menu": rec.get("menu", ""),
            "address": rec.get("address", ""),
            "phone": rec.get("phone", ""),
            "hours": rec.get("hours", ""),
            "closed_days": rec.get("closed_days", ""),
            "parking": rec.get("parking", ""),
        })
    return records


def _first_nonempty(group, field):
    for r in group:
        v = r.get(field, "")
        if v not in ("", None):
            return v
    return ""


def _best_place(group):
    """대표 상호명 선택. 중복수록 접미사(' 2' 등 끝의 ' 숫자')가 없는 형제 이름을 우선.
    없는 이름을 만들지 않고, 그룹에 실제로 존재하는 이름 중에서만 고른다.
    우선순위: (접미사X & 좌표O) > (접미사X) > (좌표O) > 첫 값."""
    def clean_name(r):
        return re.search(r"\s\d+$", r["place"].strip()) is None
    for r in group:
        if clean_name(r) and r.get("lat", "") != "":
            return r["place"]
    for r in group:
        if clean_name(r):
            return r["place"]
    for r in group:
        if r.get("lat", "") != "":
            return r["place"]
    return group[0]["place"]


def _union_menu(group):
    """여러 레코드 메뉴를 아이템 단위 중복 제거하며 합침 (순서 보존)."""
    menus = []
    for r in group:
        for m in (r.get("menu", "") or "").split(", "):
            m = m.strip()
            if m and m not in menus:
                menus.append(m)
    return ", ".join(menus)


def merge_group(group):
    """중복 레코드(같은 식당)들을 하나로 병합. 정보 손실 없이 union."""
    # 키 순서를 build_records(FIELDS)와 동일하게 유지 (JSON 컬럼순서 일관성)
    merged = {
        # 추적용으로 모든 poi_id 보존 (|구분). DB PK 로도 유일.
        "poi_id": "|".join(sorted(r["poi_id"] for r in group)),
        "place": _best_place(group),
        "area": _first_nonempty(group, "area"),
        "lat": _first_nonempty(group, "lat"),
        "lng": _first_nonempty(group, "lng"),
        "menu": _union_menu(group),
        "address": _first_nonempty(group, "address"),
        "phone": _first_nonempty(group, "phone"),
        "hours": _first_nonempty(group, "hours"),
        "closed_days": _first_nonempty(group, "closed_days"),
        "parking": _first_nonempty(group, "parking"),
    }
    return merged


def _norm_phone(p):
    """전화번호에서 숫자만 남김 (구분자 표기 차이 흡수)."""
    return re.sub(r"\D", "", p or "")


def _merge_by_key(records, keyfunc):
    """keyfunc 로 그룹핑해 병합. key 가 None 이면 개별 유지."""
    groups = {}
    singles = []
    for r in records:
        k = keyfunc(r)
        if k is None:
            singles.append(r)
        else:
            groups.setdefault(k, []).append(r)
    out, dgroups, extra = [], 0, 0
    for grp in groups.values():
        if len(grp) == 1:
            out.append(grp[0])
        else:
            out.append(merge_group(grp))
            dgroups += 1
            extra += len(grp) - 1
    return out + singles, dgroups, extra


def reconcile_duplicates(records):
    """같은 식당이 여러 POI_id/이름변형으로 존재하는 문제를 2단계로 병합.
    A) (place, address) 정확히 동일 → 명백한 이중 POI_id 병합
    B) (address, 숫자전화) 동일 → 상호명 표기만 다른 쌍 병합
       (예: '본죽 광주송정점' vs '본죽 광주송정점 2', '보해식육식당' vs '보해식당')
    address(또는 전화) 없으면 확신 불가 → 개별 유지.
    반환: (레코드, 병합그룹수, 제거된 잉여행수)."""
    def key_a(r):
        p, a = r["place"].strip(), (r["address"] or "").strip()
        return (p, a) if p and a else None
    records, ga, ea = _merge_by_key(records, key_a)

    def key_b(r):
        a, ph = (r["address"] or "").strip(), _norm_phone(r.get("phone"))
        return (a, ph) if a and ph else None
    records, gb, eb = _merge_by_key(records, key_b)

    return records, ga + gb, ea + eb


def save(tag, records):
    OUT.mkdir(parents=True, exist_ok=True)
    DEBUG.mkdir(parents=True, exist_ok=True)

    (OUT / f"ba01_{tag}_merged.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    with open(OUT / f"ba01_{tag}_merged.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(records)


def run():
    report = []
    def log(s):
        print(s)
        report.append(str(s))

    for tag in ("TL", "VL"):
        log(f"\n{'='*50}\n[{tag}] 병합 시작\n{'='*50}")

        store, tstats = pass_triples(tag)
        log(f"[트리플] 파일 {tstats['files']} (읽기실패 {tstats['file_fail']})")
        log(f"[트리플] 전체 triple {tstats['triple_total']}")
        log(f"[트리플] 깨진 줄 스킵(길이!=3): {tstats['skip_len']}")
        log(f"[트리플] 관계 화이트리스트 외 무시: {tstats['skip_relation']}")
        log(f"[트리플] 빈값/알수없음 스킵: {tstats['skip_value']}")
        log(f"[트리플] 채운 사실값: {tstats['used']}")
        log(f"[트리플] 고유 식당(POI): {len(store)}")

        qstats = pass_qa(tag, store)
        log(f"[QA] 파일 {qstats['files']} (읽기실패 {qstats['file_fail']})")
        log(f"[QA] QA에만 있던 신규 식당 추가: {qstats['qa_only_new']}")
        log(f"[QA] 좌표 채운 식당: {qstats['coords_filled']}")

        records = build_records(store)
        log(f"[병합전] POI 기준 행 수: {len(records)}")

        # 중복 식당 병합 (같은 식당이 두 POI_id 로 존재)
        records, dup_groups, extra_removed = reconcile_duplicates(records)
        log(f"[중복병합] 병합한 그룹: {dup_groups}, 제거된 잉여행: {extra_removed}")

        if not records:                       # 방어: 빈 split
            log(f"[경고] {tag}: 레코드 0건 — 원본 폴더/글롭 확인 필요. 스킵.")
            continue

        with_coords = sum(1 for r in records if r["lat"] != "")
        with_menu = sum(1 for r in records if r["menu"] != "")
        log(f"[결과] 최종 식당 수: {len(records)}")
        log(f"[결과] 좌표 있는 식당: {with_coords} ({with_coords/len(records)*100:.1f}%)")
        log(f"[결과] 메뉴 있는 식당: {with_menu} ({with_menu/len(records)*100:.1f}%)")

        save(tag, records)
        log(f"[저장] data/processed/ba01/ba01_{tag}_merged.json / .csv")

    (DEBUG).mkdir(parents=True, exist_ok=True)
    (DEBUG / "merge_report.txt").write_text("\n".join(report), encoding="utf-8")
    print(f"\n리포트 저장: data/processed/ba01/debug/merge_report.txt")


if __name__ == "__main__":
    run()
