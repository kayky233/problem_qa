import openai
import os

# 从环境变量中读取API密钥
openai.api_key = os.getenv("OPENAI_API_KEY")

# 确保环境变量已正确设置
if not openai.api_key:
    raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")

# 获取并列出所有可用的模型
models = openai.Model.list()

# 打印模型列表
for model in models['data']:
    print(model['id'])

# 示例调用
response = openai.ChatCompletion.create(
    model="gpt-4o-2024-05-13",
    messages=[
        {
            "role": "user",
            "content": "Make a single page website that shows off different neat javascript features for drop-downs and things to display information. The website should be an HTML file with embedded javascript and CSS."
        }
    ],
    temperature=0.7,
    max_tokens=256,
    top_p=1
)

# 打印响应
print(response.choices[0].message['content'].strip())
