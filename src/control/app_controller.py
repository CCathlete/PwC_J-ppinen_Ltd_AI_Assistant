# src/control/app_controller.py
import asyncio
from dataclasses import dataclass
from pathlib import Path

from .dependency_container import Container
from .shutdown_coordinator import ShutdownCoordinator
from .process_lock import ProcessLock


@dataclass(frozen=True)
class AppController:
    kb_root: Path
    dotenv_path: Path
    lock_dir: Path

    def run(self) -> None:
        asyncio.run(self._run())

    async def _run(self) -> None:
        container = Container()
        container.config.kb_root.from_value(self.kb_root)
        container.config.dotenv_path.from_value(self.dotenv_path)

        shutdown = ShutdownCoordinator()
        shutdown.install_signal_handlers()

        openwebui_lock = ProcessLock(self.lock_dir / "openwebui.lock")
        ingestion_lock = ProcessLock(self.lock_dir / "ingestion.lock")

        openwebui_lock.acquire()
        ingestion_lock.acquire()

        try:
            ingestion_app = container.ingestion_app()

            await asyncio.gather(
                ingestion_app.monitor_and_refresh_kbs(shutdown.stop_event),
                shutdown.wait(),
            )
        finally:
            ingestion_lock.release()
            openwebui_lock.release()

