"""
train_polarity_classifier.py

prepare_polarity_dataset.py로 만든 train.jsonl / val.jsonl을 가지고
KcELECTRA(beomi/KcELECTRA-base)를 문서 단위 3-class(부정/중립/긍정) 감성 분류기로 파인튜닝한다.

라벨 불균형(긍정 73.5% vs 부정 9.8% 등) 대응을 위해 학습 데이터의 클래스 분포로부터
class weight를 자동 계산해서 가중 CrossEntropyLoss를 적용한다. (--no_class_weight로 끌 수 있음)

설치:
    pip install torch transformers scikit-learn

사용법:
    python train_polarity_classifier.py \
        --train_file ../dataset/processed/train.jsonl \
        --val_file ../dataset/processed/val.jsonl \
        --output_dir ./kcelectra-polarity \
        --epochs 3 --batch_size 16

참고 (Mac 사용자):
    Apple Silicon이면 최신 transformers/torch가 MPS 백엔드를 자동으로 잡아서 CPU보다는 빠르지만,
    그래도 18,914건 전체를 3 epoch 돌리면 꽤 오래 걸릴 수 있다. 처음엔 --epochs 1로 빠르게
    한 바퀴 돌려서 파이프라인이 끝까지 도는지부터 확인하는 걸 권장. 너무 느리면 Colab(GPU)로 옮기는 것도 방법.
"""

import argparse
import json
import os

import numpy as np
import torch
from torch.utils.data import Dataset
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.utils.class_weight import compute_class_weight
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

LABEL_NAMES = {0: "부정", 1: "중립", 2: "긍정"}


def load_jsonl(path):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


class PolarityDataset(Dataset):
    def __init__(self, records, tokenizer, max_length=256):
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        rec = self.records[idx]
        enc = self.tokenizer(
            rec["text"],
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["labels"] = torch.tensor(rec["label"], dtype=torch.long)
        return item


class WeightedLossTrainer(Trainer):
    """클래스 불균형 보정을 위해 가중 CrossEntropyLoss를 쓰는 Trainer.
    transformers 버전마다 compute_loss로 넘어오는 추가 인자가 달라질 수 있어 **kwargs로 흡수한다."""

    def __init__(self, *args, class_weights=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        weight = self.class_weights.to(logits.device) if self.class_weights is not None else None
        loss_fct = torch.nn.CrossEntropyLoss(weight=weight)
        loss = loss_fct(logits.view(-1, logits.size(-1)), labels.view(-1))
        return (loss, outputs) if return_outputs else loss


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    report = classification_report(
        labels,
        preds,
        labels=[0, 1, 2],
        target_names=[LABEL_NAMES[i] for i in [0, 1, 2]],
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": accuracy_score(labels, preds),
        "macro_f1": f1_score(labels, preds, average="macro", labels=[0, 1, 2], zero_division=0),
        "f1_부정": report["부정"]["f1-score"],
        "f1_중립": report["중립"]["f1-score"],
        "f1_긍정": report["긍정"]["f1-score"],
    }


def build_training_args(args):
    """transformers 버전에 따라 eval_strategy / evaluation_strategy 파라미터 이름이 달라서 둘 다 시도."""
    common = dict(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        logging_steps=50,
        save_total_limit=2,
        seed=args.seed,
        report_to="none",
    )
    try:
        return TrainingArguments(eval_strategy="epoch", **common)
    except TypeError:
        return TrainingArguments(evaluation_strategy="epoch", **common)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--train_file", required=True)
    ap.add_argument("--val_file", required=True)
    ap.add_argument("--model_name", default="beomi/KcELECTRA-base")
    ap.add_argument("--output_dir", default="./kcelectra-polarity")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max_length", type=int, default=256)
    ap.add_argument("--no_class_weight", action="store_true", help="클래스 가중치 없이 일반 CrossEntropyLoss로 학습")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    for path, name in [(args.train_file, "train_file"), (args.val_file, "val_file")]:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"{name} 경로가 존재하지 않습니다: {path}")

    train_records = load_jsonl(args.train_file)
    val_records = load_jsonl(args.val_file)
    print(f"[정보] train {len(train_records)}건 / val {len(val_records)}건 로드")

    print(f"[정보] 토크나이저/모델 로드: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=3)

    train_dataset = PolarityDataset(train_records, tokenizer, args.max_length)
    val_dataset = PolarityDataset(val_records, tokenizer, args.max_length)

    class_weights = None
    if not args.no_class_weight:
        train_labels = np.array([r["label"] for r in train_records])
        weights = compute_class_weight(class_weight="balanced", classes=np.array([0, 1, 2]), y=train_labels)
        class_weights = torch.tensor(weights, dtype=torch.float)
        print(f"[정보] 클래스 가중치 (부정/중립/긍정): {weights.round(3).tolist()}")

    training_args = build_training_args(args)

    trainer = WeightedLossTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        class_weights=class_weights,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    trainer.train()

    print("\n[정보] 최종 검증 성능:")
    metrics = trainer.evaluate()
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    best_dir = os.path.join(args.output_dir, "best_model")
    trainer.save_model(best_dir)
    tokenizer.save_pretrained(best_dir)
    print(f"\n[정보] 최종 모델 저장: {best_dir}")
    print("[안내] extract_trend_tags.py의 placeholder_polarity_fn 자리에 이 모델의 predict 함수를 넣어 교체하세요.")


if __name__ == "__main__":
    main()
