import copy
import inspect
from typing import Any

from .optimizers import (
    ContextPruner,
    JsonStabilizer,
    OutputConstraint,
    PrefixStabilizer,
    SemanticPruner,
)


def _optimize_kwargs(kwargs, optimizers, json_stabilizer, stabilize_tools):
    """对请求参数做统一拦截：深拷贝 messages 后过优化器链，再稳定化 tools。

    同步与异步代理共用同一段逻辑，保证行为一致。
    """
    # 1. 深拷贝 messages，避免优化器原地修改污染调用方（也避免重复追加约束）
    if "messages" in kwargs:
        messages = copy.deepcopy(kwargs["messages"])
        for opt in optimizers:
            messages = opt.optimize(messages)
        kwargs["messages"] = messages

    # 2. 稳定化 tools / functions（JSON 键名深度排序，最大化缓存命中）
    if stabilize_tools:
        kwargs = json_stabilizer.stabilize_tools(kwargs)

    return kwargs


class TokenSaver:
    """包装官方 OpenAI 客户端（同步 / 异步），实现无缝 Token 优化。"""

    def __init__(
        self,
        client: Any,
        max_history: int = 10,
        stabilize_tools: bool = True,
        use_semantic_pruning: bool = False,
        summarizer_client: Any = None,
        summary_model: str = "gpt-3.5-turbo",
        keep_recent: int = 4,
    ):
        self._client = client

        # 上下文优化器：默认简单裁剪，可切换为语义级压缩
        if use_semantic_pruning:
            context_optimizer = SemanticPruner(
                max_messages=max_history,
                summarizer_client=summarizer_client,
                summary_model=summary_model,
                keep_recent=keep_recent,
            )
        else:
            context_optimizer = ContextPruner(max_messages=max_history)

        # 装配优化器链（按顺序执行）
        self.optimizers = [
            PrefixStabilizer(),
            context_optimizer,
            OutputConstraint(),
        ]

        self.json_stabilizer = JsonStabilizer()
        self._stabilize_tools = stabilize_tools

        # 依据 create 是否为协程函数，判断同步 / 异步客户端，装配对应代理
        if inspect.iscoroutinefunction(client.chat.completions.create):
            self.chat = _AsyncChatProxy(
                client.chat,
                self.optimizers,
                self.json_stabilizer,
                self._stabilize_tools,
            )
        else:
            self.chat = _ChatProxy(
                client.chat,
                self.optimizers,
                self.json_stabilizer,
                self._stabilize_tools,
            )

    def __getattr__(self, name):
        # 将其他未修改的属性（如 models）原样返回给官方客户端
        return getattr(self._client, name)


class _ChatProxy:
    def __init__(self, original_chat, optimizers, json_stabilizer, stabilize_tools):
        self._original_chat = original_chat
        self._optimizers = optimizers
        self.completions = _CompletionsProxy(
            original_chat.completions,
            optimizers,
            json_stabilizer,
            stabilize_tools,
        )

    def __getattr__(self, name):
        return getattr(self._original_chat, name)


class _CompletionsProxy:
    def __init__(
        self, original_completions, optimizers, json_stabilizer, stabilize_tools
    ):
        self._original_completions = original_completions
        self._optimizers = optimizers
        self._json_stabilizer = json_stabilizer
        self._stabilize_tools = stabilize_tools

    def create(self, *args, **kwargs):
        kwargs = _optimize_kwargs(
            kwargs, self._optimizers, self._json_stabilizer, self._stabilize_tools
        )
        return self._original_completions.create(*args, **kwargs)


class _AsyncChatProxy:
    def __init__(self, original_chat, optimizers, json_stabilizer, stabilize_tools):
        self._original_chat = original_chat
        self._optimizers = optimizers
        self.completions = _AsyncCompletionsProxy(
            original_chat.completions,
            optimizers,
            json_stabilizer,
            stabilize_tools,
        )

    def __getattr__(self, name):
        return getattr(self._original_chat, name)


class _AsyncCompletionsProxy:
    def __init__(
        self, original_completions, optimizers, json_stabilizer, stabilize_tools
    ):
        self._original_completions = original_completions
        self._optimizers = optimizers
        self._json_stabilizer = json_stabilizer
        self._stabilize_tools = stabilize_tools

    async def create(self, *args, **kwargs):
        kwargs = _optimize_kwargs(
            kwargs, self._optimizers, self._json_stabilizer, self._stabilize_tools
        )
        return await self._original_completions.create(*args, **kwargs)
