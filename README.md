# 🛡️ LLM Token-Saver

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Run Tests](https://github.com/quan0618/token-saver/actions/workflows/test.yml/badge.svg)](https://github.com/quan0618/token-saver/actions/workflows/test.yml)

**LLM Token-Saver** 是一个极致轻量、无侵入的 LLM API 中间件。只需一行代码包装你现有的 OpenAI 兼容客户端，就能自动优化 Prompt 结构、最大化上下文缓存（Context Cache）命中率、并压缩超长对话历史，帮你直接砍掉一大笔 API 账单。

## ✨ 核心特性

- **⚡ 零侵入接入**：完全兼容 OpenAI 官方 SDK 格式，无需重写业务逻辑。
- **🎯 前缀稳定器 (Prefix Stabilizer)**：自动把 System Prompt 中的动态变量（时间戳等）挪到末尾，确保请求前缀字节级一致，强制触发缓存命中。
- **🧩 JSON/Tools 稳定器 (Json Stabilizer)**：对 `tools` / `functions` 定义做**递归键排序**，即使你每次写代码时字典键序不同，发出去的字符串也字节级一致 —— Tool 定义再大也不会因为键序抖动而反复失效。
- **✂️ 上下文瘦身 (Context Pruner)**：超限时自动截断最早的历史，防止输入 Token 无限膨胀。
- **🧠 语义级裁剪 (Semantic Pruner)**：可选增强 —— 超限时调用一个**便宜模型**把早期对话压缩成一句话摘要，多轮对话更连贯，省 Token 更多。
- **🤐 输出防废话 (Output Constraint)**：自动注入隐藏提示词，让大模型直接给结果，减少输出 Token 浪费。

## 📦 安装

```bash
pip install -e .
```

## 🚀 极简用法

```python
from openai import OpenAI
from token_saver import TokenSaver

raw_client = OpenAI(api_key="your-api-key", base_url="https://api.deepseek.com/v1")
client = TokenSaver(client=raw_client)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个助手。当前时间：2024-05-20 12:00:00"},
        {"role": "user", "content": "给我讲个笑话"},
    ],
)
```

## 🛠️ 高级配置

```python
client = TokenSaver(
    client=raw_client,
    max_history=10,             # 最多保留的消息条数（含 system）
    stabilize_tools=True,       # 是否对 tools 做 JSON 键排序
)
```

### 语义级历史裁剪（省钱利器）

传入一个便宜模型的客户端，超限时自动把早期对话总结成一句话：

```python
from openai import OpenAI

raw_client = OpenAI(...)              # 主模型（贵）
cheap_client = OpenAI(...)            # 便宜模型（如 qwen-turbo / gpt-3.5-turbo）

client = TokenSaver(
    client=raw_client,
    use_semantic_pruning=True,
    summarizer_client=cheap_client,
    summary_model="qwen-turbo",
    keep_recent=4,                    # 保留最近 4 条不压缩
)
```

> ⚠️ 注意：`summarizer_client` 必须是一个**原生**客户端，不要再套一层 `TokenSaver`，否则会递归总结。

## 🧪 测试

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

每次 push 到 GitHub 会自动跑一遍测试（见 `.github/workflows/test.yml`），覆盖 Python 3.8 ~ 3.12。

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request！如果你觉得这个项目帮你省了钱，请给个 ⭐️ Star 支持一下！
