import hashlib
import json
from typing import Any, Dict, List, Optional

from .base import BaseOptimizer
from .context import ContextPruner


class SemanticPruner(BaseOptimizer):
    """语义级历史裁剪：超限时用便宜模型把早期对话压缩成一条摘要。

    相比 ContextPruner 的"无脑砍掉最早几条"，它保留了历史语义，多轮对话更连贯，
    同时把超长历史压缩到一条摘要，显著降低输入 Token。

    摘要缓存：以"待压缩历史"的 MD5 为 key，避免对同一段历史反复调用便宜模型。
    安全兜底：若未配置 summarizer_client、或总结调用失败，自动退化为
    ContextPruner 的简单裁剪，绝不让请求因总结失败而中断。
    """

    def __init__(
        self,
        max_messages: int = 10,
        summarizer_client: Any = None,
        summary_model: str = "gpt-3.5-turbo",
        keep_recent: int = 4,
        max_chars_per_message: int = 2000,
    ):
        self.max_messages = max_messages
        self.summarizer_client = summarizer_client
        self.summary_model = summary_model
        self.keep_recent = keep_recent
        self.max_chars_per_message = max_chars_per_message
        self._fallback_pruner = ContextPruner(max_messages=max_messages)
        # 摘要缓存：key 为待压缩历史的 MD5，value 为摘要文本
        self._summary_cache = {}

    def optimize(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if len(messages) <= self.max_messages:
            return messages

        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        # 若近期对话本身已接近上限，没有可压缩的"早期历史"，直接兜底裁剪
        if len(other_msgs) <= self.keep_recent:
            return self._fallback_pruner.optimize(messages)

        to_summarize = other_msgs[:-self.keep_recent]
        recent = other_msgs[-self.keep_recent:]

        if self.summarizer_client is None:
            return self._fallback_pruner.optimize(messages)

        summary = self._get_cached_or_summarize(to_summarize)
        if not summary:
            return self._fallback_pruner.optimize(messages)

        # 摘要作为一条带标记的 system 消息，插在 system 之后、近期对话之前
        summary_msg = {"role": "system", "content": f"[对话历史摘要] {summary}"}
        return system_msgs + [summary_msg] + recent

    def _get_cached_or_summarize(
        self, to_summarize: List[Dict[str, str]]
    ) -> Optional[str]:
        """优先从缓存取摘要；未命中才调用便宜模型，并把结果写入缓存。"""
        digest = self._get_hash(to_summarize)
        if digest and digest in self._summary_cache:
            return self._summary_cache[digest]

        summary = self._summarize(to_summarize)
        if summary and digest:
            self._summary_cache[digest] = summary
        return summary

    def _get_hash(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """对待压缩历史做稳定的 JSON 序列化，生成 MD5 作为缓存键。"""
        try:
            payload = json.dumps(messages, ensure_ascii=False, sort_keys=True)
            return hashlib.md5(payload.encode("utf-8")).hexdigest()
        except (TypeError, ValueError):
            # 内容不可 JSON 序列化时，跳过缓存，直接走真实总结
            return None

    def _summarize(self, to_summarize: List[Dict[str, str]]) -> Optional[str]:
        # 先截断每条消息，避免摘要请求本身过大
        trimmed = []
        for m in to_summarize:
            content = m.get("content", "")
            if isinstance(content, str) and len(content) > self.max_chars_per_message:
                content = content[: self.max_chars_per_message] + "…"
            trimmed.append({"role": m.get("role"), "content": content})

        trimmed.append(
            {
                "role": "user",
                "content": "请把以上对话压缩成一句话摘要（不超过 80 字），"
                "保留关键人物、核心结论和未完成事项。",
            }
        )

        # 优先用精简参数；若端点不支持，降级为完全默认参数再试一次
        for extra in ({"temperature": 0, "max_tokens": 200}, {}):
            try:
                resp = self.summarizer_client.chat.completions.create(
                    model=self.summary_model,
                    messages=trimmed,
                    **extra,
                )
                content = resp.choices[0].message.content
                return content.strip() if content else None
            except Exception:
                continue
        return None
