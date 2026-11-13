import json
from typing import Any, Dict


class JsonStabilizer:
    """对请求中的 tools / functions 参数做深度键排序，保证字节级一致。

    背景：Python 3.7+ 的 dict 保留插入顺序，但业务代码每次构造 tools 字典时
    键的顺序可能不同。OpenAI 系的 prompt cache 是按"完整请求前缀"匹配的，
    只要键顺序变一次，几十 K 的 Tool 定义缓存就全部失效。

    原理：json.dumps(sort_keys=True) 会递归排序所有嵌套 dict 的键，再
    json.loads 回来即可得到一个"键名按字母序插入"的 dict。OpenAI SDK 序列化
    时按 dict 的插入顺序输出，因此最终发出去的字符串字节级一致。
    """

    # 新版 tools + 旧版 functions 兼容
    _TOOL_KEYS = ("tools", "functions")

    def stabilize_tools(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """原地替换 kwargs 中的 tools/functions 为深度排序后的结构。"""
        for key in self._TOOL_KEYS:
            if key in kwargs and isinstance(kwargs[key], list):
                kwargs[key] = self._sort_json(kwargs[key])

        # tool_choice 若是结构化 dict（例如指定某个 function），也一并排序，
        # 避免这一小段前缀破坏缓存一致性。
        tool_choice = kwargs.get("tool_choice")
        if isinstance(tool_choice, dict):
            kwargs["tool_choice"] = self._sort_json(tool_choice)

        return kwargs

    @staticmethod
    def _sort_json(obj: Any) -> Any:
        """通过 JSON round-trip 实现所有嵌套 dict 键的递归字母序排序。

        返回一个全新对象，不修改调用方传入的原始数据结构。
        """
        return json.loads(
            json.dumps(
                obj,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
