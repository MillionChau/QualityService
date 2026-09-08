import os
import sys
import io
import json
import joblib
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Fix encoding cho stdout Windows terminal
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score
from app.pipeline.tokenizer import VietnameseTokenizer
from app.core.config import settings


def train_it_classifier(dataset: List[Dict[str, Any]], model_save_path: str, vectorizer_save_path: str):
    print("\n" + "="*85)
    print(" HUẤN LUYỆN MÔ HÌNH PHÂN LOẠI LĨNH VỰC IT (IT DOMAIN CLASSIFIER)")
    print("="*85)

    tokenizer = VietnameseTokenizer()

    texts = []
    labels = []

    for sample in dataset:
        raw_text = sample.get("text", "")
        # Phân loại theo nhãn is_it (1 hoặc 0 / True hoặc False)
        is_it_label = sample.get("is_it")
        if is_it_label is None:
            is_it_label = sample.get("expected_is_it", 0)

        label = 1 if bool(is_it_label) else 0

        # Tách từ tiếng Việt
        tokenized_text = tokenizer.tokenize(raw_text)

        texts.append(tokenized_text)
        labels.append(label)

    print(f"Tổng số mẫu huấn luyện: {len(texts)} (IT: {sum(labels)}, Non-IT: {len(labels) - sum(labels)})")

    # 1. Khởi tạo TF-IDF Vectorizer với feature space mở rộng và n-grams (1, 3)
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=25000,
        min_df=2,
        sublinear_tf=True
    )
    X_vectors = vectorizer.fit_transform(texts)

    # 2. Khởi tạo & Fit mô hình Logistic Regression tối ưu cho text classification
    clf = LogisticRegression(C=3.0, class_weight="balanced", max_iter=1500, random_state=42)
    clf.fit(X_vectors, labels)

    # 3. Đánh giá chất lượng mô hình trên tập huấn luyện
    preds = clf.predict(X_vectors)
    acc = accuracy_score(labels, preds)

    print("\n--- KẾT QUẢ HUẤN LUYỆN IT ---")
    print(f"Accuracy Score: {acc * 100:.2f}%")
    print("\nBáo cáo chi tiết (Classification Report):")
    print(classification_report(labels, preds, target_names=["Non-IT", "IT"]))

    # 4. Lưu file mô hình & vectorizer
    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    os.makedirs(os.path.dirname(vectorizer_save_path), exist_ok=True)

    joblib.dump(clf, model_save_path)
    joblib.dump(vectorizer, vectorizer_save_path)

    print(f"[SUCCESS] Đã xuất mô hình thành công tại: {model_save_path}")
    print(f"[SUCCESS] Đã xuất vectorizer thành công tại: {vectorizer_save_path}\n")


def train_toxic_classifier(dataset: List[Dict[str, Any]], model_save_path: str, vectorizer_save_path: str):
    print("\n" + "="*85)
    print(" HUẤN LUYỆN MÔ HÌNH PHÂN LOẠI NỘI DUNG ĐỘC HẠI (TOXIC CLASSIFIER)")
    print("="*85)

    tokenizer = VietnameseTokenizer()

    texts = []
    labels = []

    for sample in dataset:
        raw_text = sample.get("text", "")
        tox_label = sample.get("toxicity") or sample.get("expected_toxicity", "safe")

        # Label: 'toxic' vs 'safe'
        label = "toxic" if str(tox_label).lower() in ["toxic", "suspicious"] else "safe"

        tokenized_text = tokenizer.tokenize(raw_text)
        texts.append(tokenized_text)
        labels.append(label)

    print(f"Tổng số mẫu huấn luyện Toxic: {len(texts)} (Toxic: {labels.count('toxic')}, Safe: {labels.count('safe')})")

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=25000,
        min_df=2,
        sublinear_tf=True
    )
    X_vectors = vectorizer.fit_transform(texts)

    clf = LogisticRegression(C=3.5, max_iter=1500, class_weight="balanced", random_state=42)
    clf.fit(X_vectors, labels)

    preds = clf.predict(X_vectors)
    acc = accuracy_score(labels, preds)

    print("\n--- KẾT QUẢ HUẤN LUYỆN TOXIC ---")
    print(f"Accuracy Score: {acc * 100:.2f}%")
    print("\nBáo cáo chi tiết (Classification Report):")
    print(classification_report(labels, preds))

    os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
    os.makedirs(os.path.dirname(vectorizer_save_path), exist_ok=True)

    joblib.dump(clf, model_save_path)
    joblib.dump(vectorizer, vectorizer_save_path)

    print(f"[SUCCESS] Đã xuất mô hình Toxic PKL tại: {model_save_path}")
    print(f"[SUCCESS] Đã xuất Vectorizer Toxic PKL tại: {vectorizer_save_path}\n")


def main():
    default_dataset = "training_dataset.json" if Path("training_dataset.json").exists() else "test_dataset.json"
    parser = argparse.ArgumentParser(description="Script huấn luyện ML models cho QualityService.")
    parser.add_argument("--dataset", "-d", type=str, default=default_dataset, help="Đường dẫn file dataset training JSON.")
    parser.add_argument("--it-model-out", type=str, default=settings.IT_MODEL_PATH, help="Đường dẫn lưu file IT model .pkl.")
    parser.add_argument("--it-vec-out", type=str, default=settings.IT_VECTORIZER_PATH, help="Đường dẫn lưu file IT vectorizer .pkl.")
    parser.add_argument("--toxic-model-out", type=str, default=settings.TOXIC_PKL_MODEL_PATH, help="Đường dẫn lưu file Toxic model .pkl.")
    parser.add_argument("--toxic-vec-out", type=str, default=settings.TOXIC_PKL_VECTORIZER_PATH, help="Đường dẫn lưu file Toxic vectorizer .pkl.")

    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"[ERROR] File dataset {dataset_path} không tồn tại.")
        sys.exit(1)

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # 1. Huấn luyện mô hình IT Classifier
    train_it_classifier(dataset, args.it_model_out, args.it_vec_out)

    # 2. Huấn luyện mô hình Toxic Classifier
    train_toxic_classifier(dataset, args.toxic_model_out, args.toxic_vec_out)


if __name__ == "__main__":
    main()

