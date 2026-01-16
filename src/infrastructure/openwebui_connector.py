# src/infrastructure/openwebui_connector.py
import httpx
from pathlib import Path
from httpx import Response
from typing import Protocol
from dataclasses import dataclass
from returns.future import FutureResult, future_safe

from .logging import Logger


@dataclass(frozen=True)
class AIProvider(Protocol):
    """Encapsulates HTTP logic to create KBs and embed files."""

    base_url: str
    token: str

    def _headers(self) -> dict[str, str]:
        ...

    def create_kb(self, name: str, description: str, public: bool) -> FutureResult[str, Exception]:
        """Create a new knowledge base."""
        ...

    def embed_file(self, kb_id: str, path: Path) -> FutureResult[None, Exception]:
        """Upload a file and attach it to a KB."""
        ...


@dataclass(frozen=True)
class OpenWebUIConnector(AIProvider):
    """Encapsulates HTTP logic to create KBs and embed files."""

    base_url: str
    token: str
    logger: Logger

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    def create_kb(self, name: str, description: str, public: bool) -> FutureResult[str, Exception]:
        """Create a new knowledge base."""
        @future_safe
        async def _() -> str:
            async with httpx.AsyncClient() as client:

                r: Response = await client.post(
                    f"{self.base_url}/api/v1/knowledge/",
                    headers={
                        **self._headers(), "Content-Type": "application/json"},
                    json={"name": name, "description": description,
                          "public": public},
                )
                r.raise_for_status()

                # return r.json()["id"]
                # Using the name of the KB as its id if creation was successful.
                return name

        return _()

    def embed_file(self, kb_id: str, path: Path) -> FutureResult[None, Exception]:
        """Upload a file and attach it to a KB."""
        @future_safe
        async def _() -> None:
            async with httpx.AsyncClient() as client:
                # Upload file
                with open(path, "rb") as f:
                    r: Response = await client.post(
                        f"{self.base_url}/api/v1/files/",
                        headers=self._headers(),
                        files={"file": f},
                    )
                r.raise_for_status()
                file_id: str = r.json()["id"]

                # Attach to KB
                r2: Response = await client.post(
                    f"{self.base_url}/api/v1/knowledge/{kb_id}/file/add",
                    headers={
                        **self._headers(), "Content-Type": "application/json"},
                    json={"file_id": file_id},
                )
                r2.raise_for_status()

        return _()
