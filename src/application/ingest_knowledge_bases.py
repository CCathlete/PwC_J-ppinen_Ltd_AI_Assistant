# src/application/ingest_knowledge_bases.py

import asyncio
from pathlib import Path
from dataclasses import dataclass

from ..domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager


@dataclass(frozen=True)
class KnowledgeBaseIngestionApp:
    kb_manager:KnowledgeBaseManager
    root: Path

    async def monitor_and_refresh_kbs(self):
        tasks = [
            self.kb_manager.ingest_folder(folder).awaitable()
            for folder in self.kb_manager.fs.list_subfolders(self.root)
        ]
        await asyncio.gather(*tasks)

