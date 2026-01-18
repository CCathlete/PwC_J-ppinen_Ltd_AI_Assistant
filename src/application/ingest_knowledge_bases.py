# src/application/ingest_knowledge_bases.py
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from returns.future import FutureResult, future_safe
from returns.io import IOSuccess, IOFailure, IOResult
from returns.result import Success, Failure

from domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from infrastructure.env import Env


@dataclass(frozen=True)
class KnowledgeBaseIngestionProcess:
    kb_manager: KnowledgeBaseManager
    root: Path
    env: Env
    logger: logging.Logger

    def monitor_and_refresh_kbs(self) -> FutureResult[None, Exception]:
        @future_safe
        async def _loop() -> None:
            interval_raw: str | bool | int | float = self.env.vars.get(
                "REFRESH_INTERVAL", 60)
            interval: float = float(interval_raw) if interval_raw else 60.0

            while True:
                for folder in self.kb_manager.fs.list_subfolders(self.root):

                    self.logger.info(
                        "Starting sync cycle for folder: %s", folder.name)

                    # We treat each folder ingestion as a set of awaitable tasks
                    tasks = self.kb_manager.ingest_folder(folder)

                    if not tasks:
                        continue

                    for task in tasks:
                        result: IOResult[None, Exception] = await task.awaitable()

                        match result:
                            case IOSuccess(Success(_)):
                                self.logger.info(
                                    "Sync cycle completed for folder: %s", folder.name)
                            case IOFailure(Failure(e)):
                                self.logger.error(
                                    "Sync cycle failed for folder %s: %s", folder.name, e)
                                raise e

                            case _: pass

                self.logger.debug(
                    "Sleeping for %s seconds before next refresh", interval)
                await asyncio.sleep(interval)

        return _loop()
