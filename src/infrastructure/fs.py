# src/infrastructure/fs.py
from pathlib import Path
from typing import Protocol

class IFileSystem(Protocol):
    """Filesystem operations."""

    def list_subfolders(self, root: Path) -> list[Path]:
        ...

    def list_files(self, folder: Path, exclude: list[str] = []) -> list[Path]:
        ...

    def get_unembedded_files(self, folder: Path, embedded_files: set[str]) -> list[Path]:
        """Return files in folder that are not yet embedded."""
        ...

class FileSystem:
    """Concrete FS helper."""

    def list_subfolders(self, root: Path) -> list[Path]:
        return [f for f in root.iterdir() if f.is_dir()]

    def list_files(self, folder: Path, exclude: list[str] = []) -> list[Path]:
        return [f for f in folder.iterdir() if f.is_file() and f.name not in exclude]

    def get_unembedded_files(self, folder: Path, embedded_files: set[str]) -> list[Path]:
        """Return files in folder that are not yet embedded."""
        files = self.list_files(folder, exclude=["kbconfig.yaml"])
        return [f for f in files if f.name not in embedded_files]

