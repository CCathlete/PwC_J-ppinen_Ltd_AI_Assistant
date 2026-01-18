# src/control/dependency_container.py
from pathlib import Path
from dependency_injector import containers, providers

from infrastructure.env import Env
from infrastructure.logging import create_logger
from infrastructure.fs import FileSystem, IFileSystem
from infrastructure.openwebui_connector import AIProvider, OpenWebUIConnector
from application.ingest_knowledge_bases import KnowledgeBaseIngestionProcess
from domain.knowledge_base.knowledge_base_manager import KnowledgeBaseManager

# ------------------------ Factory / Provider functions ------


def env_provider_func(path: str | Path) -> Env:
    return Env().load(path).unwrap()


def get_from_env(env: Env, key: str) -> str | int | float | None:
    return env.vars.get(key)


def get_log_dir(root: Path) -> Path:
    return root / "logs"


# ------------------------ Dependency Container ------------------------


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # -------------------- Infrastructure --------------------

    env: providers.Singleton[Env] = providers.Singleton(
        env_provider_func,
        path=config.dotenv_path
    )

    fs: providers.Singleton[IFileSystem] = providers.Singleton(FileSystem)

    logger = providers.Singleton(
        create_logger,
        name="app",
        # config.project_root is a Path object from the dict,
        log_dir=providers.Callable(get_log_dir, config.project_root),
        logfile_size_limit_mb=config.logfile_size_limit_MB,
    )

    connector: providers.Singleton[AIProvider] = providers.Singleton(
        OpenWebUIConnector,
        base_url=providers.Callable(
            get_from_env,
            env=env,
            key="OPENWEBUI_URL"
        ),
        token=providers.Callable(
            get_from_env,
            env=env,
            key="OPENWEBUI_API_KEY"
        ),
        logger=logger,
    )

    # -------------------- Domain --------------------
    kb_manager: providers.Singleton[KnowledgeBaseManager] = providers.Singleton(
        KnowledgeBaseManager,
        fs=fs,
        connector=connector,
        logger=logger,
        _embedded_files=providers.Object({}),
    )

    # -------------------- Application --------------------
    ingestion_process: providers.Factory[KnowledgeBaseIngestionProcess] = providers.Factory(
        KnowledgeBaseIngestionProcess,
        kb_manager=kb_manager,
        root=config.kb_root,
        logger=logger,
        env=env,
    )
