# 基于 Qwen 的智能制造知识库问答 RAG Demo

这是一个适合写进算法/大模型应用实习简历的最小闭环项目，目标是完成：

- 制造业资料上传与解析
- 文档自动切分
- 向量建库与检索
- 基于 Qwen API 的答案生成
- 参考片段回显

项目默认内置了 5 份半导体/智能制造示例资料，可以直接用于本地演示。

## 项目亮点

- 面向智能制造场景，问题贴近晶圆制造、缺陷检测、良率分析等面试高频主题
- 用 `Qwen + Chroma + LangChain Text Splitter + Gradio` 搭出完整 RAG 闭环
- 支持上传 `md / txt / pdf / docx` 资料，便于快速扩展知识库
- 回答附带参考片段，适合展示“基于知识库回答”而不是纯聊天

## 目录结构

```text
.
├── app.py
├── data
│   └── docs
├── requirements.txt
└── src
    └── rag_demo
```

## 快速启动

1. 创建虚拟环境并安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 配置环境变量

```bash
cp .env.example .env
```

如果你使用阿里云 DashScope 的 Qwen 兼容接口，可以按下面填写：

```env
OPENAI_API_KEY=你的 DashScope Key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CHAT_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v3
```

3. 启动 Demo

```bash
python app.py
```

启动后进入页面，先点击“重建知识库”，再输入问题即可。

## 示例问题

- 什么是晶圆制造中的光刻工艺？
- CMP 工艺的作用是什么？
- 半导体缺陷检测常见方法有哪些？
- SPC 在良率提升中起什么作用？

## 适合写在简历上的表述

你可以把这个项目写成：

> 基于 Qwen API、Chroma 与 Gradio 搭建智能制造知识库问答系统，完成制造业文档解析、文本切分、向量检索与答案生成闭环；支持多格式资料上传和参考片段回显，提升垂直领域问答准确性与可解释性。

如果要再强化一点，可以补充两条：

- 设计面向制造场景的中文 Prompt，约束模型基于检索片段作答，降低幻觉
- 通过 Top-K 检索与分块策略优化知识召回效果，提升回答相关性

## 后续可扩展方向

- 加入问答评测集，统计命中率与答案一致性
- 增加重排序模型，提高检索质量
- 引入 Agent，将“问答、总结、术语解释、工艺对比”做成多工具流程
- 后续替换为本地部署开源模型，扩展成“部署 + 应用”组合项目
