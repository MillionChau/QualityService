import io
import sys
import json
from pathlib import Path
from app.services.quality_service import quality_service

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def evaluate():
    quality_service.initialize()
    dataset_path = Path('test_dataset.json')
    if not dataset_path.exists():
        print("test_dataset.json does not exist.")
        return

    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = len(data)
    is_it_correct = 0
    toxic_correct = 0
    level_correct = 0
    valid_correct = 0

    it_fp = 0
    it_fn = 0
    toxic_fp = 0
    toxic_fn = 0

    categories = {}

    for item in data:
        text = item.get('text', '')
        exp_is_it = bool(item.get('is_it', 0))
        exp_toxic = str(item.get('toxicity', 'safe')).lower()
        if exp_toxic == 'suspicious':
            exp_toxic = 'toxic'
        exp_level = item.get('quality_level', 'average')
        cat = item.get('category', 'Unknown')
        
        if cat not in categories:
            categories[cat] = {'total': 0, 'it_correct': 0, 'toxic_correct': 0, 'level_correct': 0}
        categories[cat]['total'] += 1
        
        res = quality_service.pipeline.process(text)
        
        pred_is_it = res.is_it
        pred_toxic = res.toxicity.label
        if pred_toxic == 'suspicious':
            pred_toxic = 'toxic'
        pred_level = res.quality_level
        pred_valid = res.is_valid
        exp_valid = (exp_is_it is True) and (exp_toxic == 'safe')
        
        if pred_is_it == exp_is_it:
            is_it_correct += 1
            categories[cat]['it_correct'] += 1
        else:
            if pred_is_it and not exp_is_it:
                it_fp += 1
            else:
                it_fn += 1
                
        if pred_toxic == exp_toxic:
            toxic_correct += 1
            categories[cat]['toxic_correct'] += 1
        else:
            if pred_toxic == 'toxic' and exp_toxic != 'toxic':
                toxic_fp += 1
            else:
                toxic_fn += 1
                
        if pred_level == exp_level:
            level_correct += 1
            categories[cat]['level_correct'] += 1
            
        if pred_valid == exp_valid:
            valid_correct += 1

    print("\n" + "="*80)
    print(" KẾT QUẢ ĐÁNH GIÁ TRÊN TẬP TEST (test_dataset.json - 2000 MẪU)")
    print("="*80)
    print(f"TỔNG SỐ MẪU: {total}")
    print(f"ĐỘ CHÍNH XÁC IT (IS_IT):         {is_it_correct}/{total} ({is_it_correct/total*100:.2f}%)")
    print(f"ĐỘ CHÍNH XÁC TOXIC:             {toxic_correct}/{total} ({toxic_correct/total*100:.2f}%)")
    print(f"ĐỘ CHÍNH XÁC IS_VALID (DevRadar):{valid_correct}/{total} ({valid_correct/total*100:.2f}%)")
    print(f"ĐỘ CHÍNH XÁC QUALITY LEVEL:     {level_correct}/{total} ({level_correct/total*100:.2f}%)")
    print(f"IT False Positives: {it_fp}, IT False Negatives: {it_fn}")
    print(f"Toxic False Positives: {toxic_fp}, Toxic False Negatives: {toxic_fn}")

    print("\n--- CHI TIẾT THEO CHUYÊN MỤC ---")
    for c, stats in sorted(categories.items(), key=lambda x: x[1]['total'], reverse=True):
        it_pct = stats['it_correct'] / stats['total'] * 100
        tox_pct = stats['toxic_correct'] / stats['total'] * 100
        print(f"{c:26} (N={stats['total']:4}): IT={it_pct:5.1f}%, Toxic={tox_pct:5.1f}%")

if __name__ == '__main__':
    evaluate()

