# src/domain/knowledge_base/knowledge_base_manager.py
from pathlib import Path
from dataclasses import dataclass
from returns.future import FutureResult
from ...infrastructure.fs import IFileSystem
from ...infrastructure.openwebui_connector import AIProvider
from .kb_config import KnowledgeBaseConfig

@dataclass(frozen=True)
class KnowledgeBaseManager:
    fs: IFileSystem
    connector: AIProvider

    _embedded_files: dict[str, set[str]]

    def __post_init__(self):
        object.__setattr__(self, "_embedded_files", {})

    def ingest_folder(self, folder: Path) -> FutureResult[None, Exception]:
        config = KnowledgeBaseConfig.load(folder / "kbconfig.yaml")
        return self.connector.create_kb(config.name, config.description, config.public)\
            .bind(lambda kb_id: self._embed_new_files(kb_id, folder))

    def _embed_new_files(self, kb_id: str, folder: Path) -> FutureResult[None, Exception]:
        embedded = self._embedded_files.get(kb_id, set())
        files_to_embed = self.fs.get_unembedded_files(folder, embedded)
        chain: FutureResult[None, Exception] | None = None

        for file in files_to_embed:
            step = self.connector.embed_file(kb_id, file)\
                .map(lambda _: embedded.add(file.name))  # mark as embedded after success
            chain = step if chain is None else chain.bind(lambda _: step)

        self._embedded_files[kb_id] = embedded
        return chain or FutureResult.from_value(None)

