# src/application/ingest_knowledge_bases.py
import asyncio
from pathlib import Path
from dataclasses import dataclass
from returns.future import FutureResult, future_safe

from ..domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from ..domain.knowledge_base.kb_config import KnowledgeBaseConfig
from ..infrastructure.env import Env

@dataclass(frozen=True)
class KnowledgeBaseIngestionApp:
    kb_manager: KnowledgeBaseManager
    root: Path
    env: Env  # injected singleton

    def monitor_and_refresh_kbs(self) -> FutureResult[None, Exception]:
        """
        Continuously monitors KB folders, embedding new files.
        Returns a FutureResult that will fail if any ingestion fails.
        """

        @future_safe
        async def _loop() -> None:
            while True:
                tasks_monads: list[FutureResult[None, Exception]] = []
                for folder in self.kb_manager.fs.list_subfolders(self.root):
                    config = KnowledgeBaseConfig.load(folder / "kbconfig.yaml")
                    kb_name = config.name

                    embedded_files = self.kb_manager.fetch_embedded_files().get(kb_name, set())
                    new_files = self.kb_manager.fs.get_unembedded_files(folder, embedded_files)

                    if new_files:
                        # ingest_folder returns a FutureResult
                        tasks_monads.append(self.kb_manager.ingest_folder(folder))

                if tasks_monads:
                    # gather and propagate the first failure if any had occured.
                    results = await asyncio.gather(*(task.awaitable() for task in tasks_monads), return_exceptions=True)
                    for res in results:
                        if isinstance(res, Exception):
                            raise res

                interval: str | bool | int | float = self.env.vars.get("REFRESH_INTERVAL", 60)
                if not isinstance(interval, (int, float)):
                    interval = 60
                await asyncio.sleep(interval)

        return _loop()

