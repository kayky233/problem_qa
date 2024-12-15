from gpt_api import GPTAPI

# 创建 GPTAPI 实例
api = GPTAPI()

# 获取所有可用模型
models = api.get_models()
print("Available models:")
for model in models:
    print(model)

# 获取响应
response = api.get_chat_response(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's the capital of France?"}],
    temperature=0.6,
    max_tokens=50
)
print("\nGPT Response:")
print(response)
