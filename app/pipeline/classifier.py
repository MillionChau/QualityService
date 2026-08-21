from typing import Dict, Any, Tuple
from app.models.it_classifier import ITDomainClassifier
from app.models.toxic_classifier import ToxicClassifier


class ClassifierPipeline:
    def __init__(self, it_classifier: ITDomainClassifier, toxic_classifier: ToxicClassifier):
        self.it_classifier = it_classifier
        self.toxic_classifier = toxic_classifier

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Thực hiện phân loại cả IT Domain lẫn Toxicity.
        """
        is_it, it_prob = self.it_classifier.predict(text)
        toxic_label, toxic_prob = self.toxic_classifier.predict(text)

        return {
            "is_it": is_it,
            "it_probability": it_prob,
            "toxicity": {
                "label": toxic_label,
                "probability": toxic_prob
            }
        }
