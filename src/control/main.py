from pathlib import Path
from control.app_controller import AppController
from control.dependency_container import Container
import logging

def main() -> None:
    # 1. Instantiate container and logger
    container = Container()
    logger: logging.Logger = container.logger()

    # 2. Instantiate controller
    controller = AppController(
        kb_root=Path("knowledge_bases"),
        dotenv_path=Path(".env"),
        lock_dir=Path("/tmp"),
        logger=logger,
    )

    # 3. Get the processes
    openwebui_proc = controller.serve_openwebui_process()
    ingestion_proc = controller.knowledge_base_ingestion_process()

    # 4. Start them
    openwebui_proc.start()
    ingestion_proc.start()
    logger.info("OpenWebUI and KB ingestion processes started")

    # 5. Wait for both processes
    openwebui_proc.join()
    ingestion_proc.join()
    logger.info("All processes finished")

if __name__ == "__main__":
    main()

