import json

from token_saver.optimizers import JsonStabilizer


def test_nested_keys_sorted_recursively():
    stab = JsonStabilizer()
    tools = [
        {
            "type": "function",
            "function": {
                "parameters": {
                    "type": "object",
                    "properties": {
                        "z": {},
                        "a": {"type": "string", "description": "x"},
                    },
                },
                "name": "n",
            },
        }
    ]
    out = stab.stabilize_tools({"tools": tools})
    fn = out["tools"][0]["function"]
    assert list(fn.keys()) == ["name", "parameters"]
    props = fn["parameters"]["properties"]
    assert list(props.keys()) == ["a", "z"]
    assert list(props["a"].keys()) == ["description", "type"]


def test_idempotent():
    stab = JsonStabilizer()
    kwargs = {"tools": [{"b": 1, "a": [{"d": 2, "c": 3}]}]}
    first = stab.stabilize_tools(dict(kwargs))
    second = stab.stabilize_tools(dict(kwargs))
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_original_tools_not_mutated():
    stab = JsonStabilizer()
    tools = [{"b": 1, "a": 2}]
    stab.stabilize_tools({"tools": tools})
    # 原始对象保持原键序，未被原地修改
    assert list(tools[0].keys()) == ["b", "a"]


def test_ignores_non_list_tools():
    stab = JsonStabilizer()
    assert stab.stabilize_tools({"tools": "auto"}) == {"tools": "auto"}


def test_tool_choice_dict_sorted():
    stab = JsonStabilizer()
    kwargs = {
        "tool_choice": {"type": "function", "function": {"name": "x"}},
        "tools": [{"b": 1, "a": 2}],
    }
    out = stab.stabilize_tools(kwargs)
    assert list(out["tool_choice"].keys()) == ["function", "type"]
