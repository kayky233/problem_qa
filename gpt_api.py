import openai
import os
import pdfplumber
import pytesseract
from PIL import Image
import PyPDF2
from concurrent.futures import ThreadPoolExecutor, as_completed

class GPTAPI:
    def __init__(self, api_key=None):
        """
        初始化 GPTAPI 类，支持通过环境变量或直接传递 API 密钥。
        """
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")

        if not openai.api_key:
            raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")

    def get_models(self):
        """
        获取并返回可用的所有模型列表。
        :return: List of model IDs
        """
        try:
            models = openai.Model.list()
            return [model['id'] for model in models['data']]
        except openai.error.OpenAIError as e:
            print(f"Error fetching models: {e}")
            return []

    def get_chat_response(self, model: str, messages: list, temperature: float = 0.7, max_tokens: int = 512):
        """
        向 OpenAI API 发送聊天请求，获取响应。
        :param model: (str) 要使用的模型 ID。
        :param messages: (list) 消息内容，以字典形式传递，例如：{'role': 'user', 'content': 'Hello!' }
        :param temperature: (float) 控制生成的多样性，默认 0.7。
        :param max_tokens: (int) 最大令牌数，默认 512。
        :return: 响应文本
        """
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response['choices'][0]['message']['content'].strip()
        except openai.error.OpenAIError as e:
            print(f"Error fetching response: {e}")
            return None

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        使用 pdfplumber 提取 PDF 文档中所有页面的文本内容。
        """
        full_text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        full_text += f"第{i+1}页:\n{page_text}\n\n"
                    else:
                        print(f"警告: 第{i+1}页未提取到文本内容")
            return full_text.strip()
        except Exception as e:
            print(f"PDF 提取失败: {e}")
            return ""

    def extract_text_with_ocr(self, file_path: str) -> str:
        """
        使用 OCR 提取扫描版 PDF 文档的文本内容。
        """
        text = ""
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page_number, page in enumerate(reader.pages):
                    # 使用 OCR 处理页面图像
                    image = page.to_image(resolution=300)
                    page_text = pytesseract.image_to_string(Image.open(image.stream))
                    text += f"第{page_number + 1}页:\n{page_text}\n\n"
            return text.strip()
        except Exception as e:
            print(f"OCR 提取失败: {e}")
            return ""

    def extract_text_from_documents(self, directory_path: str) -> list:
        """
        扫描目录中的文档（PDF 和 TXT 文件），提取文本内容。
        :param directory_path: (str) 包含文档的目录路径。
        :return: (list) 文档列表，每个元素包含 'name' 和 'content'。
        """
        documents = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[-1].lower()
                text = ""

                try:
                    if ext == ".pdf":
                        text = self.extract_text_from_pdf(file_path)
                        if not text:
                            text = self.extract_text_with_ocr(file_path)
                    elif ext == ".txt":
                        with open(file_path, "r", encoding="utf-8") as f:
                            text = f.read()

                    if text:
                        documents.append({"name": file, "content": text})
                        print(f"已加载文档: {file}, 字符数: {len(text)}")
                    else:
                        print(f"文档 {file} 解析失败或内容为空！")
                except Exception as e:
                    print(f"处理文件 {file} 出错: {e}")

        print(f"\n共加载 {len(documents)} 个文档！")
        return documents

    def analyze_large_document(self, document_content: str, query: str, model: str = "gpt-4", chunk_size: int = 3000):
        """
        分段处理大文本内容，按块传递给 GPT 模型进行分析。
        :param document_content: (str) 提取到的文档完整文本。
        :param query: (str) 用户查询。
        :param model: (str) GPT 模型。
        :param chunk_size: (int) 每次传递的最大字符数。
        :return: 总结结果。
        """
        if not document_content or not query:
            return "文档内容或查询问题为空，无法进行分析。"

        # 按 chunk_size 切分文档内容
        chunks = [document_content[i:i + chunk_size] for i in range(0, len(document_content), chunk_size)]
        results = []

        print(f"文档已拆分为 {len(chunks)} 个部分，每部分 {chunk_size} 字符")

        # 遍历每个 chunk，逐块发送给 GPT
        for idx, chunk in enumerate(chunks):
            print(f"分析第 {idx + 1}/{len(chunks)} 部分...")
            prompt = f"请根据以下文档内容回答问题: {query}\n\n{chunk}"
            try:
                response = self.get_chat_response(
                    model=model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的文档分析助手，能够基于提供的文档内容回答问题。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024
                )
                results.append(response if response else "")
            except Exception as e:
                print(f"分析第 {idx + 1} 部分出错: {e}")
                results.append("")

        # 合并所有部分的结果
        final_summary = "\n".join(results).strip()
        return final_summary

    def extract_relevant_content(self, document_content: str, keywords: list) -> str:
        """
        根据关键词从文档内容中提取相关段落。
        :param document_content: (str) 文档完整文本。
        :param keywords: (list) 关键词列表。
        :return: 提取的相关段落。
        """
        relevant_content = []
        for line in document_content.split("\n"):
            if any(keyword in line for keyword in keywords):
                relevant_content.append(line)
        return "\n".join(relevant_content)

    def analyze_chunk(self, chunk: str, query: str, model: str = "gpt-4") -> str:
        """
        分析单个文档块内容。
        """
        try:
            prompt = f"请根据以下文档内容回答问题: {query}\n\n{chunk}"
            response = self.get_chat_response(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的文档分析助手，能够基于提供的文档内容回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512
            )
            return response if response else ""
        except Exception as e:
            print(f"分析块内容失败: {e}")
            return ""

    def analyze_large_document_parallel(self, document_content: str, query: str, model: str = "gpt-4", chunk_size: int = 3000, max_workers: int = 4):
        """
        并行分析大文本内容，按块传递给 GPT 模型进行分析。
        """
        if not document_content or not query:
            return "文档内容或查询问题为空，无法进行分析。"

        # 按 chunk_size 切分文档内容
        chunks = [document_content[i:i + chunk_size] for i in range(0, len(document_content), chunk_size)]
        print(f"文档已拆分为 {len(chunks)} 个部分，每部分 {chunk_size} 字符")

        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {executor.submit(self.analyze_chunk, chunk, query, model): chunk for chunk in chunks}

            for future in as_completed(future_to_chunk):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"并行处理任务出错: {e}")

        # 合并所有部分的结果
        final_summary = "\n".join(results).strip()
        return final_summary
