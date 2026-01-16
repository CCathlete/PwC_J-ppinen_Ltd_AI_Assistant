# domain/knowledge_base/knowledge_base_manager.py
import logging
from pathlib import Path
from dataclasses import dataclass
from returns.io import IOResult, IOSuccess, IOFailure
from returns.future import FutureResult, future_safe
from returns.result import Success, Failure

from .kb_config import KnowledgeBaseConfig
from ...infrastructure.fs import IFileSystem
from ...infrastructure.openwebui_connector import AIProvider


@dataclass(frozen=True)
class KnowledgeBaseManager:
    fs: IFileSystem
    connector: AIProvider
    _embedded_files: dict[str, set[str]]
    logger: logging.Logger

    def __post_init__(self) -> None:
        object.__setattr__(self, "_embedded_files", {})

    def fetch_embedded_files(self) -> dict[str, set[str]]:
        return self._embedded_files.copy()

    def ingest_folder(self, folder: Path) -> list[FutureResult[None, Exception]]:
        try:
            config = KnowledgeBaseConfig.load(folder / "kbconfig.yaml")
        except Exception as e:
            self.logger.exception(
                "Failed to load kbconfig for folder '%s': %s", folder, e)
            return []

        kb_name: str = config.name

        @future_safe
        async def orchestrate_ingestion() -> None:
            kb_res = await self.connector.create_kb(
                config.name, config.description, config.public
            ).awaitable()

            match kb_res:
                case IOSuccess(Success(kb_id)):
                    remote_res: IOResult[list[str], Exception] = await self.connector.get_kb_files(kb_id).awaitable()

                    match remote_res:
                        case IOSuccess(Success(remote_filenames)):
                            local_files: list[Path] = [
                                f for f in self.fs.list_files(folder)
                                if f.name != "kbconfig.yaml" and not f.name.startswith(".")
                            ]

                            to_upload: list[Path] = [
                                f for f in local_files if f.name not in remote_filenames
                            ]

                            if not to_upload:
                                self.logger.info(
                                    "KB '%s' is up to date.", kb_name)
                                return

                            self.logger.info(
                                "Found %s files missing from KB '%s'.", len(to_upload), kb_name)

                            for file in to_upload:
                                try:
                                    res: IOResult[None, Exception] = await self.connector.embed_file(kb_id, file).awaitable()
                                    match res:
                                        case IOSuccess(Success(_)):
                                            self.logger.info(
                                                "Successfully synced: %s", file.name)
                                        case IOFailure(Failure(err)):
                                            self.logger.error(
                                                "Failed to sync file '%s': %s", file.name, err)
                                        case _: pass
                                except Exception as e:
                                    self.logger.exception(
                                        "Unexpected error syncing '%s': %s", file.name, e)

                        case IOFailure(Failure(e)):
                            self.logger.error(
                                "Could not fetch remote state for KB '%s': %s", kb_name, e)
                        case _: pass

                case IOFailure(Failure(e)):
                    self.logger.error(
                        "KB creation/resolution failed for '%s': %s", kb_name, e)
                case _: pass

        return [orchestrate_ingestion()]
