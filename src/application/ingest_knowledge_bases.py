# src/application/ingest_knowledge_bases.py

from pathlib import Path
from ..domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
import asyncio

class KnowledgeBaseIngestionApp:
    def __init__(self, kb_manager: KnowledgeBaseManager, root: Path):
        self.kb_manager = kb_manager
        self.root = root

    async def run(self):
        tasks = [
            self.kb_manager.ingest_folder(folder).awaitable()
            for folder in self.kb_manager.fs.list_subfolders(self.root)
        ]
        await asyncio.gather(*tasks)

