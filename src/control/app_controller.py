# src/control/app_controller.py
import sys
import signal
import asyncio
import logging
import subprocess
from pathlib import Path
from types import FrameType
from dataclasses import dataclass
from multiprocessing import Process
from returns.future import FutureResult

from .dependency_container import Container
from .shutdown_coordinator import ShutdownCoordinator


@dataclass(frozen=True)
class AppController:
    kb_root: Path
    dotenv_path: Path
    lock_dir: Path
    project_root: Path
    logfile_size_limit_MB: int
    logger: logging.Logger

    def serve_openwebui_process(self) -> Process:
        return Process(target=self._run_openwebui, name="OpenWebUIServer", daemon=False)

    def knowledge_base_ingestion_process(self) -> Process:
        return Process(target=self._run_ingestion, name="KBIngestion", daemon=False)

    def _run_openwebui(self) -> None:
        import time

        # Local state for the process loop
        running = True

        def handle_signal(signum: int, _: FrameType | None) -> None:
            nonlocal running
            self.logger.info(
                f"Received signal {signum}, stopping OpenWebUI watchdog")
            running = False

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        self.logger.info("Starting OpenWebUI watchdog loop")
        
        bin_dir: Path = Path(sys.executable).parent
        openwebui: Path = bin_dir / "open-webui"

        while running:
            try:
                # Running without capture_output to see the server logs
                subprocess.run(
                    [str(openwebui), "serve", "--host", "0.0.0.0", "--port", "3000"],
                    check=True
                )
            except subprocess.CalledProcessError as e:
                self.logger.warning(
                    f"OpenWebUI exited with code {e.returncode}. "
                    "Likely port 3000 is occupied. Retrying in 5s..."
                )
            except Exception:
                self.logger.exception("Unexpected error in OpenWebUI watchdog")

            if running:
                time.sleep(5)

        self.logger.info("OpenWebUI process shutdown complete")

    def _run_ingestion(self) -> None:
        try:
            self.logger.info("Starting KB ingestion process")

            # Re-initialize and re-configure the container inside the new process memory space
            container = Container()
            container.config.from_dict({
                "kb_root": self.kb_root,
                "dotenv_path": self.dotenv_path,
                "project_root": self.project_root,
                "logfile_size_limit_MB": self.logfile_size_limit_MB
            })

            shutdown = ShutdownCoordinator()
            shutdown.install_signal_handlers()

            ingestion_app = container.ingestion_process()

            async def resilient_loop() -> None:
                while not shutdown.stop_event.is_set():
                    try:
                        result: FutureResult[None, Exception] = ingestion_app.monitor_and_refresh_kbs(
                        )
                        await result.awaitable()
                    except Exception:
                        self.logger.exception("Error during KB ingestion loop")

                    await asyncio.sleep(1)

            asyncio.run(resilient_loop())
        except Exception:
            self.logger.exception(
                "KBIngestion process crashed during initialization")
