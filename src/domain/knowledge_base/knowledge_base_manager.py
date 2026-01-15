# domain/knowledge_base/knowledge_base_manager.py
import logging
from pathlib import Path
from dataclasses import dataclass
from returns.io import IOFailure, IOResult
from returns.future import FutureResult, future_safe

from .kb_config import KnowledgeBaseConfig
from ...infrastructure.fs import IFileSystem
from ...infrastructure.openwebui_connector import AIProvider

@dataclass(frozen=True)
class KnowledgeBaseManager:
    fs: IFileSystem
    connector: AIProvider
    _embedded_files: dict[str, set[str]]  # {kb_id: set(filepath_strs)}
    logger: logging.Logger

    def __post_init__(self) -> None:
        object.__setattr__(self, "_embedded_files", {})

    def fetch_embedded_files(self) -> dict[str, set[str]]:
        return self._embedded_files.copy()

    def ingest_folder(self, folder: Path) -> list[FutureResult[None, Exception]]:
        """
        Return one FutureResult per file in folder.
        KB is created only once if needed.
        Failures are per-file and logged.
        """
        try:
            config = KnowledgeBaseConfig.load(folder / "kbconfig.yaml")
        except Exception as e:
            self.logger.exception("Failed to load kbconfig for folder '%s': %s", folder, e)
            return []

        kb_name = config.name
        embedded = self._embedded_files.get(kb_name, set())
        files_to_embed = self.fs.get_unembedded_files(folder, embedded)

        if not files_to_embed:
            return []

        kb_id_future: FutureResult[str, Exception]
        if kb_name not in self._embedded_files:
            # Create KB first if it does not exist
            kb_id_future = self.connector.create_kb(
                config.name, config.description, config.public
            )
        else:
            kb_id_future = FutureResult.from_value(kb_name)

        @future_safe
        async def embed_file(file: Path, kb_id_future: FutureResult[str, Exception] = kb_id_future) -> None:
            try:
                # After awaiting the future monad it returns a static monad so instead 
                # of FutureResult we get IOResult.
                # NOTE: We're awaiting here because we don't want to proceed before the kb is created.
                io_res: IOResult[str, Exception] = await kb_id_future.awaitable()

                match io_res:
                    case IOResult(success=value):
                        kb_id: str = value
                        await self.connector.embed_file(kb_id, file).awaitable()
                        embedded.add(file.name)

                    case IOFailure(failure=e):
                        self.logger.exception(
                            "Failed to create KB for folder '%s': %s", folder, e
                        )

                    case _:
                        pass  # exhaustive catch-all

            except Exception as e:
                self.logger.exception(
                    "Failed to embed file '%s' in folder '%s': %s", file.name, folder, e
                )


        tasks: list[FutureResult[None, Exception]] = [embed_file(file) for file in files_to_embed]

        # Update embedded files immediately to track progress
        self._embedded_files[kb_name] = embedded

        return tasks


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
                    self.logger.exception(
                        "Failed to embed file '%s' in folder '%s': %s", file.name, folder, e
                    )

            tasks.append(embed_file_safe())

        self._embedded_files[kb_id] = embedded
        return tasks

