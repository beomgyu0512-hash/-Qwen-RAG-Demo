# Qwen RAG Demo Deployment Log

## 项目背景

- 项目名称：基于 Qwen 的智能制造知识库问答 RAG Demo
- 项目目录：`/Users/clea/Documents/GitHub/-Qwen-RAG-Demo`
- 目标：在空仓库中快速搭建一个可运行、可演示、可写入简历的 RAG 闭环 Demo

## 开发过程问题记录

### 1. 初始构建

- 处理：
  - 新建了 `src/rag_demo` 代码目录
  - 新建了 `app.py`
  - 新建了 `requirements.txt`
  - 新建了 `.env.example`
  - 新建了 `README.md`
  - 新建了 `data/docs` 示例资料目录
- 结果：项目具备了最小可运行骨架。

### 2. Python 编译缓存写入系统目录失败

- 现象：执行 `python3 -m compileall app.py src` 时，出现系统缓存目录权限错误。
- 原因：默认 `.pyc` 缓存写入到了系统缓存路径，当前环境无写权限。
- 处理：
  - 改用工作区本地缓存方式执行编译检查：
    - `PYTHONPYCACHEPREFIX=.pycache python3 -m compileall app.py src`
- 结果：编译检查可正常完成。

### 3. Python 版本兼容问题

- 现象：本机 Python 版本为 `3.9.6`，部分代码写法和依赖默认更偏向 Python 3.10+。
- 具体问题：
  - `dataclass(slots=True)` 在当前环境不兼容
  - 代码中出现了 `zip(..., strict=True)` 这类更高版本写法
- 处理：
  - 移除了 `@dataclass(slots=True)` 中的 `slots=True`
  - 将 `zip(..., strict=True)` 改为普通 `zip(...)`
- 结果：代码兼容 Python 3.9。

### 4. 依赖安装失败

- 现象：首次执行 `pip install -r requirements.txt` 时失败。
- 原因：
  - 受限环境下网络访问受阻
  - 部分依赖版本与 Python 3.9 不完全匹配
- 处理：
  - 调整了依赖版本约束
  - 将 `gradio` 限制到 `4.44.x` 兼容区间
  - 增加 `huggingface_hub<1.0` 以匹配当前 `gradio`
- 最终依赖配置：
  - `chromadb>=0.6.3`
  - `gradio>=4.44.0,<5.0.0`
  - `huggingface_hub<1.0`
  - `openai>=1.68.2`
  - 其他基础文档解析依赖
- 结果：依赖成功安装。

### 5. Gradio 与 huggingface_hub 版本不兼容

- 现象：导入 `gradio` 时，出现 `ImportError: cannot import name 'HfFolder'`
- 原因：`gradio 4.44` 与 `huggingface_hub 1.x` 不兼容。
- 处理：
  - 在依赖中显式加入：
    - `huggingface_hub<1.0`
- 结果：`gradio` 可以正常导入。

### 6. Gradio API schema 生成异常

- 现象：页面启动后访问时报错：
  - `TypeError: argument of type 'bool' is not iterable`
- 原因：`gradio 4.44` 在当前组件定义和 API schema 生成过程中存在兼容问题。
- 处理：
  - 将上传组件从 `gr.Files` 调整为更稳的 `gr.File`
  - 设置 `type="filepath"`
  - 在按钮事件中加入 `show_api=False`
  - 避开有问题的 API schema 展示逻辑
- 结果：页面可正常渲染。

### 7. localhost 可达性与端口占用问题

- 现象：
  - Gradio 启动阶段曾提示 localhost 不可访问
  - 之后又出现 `Cannot find empty port in range: 7860-7959`
- 原因：
  - 默认端口区间内已有占用
  - 当前环境的 localhost 检测比较严格
- 处理：
  - 修改启动逻辑，不再固定单端口
  - 在 `app.py` 中按顺序尝试多个候选端口
  - 成功后记录启动地址
- 结果：服务最终成功在本地地址运行。

### 8. 上传文件类型兼容处理

- 现象：不同版本的 Gradio 上传组件返回对象格式可能不同。
- 风险：如果只按字符串路径处理，可能在某些环境报错。
- 处理：
  - 在上传文件保存逻辑中同时兼容：
    - 直接字符串路径
    - 带 `.name` 属性的文件对象
- 结果：上传文件处理更稳。

### 9. 网站上传能力与项目定位的区别

- 问题：需要明确当前网站到底是“只能上传智能制造资料”，还是“技术上可以上传任意文件”。
- 分析：
  - 从程序实现上看，上传组件没有限制行业领域，只限制文件格式。
  - 当前支持的格式包括：
    - `.md`
    - `.txt`
    - `.pdf`
    - `.docx`
  - 只要格式正确，系统都会尝试进行：
    - 文档解析
    - 文本切分
    - 向量建库
    - 检索问答
- 当前项目为什么仍然偏“智能制造”：
  - 内置示例知识文档全部是半导体/智能制造资料
  - Prompt 中将模型角色设定为“智能制造知识库助手”
  - 页面标题和说明文案都围绕智能制造场景
- 结论：
  - 技术能力上：当前网站可以上传任意支持格式的文件
  - 项目语义上：当前仍然是一个智能制造垂直领域 Demo
  - 如果上传其他领域资料，系统也能运行，但回答风格和页面表述仍会带有智能制造背景
- 后续可选优化：
  - 如果要保留简历项目定位，则继续保持“智能制造版”
  - 如果要改成通用知识库网站，则需要进一步修改：
    - 页面标题
    - 页面文案
    - Prompt 中的角色设定


## 当前项目状态

- 已完成项目骨架搭建
- 已完成 RAG 核心链路实现
- 已完成 Gradio 页面
- 已加入智能制造/半导体示例知识文档
- 已处理主要环境兼容问题
- 当前项目可在本地启动并访问页面

## 当前可运行入口

- 启动命令：

```bash
cd /Users/clea/Documents/GitHub/-Qwen-RAG-Demo
source .venv/bin/activate
python app.py
```

- 运行后访问本地地址：
  - `http://127.0.0.1:7860`
  - 或程序实际打印出的其他可用端口

## 后续建议

- 增加异常处理提示，避免页面直接抛底层错误
- 增加一份问答测试集，用于演示效果验证
- 将本文件持续作为项目开发日志维护
