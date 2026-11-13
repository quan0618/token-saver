<div align="center">
  <h1>🛡️ LLM Token-Saver</h1>
  <p><strong>一行代码，帮你砍掉 70% 的 LLM API 账单。</strong></p>
  
  [![PyPI version](https://img.shields.io/badge/pypi-v0.3.0-blue.svg)](https://pypi.org/project/llm-token-saver/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
</div>

---

**LLM Token-Saver** 是一个极致轻量、无侵入的 LLM API 中间件。只需一行代码包装你现有的 OpenAI 兼容客户端，就能自动优化 Prompt 结构、最大化上下文缓存（Context Cache）命中率、并压缩超长对话历史。

**为什么你需要它？**
如果你在 System Prompt 里放了时间戳，或者使用 Function Calling 时字典键序发生漂移，你的**缓存命中率会瞬间归零**，API 费用将以原价飙升。Token-Saver 会在后台悄悄帮你修复这些问题。

## ✨ 核心特性

- **⚡ 零侵入接入**：完全兼容 OpenAI 官方 SDK 格式（同步/异步），无需重写业务逻辑。
- **🎯 前缀稳定器 (Prefix Stabilizer)**：自动把动态变量（时间戳等）挪到末尾，确保请求前缀字节级一致，强制触发缓存命中（DeepSeek 命中后价格低至 1 折）。
- **🧩 JSON/Tools 稳定器 (Json Stabilizer)**：对 `tools` / `functions` 定义做递归键排序，彻底避免因 Python 字典键序抖动导致的缓存失效。
- **✂️ 上下文瘦身 (Context Pruner)**：超限时自动截断最早的历史，防止输入 Token 无限膨胀。
- **🧠 语义级裁剪 (Semantic Pruner)**：超限时自动调用便宜模型把早期对话压缩成一句话摘要，多轮对话更连贯，省 Token 更多。
- **🤐 输出防废话 (Output Constraint)**：自动注入隐藏提示词，让大模型直接给结果，减少输出 Token 浪费。

## 📦 安装

```bash
pip install llm-token-saver
```

## 🚀 极简用法 (同步)

只需要用 `TokenSaver` 包装你现有的官方客户端，其他代码完全不用改：

```python
from openai import OpenAI
from token_saver import TokenSaver

# 1. 初始化原生客户端
raw_client = OpenAI(api_key="your-api-key", base_url="https://api.deepseek.com/v1")

# 2. 用 TokenSaver 包裹它！
client = TokenSaver(client=raw_client)

# 3. 像平常一样调用 (Token-Saver 会在后台自动优化)
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个助手。当前时间：2024-05-20 12:00:00"},
        {"role": "user", "content": "给我讲个笑话"},
    ],
)
```

## ⚡ 极简用法 (异步 Async)

完美兼容 `AsyncOpenAI`，不阻塞你的高并发业务：

```python
import asyncio
from openai import AsyncOpenAI
from token_saver import TokenSaver

async def main():
    raw_client = AsyncOpenAI(api_key="your-api-key")
    client = TokenSaver(client=raw_client)
    
    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "你好"}]
    )
    print(response.choices[0].message.content)

asyncio.run(main())
```

## 🛠️ 高级配置

你可以自定义裁剪策略和开关：

```python
client = TokenSaver(
    client=raw_client,
    max_history=10,             # 最多保留的消息条数（含 system）
    stabilize_tools=True,       # 是否对 tools 做 JSON 键排序
)
```

### 🧠 语义级历史裁剪（省钱利器）

传入一个便宜模型的客户端，超限时自动把早期对话总结成一句话，并带有内存缓存（同段历史不重复扣费）：

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
*(⚠️ 注意：`summarizer_client` 必须是原生客户端，不要再套一层 `TokenSaver`，以免递归调用。)*

## 🧪 本地开发与测试

如果你想参与贡献或本地运行测试：

```bash
# 克隆代码后，以开发者模式安装依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v
```
*(每次 push 到 GitHub 会自动跑 CI 测试)*

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request！
如果你觉得这个项目帮你省了钱，请给个 ⭐️ **Star** 支持一下！这是对我最大的鼓励。