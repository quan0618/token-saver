import pytest

from token_saver import TokenSaver


class MockAsyncCompletions:
    def __init__(self):
        self.received = None

    async def create(self, **kwargs):
        self.received = kwargs
        return "Mocked Async Response"


class MockAsyncChat:
    def __init__(self):
        self.completions = MockAsyncCompletions()


class MockAsyncOpenAI:
    def __init__(self):
        self.chat = MockAsyncChat()


@pytest.mark.asyncio
async def test_async_client_interception():
    raw = MockAsyncOpenAI()
    client = TokenSaver(client=raw, max_history=3)

    messages = [
        {"role": "system", "content": "你是助手。当前时间：2024-01-01 00:00:00"},
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "q3"},
    ]

    res = await client.chat.completions.create(model="x", messages=messages)

    assert res == "Mocked Async Response"

    got = raw.chat.completions.received["messages"]
    # 裁剪：system + 最近 2 条 = 3 条
    assert len(got) == 3
    assert [m["role"] for m in got] == ["system", "assistant", "user"]
    # 时间戳被优化：动态部分挪到 system 内容末尾
    assert got[0]["content"].startswith("你是助手。")
    assert "系统动态信息" in got[0]["content"]
    assert got[0]["content"].endswith("2024-01-01 00:00:00")
