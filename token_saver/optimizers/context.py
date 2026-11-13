from typing import List, Dict
from .base import BaseOptimizer

class ContextPruner(BaseOptimizer):
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages

    def optimize(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if len(messages) <= self.max_messages:
            return messages
        
        # 必须保留 system 开头的消息，裁剪后面的
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]
        
        # 只保留最近的 N 条对话
        keep_count = self.max_messages - len(system_msgs)
        pruned_others = other_msgs[-keep_count:] if keep_count > 0 else []
        
        return system_msgs + pruned_others