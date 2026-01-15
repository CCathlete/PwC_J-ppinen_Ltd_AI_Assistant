# src/infrastructure/openwebui_connector.py

from pathlib import Path
import httpx
from returns.future import FutureResult, future_safe
from httpx import Response

class OpenWebUIConnector:
    """Encapsulates HTTP logic to create KBs and embed files."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def create_kb(self, name: str, description: str, public: bool) -> FutureResult[str, Exception]:
        """Create a new knowledge base."""
        @future_safe
        async def _() -> str:
            async with httpx.AsyncClient() as client:
                r: Response = await client.post(
                    f"{self.base_url}/api/v1/knowledge/",
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json={"name": name, "description": description, "public": public},
                )
                r.raise_for_status()
                return r.json()["id"]

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
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json={"file_id": file_id},
                )
                r2.raise_for_status()

        return _()

