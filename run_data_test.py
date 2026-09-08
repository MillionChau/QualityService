import sys
import io
import json
import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure UTF-8 encoding on Windows terminal
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Thêm thư mục hiện tại vào sys.path để import app module
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from app.services.quality_service import quality_service
from app.clients.mongo_client import mongo_client
from app.schemas.quality import QualityResult


DEFAULT_DATASET_PATH = Path(__file__).parent / "test_dataset.json"


def load_dataset(file_path: Path) -> List[Dict[str, Any]]:
    if not file_path.exists():
        print(f"File {file_path} không tồn tại. Tạo file mẫu...")
        default_data = [
            {
                "id": "item_1",
                "text": "Hướng dẫn sử dụng Docker và Kubernetes để deploy ứng dụng Python FastAPI microservice.",
                "expected_is_it": True,
                "expected_quality_level": "good",
                "expected_toxicity": "safe",
                "notes": "Bài viết IT"
            }
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_dataset(file_path: Path, data: List[Dict[str, Any]]) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[SUCCESS] Đã lưu thành công dữ liệu vào file {file_path.name}")


def evaluate_item(pipeline_process, item: Dict[str, Any]) -> Dict[str, Any]:
    text = item.get("text", item.get("content", ""))
    res: QualityResult = pipeline_process(text)

    pred_is_valid = res.is_valid
    pred_is_it = res.is_it
    pred_level = res.quality_level
    pred_toxic = res.toxicity.label

    # Lấy nhãn kỳ vọng từ dataset (hỗ trợ cả schema cũ và mới)
    raw_exp_is_it = item.get("expected_is_it", item.get("is_it", None))
    exp_is_it = bool(raw_exp_is_it) if raw_exp_is_it is not None else None

    exp_level = item.get("expected_quality_level", item.get("quality_level", None))

    raw_exp_toxic = item.get("expected_toxicity", item.get("toxicity", None))
    exp_toxic = str(raw_exp_toxic).lower() if raw_exp_toxic is not None else "safe"

    # Quy tắc Đánh giá DevRadar: Hợp lệ (True) = (IT == True) VÀ (Toxicity == 'safe')
    exp_is_valid = (exp_is_it is True) and (exp_toxic == "safe") if exp_is_it is not None else None

    is_it_match = (exp_is_it is None) or (pred_is_it == exp_is_it)
    toxic_match = (exp_toxic is None) or (pred_toxic == exp_toxic)
    valid_match = (exp_is_valid is None) or (pred_is_valid == exp_is_valid)

    overall_match = is_it_match and toxic_match and valid_match

    return {
        "id": item.get("id", item.get("content_id", "N/A")),
        "text": text,
        "notes": item.get("notes", ""),
        "pred_is_valid": pred_is_valid,
        "exp_is_valid": exp_is_valid,
        "pred_is_it": pred_is_it,
        "pred_it_prob": res.it_probability,
        "exp_is_it": exp_is_it,
        "pred_score": res.quality_score,
        "pred_level": pred_level,
        "exp_level": exp_level,
        "pred_toxic": pred_toxic,
        "exp_toxic": exp_toxic,
        "issues_count": len(res.issues),
        "is_it_match": is_it_match,
        "toxic_match": toxic_match,
        "valid_match": valid_match,
        "overall_match": overall_match,
        "raw_result": res
    }


def put_single_label_to_db(content_id: str, text: str, expected_is_it: Optional[bool],
                            expected_quality_level: Optional[str], expected_toxicity: Optional[str],
                            notes: Optional[str] = "") -> bool:
    """
    Thực hiện PUT nhãn bài viết trực tiếp vào CSDL MongoDB Atlas qua API hoặc Direct Client.
    """
    api_url = "http://localhost:8001/api/v1/quality/relabel"
    payload = {
        "content_id": content_id,
        "content": text,
        "expected_is_it": expected_is_it,
        "expected_quality_level": expected_quality_level,
        "expected_toxicity": expected_toxicity,
        "notes": notes
    }

    # 1. Thử gửi qua HTTP PUT API
    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.put(api_url, json=payload)
            if res.status_code == 200:
                print(f"  [API PUT 200] Đã gửi PUT bài viết '{content_id}' thành công qua QualityService API!")
                return True
    except Exception:
        pass

    # 2. Fallback ghi trực tiếp vào MongoDB Atlas qua Async MongoClient
    async def _direct_db_update():
        mongo_client.connect()
        ok = await mongo_client.update_label(content_id, payload)
        mongo_client.close()
        return ok

    try:
        ok = asyncio.run(_direct_db_update())
        if ok:
            print(f"  [DB DIRECT] Đã PUT bài viết '{content_id}' trực tiếp vào CSDL MongoDB Atlas thành công!")
            return True
        else:
            print(f"  [WARN] Không thể kết nối MongoDB Atlas (kiểm tra MONGODB_URL trong .env).")
            return False
    except Exception as e:
        print(f"  [ERROR] Lỗi khi PUT dữ liệu vào MongoDB: {e}")
        return False


def test_input_text_interactively():
    """
    Cho phép người dùng nhập trực tiếp văn bản từ bàn phím để test label và lưu vào CSDL.
    """
    quality_service.initialize()
    pipeline = quality_service.pipeline

    print("\n" + "="*85)
    print(" 🎯 NHẬP VĂN BẢN TRỰC TIẾP ĐỂ TEST LABEL VÀ LƯU VÀO CSDL")
    print("="*85)

    while True:
        print("\nNhập nội dung bài viết cần test (hoặc gõ 'q' để quay lại menu chính):")
        lines = []
        try:
            line = input("> ").strip()
            if line.lower() == 'q':
                break
            if not line:
                continue
            lines.append(line)
        except EOFError:
            break

        text = "\n".join(lines)

        # Chạy dự đoán từ Quality Pipeline
        res: QualityResult = pipeline.process(text)

        status_str = "✅ PASSED (Bài viết IT Hợp Lệ)" if res.is_valid else "❌ FAILED (Bài viết bị Từ chối: Non-IT hoặc Toxic)"

        print("\n" + "-"*65)
        print(" KẾT QUẢ DỰ ĐOÁN TỪ QUALITY SERVICE PIPELINE:")
        print("-" * 65)
        print(f"  - Trạng thái DevRadar:     {status_str}")
        print(f"  - IT Domain Classification: {res.is_it} (Độ tin cậy: {res.it_probability * 100:.1f}%)")
        print(f"  - Quality Score:            {res.quality_score} / 100")
        print(f"  - Quality Level:            {res.quality_level.upper()}")
        print(f"  - Content Toxicity:         {res.toxicity.label.upper()} (Prob: {res.toxicity.probability:.2f})")
        print(f"  - Số từ (Word Count):        {res.statistics.word_count}")
        print(f"  - Vấn đề phát hiện (Issues): {len(res.issues)} issue(s)")
        for iss in res.issues:
            print(f"      + [{iss.type}] {iss.message or iss.original}")

        print("-" * 65)

        save_choice = input("\nBạn có muốn gán nhãn đúng và PUT lưu bài viết này vào CSDL không? (Y/n): ").strip().lower()
        if save_choice != 'n':
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_id = f"test_{ts}"
            content_id = input(f"Mã bài viết (content_id, mặc định [{default_id}]): ").strip() or default_id

            # Sửa / Xác nhận nhãn IT
            it_in = input(f"Nhãn IT thực tế (t=True, f=False, Enter giữ theo dự đoán [{res.is_it}]): ").strip().lower()
            if it_in == 't':
                exp_is_it = True
            elif it_in == 'f':
                exp_is_it = False
            else:
                exp_is_it = res.is_it

            # Sửa / Xác nhận nhãn Quality Level
            lvl_in = input(f"Nhãn Chất lượng (excellent/good/average/poor, Enter giữ theo dự đoán [{res.quality_level}]): ").strip().lower()
            exp_level = lvl_in if lvl_in in ['excellent', 'good', 'average', 'poor'] else res.quality_level

            # Sửa / Xác nhận nhãn Toxicity
            tox_in = input(f"Nhãn Độc hại (safe/toxic/suspicious, Enter giữ theo dự đoán [{res.toxicity.label}]): ").strip().lower()
            exp_toxic = tox_in if tox_in in ['safe', 'toxic', 'suspicious'] else res.toxicity.label

            notes = input("Ghi chú mô tả (tùy chọn): ").strip()

            # Thực hiện PUT bài viết và nhãn vào CSDL
            put_single_label_to_db(content_id, text, exp_is_it, exp_level, exp_toxic, notes)


def fetch_db_and_relabel():
    """
    Tải danh sách bài viết trực tiếp từ CSDL MongoDB Atlas để test & sửa nhãn.
    """
    quality_service.initialize()
    pipeline = quality_service.pipeline

    print("\n" + "="*85)
    print(" 📦 LẤY DỮ LIỆU BÀI VIẾT TỪ CSDL MONGODB ATLAS ĐỂ TEST & SỬA NHÃN")
    print("="*85)

    # 1. Lấy dữ liệu từ CSDL
    async def _fetch_from_db():
        mongo_client.connect()
        results = await mongo_client.list_results(limit=100)
        mongo_client.close()
        return results

    try:
        db_items = asyncio.run(_fetch_from_db())
    except Exception as e:
        print(f"[ERROR] Không thể kết nối MongoDB Atlas: {e}")
        return

    if not db_items:
        print("Không có bài viết nào trong bộ sưu tập 'quality_results' của CSDL MongoDB Atlas.")
        return

    print(f"Đã tìm thấy {len(db_items)} bài viết trong CSDL MongoDB Atlas.\n")

    for idx, item in enumerate(db_items):
        content_id = item.get("content_id", item.get("id", f"db_item_{idx}"))
        text = item.get("content", item.get("cleaned_text", item.get("text", "")))
        if not text:
            continue

        res = evaluate_item(pipeline.process, {"id": content_id, "text": text, **item})

        print(f"\n--- Bài viết CSDL [{idx + 1}/{len(db_items)}] ID: {content_id} ---")
        snippet = text[:120].replace('\n', ' ') + ('...' if len(text) > 120 else '')
        print(f"Nội dung: {snippet}")
        print(f"Dự đoán mô hình:  IS_IT={res['pred_is_it']} (prob {res['pred_it_prob']:.2f}) | Quality={res['pred_level']} ({res['pred_score']}) | Toxic={res['pred_toxic']}")
        print(f"Nhãn trong CSDL:  IS_IT={item.get('expected_is_it')} | Quality={item.get('expected_quality_level')} | Toxic={item.get('expected_toxicity')}")

        choice = input("\nBạn có muốn sửa nhãn và PUT cập nhật lại CSDL không? (y/N/q - Enter giữ nguyên, q để thoát): ").strip().lower()
        if choice == 'q':
            break
        if choice == 'y':
            it_in = input(f"Sửa expected_is_it (t=True, f=False, Enter giữ nguyên [{item.get('expected_is_it')}]): ").strip().lower()
            exp_is_it = item.get('expected_is_it')
            if it_in == 't': exp_is_it = True
            elif it_in == 'f': exp_is_it = False

            lvl_in = input(f"Sửa expected_quality_level (excellent/good/average/poor, Enter giữ nguyên [{item.get('expected_quality_level')}]): ").strip().lower()
            exp_level = lvl_in if lvl_in in ['excellent', 'good', 'average', 'poor'] else item.get('expected_quality_level')

            tox_in = input(f"Sửa expected_toxicity (safe/toxic/suspicious, Enter giữ nguyên [{item.get('expected_toxicity')}]): ").strip().lower()
            exp_toxic = tox_in if tox_in in ['safe', 'toxic', 'suspicious'] else item.get('expected_toxicity')

            notes = input(f"Ghi chú (Enter giữ nguyên [{item.get('notes', '')}]): ").strip() or item.get('notes', '')

            put_single_label_to_db(content_id, text, exp_is_it, exp_level, exp_toxic, notes)


def run_evaluation(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    print("\n" + "="*95)
    print(" DỰ ĐOÁN VÀ ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU DEVRADAR (IT + SAFE TOXIC = TRUE)")
    print("="*95)

    quality_service.initialize()
    pipeline = quality_service.pipeline

    results = []
    it_matches = 0
    valid_matches = 0
    total_eval = 0

    print(f"\n{'ID':<10} | {'Text Snippet':<30} | {'IS_VALID (DevRadar)':<22} | {'Score / Level':<15} | {'Match'}")
    print("-" * 95)

    for item in dataset:
        res = evaluate_item(pipeline.process, item)
        results.append(res)
        total_eval += 1

        snippet = res['text'][:26].replace("\n", " ") + ("..." if len(res['text']) > 26 else "")
        valid_str = f"{res['pred_is_valid']} / Exp:{res['exp_is_valid']}"
        score_str = f"{res['pred_score']} ({res['pred_level']})"
        status_str = "✓ MATCH" if res['overall_match'] else "✗ MISMATCH"

        print(f"{res['id']:<10} | {snippet:<30} | {valid_str:<22} | {score_str:<15} | {status_str}")

        if res['is_it_match']:
            it_matches += 1
        if res['valid_match']:
            valid_matches += 1

    print("-" * 95)
    if total_eval > 0:
        it_acc = (it_matches / total_eval) * 100
        valid_acc = (valid_matches / total_eval) * 100
        print(f"📊 BÁO CÁO TỔNG HỢP ({total_eval} bản ghi):")
        print(f"  - Độ chính xác Phân loại Lĩnh vực IT (is_it):       {it_matches}/{total_eval} ({it_acc:.1f}%)")
        print(f"  - Độ chính xác Duyệt bài DevRadar (IT + Not Toxic):  {valid_matches}/{total_eval} ({valid_acc:.1f}%)\n")

    return results


def sync_dataset_to_db(dataset: List[Dict[str, Any]]):
    print("\n" + "="*85)
    print(" ĐỒNG BỘ / PUT TOÀN BỘ DATASET FILE VÀO CSDL (MONGODB ATLAS)")
    print("="*85)

    synced_count = 0
    for item in dataset:
        content_id = item.get("id")
        text = item.get("text")
        exp_is_it = item.get("expected_is_it")
        exp_level = item.get("expected_quality_level")
        exp_toxic = item.get("expected_toxicity")
        notes = item.get("notes")

        if put_single_label_to_db(content_id, text, exp_is_it, exp_level, exp_toxic, notes):
            synced_count += 1

    print(f"\n-> Kết quả: {synced_count}/{len(dataset)} mẫu đã được PUT đồng bộ vào CSDL MongoDB Atlas.\n")


def main():
    parser = argparse.ArgumentParser(description="Công cụ test dữ liệu và chỉnh sửa nhãn cho DevRadar QualityService.")
    parser.add_argument("--file", "-f", type=str, default=str(DEFAULT_DATASET_PATH), help="Đường dẫn file JSON dataset.")
    parser.add_argument("--input", action="store_true", help="Nhập văn bản trực tiếp để test label và lưu CSDL.")
    parser.add_argument("--fetch-db", action="store_true", help="Tải bài viết từ CSDL MongoDB Atlas để test & sửa nhãn.")
    parser.add_argument("--eval", action="store_true", help="Chạy đánh giá toàn bộ local dataset.")
    parser.add_argument("--sync", action="store_true", help="Đồng bộ / PUT dữ liệu local dataset vào CSDL.")

    args = parser.parse_args()

    file_path = Path(args.file)
    dataset = load_dataset(file_path)

    if args.input:
        test_input_text_interactively()
    elif args.fetch_db:
        fetch_db_and_relabel()
    elif args.eval:
        run_evaluation(dataset)
    elif args.sync:
        sync_dataset_to_db(dataset)
    else:
        # Menu tương tác CLI chính
        while True:
            print("\n" + "="*65)
            print(" 🚀 DEV RADAR - QUALITY SERVICE DATA TESTER & RELABELER")
            print("="*65)
            print("1. 📝 Nhập văn bản trực tiếp để Test Label & Lưu vào CSDL MongoDB")
            print("2. 📦 Tải bài viết từ CSDL MongoDB Atlas để Test & Sửa nhãn")
            print("3. 📊 Đánh giá tập dữ liệu file JSON local (Evaluate Dataset)")
            print("4. 🔄 Đồng bộ / PUT toàn bộ file JSON local vào CSDL MongoDB Atlas")
            print("5. 🚪 Thoát")

            choice = input("\nChọn thao tác (1-5): ").strip()
            if choice == "1":
                test_input_text_interactively()
            elif choice == "2":
                fetch_db_and_relabel()
            elif choice == "3":
                run_evaluation(dataset)
            elif choice == "4":
                sync_dataset_to_db(dataset)
            elif choice == "5":
                print("Tạm biệt!")
                break
            else:
                print("Lựa chọn không hợp lệ.")


if __name__ == "__main__":
    main()
