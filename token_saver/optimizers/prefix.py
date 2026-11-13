import re
from typing import List, Dict
from .base import BaseOptimizer

class PrefixStabilizer(BaseOptimizer):
    def __init__(self):
        # 匹配常见的日期时间格式，如 "当前时间：2024-05-20 12:00:00"
        self.time_pattern = r'(当前时间[：:]\s*[\d\-\/:年月日时分秒\s]+)'

    def optimize(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if not messages:
            return messages

        for msg in messages:
            if msg.get("role") == "system" and isinstance(msg.get("content"), str):
                content = msg["content"]
                match = re.search(self.time_pattern, content)
                
                if match:
                    dynamic_part = match.group(1)
                    # 剥离动态部分
                    static_content = content.replace(dynamic_part, "").strip()
                    # 拼接回末尾
                    msg["content"] = f"{static_content}\n\n[系统动态信息]: {dynamic_part}"
                    
        return messages