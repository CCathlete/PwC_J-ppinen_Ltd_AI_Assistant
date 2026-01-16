import logging
from pathlib import Path
from typing import TypeAlias

Logger: TypeAlias = logging.Logger


# The file handler class doesn't go well with data classes.
class TruncatingFileHandler(logging.FileHandler):
    def __init__(
        self,
        filename: Path,
        max_bytes: int,
        mode: str = "a",
        encoding: str | None = None,
        delay: bool = False,
    ) -> None:
        self.max_bytes: int = max_bytes
        filename.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(
            filename=str(filename),
            mode=mode,
            encoding=encoding,
            delay=delay,
        )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self.stream and self.stream.tell() >= self.max_bytes:
                self.stream.seek(0)
                self.stream.truncate()
            super().emit(record)
        except Exception:
            self.handleError(record)


def create_logger(
    *,
    name: str,
    log_dir: Path,
    logfile_size_limit_mb: int,
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    handler = TruncatingFileHandler(
        filename=log_dir / "app.log",
        max_bytes=logfile_size_limit_mb * 1024 * 1024,
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
