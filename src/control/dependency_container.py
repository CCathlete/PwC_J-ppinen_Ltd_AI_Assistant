# src/control/dependency_container.py
from dependency_injector import containers, providers

from ..infrastructure.env import Env
from ..infrastructure.logging import create_logger
from ..infrastructure.fs import FileSystem, IFileSystem
from ..infrastructure.openwebui_connector import AIProvider, OpenWebUIConnector
from ..application.ingest_knowledge_bases import KnowledgeBaseIngestionProcess
from ..domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # -------------------- Infrastructure --------------------
    env: providers.Singleton[Env] = providers.Singleton(
        lambda path: Env().load(path).unwrap(),
        path=config.dotenv_path
    )

    fs: providers.Singleton[IFileSystem] = providers.Singleton(FileSystem)

    connector: providers.Singleton[AIProvider] = providers.Singleton(
        OpenWebUIConnector,
        base_url=providers.Callable(
            lambda env: env.vars.get("OPENWEBUI_URL"), env),
        token=providers.Callable(
            lambda env: env.vars.get("OPENWEBUI_TOKEN"), env),
    )

    logger = providers.Singleton(
        create_logger,
        name="app",
        # config.project_root is a Path object from the dict,
        # so we can call .joinpath() on it directly
        log_dir=providers.Callable(
            lambda root: root.joinpath("logs"), config.project_root),
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
        root=config.kb_root,
        logger=logger,
        env=env,
    )
