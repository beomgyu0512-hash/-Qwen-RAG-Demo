from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from uuid import uuid4

import chromadb
import docx2txt
from chromadb.api.models.Collection import Collection
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pypdf import PdfReader

from src.rag_demo.config import AppConfig


SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf", ".docx"}


@dataclass
class RetrievedChunk:
    source: str
    chunk_id: int
    content: str
    score: float | None = None


class QwenClient:
    def __init__(self, config: AppConfig) -> None:
        if not config.api_key:
            raise ValueError("未检测到 OPENAI_API_KEY，请先配置 .env。")
        self.chat_model = config.chat_model
        self.embedding_model = config.embedding_model
        self.client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=[text.replace("\n", " ").strip() for text in texts],
        )
        return [item.embedding for item in response.data]

    def embed_query(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=text.replace("\n", " ").strip(),
        )
        return response.data[0].embedding

    def answer(self, question: str, context: str) -> str:
        system_prompt = (
            "你是智能制造知识库助手。"
            "请严格基于提供的参考资料作答，不要虚构不存在的工艺参数或结论。"
            "如果资料不足，请明确说明“知识库资料不足以回答该问题”。"
            "回答时优先给出结论，再给出要点，语言简洁、专业。"
        )
        user_prompt = (
            f"用户问题：{question}\n\n"
            "参考资料：\n"
            f"{context}\n\n"
            "请基于参考资料回答，并在最后补一句“依据知识库片段整理”。"
        )
        response = self.client.chat.completions.create(
            model=self.chat_model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content.strip()


class ManufacturingRAGService:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig.from_env()
        self.config.ensure_dirs()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", "。", "；", "，", " ", ""],
        )

    def _client(self) -> chromadb.PersistentClient:
        return chromadb.PersistentClient(path=str(self.config.chroma_dir))

    def _collection(self) -> Collection:
        client = self._client()
        return client.get_collection(self.config.collection_name)

    def _load_text(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
        if suffix == ".docx":
            return docx2txt.process(str(path)).strip()
        return path.read_text(encoding="utf-8").strip()

    def _load_documents(self, paths: Iterable[Path]) -> list[Document]:
        documents: list[Document] = []
        for path in paths:
            if path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            text = self._load_text(path)
            if not text:
                continue
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "source_path": str(path),
                    },
                )
            )
        return documents

    def _split_documents(self, documents: list[Document]) -> list[Document]:
        chunks = self.splitter.split_documents(documents)
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = index
        return chunks

    def sample_files(self) -> list[Path]:
        return sorted(
            path
            for path in self.config.docs_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
        )

    def save_uploaded_files(self, files: list[object] | None) -> list[Path]:
        saved_paths: list[Path] = []
        for file_item in files or []:
            raw_path = getattr(file_item, "name", file_item)
            src = Path(str(raw_path))
            if src.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            target = self.config.upload_dir / f"{uuid4().hex}_{src.name}"
            shutil.copy2(src, target)
            saved_paths.append(target)
        return saved_paths

    def build_index(self, uploaded_files: list[object] | None = None) -> list[Path]:
        qwen = QwenClient(self.config)
        files = self.sample_files()
        files.extend(self.save_uploaded_files(uploaded_files))
        if not files:
            raise ValueError("未找到可入库文档，请先在 data/docs 中放入资料或通过页面上传文件。")

        documents = self._load_documents(files)
        if not documents:
            raise ValueError("文档已找到，但未解析出有效文本。请检查文件格式或内容。")

        chunks = self._split_documents(documents)
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        ids = [f"chunk-{index}" for index in range(len(chunks))]
        embeddings = qwen.embed_texts(texts)

        client = self._client()
        try:
            client.delete_collection(self.config.collection_name)
        except Exception:
            pass
        collection = client.create_collection(name=self.config.collection_name)
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return files

    def is_ready(self) -> bool:
        try:
            self._collection()
            return True
        except Exception:
            return False

    def answer_question(
        self,
        question: str,
        top_k: int | None = None,
    ) -> tuple[str, list[RetrievedChunk]]:
        if not question.strip():
            raise ValueError("请输入问题。")
        if not self.is_ready():
            raise ValueError("知识库尚未建立，请先点击“重建知识库”。")

        qwen = QwenClient(self.config)
        collection = self._collection()
        query_embedding = qwen.embed_query(question)
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k or self.config.top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = result["documents"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        snippets: list[RetrievedChunk] = []
        context_parts: list[str] = []
        for rank, (content, metadata, distance) in enumerate(
            zip(documents, metadatas, distances),
            start=1,
        ):
            snippets.append(
                RetrievedChunk(
                    source=metadata["source"],
                    chunk_id=int(metadata.get("chunk_id", rank)),
                    content=content,
                    score=float(distance) if distance is not None else None,
                )
            )
            context_parts.append(
                f"[片段{rank}] 来源：{metadata['source']}\n{content}"
            )

        answer = qwen.answer(question=question, context="\n\n".join(context_parts))
        return answer, snippets

    @staticmethod
    def format_sources(snippets: list[RetrievedChunk]) -> str:
        if not snippets:
            return "暂无参考片段。"

        lines = ["### 参考片段"]
        for index, snippet in enumerate(snippets, start=1):
            score_text = ""
            if snippet.score is not None:
                score_text = f" | 检索距离: {snippet.score:.4f}"
            lines.append(
                f"**{index}. {snippet.source} / Chunk {snippet.chunk_id}**{score_text}\n\n"
                f"{snippet.content.strip()}\n"
            )
        return "\n".join(lines)
