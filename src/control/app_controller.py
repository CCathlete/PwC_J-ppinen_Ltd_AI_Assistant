# src/control/app_controller.py
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
    logger: logging.Logger

    def serve_openwebui_process(self) -> Process:
        return Process(target=self._run_openwebui, name="OpenWebUIServer", daemon=False)

    def knowledge_base_ingestion_process(self) -> Process:
        return Process(target=self._run_ingestion, name="KBIngestion", daemon=False)

    def _run_openwebui(self) -> None:
        def handle_signal(signum: int, _: FrameType | None) -> None:
            self.logger.info(
                f"Received signal {signum}, terminating OpenWebUI")
            exit(0)

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        try:
            self.logger.info("Starting OpenWebUI process")
            subprocess.run(
                ["open-webui", "serve", "--host", "0.0.0.0", "--port", "3000"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(
                f"OpenWebUI process exited with error code {e.returncode}")
        except Exception:
            self.logger.exception("Unexpected crash in OpenWebUI process")

    def _run_ingestion(self) -> None:
        try:
            self.logger.info("Starting KB ingestion process")

            container = Container()
            container.config.kb_root.from_value(self.kb_root)
            container.config.dotenv_path.from_value(self.dotenv_path)
            container.config.project_root

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
                        self.logger.exception(
                            "Internal error during KB ingestion loop")

                    await asyncio.sleep(1)

            asyncio.run(resilient_loop())

        except Exception:
            self.logger.exception(
                "KBIngestion process failed during initialization")
        finally:
            self.logger.info("KB ingestion process shutdown")
