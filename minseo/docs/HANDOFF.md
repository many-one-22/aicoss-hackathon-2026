# 프로젝트 인수인계 (HANDOFF)

> 새 Claude 세션/다른 팀원이 이 문서만 읽고 이어서 작업할 수 있게 만든 인수인계서.
> 최종 갱신: 2026-08-03

---

## 0. 이 프로젝트가 뭔가

**남도 식탁 큐레이터 AI** — 2026 AICOSS 하계 해커톤 Track 2(지역 산업·상권·특산물).
광주·전남 **향토음식점을 추천**하고, 식재료 **영양·시세·제철**을 안내하는 서비스.

**⚠️ 절대 제약: 승인된 데이터(B-A01~A09, B-P01~P07)만 사용.** 외부 데이터·손수 만든 "리스트 데이터"는 금지. (단 짜장→중식 같은 **처리용 키워드 사전**은 허용 — 데이터 소스가 아니라 로직이므로.)

**담당 분담(태스크리스트 기준):** 민서=B-A01·B-A07·B-P01/P07 / 소희=B-A09 / 다원=B-A06 / 세은=B-P02·P03.
**이 문서는 민서 파트(B-A01·A07·P07)까지의 상태.**

---

## 1. 데이터 인벤토리 (뭘 받았나)

| 데이터 | 받음? | 위치 | 비고 |
|---|---|---|---|
| B-A01 (관광 KVQA, 식당) | ✅ | `B-A01/` (수십 GB 원본) | Train/Validation × QA·트리플·이미지캡셔닝 |
| B-A07 칼로리데이터셋 (영양) | ✅ | `B-A07/*.xlsx` | 400음식 영양표만. **이미지 200GB는 안 받음(안 씀)** |
| B-P07 (월별 농축수산물 소매가) | ✅ | `B-P07/*.csv` | 전국·2024·92품목 |
| B-P01 (KAMIS 농·수산 소매가) | ❌ | `B-P01/`(빈 폴더) | 웹만 탐색, 다운 안 함 |
| B-A09·B-P02·B-P03·B-A06 | ❌ | - | 다른 담당 |

**⚠️ 원본 대용량 폴더(B-A01/A07/P07/P01)는 `.gitignore`로 git 제외.** 파생 산출물(`Data/`)과 스크립트만 커밋.

---

## 2. 완료된 것

### ① B-A01 식당 데이터 — ✅ 완료
- `scripts/merge_ba01.py` → `Data/ba01/ba01_{TL,VL}_merged.*` (병합, 중복제거)
- `scripts/run_tags.py` (→ tag_cuisine/ingredient/local) → `Data/ba01/ba01_{TL,VL}_tagged.*`
- **결과: TL 25,275 / VL 4,370 식당, 14필드** (poi_id,place,area,lat,lng,menu,address,phone,hours,closed_days,parking,cuisine_type,ingredient_category,local_score)
- 태그: cuisine_type(한식16,098/카페7,227/치킨1,762/양식1,435/주점1,255/중식1,171/일식697) · ingredient_category(육류9,754/해산물6,185/채소2,995 멀티) · local_score(남도향토 ≥1점 2,398)
- 상세: `Data/ba01/README.md`

### ② B-A07 영양 데이터 — ✅ 완료
- `scripts/build_nutrition.py` → `Data/ba07/nutrition.{json,csv}` (400음식 × 영양16컬럼)
- 건강플래그 **안 만듦**(원본 수치만). Atwater 정합성 90% 검증됨.

### ③ B-P07 시세 파이프라인 — ✅ 구현+리뷰+수정 (feature 브랜치)
- 브랜치 `feature/price-pipeline` (main에 **아직 merge 안 함**)
- 모듈: `price_ingredients`(재료추출) → `build_price`(가격집계) → `price_seasonality`(제철) → `price_lookup`(조회), `run_price`(러너)
- `Data/price/`: ingredient_map.csv · price_monthly.csv(집계 984행/92품목) · seasonality.json
- **테스트 12개 통과** (`python -m pytest tests/ -v`)
- 조회 예: `lookup_menu("고등어조림, 배추김치", "광주")` → 재료별 현재시세·추이·제철, 시세없으면 전통시장 안내

