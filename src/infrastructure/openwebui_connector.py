# src/infrastructure/openwebui_connector.py
import httpx
import asyncio
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
from httpx import Response
from returns.future import FutureResult, future_safe

from .logging import Logger


class AIProvider(ABC):
    base_url: str
    token: str

    @abstractmethod
    def get_all_kbs(self) -> FutureResult[dict[str, str], Exception]:
        ...

    @abstractmethod
    def embed_file(self, kb_id: str, path: Path) -> FutureResult[None, Exception]:
        ...

    @abstractmethod
    def get_kb_files(self, kb_id: str) -> FutureResult[list[str], Exception]:
        ...


@dataclass(frozen=True)
class OpenWebUIConnector(AIProvider):
    base_url: str
    token: str
    logger: Logger

    def __post_init__(self) -> None:
        self.logger.info(
            "BASE_URL=%r IS_TOKEN=%s",
            self.base_url,
            bool(self.token)
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer %s" % self.token}

    def get_all_kbs(self) -> FutureResult[dict[str, str], Exception]:
        @future_safe
        async def _() -> dict[str, str]:
            clean_url = self.base_url.strip().rstrip("/")

            async with httpx.AsyncClient(timeout=30.0) as client:
                r: Response = await client.get(
                    f"{clean_url}/api/v1/knowledge/",
                    headers={
                        **self._headers(),
                        "Accept": "application/json",
                    },
                )
                r.raise_for_status()

                items: list[dict[str, str]] = r.json().get("items", [])

                return {
                    item["name"]: item["id"]
                    for item in items
                    if "name" in item and "id" in item
                }

        return _()

    def embed_file(
        self,
        kb_id: str,
        path: Path,
    ) -> FutureResult[None, Exception]:
        @future_safe
        async def _() -> None:
            clean_url = self.base_url.strip().rstrip("/")

            async with httpx.AsyncClient(timeout=30.0) as client:
                # 1. Upload File -------------------------------------------
                self.logger.info("Uploading: %s", path.name)
                with open(path, "rb") as f:
                    r = await client.post(
                        f"{clean_url}/api/v1/files/",
                        headers={
                            **self._headers(),
                            "Accept": "application/json"
                        },
                        files={"file": f}
                    )
                r.raise_for_status()
                file_id: str = r.json()["id"]

                # 2. Poll for 'completed' status --------------------------
                max_retries = 10
                for i in range(max_retries):
                    status_res = await client.get(
                        f"{clean_url}/api/v1/files/{file_id}/process/status",
                        headers=self._headers()
                    )
                    status_res.raise_for_status()
                    status = status_res.json().get("status")

                    if status == "completed":
                        break
                    if status == "failed":
                        raise Exception(
                            "Embedding failed for file %s" % file_id)

                    self.logger.debug(
                        "Waiting for embedding: %s (attempt %s)", path.name, i+1)
                    await asyncio.sleep(2)
                else:
                    raise Exception(
                        "Timeout waiting for file processing: %s" % file_id)

                # 3. Add to Knowledge Base -------------------------------
                self.logger.info("Attaching %s to KB %s", path.name, kb_id)
                r2 = await client.post(
                    f"{clean_url}/api/v1/knowledge/{kb_id}/file/add",
                    headers={
                        **self._headers(), "Content-Type": "application/json"},
                    json={"file_id": file_id}
                )
                r2.raise_for_status()

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
                items: list[dict[str, str]] = data.get("items", [])

                return [
                    item.get("filename", "")
                    for item in items
                    if item and item.get("filename")
                ]
        return _()
