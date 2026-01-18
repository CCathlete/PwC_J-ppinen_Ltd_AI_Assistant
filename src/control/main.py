# src/control/main.py
import logging
from typing import Any
from pathlib import Path
from dotenv import load_dotenv
from returns.result import Success, Result

from .app_controller import AppController
from .dependency_container import Container
load_dotenv()

def main() -> None:
    config: dict[str, Any] = {
        "kb_root": Path("knowledge_bases"),
        "dotenv_path": Path(".env"),
        "lock_dir": Path("/tmp"),
        "project_root": Path(__file__).parents[2],
        "logfile_size_limit_MB": 10,
    }

    run_app(config).alt(
        lambda err: print(f"Application failed: {err}")
    )


def run_app(config: dict[str, Any]) -> Result[None, Exception]:
    container = Container()
    container.config.from_dict(config)

    logger: logging.Logger = container.logger()

    controller = AppController(
        kb_root=config["kb_root"],
        dotenv_path=config["dotenv_path"],
        lock_dir=config["lock_dir"],
        project_root=config["project_root"],
        logfile_size_limit_MB=config["logfile_size_limit_MB"],
        logger=logger,
    )

    return Success(controller).map(execute_lifecycle)


def execute_lifecycle(controller: AppController) -> None:
    openwebui_proc = controller.serve_openwebui_process()
    ingestion_proc = controller.knowledge_base_ingestion_process()

    openwebui_proc.start()
    ingestion_proc.start()

    openwebui_proc.join()
    ingestion_proc.join()


if __name__ == "__main__":
    main()
