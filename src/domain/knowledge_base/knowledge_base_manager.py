# src/domain/knowledge_base/knowledge_base_manager.py

from pathlib import Path
from returns.future import FutureResult
from ...infrastructure.fs import IFileSystem
from ...infrastructure.openwebui_connector import AIProvider
from .kb_config import KnowledgeBaseConfig
from dataclasses import dataclass

@dataclass(frozen=True)
class KnowledgeBaseManager:
    fs: IFileSystem
    connector: AIProvider

    def ingest_folder(self, folder: Path) -> FutureResult[None, Exception]:
        config = KnowledgeBaseConfig.load(folder / "kbconfig.yaml")
        return self.connector.create_kb(config.name, config.description, config.public)\
            .bind(lambda kb_id: self._embed_files(kb_id, folder))

    def _embed_files(self, kb_id: str, folder: Path) -> FutureResult[None, Exception]:
        chain: FutureResult[None, Exception] | None = None
        files = self.fs.list_files(folder, exclude=["kbconfig.yaml"])
        for file in files:
            step = self.connector.embed_file(kb_id, file)
            chain = step if chain is None else chain.bind(lambda _: step)
        return chain or FutureResult.from_value(None)

