# src/control/dependency_container.py
from dependency_injector import containers, providers

from ..infrastructure.fs import FileSystem, IFileSystem
from ..infrastructure.openwebui_connector import AIProvider
from ..infrastructure.env import Env
from ..domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager
from ..application.ingest_knowledge_bases import KnowledgeBaseIngestionApp


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the app."""

    config = providers.Configuration()  # runtime config for paths, .env, etc.

    # -------------------- Infrastructure --------------------
    env: providers.Singleton[Env] = providers.Singleton(
        lambda path: Env().load(path),
        config.dotenv_path  # e.g. ".env"
    )

    fs: providers.Singleton[IFileSystem] = providers.Singleton(FileSystem)
    connector: providers.Singleton[AIProvider] = providers.Singleton(AIProvider)

    # -------------------- Domain --------------------
    kb_manager: providers.Singleton[KnowledgeBaseManager] = providers.Singleton(
        KnowledgeBaseManager,
        fs=fs,
        connector=connector,
    )

    # -------------------- Application --------------------
    ingestion_app: providers.Factory[KnowledgeBaseIngestionApp] = providers.Factory(
        KnowledgeBaseIngestionApp,
        kb_manager=kb_manager,
        root=config.kb_root,  # Path to KB root folder
        env=env,
    )

