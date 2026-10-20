import io
import sys
import json
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix
from app.services.quality_service import quality_service

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def run_inspection():
    quality_service.initialize()
    with open('test_dataset.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    y_it_true = []
    y_it_pred = []
    y_tox_true = []
    y_tox_pred = []
    y_lvl_true = []
    y_lvl_pred = []
    
    it_fp_samples = []
    it_fn_samples = []
    tox_fp_samples = []
    tox_fn_samples = []

    for item in data:
        text = item.get('text', '')
        exp_is_it = int(item.get('is_it', 0))
        exp_toxic = str(item.get('toxicity', 'safe')).lower()
        if exp_toxic == 'suspicious':
            exp_toxic = 'toxic'
        exp_lvl = item.get('quality_level', 'average')
        cat = item.get('category', 'Unknown')

        res = quality_service.pipeline.process(text)
        pred_is_it = 1 if res.is_it else 0
        pred_toxic = res.toxicity.label
        if pred_toxic == 'suspicious':
            pred_toxic = 'toxic'
        pred_lvl = res.quality_level

        y_it_true.append(exp_is_it)
        y_it_pred.append(pred_is_it)
        y_tox_true.append(exp_toxic)
        y_tox_pred.append(pred_toxic)
        y_lvl_true.append(exp_lvl)
        y_lvl_pred.append(pred_lvl)

        if pred_is_it == 1 and exp_is_it == 0:
            it_fp_samples.append((item.get('id'), cat, text[:70], res.it_probability))
        elif pred_is_it == 0 and exp_is_it == 1:
            it_fn_samples.append((item.get('id'), cat, text[:70], res.it_probability))

        if pred_toxic == 'toxic' and exp_toxic == 'safe':
            tox_fp_samples.append((item.get('id'), cat, text[:70], res.toxicity.probability))
        elif pred_toxic == 'safe' and exp_toxic == 'toxic':
            tox_fn_samples.append((item.get('id'), cat, text[:70], res.toxicity.probability))

    report = {}
    report['it_classification'] = classification_report(y_it_true, y_it_pred, target_names=['Non-IT', 'IT'], output_dict=True)
    report['toxic_classification'] = classification_report(y_tox_true, y_tox_pred, output_dict=True)
    report['level_classification'] = classification_report(y_lvl_true, y_lvl_pred, output_dict=True)

    with open('eval_report_details.json', 'w', encoding='utf-8') as f:
        json.dump({
            'report': report,
            'it_fp_count': len(it_fp_samples),
            'it_fn_count': len(it_fn_samples),
            'tox_fp_count': len(tox_fp_samples),
            'tox_fn_count': len(tox_fn_samples),
            'it_fp_samples': it_fp_samples[:10],
            'it_fn_samples': it_fn_samples[:10],
            'tox_fp_samples': tox_fp_samples[:10],
            'tox_fn_samples': tox_fn_samples[:10],
        }, f, ensure_ascii=False, indent=2)

    print("SUCCESS: eval_report_details.json created.")

if __name__ == '__main__':
    run_inspection()
