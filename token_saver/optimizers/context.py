from typing import Dict, List

from .base import BaseOptimizer


class ContextPruner(BaseOptimizer):
    """当消息总数超过 max_messages 时，保留全部 system 消息 + 最近 N 条对话。"""

    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages

    def optimize(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if len(messages) <= self.max_messages:
            return messages

        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        if other_msgs:
            # 至少为对话保留 1 个槽位，其余预算给 system
            system_msgs = system_msgs[: max(0, self.max_messages - 1)]
            keep_count = max(1, self.max_messages - len(system_msgs))
        else:
            # 极端情况：只有 system 消息，也严格压到预算内
            system_msgs = system_msgs[: self.max_messages]
            keep_count = 0

        pruned_others = other_msgs[-keep_count:]
        return system_msgs + pruned_others
