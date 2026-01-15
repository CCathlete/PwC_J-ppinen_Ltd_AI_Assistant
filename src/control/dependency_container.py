# src/control/dependency_container.py
from dependency_injector import containers, providers

from ..infrastructure.env import Env
from ..infrastructure.logging import create_logger
from ..infrastructure.fs import FileSystem, IFileSystem
from ..infrastructure.openwebui_connector import AIProvider
from ..application.ingest_knowledge_bases import KnowledgeBaseIngestionProcess
from ..domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the app."""

    config = providers.Configuration()  # runtime config for paths, .env, etc.

    # -------------------- Infrastructure --------------------
    env: providers.Singleton[Env] = providers.Singleton(
        lambda path: Env().load(path).unwrap(),
        path=config.dotenv_path  # e.g. ".env"
    )

    fs: providers.Singleton[IFileSystem] = providers.Singleton(FileSystem)
    connector: providers.Singleton[AIProvider] = providers.Singleton(AIProvider)

    logger = providers.Singleton(
    create_logger,
    name="app",
    log_dir=config.project_root.provided.joinpath("logs"),
    logfile_size_limit_mb=config.logfile_size_limit_MB,
    )

    # -------------------- Domain --------------------
    kb_manager: providers.Singleton[KnowledgeBaseManager] = providers.Singleton(
        KnowledgeBaseManager,
        fs=fs,
        connector=connector,
        logger=logger,
    )

    # -------------------- Application --------------------
    ingestion_process: providers.Factory[KnowledgeBaseIngestionProcess] = providers.Factory(
        KnowledgeBaseIngestionProcess,
        kb_manager=kb_manager,
        root=config.kb_root,  # Path to KB root folder
        logger=logger,
        env=env,
    )

