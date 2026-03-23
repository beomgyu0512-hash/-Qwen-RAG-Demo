from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AppConfig:
    project_root: Path
    data_dir: Path
    docs_dir: Path
    upload_dir: Path
    chroma_dir: Path
    api_key: str
    base_url: str
    chat_model: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    collection_name: str = "manufacturing_knowledge"

    @classmethod
    def from_env(cls) -> "AppConfig":
        project_root = Path(__file__).resolve().parents[2]
        data_dir = project_root / "data"
        return cls(
            project_root=project_root,
            data_dir=data_dir,
            docs_dir=data_dir / "docs",
            upload_dir=data_dir / "uploads",
            chroma_dir=data_dir / "chroma",
            api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            base_url=os.getenv(
                "OPENAI_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ).strip(),
            chat_model=os.getenv("CHAT_MODEL", "qwen-plus").strip(),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-v3").strip(),
            chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "100")),
            top_k=int(os.getenv("TOP_K", "4")),
        )

    def ensure_dirs(self) -> None:
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
