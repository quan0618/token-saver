from typing import Any
from .optimizers import PrefixStabilizer, ContextPruner, OutputConstraint

class TokenSaver:
    """包装官方的 OpenAI 客户端，实现无缝 Token 优化。"""
    
    def __init__(self, client: Any, max_history: int = 10):
        self._client = client
        
        # 装配优化器链
        self.optimizers = [
            PrefixStabilizer(),
            ContextPruner(max_messages=max_history),
            OutputConstraint()
        ]
        
        # 注意这里：直接用 _ChatProxy 类名，不要加 self.
        self.chat = _ChatProxy(self._client.chat, self.optimizers)
        
    def __getattr__(self, name):
        # 将其他未修改的属性（如 models）原样返回给官方客户端
        return getattr(self._client, name)

class _ChatProxy:
    def __init__(self, original_chat, optimizers):
        self._original_chat = original_chat
        self._optimizers = optimizers
        
        # 注意这里：直接用 _CompletionsProxy 类名
        self.completions = _CompletionsProxy(original_chat.completions, optimizers)

    def __getattr__(self, name):
        return getattr(self._original_chat, name)

class _CompletionsProxy:
    def __init__(self, original_completions, optimizers):
        self._original_completions = original_completions
        self._optimizers = optimizers

    def create(self, *args, **kwargs):
        # 1. 拦截参数中的 messages
        if "messages" in kwargs:
            messages = kwargs["messages"]
            # 2. 依次通过优化器链
            for opt in self._optimizers:
                messages = opt.optimize(messages)
            # 3. 替换为优化后的 messages
            kwargs["messages"] = messages
            
        # 4. 放行请求给官方客户端
        return self._original_completions.create(*args, **kwargs)