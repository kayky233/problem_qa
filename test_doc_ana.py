from gpt_api import GPTAPI

# 初始化 GPTAPI
gpt_api = GPTAPI()

# 加载文档
directory_path = "docs"  # 指定文档目录
documents = gpt_api.extract_text_from_documents(directory_path)

# 检查文档内容
if not documents:
    print("没有有效的文档内容，请检查目录！")
else:
    query = "保持模式是什么？"  # 用户查询
    combined_content = "\n\n".join([doc["content"] for doc in documents])
    result = gpt_api.analyze_large_document(combined_content, query)
    print("\n分析结果：", result)
