# src/application/ingest_knowledge_bases.py
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from returns.future import FutureResult, future_safe

from ..domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from ..domain.knowledge_base.kb_config import KnowledgeBaseConfig
from ..infrastructure.env import Env

@dataclass(frozen=True)
class KnowledgeBaseIngestionProcess:
    kb_manager: KnowledgeBaseManager
    root: Path
    env: Env
    logger: "logging.Logger"  # inject logger

    def monitor_and_refresh_kbs(self) -> FutureResult[None, Exception]:
        """
        Continuously monitors KB folders, embedding new files.
        Resilient: errors in a file or folder are logged and skipped.
        """

        @future_safe
        async def _loop() -> None:
            while True:
                for folder in self.kb_manager.fs.list_subfolders(self.root):
                    try:
                        config = KnowledgeBaseConfig.load(folder / "kbconfig.yaml")
                        kb_name = config.name
                    except Exception as e:
                        self.logger.exception(
                            "Failed to load kbconfig for folder '%s': %s", folder, e
                        )
                        continue  # skip this folder

                    try:
                        # Call ingest_folder which handles per-file embedding internally
                        await self.kb_manager.ingest_folder(folder).awaitable()
                        self.logger.info("Finished embedding files for KB '%s'", kb_name)
                    except Exception as e:
                        self.logger.exception(
                            "Error ingesting folder '%s' for KB '%s': %s",
                            folder, kb_name, e
                        )
                        continue  # skip to next folder

                # sleep for refresh interval
                interval: str | bool | int | float = self.env.vars.get("REFRESH_INTERVAL", 60)
                if not isinstance(interval, (int, float)):
                    interval = 60
                await asyncio.sleep(interval)

        return _loop()

