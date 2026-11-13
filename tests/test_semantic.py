from types import SimpleNamespace

from token_saver.optimizers import SemanticPruner


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        msg = SimpleNamespace(content="用户之前讨论了天气。")
        choice = SimpleNamespace(message=msg)
        return SimpleNamespace(choices=[choice])


class FakeChat:
    def __init__(self):
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()


def _messages(n_others):
    return [{"role": "system", "content": "SYS"}] + [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg{i}"}
        for i in range(n_others)
    ]


def test_no_prune_when_under_limit():
    pruner = SemanticPruner(max_messages=100, summarizer_client=FakeClient())
    msgs = _messages(5)
    assert pruner.optimize(msgs) == msgs


def test_summarizes_when_over_limit():
    client = FakeClient()
    pruner = SemanticPruner(
        max_messages=6,
        summarizer_client=client,
        summary_model="qwen-turbo",
        keep_recent=4,
    )
    msgs = _messages(12)  # 1 system + 12 others = 13 > 6
    out = pruner.optimize(msgs)
    # 1 system + 1 summary + 4 recent = 6
    assert len(out) == 6
    assert out[0]["content"] == "SYS"
    assert out[1]["role"] == "system"
    assert out[1]["content"].startswith("[对话历史摘要]")
    assert client.chat.completions.calls
    assert client.chat.completions.calls[0]["model"] == "qwen-turbo"


def test_falls_back_without_summarizer():
    pruner = SemanticPruner(max_messages=6, summarizer_client=None, keep_recent=4)
    out = pruner.optimize(_messages(12))
    # 无 summarizer：退化为简单裁剪 = system(1) + 最近 5 条
    assert len(out) == 6
    assert out[0]["content"] == "SYS"
    assert all(m["role"] != "system" for m in out[1:])


def test_falls_back_on_summary_error():
    class BrokenCompletions:
        def create(self, **kwargs):
            raise RuntimeError("boom")

    class BrokenChat:
        completions = BrokenCompletions()

    class BrokenClient:
        chat = BrokenChat()

    pruner = SemanticPruner(
        max_messages=6, summarizer_client=BrokenClient(), keep_recent=4
    )
    out = pruner.optimize(_messages(12))
    # 总结失败 → 退化为简单裁剪，不抛异常
    assert len(out) == 6
    assert out[0]["content"] == "SYS"
