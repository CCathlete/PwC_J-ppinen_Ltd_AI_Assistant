# src/control/app_controller.py
import signal
import logging
import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path
from multiprocessing import Process
from types import FrameType

from .dependency_container import Container
from .shutdown_coordinator import ShutdownCoordinator


@dataclass(frozen=True)
class AppController:
    kb_root: Path
    dotenv_path: Path
    lock_dir: Path
    logger: logging.Logger

    def serve_openwebui_process(self) -> Process:
        """Return a Process that runs the OpenWebUI server."""
        p = Process(target=self._run_openwebui, name="OpenWebUIServer", daemon=False)
        return p

    def knowledge_base_ingestion_process(self) -> Process:
        """Return a Process that runs the KB ingestion loop."""
        p = Process(target=self._run_ingestion, name="KBIngestion", daemon=False)
        return p

    # ---------------- Internal helpers ----------------
    
    def _run_openwebui(self) -> None:
        self.logger.info("Starting OpenWebUI process")
        
        # Setup signal handlers so CTRL+C / termination works
        def handle_signal(signum: int, _:FrameType | None) -> None:
            self.logger.info(f"Received signal {signum}, terminating OpenWebUI")
            # subprocess.run will exit on its own; we just log here
            exit(0)

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        try:
            # Run OpenWebUI; blocking call
            subprocess.run(
                ["open-webui", "serve", "--host", "0.0.0.0", "--port", "3000"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            self.logger.exception("OpenWebUI process exited with error: %s", e)
            raise
        except Exception as e:
            self.logger.exception("Unexpected error in OpenWebUI process: %s", e)
            raise
        finally:
            self.logger.info("OpenWebUI process shutdown")

    def _run_ingestion(self) -> None:
        self.logger.info("Starting KB ingestion process")
        # Instantiate DI container in this process
        container = Container()
        container.config.kb_root.from_value(self.kb_root)
        container.config.dotenv_path.from_value(self.dotenv_path)

        shutdown = ShutdownCoordinator()
        shutdown.install_signal_handlers()

        ingestion_app = container.ingestion_app()
        # Run ingestion loop until shutdown signal
        asyncio.run(ingestion_app.monitor_and_refresh_kbs(shutdown.stop_event))
        self.logger.info("KB ingestion process shutdown")

