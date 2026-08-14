# namdo.sqlite 스키마 특이사항

`aicoss-hackathon-2026/minseo/data/processed/namdo.sqlite`를 직접 조회해서 확인한 내용입니다.
Pydantic 모델(`app/models.py`)이나 다른 코드에서 이 DB 값을 다룰 때 참고해주세요.

## restaurants 테이블

- `local_score`: 타입이 `INTEGER`이고 실제 값도 `0`, `1` 같은 정수입니다. `float`이 아니라 `int`로 다뤄야 합니다.
- `parking`: 컬럼이 1개이며, 값은 `"있음"` / `"없음"` 같은 한글 텍스트입니다. `"Y"/"N"`이 아니므로 bool로 변환하려면 `"있음" -> True` 매핑이 필요합니다. (참고: `markets` 테이블의 `parking_p02`/`parking_p03`은 컬럼이 2개이고 값이 `"Y"/"N"`이라 서로 형식이 다릅니다.)

## seasonality 테이블

- `peak_months`: 타입이 `TEXT`입니다. 값이 `[10, 11, 12]`처럼 리스트처럼 보이지만 실제로는 **JSON 문자열**입니다. SQLite에는 배열 타입이 없어서 JSON으로 직렬화해 저장한 것으로 보입니다. 파이썬 리스트로 쓰려면 `json.loads(row["peak_months"])`로 파싱해야 합니다.
- `trend_12m`도 동일하게 JSON 문자열(월별 가격 리스트)이라 `json.loads`가 필요합니다.
- `level`은 `"저렴"/"평균"/"비쌈"` 같은 한글 카테고리 텍스트입니다.

## nutrition 테이블

- 숫자 컬럼(`magnesium_mg` 등) 중 일부는 값이 비어 `None`으로 조회될 수 있습니다.

## markets 테이블

- `num_stores`: 값이 `49`처럼 숫자로 보이지만 컬럼 타입이 `TEXT`라서 조회하면 문자열 `'49'`로 나옵니다. 숫자로 써야 하면 `int(row["num_stores"])` 변환이 필요합니다.
