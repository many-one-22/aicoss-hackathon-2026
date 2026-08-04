# -*- coding: utf-8 -*-
"""
광주·전남 향토음식점 후보 필터링 전처리 파이프라인
====================================================
입력 : TL_2.관광서비스_2.음식점_1.음식  (관광 특화 말뭉치, JSON 86,584개)
동작 :
  1) 전체 JSON 스캔 → 주소/음식점명/전화/설명 추출
  2) 주소 기준으로 '광주광역시' / '전라남도(전남)' 만 필터
  3) 유명 프랜차이즈(체인) + 카페 + 베이커리 + 주점 제외
  4) 남은 것 = 향토음식점 후보
출력 : (같은 폴더)
  - 광주전남_음식점_전처리결과.csv   (필터·분류된 전체 레코드, 파일 단위)
  - 광주전남_향토음식점_후보.csv     (향토음식점 후보만, 음식점 단위 중복제거)
  - 필터링_결과요약.md               (요약 표 리포트)
실행 : py preprocess.py
"""
import os, json, re, csv, collections

# --------------------------------------------------------------------------
# 경로
# --------------------------------------------------------------------------
DATA_DIR = r"D:\Hack\TL_2.관광서비스_2.음식점_1.음식\TL_2.관광서비스_2.음식점_1.음식"
OUT_DIR  = r"D:\Hack\전처리_결과"
os.makedirs(OUT_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# 1. 지역 판별
# --------------------------------------------------------------------------
# 전남 22개 시·군
JN_CITY = {"목포시","여수시","순천시","나주시","광양시","담양군","곡성군","구례군",
           "고흥군","보성군","화순군","장흥군","강진군","해남군","영암군","무안군",
           "함평군","영광군","장성군","완도군","진도군","신안군"}

def get_address(d):
    """JSON 문서에서 주소(AD) 문장을 찾아 주소 문자열을 반환."""
    try:
        for s in d["docu_info"]["sentences"]:
            txt = s.get("sentence", "")
            if txt.startswith("주소"):
                idx = txt.find(")")
                if idx != -1:
                    return txt[idx + 1:].strip()
    except Exception:
        pass
    # 예비: contains 원문에서 정규식 추출
    try:
        c = d["docu_info"]["contains"]
        m = re.search(r"주소\(AD\)\s*(.*?)(?:용어\(|전화번호\(|시간\(|부대정보\(|$)", c)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""

def region_of(addr):
    """주소 첫 토큰으로 광주/전남 판별. 해당 없으면 None (경기 광주시 등은 제외)."""
    if not addr:
        return None
    t = addr.split()
    if not t:
        return None
    first = t[0]
    if first.startswith("광주광역"):
        return "광주"
    if first == "광주":                 # '광주 서구 ...' (광역시). '광주시'(경기)는 제외됨
        return "광주"
    if first in ("전라남도", "전남"):
        return "전남"
    if first in JN_CITY:                # '여수시 ...' 처럼 시·군 단독 표기
        return "전남"
    return None

def sigungu_of(addr, region):
    """주소에서 시·군·구 추출 (둘째 토큰)."""
    t = addr.split()
    if len(t) >= 2:
        # '광주광역시 광산구' / '전남 여수시' / '전라남도 순천시'
        if t[0] in ("광주광역시", "광주", "전남", "전라남도"):
            return t[1]
        # 시·군 단독표기면 첫 토큰이 곧 시·군
        if t[0] in JN_CITY:
            return t[0]
    return t[0] if t else ""

# --------------------------------------------------------------------------
# 2. 분류용 키워드
# --------------------------------------------------------------------------
# (a) 유명 프랜차이즈/체인 — 이름에 브랜드가 포함되면 제외
CHAIN = [
    # 버거·패스트푸드
    "맥도날드","롯데리아","버거킹","케이에프씨","kfc","맘스터치","서브웨이",
    "노브랜드버거","프랭크버거","모스버거","파파이스",
    # 커피·카페 체인
    "스타벅스","투썸","이디야","메가커피","메가엠지씨","메가mgc","megamgc","빽다방",
    "컴포즈","매머드","커피빈","폴바셋","할리스","엔제리너스","탐앤탐스","파스쿠찌",
    "요거프레소","더벤티","감성커피","커피에반하다","하삼동","벤티프레소","텐퍼센트",
    "백억커피","더리터","카페베네","셀렉토","토프레소","드롭탑","달콤커피","공차","쥬씨",
    "매머드커피","커피명가","더카페","이삭토스트",
    # 베이커리·도넛 체인
    "파리바게","뚜레쥬르","던킨","베스킨라빈스","배스킨라빈스","브레댄코","성심당? ".strip(),
    # 치킨 체인
    "교촌","bbq","비비큐","bhc","굽네","네네치킨","페리카나","처갓집","자담치킨",
    "60계","노랑통닭","호식이","또래오래","멕시카나","지코바","푸라닭","치킨플러스",
    # 피자 체인
    "도미노","피자헛","미스터피자","파파존스","피자스쿨","피자마루","오구쌀피자",
    "피자알볼로","반올림피자","유로코피자","피자나라",
    # 한식·분식·기타 프랜차이즈
    "김밥천국","김가네","김밥나라","한솥","본죽","죽이야기","명륜진사갈비","새마을식당","한신포차",
    "원할머니보쌈","놀부","신전떡볶이","죠스떡볶이","엽기떡볶이","국대떡볶이","스쿨푸드",
    "국수나무","채선당","애슐리","빕스","아웃백","매드포갈릭","유가네","역전우동",
    "큰맘할매순대국","봉구스","본도시락","하남돼지집","고봉민김밥","한촌설렁탕",
    # 지역·중소 프랜차이즈 (검증 과정에서 후보에 다수 잔존 → 추가)
    "투다리","두찜","써브웨이","명랑핫도그","얌샘","이바돔","감탄떡볶이","또봉이",
    "부어치킨","서가앤쿡","티바두마리","바르다김선생","봉추찜닭","연안식당","포베이",
    "라라코스트","맥시칸","멕시칸","난타5000","청년피자","7번가피자","바른치킨",
    "걸작떡볶이","탕화쿵푸","역전할머니","가마로강정","조가네갈비",
]
CHAIN = [c.lower() for c in CHAIN if c and "?" not in c]

# (b) 카페
CAFE_NAME = ["카페","까페","커피","coffee","cafe","로스터","브루","찻집","다방","다원",
             "티하우스","티룸","에스프레소","라운지"]
# (c) 베이커리·제과
BAKERY_NAME = ["베이커리","제과","제빵","빵","브레드","케이크","케익","도넛","도너츠",
               "파티세리","과자","페이스트리","마카롱","크로플","도나스"]
# (d) 주점·술집
PUB_NAME = ["주점","포차","포장마차","호프","펍"," bar","와인바","칵테일","이자카야",
            "술집","맥주","비어","선술집","요리주점","와인","막걸리집","전통주점"]

# (e) 향토·한식 음식점(후보) 신호 — 이름에 있으면 카페/설명보다 우선
MEAL_NAME = [
    "식당","한정식","정식","백반","밥집","국밥","국수","칼국수","수제비","막국수",
    "회센타","회센터","회집","횟집","수산","활어","물회","해물","해산물","조개",
    "갈비","불고기","삼겹","곱창","막창","대창","숯불","고깃집","정육","한우","떡갈비",
    "낙지","홍어","장어","붕장어","아구","아귀","복국","매운탕","지리","해장","게장",
    "보쌈","족발","순대","곰탕","설렁탕","추어탕","육개장","감자탕","뼈다귀","해장국",
    "냉면","만두","분식","떡볶이","김밥","찌개","전골","두부","순두부","청국장",
    "쌈밥","비빔밥","보리밥","오리","삼계","백숙","닭","짬뽕","반점","중화","중국집",
    "초밥","스시","돈까스","돈가스","우동","라멘","라면","파스타","스테이크","뷔페","부페",
    "한상","밥상","정찬","남도","향토","맛집","food","kitchen","다이닝","전복","굴",
    "매생이","꼬막","주꾸미","쭈꾸미","대게","꽃게","갈치","전어","짱뚱어","세발낙지",
    "연포탕","한식","가든","별미","먹거리","기사식당","맘마","솥밥","백종원? ".strip(),
]
MEAL_NAME = [m for m in MEAL_NAME if m and "?" not in m]

# 설명(본문) 기반 신호
CAFE_DESC   = ["카페","커피","디저트","브런치","라떼","아메리카노","에스프레소","베이커리","빙수"]
BAKERY_DESC = ["베이커리","제과","빵","케이크","도넛","파티세리","페이스트리"]
PUB_DESC    = ["주점","포차","호프","술집","이자카야","안주","막걸리","칵테일","와인바"]
MEAL_DESC   = ["맛집","식당","한정식","백반","국밥","한식","향토","음식점","정식","횟집","맛있"]

def has_any(text, kws):
    return any(k in text for k in kws)

def classify(name, desc):
    """반환: (분류, 제외여부, 제외사유)
    분류 ∈ {체인, 카페, 베이커리, 주점, 향토음식점}"""
    low  = name.lower()
    dlow = desc.lower()

    # 1) 체인 (최우선 제외)
    for c in CHAIN:
        if c in low:
            return "체인", True, f"유명체인점({c})"

    # 2) 이름에 명확한 식사 메뉴 신호 → 향토음식점 (카페 오분류 방지)
    name_meal  = has_any(name, MEAL_NAME)
    name_cafe  = has_any(low, [k.lower() for k in CAFE_NAME])
    name_bake  = has_any(name, BAKERY_NAME)
    name_pub   = has_any(low, [k.lower() for k in PUB_NAME])

    if name_meal and not (name_cafe or name_bake):
        return "향토음식점", False, ""

    # 3) 이름 기반 카페/베이커리/주점
    if name_cafe:
        return "카페", True, "카페"
    if name_bake:
        return "베이커리", True, "베이커리/제과"
    if name_pub:
        return "주점", True, "주점/술집"

    # 4) 이름이 모호 → 설명(본문)으로 판별
    cafe_score = sum(dlow.count(k) for k in CAFE_DESC)
    bake_score = sum(desc.count(k) for k in BAKERY_DESC)
    pub_score  = sum(desc.count(k) for k in PUB_DESC)
    meal_score = sum(desc.count(k) for k in MEAL_DESC)

    if cafe_score >= 2 and cafe_score > meal_score:
        return "카페", True, "카페(본문판별)"
    if bake_score >= 2 and bake_score > meal_score:
        return "베이커리", True, "베이커리/제과(본문판별)"
    if pub_score >= 2 and pub_score > meal_score:
        return "주점", True, "주점/술집(본문판별)"

    # 5) 그 외 → 향토음식점 후보(기본값)
    return "향토음식점", False, ""

# --------------------------------------------------------------------------
# 3. 전체 스캔
# --------------------------------------------------------------------------
def short_desc(d):
    """설명 앞부분(개요) 일부를 요약용으로."""
    try:
        c = d["docu_info"]["contains"]
        m = re.search(r"개요\s*(.*?)(?:주소\(AD\)|$)", c)
        seg = (m.group(1) if m else c).strip()
        return seg[:120]
    except Exception:
        return ""

rows = []                     # 광주/전남 전체 레코드
total_files = 0
parse_fail  = 0

with os.scandir(DATA_DIR) as it:
    for e in it:
        if not e.name.lower().endswith(".json"):
            continue
        total_files += 1
        try:
            with open(e.path, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            parse_fail += 1
            continue

        addr = get_address(d)
        region = region_of(addr)
        if region is None:
            continue

        ti   = d.get("tour_info", {})
        name = (ti.get("Tourist Spot") or d.get("docu_info", {}).get("content") or "").strip()
        src  = ti.get("source", "")
        try:
            desc = d["docu_info"]["contains"]
        except Exception:
            desc = ""
        # 전화번호
        tel = ""
        m = re.search(r"(\d{2,4}-\d{3,4}-\d{4})", desc)
        if m:
            tel = m.group(1)

        cate, excluded, reason = classify(name, desc)
        rows.append({
            "파일명": e.name,
            "source": src,
            "지역": region,
            "시군구": sigungu_of(addr, region),
            "음식점명": name,
            "주소": addr,
            "전화번호": tel,
            "분류": cate,
            "제외여부": "제외" if excluded else "후보",
            "제외사유": reason,
            "설명": short_desc(d),
        })

# --------------------------------------------------------------------------
# 4. 집계
# --------------------------------------------------------------------------
def cnt(pred):
    return sum(1 for r in rows if pred(r))

gj_total = cnt(lambda r: r["지역"] == "광주")
jn_total = cnt(lambda r: r["지역"] == "전남")
region_total = gj_total + jn_total

def cand(r):    return r["제외여부"] == "후보"
gj_cand = cnt(lambda r: r["지역"] == "광주" and cand(r))
jn_cand = cnt(lambda r: r["지역"] == "전남" and cand(r))
cand_total = gj_cand + jn_cand

# 제외 사유별
by_cate = collections.Counter(r["분류"] for r in rows if r["제외여부"] == "제외")
excluded_total = region_total - cand_total

# 향토음식점 후보 중복제거 (음식점 단위 = 이름+주소)
seen = set()
cand_rows_dedup = []
for r in rows:
    if not cand(r):
        continue
    key = (r["지역"], r["음식점명"], r["주소"])
    if key in seen:
        continue
    seen.add(key)
    cand_rows_dedup.append(r)
cand_dedup_total = len(cand_rows_dedup)
gj_cand_dedup = sum(1 for r in cand_rows_dedup if r["지역"] == "광주")
jn_cand_dedup = sum(1 for r in cand_rows_dedup if r["지역"] == "전남")

# --------------------------------------------------------------------------
# 5. 출력 파일
# --------------------------------------------------------------------------
def write_csv(path, fieldnames, data):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)

# (1) 전처리 결과 전체 (파일 단위)
write_csv(os.path.join(OUT_DIR, "광주전남_음식점_전처리결과.csv"),
          ["파일명","source","지역","시군구","음식점명","주소","전화번호","분류","제외여부","제외사유","설명"],
          rows)

# (2) 향토음식점 후보 (음식점 단위 중복제거)
write_csv(os.path.join(OUT_DIR, "광주전남_향토음식점_후보.csv"),
          ["지역","시군구","음식점명","주소","전화번호","설명"],
          cand_rows_dedup)

# (3) 요약 리포트
region_by_sgg = collections.Counter((r["지역"], r["시군구"]) for r in cand_rows_dedup)
summary = []
summary.append("# 광주·전남 향토음식점 필터링 결과 요약\n")
summary.append(f"- 데이터셋: 관광 특화 말뭉치(음식점) JSON `{total_files:,}`개 전체 스캔")
summary.append(f"- 대상 지역: **광주광역시 · 전라남도** (주소 기준)")
summary.append(f"- 제외 대상: 유명 프랜차이즈(버거킹·롯데리아·메가커피 등) + 카페 + 베이커리 + 주점\n")

summary.append("## 필터링 결과 (파일 단위)\n")
summary.append("| 항목 | 수치 |")
summary.append("| --- | --- |")
summary.append(f"| 전체 스캔 | {total_files:,}개 파일 (전국 전체) |")
summary.append(f"| 광주·전남 추출 | **{region_total:,}개** (광주 {gj_total:,} + 전남 {jn_total:,}) |")
summary.append(f"| 향토음식점 후보 | **{cand_total:,}개** (광주 {gj_cand:,} + 전남 {jn_cand:,}) |")
summary.append(f"| 제외 | 약 {excluded_total:,}개 (카페·베이커리·주점·유명체인 등) |\n")

summary.append("## 제외 내역 (파일 단위)\n")
summary.append("| 제외 분류 | 수치 |")
summary.append("| --- | --- |")
for c in ["체인","카페","베이커리","주점"]:
    summary.append(f"| {c} | {by_cate.get(c,0):,}개 |")
summary.append(f"| **제외 합계** | **{excluded_total:,}개** |\n")

summary.append("## 향토음식점 후보 (음식점 단위, 중복제거)\n")
summary.append("| 항목 | 수치 |")
summary.append("| --- | --- |")
summary.append(f"| 후보 음식점 수 | **{cand_dedup_total:,}곳** (광주 {gj_cand_dedup:,} + 전남 {jn_cand_dedup:,}) |\n")

summary.append("### 시·군·구별 향토음식점 후보 분포 (상위 25)\n")
summary.append("| 지역 | 시군구 | 후보 수 |")
summary.append("| --- | --- | --- |")
for (reg, sgg), c in region_by_sgg.most_common(25):
    summary.append(f"| {reg} | {sgg} | {c:,} |")
summary.append("")
summary.append("---")
summary.append("### 산출물")
summary.append("- `preprocess.py` — 전처리·필터링 코드")
summary.append("- `광주전남_음식점_전처리결과.csv` — 광주·전남 전체 레코드(분류·제외사유 포함, 파일 단위)")
summary.append("- `광주전남_향토음식점_후보.csv` — 향토음식점 후보(음식점 단위 중복제거)")
summary.append(f"\n> 참고: JSON 파싱 실패/주소없음 등으로 지역 판별에서 빠진 파일이 있으며, "
               f"'전체 스캔'은 전국 전체 파일 수입니다.")

with open(os.path.join(OUT_DIR, "필터링_결과요약.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(summary))

# --------------------------------------------------------------------------
# 6. 콘솔 요약
# --------------------------------------------------------------------------
print("="*60)
print(f"전체 스캔 파일        : {total_files:,}  (파싱실패 {parse_fail:,})")
print(f"광주+전남 추출(파일)  : {region_total:,}  (광주 {gj_total:,} / 전남 {jn_total:,})")
print(f"향토음식점 후보(파일) : {cand_total:,}  (광주 {gj_cand:,} / 전남 {jn_cand:,})")
print(f"제외(파일)            : {excluded_total:,}  {dict(by_cate)}")
print(f"후보 음식점(중복제거) : {cand_dedup_total:,}  (광주 {gj_cand_dedup:,} / 전남 {jn_cand_dedup:,})")
print("="*60)
print("출력 폴더:", OUT_DIR)
