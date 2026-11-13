from typing import Dict, List

from .base import BaseOptimizer


class OutputConstraint(BaseOptimizer):
    """在最后一条 user 消息后追加约束，让模型直接给结果，减少输出 Token 浪费。"""

    DEFAULT_PROMPT = "(注意：请直接给出答案，不要输出客套话或废话。)"

    def __init__(self, prompt: str = DEFAULT_PROMPT):
        self.prompt = prompt

    def optimize(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        for msg in reversed(messages):
            if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                msg["content"] += f"\n\n{self.prompt}"
                break
        return messages
