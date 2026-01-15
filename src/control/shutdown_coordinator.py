# src/control/shutdown_coordinator.py
import asyncio
import signal
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ShutdownCoordinator:
    stop_event: asyncio.Event = field(default_factory=asyncio.Event)

    def install_signal_handlers(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._on_signal)

    def _on_signal(self) -> None:
        self.stop_event.set()

    async def wait(self) -> None:
        await self.stop_event.wait()

