# src/control/process_lock.py
import os
from pathlib import Path
from dataclasses import dataclass


class ProcessLockError(RuntimeError):
    pass


@dataclass
class ProcessLock:
    lock_file: Path

    def acquire(self) -> None:
        if self.lock_file.exists():
            raise ProcessLockError(f"Process already running: {self.lock_file}")

        self.lock_file.write_text(str(os.getpid()))

    def release(self) -> None:
        if self.lock_file.exists():
            self.lock_file.unlink()

