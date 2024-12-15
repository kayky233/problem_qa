import os
import streamlit as st
import pandas as pd
from datetime import datetime
from gpt_api import GPTAPI  # 使用您已经封装好的 GPTAPI

# 创建 GPTAPI 实例
gpt_api = GPTAPI()

# 支持的文件格式
SUPPORTED_FILE_TYPES = [".pdf", ".docx", ".xlsx"]

# 加载目录下的所有文档
def load_documents_from_directory(directory_path):
    all_documents = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            ext = os.path.splitext(file)[-1].lower()
            try:
                if ext == ".pdf":
                    with open(file_path, "rb") as f:
                        content = f.read()
                    all_documents.append({"type": "pdf", "name": file, "content": content})
                elif ext == ".docx":
                    with open(file_path, "rb") as f:
                        content = f.read()
                    all_documents.append({"type": "docx", "name": file, "content": content})
                elif ext in [".xlsx", ".xls"]:
                    df = pd.read_excel(file_path)
                    content = df.to_string()
                    all_documents.append({"type": "excel", "name": file, "content": content})
            except Exception as e:
                st.error(f"加载文件 {file} 时发生错误：{e}")
    return all_documents

# 初始化文档目录
DOCUMENT_DIRECTORY = "docs"
if not os.path.exists(DOCUMENT_DIRECTORY):
    os.makedirs(DOCUMENT_DIRECTORY)

# 加载所有文档
documents = load_documents_from_directory(DOCUMENT_DIRECTORY)
if len(documents) > 0:
    st.success(f"成功加载 {len(documents)} 个文档！")
else:
    st.warning("当前目录没有有效文档，请添加文档后重试。")

# 定义表格的列
columns = [
    "序号", "版本类型", "单板类型", "问题描述", "问题单号",
    "日志链接", "当前分析人", "当前分析进展", "问题结论",
    "是否闭环", "问题提出人", "创建时间", "停留时间（天）"
]

# 初始化数据
if "data" not in st.session_state:
    if os.path.exists("问题统计.xlsx"):
        st.session_state["data"] = pd.read_excel("问题统计.xlsx")
    else:
        st.session_state["data"] = pd.DataFrame(columns=columns)

# 控制流程状态
if "input_finished" not in st.session_state:
    st.session_state["input_finished"] = False

st.title("问题统计与分析 (支持文档辅助分析)")

# 输入表单
if not st.session_state["input_finished"]:
    st.subheader("请输入问题信息")
    identity_input = st.radio("请选择您的身份：", ["问题提出人", "问题解决人"])

    form_data = {}
    form_data["序号"] = len(st.session_state["data"]) + 1
    form_data["创建时间"] = datetime.now().strftime("%Y-%m-%d")
    form_data["停留时间（天）"] = 0

    if identity_input == "问题提出人":
        form_data["版本类型"] = st.text_input("请输入版本类型")
        form_data["问题描述"] = st.text_area("请输入问题描述")
        form_data["问题单号"] = st.text_input("请输入问题单号（可选）")
        form_data["日志链接"] = st.text_input("请输入日志链接")
        form_data["问题提出人"] = st.text_input("请输入问题提出人")
    else:
        form_data["单板类型"] = st.text_input("请输入单板类型")
        form_data["问题描述"] = st.text_area("请输入问题描述")
        form_data["问题单号"] = st.text_input("请输入问题单号")
        form_data["日志链接"] = st.text_input("请输入日志链接")
        form_data["当前分析人"] = st.text_input("请输入当前分析人")
        form_data["当前分析进展"] = st.text_area("请输入当前分析进展")
        form_data["问题结论"] = st.text_area("请输入问题结论")
        form_data["是否闭环"] = st.radio("问题是否闭环？", ["否", "是"])

    # 提交表单
    if st.button("提交问题信息"):
        if not form_data["问题描述"]:
            st.error("问题描述是必填项，请填写完整！")
        else:
            with st.spinner("正在分析文档内容，请稍候..."):
                # 使用 GPTAPI 分析问题描述
                result = gpt_api.analyze_documents(
                    documents=documents,
                    query=form_data["问题描述"]
                )
                form_data["当前分析进展"] = result.get("analysis", "未能生成分析结果")
            st.session_state["data"] = pd.concat(
                [st.session_state["data"], pd.DataFrame([form_data])],
                ignore_index=True
            )
            st.success("问题已提交！")
            st.session_state["input_finished"] = True

# 展示表格
if st.session_state["input_finished"]:
    st.subheader("当前问题统计表")
    st.dataframe(st.session_state["data"], width=1000)

    # 保存并下载
    st.session_state["data"].to_excel("问题统计.xlsx", index=False)
    with open("问题统计.xlsx", "rb") as file:
        st.download_button(
            label="下载问题统计表",
            data=file,
            file_name="问题统计.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # 重置状态
    if st.button("添加新问题"):
        st.session_state["input_finished"] = False
