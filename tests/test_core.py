import copy

from token_saver import TokenSaver


class RecordingCompletions:
    def __init__(self):
        self.received = None

    def create(self, **kwargs):
        self.received = kwargs
        return "Mocked Response"


class RecordingChat:
    def __init__(self):
        self.completions = RecordingCompletions()


class RecordingOpenAI:
    def __init__(self):
        self.chat = RecordingChat()


def _make_client(**kw):
    raw = RecordingOpenAI()
    client = TokenSaver(client=raw, **kw)
    return raw, client


def test_prefix_stabilized():
    raw, client = _make_client(max_history=10)
    messages = [
        {"role": "system", "content": "你是助手。当前时间：2024-01-01 00:00:00"},
        {"role": "user", "content": "hi"},
    ]
    client.chat.completions.create(model="x", messages=messages)
    got = raw.chat.completions.received["messages"]
    assert got[0]["content"].startswith("你是助手。")
    assert "系统动态信息" in got[0]["content"]
    assert got[0]["content"].endswith("2024-01-01 00:00:00")


def test_context_pruned():
    raw, client = _make_client(max_history=3)
    messages = [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "q3"},
    ]
    client.chat.completions.create(model="x", messages=messages)
    got = raw.chat.completions.received["messages"]
    assert len(got) == 3
    assert [m["role"] for m in got] == ["system", "assistant", "user"]
    assert got[1]["content"] == "a2"
    # 最后一条 user 会追加输出约束，但仍保留原文前缀
    assert got[2]["content"].startswith("q3")


def test_output_constraint_appended():
    raw, client = _make_client(max_history=10)
    messages = [{"role": "user", "content": "hi"}]
    client.chat.completions.create(model="x", messages=messages)
    got = raw.chat.completions.received["messages"]
    assert "不要输出客套话" in got[-1]["content"]


def test_tools_sorted_recursively():
    raw, client = _make_client(max_history=10)
    tools = [
        {
            "type": "function",
            "function": {
                "parameters": {"type": "object", "properties": {"b": {}, "a": {}}},
                "name": "get_weather",
                "description": "查询天气",
            },
        }
    ]
    client.chat.completions.create(
        model="x", messages=[{"role": "user", "content": "hi"}], tools=tools
    )
    fn = raw.chat.completions.received["tools"][0]["function"]
    # description < name < parameters（字母序）
    assert list(fn.keys()) == ["description", "name", "parameters"]
    assert list(fn["parameters"]["properties"].keys()) == ["a", "b"]


def test_original_messages_not_mutated():
    raw, client = _make_client(max_history=10)
    messages = [
        {"role": "system", "content": "当前时间：2024-01-01 00:00:00"},
        {"role": "user", "content": "hi"},
    ]
    snapshot = copy.deepcopy(messages)
    client.chat.completions.create(model="x", messages=messages)
    # 调用方原始数据不应被优化器原地修改
    assert messages == snapshot
