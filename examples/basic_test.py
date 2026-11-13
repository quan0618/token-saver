import datetime
from token_saver import TokenSaver

# 1. 伪造一个原生的 OpenAI 客户端，用来捕捉它收到的请求
class MockCompletions:
    def create(self, **kwargs):
        print("\n=== 拦截并优化后的真实请求参数 ===")
        print(f"消息数量: {len(kwargs['messages'])}")
        for msg in kwargs['messages']:
            print(f"[{msg['role']}]: {msg['content']}")
        return "Mock Response"

class MockChat:
    completions = MockCompletions()

class MockOpenAI:
    chat = MockChat()

# 2. 初始化原生客户端
raw_client = MockOpenAI()

# 3. 用我们的包包裹它 (设置最多保留 4 条历史)
client = TokenSaver(client=raw_client, max_history=4)

# 4. 构造一个复杂、冗长、且带有时间戳的请求
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
messages = [
    {"role": "system", "content": f"你是一个助手。当前时间：{current_time}"},
    {"role": "user", "content": "第1轮问题"},
    {"role": "assistant", "content": "第1轮回答"},
    {"role": "user", "content": "第2轮问题"},
    {"role": "assistant", "content": "第2轮回答"},
    {"role": "user", "content": "第3轮问题"},
    {"role": "assistant", "content": "第3轮回答"},
    {"role": "user", "content": "最后一轮，请问今天天气如何？"}
]

print(f"--- 发送前的原始 messages 数量: {len(messages)} ---")

# 5. 发起请求（触发魔法）
client.chat.completions.create(
    model="deepseek-chat",
    messages=messages
)