# src/domain/knowledge_base/knowledge_base_manager.py
from pathlib import Path
from dataclasses import dataclass
from returns.future import FutureResult, future_safe
from infrastructure.fs import IFileSystem
from infrastructure.openwebui_connector import AIProvider
from .kb_config import KnowledgeBaseConfig

@dataclass(frozen=True)
class KnowledgeBaseManager:
    fs: IFileSystem
    connector: AIProvider

    _embedded_files: dict[str, set[str]] # {kb_id: set(filepath_strs)}

    def __post_init__(self) -> None:
        object.__setattr__(self, "_embedded_files", {})
    
    def fetch_embedded_files(self) -> dict[str, set[str]]:
        return self._embedded_files.copy()

    @future_safe
    def ingest_folder(self, folder: Path) -> FutureResult[None, Exception]:
        config = KnowledgeBaseConfig.load(folder / "kbconfig.yaml")
        return self.connector.create_kb(config.name, config.description, config.public)\
            .bind(lambda kb_id: self._embed_new_files(kb_id, folder))


    def _embed_new_files(self, kb_id: str, folder: Path) -> list[FutureResult[None, Exception]]:
        """
        Return a list of FutureResults, one per file.
        Each file embedding runs independently.
        """
        embedded = self._embedded_files.get(kb_id, set())
        files_to_embed = self.fs.get_unembedded_files(folder, embedded)

        tasks: list[FutureResult[None, Exception]] = []

        for file in files_to_embed:

            @future_safe
            async def embed_file_safe(file=file) -> None:
                try:
                    await self.connector.embed_file(kb_id, file).awaitable()
                    embedded.add(file.name)
                except Exception as e:
                    # Log and continue; per-file error does not fail the folder
                    print(f"Failed to embed file '{file.name}' in folder '{folder}': {e}")

            tasks.append(embed_file_safe())

        # Update embedded_files immediately to track progress
        self._embedded_files[kb_id] = embedded

        return tasks