---

## 3. 핵심 결정과 이유 (새 세션이 꼭 알아야)

- **필터링(삭제) 대신 태깅(라벨링)** — 향토키워드 없다고 식당 버리면 진짜 향토도 유실. 전부 적재하고 이름표만.
- **B-A07 이미지(200GB) 안 씀** — 이미지 인식 AI용. 우리는 텍스트(메뉴→영양) 기반. xlsx만 필요.
- **건강플래그 보류** — 저칼로리 임계값은 근거 없음. 나중에 **KDRIs(1일 권장량 대비 %)** 로 근거 있게. 식약처 기준은 가공식품용이라 한 끼엔 부적합.
- **시세는 B-P07 전국으로 먼저** — KAMIS(B-P01) 광주/순천은 나중에. 인터페이스 동일하게 두고 데이터만 추가하면 됨.
- **낙지·꼬막·홍어 시세는 어느 승인데이터에도 없음** — 남도 대표 수산인데 KAMIS/B-P07에 없음. 시세 대신 "전통시장 안내"로 우회.
- **육류(돼지·소·닭) 시세도 B-P07엔 없음** — 축산은 축평원(ekapepia)으로 이전됨. 데모는 수산·농산 요리로.
- **지역: 광주 + 순천(전남 대표)** — KAMIS 소매엔 전남 도시가 순천뿐(목포·여수 없음). 식당 데이터는 전남 전체 커버, 시세만 광주·순천.

---

## 4. 데이터 함정 (다시 안 밟게)

- **B-A01 이중 POI_id**: 같은 식당이 두 POI_id(18xxxx/42xxxx)로 중복. POI_id 단독 식별 금지 → (상호,주소)·(주소,전화) 병합.
- **트리플 BOM + 쉼표 상호명 깨짐**(AI-Hub 원본버그): utf-8-sig + 방어코드.
- **B-A07 마그네슘 65% 결측** → 마그네슘 지표는 쓰지 말 것. 복합요리 칼로리 소수 과대.
- **B-P07 한 품목 여러 행**(품종·등급·단위, 월 최대 7행): 그대로 쓰면 단위 섞임(고등어 마리+손). → build_price가 대표 단위 골라 월별 중앙값 집계.
- **키워드 substring 충돌**: 무→스무디/무침, 굴→굴비, 마라→고구마라떼, 오리→오리지날 등. 긴 키워드 우선 + 구간소비로 완화.

---

## 5. 실행 방법

```bash
# B-A01 (원본 바뀔 때만 merge, 평소엔 tags만)
python scripts/merge_ba01.py
python scripts/run_tags.py            # cuisine→ingredient→local 순서 필수

# B-A07
python scripts/build_nutrition.py

# 시세 (feature/price-pipeline 브랜치)
python scripts/run_price.py           # ingredients→price→seasonality
python -m pytest tests/ -v            # 12개 통과 확인
```

---

## 6. 남은 작업 (다음 할 것)

1. **시세 브랜치 merge** — `feature/price-pipeline` → main (superpowers:finishing-a-development-branch)
2. **KAMIS(B-P01) 광주/순천 실데이터 확보** — 수동 스냅샷 다운 → build_price에 KAMIS wide 파서 추가(인터페이스 동일). 제철 판정 신뢰도↑.
3. **Prophet 예측** (stretch) — 시세 stretch. 대표 품목 1개만 데모용.
4. **통합 DB 적재** — 식당(ba01) + 영양(ba07) + 시세(price)를 음식명·재료명·지역으로 연결. 1주차 산출물(음식DB, 가격시계열DB).
5. 팀 데이터 연계 — B-A09(산지 서술), B-P02/03(전통시장 위치)와 붙이기.

---

## 7. 상세 문서·기록 위치

- 시세 설계/계획: `Data/2026-08-03-price-pipeline-design.md`, `Data/2026-08-03-price-pipeline.md`
- B-A01 상세: `Data/ba01/README.md`
- 각 스크립트 상단 docstring에 처리 이유·주의 기록됨
- (이 세션 Claude의 메모리엔 ba01-dual-poi-id / ba01-pipeline-plan / ba07-nutrition 항목 있음 — 같은 계정이면 자동 로드)
