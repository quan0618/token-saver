# 🛡️ LLM Token-Saver

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/project/llm-token-saver/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**LLM Token-Saver** 是一个极致轻量、无侵入的 LLM API 中间件。只需一行代码，就能自动优化你的 Prompt 结构，大幅提升上下文缓存（Context Cache）命中率，并自动修剪冗长的对话历史，帮你直接砍掉 50%+ 的 API 账单！

## ✨ 核心特性

- **⚡ 零侵入接入**：完全兼容 OpenAI 官方 SDK 格式，无需重写业务逻辑。
- **🎯 前缀稳定器 (Prefix Stabilizer)**：自动提取 System Prompt 中的动态变量（如时间戳、随机 ID）到末尾，确保请求前缀字节级一致，强制触发缓存命中。
- **✂️ 上下文瘦身 (Context Pruner)**：自动检测并截断超长对话历史，防止输入 Token 无限膨胀。
- **🤐 输出防废话 (Output Constraint)**：自动注入隐藏提示词，让大模型直接给结果，减少输出 Token 浪费。

## 📦 安装

```bash
pip install llm-token-saver
```

## 🚀 极简用法

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
        {"role": "user", "content": "给我讲个笑话"}
    ]
)
```

## 🛠️ 高级配置

你可以自定义需要保留的上下文轮数：

```python
# 只保留最近的 5 条历史消息
client = TokenSaver(client=raw_client, max_history=5)
```

## 🤝 贡献与反馈

欢迎提交 Issue 或 Pull Request！如果你觉得这个项目帮你省了钱，请给个 ⭐️ Star 支持一下！
```

---

### 2. 更新后的 `pyproject.toml`（直接覆盖）

重点修改了：`name` 字段。如果你想把主页链接也加进去，记得把里面的“你的GitHub用户名”换成你自己的。

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llm-token-saver"
version = "0.1.0"
description = "A seamless LLM API middleware to maximize context cache hits and reduce token costs."
readme = "README.md"
requires-python = ">=3.8"
license = { text = "MIT" }
dependencies = [
    "openai>=1.0.0",
]

[project.urls]
Homepage = "https://github.com/quan0618/token-saver"
```
