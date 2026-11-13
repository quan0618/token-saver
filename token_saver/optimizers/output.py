from typing import List, Dict
from .base import BaseOptimizer

class OutputConstraint(BaseOptimizer):
    def optimize(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        # 找到最后一条 user 消息，追加约束
        for msg in reversed(messages):
            if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                msg["content"] += "\n\n(注意：请直接给出答案，不要输出客套话或废话。)"
                break
        return messages