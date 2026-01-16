# src/infrastructure/openwebui_connector.py
import httpx
from pathlib import Path
from httpx import Response, HTTPStatusError
from typing import Protocol, Any
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

    def get_kb_files(self, kb_id: str) -> FutureResult[list[str], Exception]:
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
            try:
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

                    kb_id: str = r.json()["id"]

                    self.logger.info(
                        "Successfully created KB: (name - %s, id - %s", name, kb_id)
                    return kb_id

            except HTTPStatusError as e:
                self.logger.error(
                    "HTTP Error creating KB '%s': %s - %s",
                    name, e.response.status_code, e.response.text
                )
                raise e
            except Exception as e:
                self.logger.exception(
                    "Unexpected error creating KB '%s'", name)
                raise e

        return _()

    def embed_file(self, kb_id: str, path: Path) -> FutureResult[None, Exception]:

        @future_safe
        async def _() -> None:
            try:
                self.logger.info(
                    "Uploading file '%s' to KB '%s'", path.name, kb_id)
                async with httpx.AsyncClient() as client:
                    with open(path, "rb") as f:
                        r: Response = await client.post(
                            "%s/api/v1/files/" % self.base_url,
                            headers=self._headers(),
                            files={"file": f},
                        )
                    r.raise_for_status()
                    file_id: str = r.json()["id"]

                    self.logger.info(
                        "Attaching file %s to KB %s", file_id, kb_id)
                    r2: Response = await client.post(
                        "%s/api/v1/knowledge/%s/file/add" % (
                            self.base_url, kb_id),
                        headers={
                            **self._headers(), "Content-Type": "application/json"},
                        json={"file_id": file_id},
                    )
                    r2.raise_for_status()
                    self.logger.info(
                        "File '%s' successfully embedded in '%s'", path.name, kb_id)
            except HTTPStatusError as e:
                self.logger.error(
                    "HTTP Error embedding file '%s': %s - %s",
                    path.name, e.response.status_code, e.response.text
                )
                raise e
            except Exception as e:
                self.logger.exception(
                    "Unexpected error embedding file '%s'", path.name)
                raise e

        return _()

    def get_kb_files(self, kb_id: str) -> FutureResult[list[str], Exception]:
        @future_safe
        async def _() -> list[str]:
            self.logger.info("Fetching remote file list for KB: %s", kb_id)
            async with httpx.AsyncClient() as client:
                r: Response = await client.get(
                    "%s/api/v1/knowledge/%s/files" % (self.base_url, kb_id),
                    headers=self._headers()
                )
                r.raise_for_status()

                # GET .../api/v1/knowledge/{id}/files responds with:
                # {"items": [{"filename": "...", ...}]}
                data = r.json()
                items: list[dict[str, Any]] = data.get("items", [])

                return [
                    item.get("filename", "")
                    for item in items
                    if isinstance(item, dict[str, str]) and item.get("filename")
                ]
        return _()
