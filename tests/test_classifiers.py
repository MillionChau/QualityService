from app.models.it_classifier import ITDomainClassifier
from app.models.toxic_classifier import ToxicClassifier
from app.pipeline.classifier import ClassifierPipeline


def test_classifiers_prediction():
    it_clf = ITDomainClassifier()
    it_clf.load_model()

    toxic_clf = ToxicClassifier()
    toxic_clf.load_model()

    pipeline = ClassifierPipeline(it_clf, toxic_clf)

    # IT Content
    it_text = "Hướng dẫn lập trình Python backend dùng FastAPI và Docker container."
    res = pipeline.classify(it_text)

    assert res["is_it"] is True
    assert res["it_probability"] > 0.5
    assert res["toxicity"]["label"] in ["safe", "suspicious", "toxic"]
