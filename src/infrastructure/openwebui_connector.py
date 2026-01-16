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
    base_url: str
    token: str

    def _headers(self) -> dict[str, str]:
        ...

    def create_kb(self, name: str, description: str, public: bool) -> FutureResult[str, Exception]:
        ...

    def embed_file(self, kb_id: str, path: Path) -> FutureResult[None, Exception]:
        ...


@dataclass(frozen=True)
class OpenWebUIConnector(AIProvider):
    base_url: str
    token: str
    logger: Logger

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer %s" % self.token}

    def create_kb(self, name: str, description: str, public: bool) -> FutureResult[str, Exception]:
        @future_safe
        async def _() -> str:
            self.logger.info("Creating Knowledge Base: %s", name)
            async with httpx.AsyncClient() as client:
                r: Response = await client.post(
                    "%s/api/v1/knowledge/" % self.base_url,
                    headers={
                        **self._headers(), "Content-Type": "application/json"},
                    json={"name": name, "description": description,
                          "public": public},
                )
                r.raise_for_status()

                self.logger.info("Successfully created KB: %s", name)
                return name

        return _()

    def embed_file(self, kb_id: str, path: Path) -> FutureResult[None, Exception]:
        @future_safe
        async def _() -> None:
            self.logger.info("Uploading file '%s' to KB '%s'",
                             path.name, kb_id)
            async with httpx.AsyncClient() as client:
                with open(path, "rb") as f:
                    r: Response = await client.post(
                        "%s/api/v1/files/" % self.base_url,
                        headers=self._headers(),
                        files={"file": f},
                    )
                r.raise_for_status()
                file_id: str = r.json()["id"]
                self.logger.info("File uploaded successfully. ID: %s", file_id)

                self.logger.info("Attaching file %s to KB %s", file_id, kb_id)
                r2: Response = await client.post(
                    "%s/api/v1/knowledge/%s/file/add" % (self.base_url, kb_id),
                    headers={
                        **self._headers(), "Content-Type": "application/json"},
                    json={"file_id": file_id},
                )
                r2.raise_for_status()
                self.logger.info(
                    "File '%s' successfully embedded in '%s'", path.name, kb_id)

        return _()
