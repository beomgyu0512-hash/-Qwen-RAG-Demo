from __future__ import annotations

import gradio as gr

from src.rag_demo.rag_service import ManufacturingRAGService


service = ManufacturingRAGService()


def rebuild_knowledge_base(files):
    used_files = service.build_index(uploaded_files=files)
    names = "、".join(path.name for path in used_files)
    return f"知识库已重建，共纳入 {len(used_files)} 份资料：{names}"


def answer_question(question, top_k):
    answer, snippets = service.answer_question(question=question, top_k=top_k)
    return answer, service.format_sources(snippets)


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Qwen 智能制造 RAG Demo") as demo:
        gr.Markdown(
            """
            # Qwen 智能制造知识库 Demo
            上传制造业资料后可重建知识库，并基于检索片段生成回答与参考引用。

            - 默认使用仓库内置的半导体示例资料
            - 支持 `md / txt / pdf / docx`
            - 首次使用前请先在 `.env` 中配置 Qwen 兼容 API Key
            """
        )

        with gr.Row():
            files = gr.File(
                label="上传制造业资料",
                file_count="multiple",
                file_types=[".md", ".txt", ".pdf", ".docx"],
                type="filepath",
            )
            with gr.Column():
                top_k = gr.Slider(
                    minimum=2,
                    maximum=6,
                    value=4,
                    step=1,
                    label="检索片段数",
                )
                rebuild_button = gr.Button("重建知识库", variant="primary")

        kb_status = gr.Textbox(
            label="知识库状态",
            value="尚未建库。请先点击“重建知识库”。",
            interactive=False,
        )
        question = gr.Textbox(
            label="输入问题",
            placeholder="例如：CMP 工艺的作用是什么？",
            lines=3,
        )
        ask_button = gr.Button("开始问答")
        answer = gr.Markdown(label="回答")
        sources = gr.Markdown(label="参考片段")

        gr.Examples(
            examples=[
                ["什么是晶圆制造中的光刻工艺？"],
                ["CMP 工艺的核心作用是什么？"],
                ["半导体缺陷检测常见方法有哪些？"],
                ["SPC 在良率提升中起什么作用？"],
            ],
            inputs=question,
        )

        rebuild_button.click(
            fn=rebuild_knowledge_base,
            inputs=files,
            outputs=kb_status,
            show_api=False,
        )
        ask_button.click(
            fn=answer_question,
            inputs=[question, top_k],
            outputs=[answer, sources],
            show_api=False,
        )

    return demo
