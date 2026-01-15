# src/application/ingest_knowledge_bases.py
import asyncio
from pathlib import Path
from dataclasses import dataclass
from ..domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from ..infrastructure.env import Env

@dataclass(frozen=True)
class KnowledgeBaseIngestionApp:
    kb_manager: KnowledgeBaseManager
    root: Path
    env: Env  # injected singleton

    async def monitor_and_refresh_kbs(self):
        while True:
            tasks = []
            for folder in self.kb_manager.fs.list_subfolders(self.root):
                # get files not yet embedded
                new_files = self.kb_manager.fs.get_unembedded_files(folder)
                if new_files:
                    # ingest only new files
                    tasks.append(self.kb_manager.ingest_files(folder, new_files).awaitable())
            if tasks:
                await asyncio.gather(*tasks)

            # fetch refresh interval from env, default to 60s if missing
            interval: str | bool | int | float = self.env.vars.get("REFRESH_INTERVAL", 60)
            assert isinstance(interval, float)
            await asyncio.sleep(interval)

