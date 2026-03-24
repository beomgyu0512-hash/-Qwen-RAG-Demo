# 基于 Qwen 的智能制造知识库问答 RAG Demo

一个面向智能制造场景的轻量级 RAG Demo，支持行业文档上传、文本切分、向量检索、答案生成和参考片段展示。项目默认内置 5 份半导体/制造业示例资料，可直接用于本地演示。

## 功能概览

- 支持 `md / txt / pdf / docx` 多格式文档接入
- 基于 Qwen 兼容接口完成 Embedding 与回答生成
- 使用 Chroma 构建本地向量库并进行 Top-K 检索
- 返回答案的同时展示参考片段，便于人工校验
- 提供 24 条测试问答和批量评测脚本

## 技术栈

- Python
- Qwen API / OpenAI 兼容接口
- LangChain Text Splitters
- Chroma
- Gradio

## 项目结构

```text
.
├── app.py
├── data
│   ├── docs
│   ├── eval
│   └── uploads
├── docs
├── scripts
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

2. 复制环境变量模板

```bash
cp .env.example .env
```

3. 填写模型配置

如果使用阿里云 DashScope 的 Qwen 兼容接口，可参考以下配置：

```env
OPENAI_API_KEY=your_dashscope_key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
CHAT_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v3
```

4. 启动 Demo

```bash
python app.py
```

启动后打开终端输出的本地地址，先点击“重建知识库”，再输入问题。

## 示例问题

- 什么是晶圆制造中的光刻工艺？
- CMP 工艺的作用是什么？
- 半导体缺陷检测常见方法有哪些？
- SPC 在良率提升中起什么作用？

## 测试问答集

项目内置 24 条人工整理的测试问答，位于 [data/eval/test_qa.csv](data/eval/test_qa.csv)。  
每条记录包含问题、标准答案要点和来源文档，可用于人工验证或扩展自动评测。

## 批量评测

运行以下命令可批量执行测试问答，并导出 `csv + md` 结果：

```bash
python scripts/evaluate_rag.py
```

常用参数：

```bash
python scripts/evaluate_rag.py --top-k 4 --input data/eval/test_qa.csv --output-dir data/eval/results
```

输出目录：

- `data/eval/results/eval_result_<timestamp>.csv`
- `data/eval/results/eval_report_<timestamp>.md`

说明：

- 如果知识库尚未建立，脚本会先基于 `data/docs` 自动建库
- 当前评测逻辑采用“答案要点覆盖率”启发式检查，适合快速筛查；正式评估建议结合人工复核

## 开发记录

项目开发过程中的兼容性问题、环境处理和结构调整记录见 [docs/development-notes.md](docs/development-notes.md)。

## 后续方向

- 增加重排序模型，提升检索精度
- 增加自动化评测指标与结果汇总
- 支持更多制造业资料和更细的工艺主题
- 替换为本地部署模型，扩展为完整的“部署 + 应用”示例
