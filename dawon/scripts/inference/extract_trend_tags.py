"""
extract_trend_tags.py

향토음식 SNS 리뷰 텍스트에서 속성별(맛/가격/양/서비스...) 트렌드 태그를 뽑아낸다.

구조:
    1. 문장 분리 (간단한 규칙 기반. 정확도가 더 필요하면 kss 라이브러리로 교체 가능)
    2. food_aspect_keywords.json의 키워드로 문장 -> 속성 매칭 (한 문장이 여러 속성에 매칭될 수 있음)
    3. 매칭된 문장을 polarity_fn(문서 단위로 학습된 KcELECTRA 극성 분류기)에 넣어 문장 단위 극성 추론
    4. 속성별로 긍/부정 집계 -> 트렌드 태그 생성 (예: "가격 호평 다수", "웨이팅 불만 존재")

지금은 polarity_fn이 자리표시자(placeholder)다. prepare_polarity_dataset.py로 만든 데이터로
KcELECTRA를 파인튜닝한 뒤, 그 모델의 predict 함수를 polarity_fn 자리에 넣어 교체하면 된다.

사용법:
    python extract_trend_tags.py --keywords food_aspect_keywords.json --text "그 집 국밥 진짜 맛있고 가격도 착해요. 근데 주차가 너무 힘들어요."
"""

import argparse
import json
import re
from collections import defaultdict
from typing import Callable, Dict, List

LABEL_NAMES = {0: "부정", 1: "중립", 2: "긍정"}

# 문장 분리용 종결 어미 패턴 (간이 버전).
# 정확도가 중요하면 `pip install kss` 로 한국어 전용 문장 분리기를 쓰는 걸 권장.
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?…])\s+|\n+")


def split_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    parts = _SENT_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def load_keywords(path: str) -> Dict[str, List[str]]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def match_aspects(sentence: str, keywords: Dict[str, List[str]]) -> List[str]:
    matched = []
    for aspect, words in keywords.items():
        if any(w in sentence for w in words):
            matched.append(aspect)
    return matched


def placeholder_polarity_fn(sentence: str) -> int:
    """임시 극성 분류기. 아주 단순한 사전 기반 판정이며 실제 KcELECTRA 모델로 교체할 것.
    반환값: 0=부정, 1=중립, 2=긍정"""
    pos_words = ["좋", "맛있", "만족", "추천", "친절", "저렴", "깨끗", "신선", "푸짐", "재방문", "강추"]
    neg_words = ["별로", "실망", "불친절", "비싸", "더러", "냄새나", "부족", "불만", "비추", "웨이팅 힘들"]
    pos_hit = any(w in sentence for w in pos_words)
    neg_hit = any(w in sentence for w in neg_words)
    if pos_hit and not neg_hit:
        return 2
    if neg_hit and not pos_hit:
        return 0
    return 1


def load_kcelectra_polarity_fn(model_dir: str):
    """train_polarity_classifier.py로 파인튜닝한 실제 KcELECTRA 모델을 로드해서,
    placeholder_polarity_fn과 똑같은 시그니처(문장 str -> 0/1/2)를 가진 함수를 반환한다.

    model_dir 예: './kcelectra-polarity/best_model'
    """
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.eval()

    device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    def predict(sentence: str) -> int:
        inputs = tokenizer(sentence, truncation=True, max_length=256, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(**inputs).logits
        return int(torch.argmax(logits, dim=-1).item())

    return predict


def extract_trend_tags(
    text: str,
    keywords: Dict[str, List[str]],
    polarity_fn: Callable[[str], int] = placeholder_polarity_fn,
) -> Dict[str, dict]:
    """리뷰 원문 -> {속성: {긍정: n, 중립: n, 부정: n, sentences: [...]}} 형태로 반환."""
    result = defaultdict(lambda: {"긍정": 0, "중립": 0, "부정": 0, "sentences": []})

    for sentence in split_sentences(text):
        aspects = match_aspects(sentence, keywords)
        if not aspects:
            continue
        polarity = polarity_fn(sentence)
        for aspect in aspects:
            result[aspect][LABEL_NAMES[polarity]] += 1
            result[aspect]["sentences"].append({"text": sentence, "polarity": LABEL_NAMES[polarity]})

    return dict(result)


def summarize_tags(aspect_scores: Dict[str, dict], min_mentions: int = 1) -> List[str]:
    """집계 결과를 사람이 읽을 수 있는 트렌드 태그 문자열로 변환.
    예: '가격 호평 다수', '웨이팅 불만 존재'"""
    tags = []
    for aspect, scores in aspect_scores.items():
        total = scores["긍정"] + scores["중립"] + scores["부정"]
        if total < min_mentions:
            continue
        if scores["긍정"] > scores["부정"] * 2:
            tags.append(f"{aspect} 호평 다수 ({scores['긍정']}건)")
        elif scores["부정"] > scores["긍정"]:
            tags.append(f"{aspect} 불만 존재 ({scores['부정']}건)")
        elif scores["긍정"] > 0:
            tags.append(f"{aspect} 언급 ({total}건, 대체로 긍정)")
    return tags


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keywords", default="food_aspect_keywords.json")
    ap.add_argument("--text", required=True, help="분석할 리뷰 원문")
    ap.add_argument(
        "--model_dir",
        default=None,
        help="파인튜닝된 KcELECTRA 모델 경로 (예: ./kcelectra-polarity/best_model). "
        "지정하면 placeholder 대신 실제 모델로 극성을 판정한다.",
    )
    args = ap.parse_args()

    keywords = load_keywords(args.keywords)

    if args.model_dir:
        print(f"[정보] 실제 모델 사용: {args.model_dir}")
        polarity_fn = load_kcelectra_polarity_fn(args.model_dir)
    else:
        print("[정보] placeholder(사전 기반) 극성 판정 사용 중 — 정확한 결과를 원하면 --model_dir로 학습된 모델을 지정하세요.")
        polarity_fn = placeholder_polarity_fn

    scores = extract_trend_tags(args.text, keywords, polarity_fn=polarity_fn)

    print("=== 속성별 집계 ===")
    for aspect, s in scores.items():
        print(f"{aspect}: 긍정 {s['긍정']} / 중립 {s['중립']} / 부정 {s['부정']}")

    print("\n=== 트렌드 태그 ===")
    for tag in summarize_tags(scores):
        print(f"- {tag}")


if __name__ == "__main__":
    main()