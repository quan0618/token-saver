import re
from typing import Dict, List

from .base import BaseOptimizer


class PrefixStabilizer(BaseOptimizer):
    """把 system prompt 中的动态部分（如时间戳）移到末尾，保持前缀字节级稳定。

    OpenAI 系的 prompt cache 按"前缀"匹配，动态内容若出现在 system prompt 前部，
    会导致每次请求前缀都不同、缓存全部失效。把静态部分保持在前、动态部分挪到
    末尾，即可让缓存持续命中。
    """

    # 匹配 "当前时间：2024-05-20 12:00:00"、"current time: 2024-05-20T12:00:00Z" 等。
    # 日期与时间之间用 [ \t] 精确匹配空格/Tab（不含换行），既支持 "2024-01-01 00:00:00"
    # 这种带空格的写法，又不会贪婪吞掉换行和后续正文。
    _BASE = r"[\d\-/:年月日时分秒TZ]+(?:[ \t]+[\d:时分秒TZ]+)?"

    _TIME_PATTERNS = [
        re.compile(rf"(当前时间[：:]\s*{_BASE})"),
        re.compile(rf"(现在时间[：:]\s*{_BASE})"),
        re.compile(rf"(current\s+time[：:]\s*{_BASE})", re.IGNORECASE),
        re.compile(rf"(timestamp[：:]\s*{_BASE})", re.IGNORECASE),
    ]

    def optimize(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not messages:
            return messages

        for msg in messages:
            if msg.get("role") == "system" and isinstance(msg.get("content"), str):
                msg["content"] = self._stabilize(msg["content"])
        return messages

    def _stabilize(self, content: str) -> str:
        for pattern in self._TIME_PATTERNS:
            match = pattern.search(content)
            if match:
                dynamic_part = match.group(1)
                # 只替换第一次出现，避免误删后续相同内容
                static_content = content.replace(dynamic_part, "", 1).strip()
                return f"{static_content}\n\n[系统动态信息]: {dynamic_part}"
        return content
