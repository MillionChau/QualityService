from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseRule(ABC):
    name: str = "base_rule"
    enabled: bool = True

    @abstractmethod
    def evaluate(self, text: str, statistics: Dict[str, Any], protected_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Đánh giá rule trên bài viết.
        Trả về dict gồm:
        {
            "score": float (0.0 đến 1.0),
            "penalty": float,
            "issues": List[Dict[str, Any]],
            "metrics": Dict[str, Any]
        }
        """
        pass
