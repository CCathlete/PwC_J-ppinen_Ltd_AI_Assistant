import logging
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TruncatingFileHandler(logging.FileHandler):
    filename: Path
    max_bytes: int
    mode: str = "a"
    encoding: str | None = None
    delay: bool = False

    def __post_init__(self) -> None:
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(
            filename=self.filename,
            mode=self.mode,
            encoding=self.encoding,
            delay=self.delay,
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
        return logger  # singleton safety

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

