# src/inrastructure/fs.py

from pathlib import Path
from typing import Protocol

class IFileSystem(Protocol):
    """
    Filesystem Operations.
    """

    def list_subfolders(self, root: Path) -> list[Path]:
        """Return subfolders in root."""
        ...

    def list_files(self, folder: Path, exclude: list[str] = []) -> list[Path]:
        """Return files in folder, excluding specified filenames."""
        ...

class FileSystem:
    """Helper for filesystem operations."""

    def list_subfolders(self, root: Path) -> list[Path]:
        """Return subfolders in root."""
        return [f for f in root.iterdir() if f.is_dir()]

    def list_files(self, folder: Path, exclude: list[str] = []) -> list[Path]:
        """Return files in folder, excluding specified filenames."""
        return [f for f in folder.iterdir() if f.is_file() and f.name not in exclude]

