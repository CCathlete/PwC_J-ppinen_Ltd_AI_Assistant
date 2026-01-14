# infra.fine_tune_rag.py

import os
import httpx
from httpx import Response
from typing import Any
from dotenv import load_dotenv

# Load .env
load_dotenv()

OPENWEBUI_URL = os.getenv("OPENWEBUI_URL", "http://localhost:3000")
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")  # Optional.

if not OPENWEBUI_API_KEY or not OPENAI_API_KEY:
    raise ValueError("Please set OPENWEBUI_API_KEY and OPENAI_API_KEY in your .env file")


def main() -> None:
    """
    We're using a synchronous pattern since we want low latency response.
    """

    headers: dict[str, str] = {"Authorization": f"Bearer {OPENWEBUI_API_KEY}"}

    with httpx.Client(base_url=OPENWEBUI_URL, headers=headers, timeout=60) as client:
        resp: Response = client.get("/api/knowledge-bases")
        resp.raise_for_status()
        kbs: list[dict[str, Any]] = resp.json()
        if not kbs:
            print("No knowledge bases found.")
            exit()

        for kb in kbs:
            kb_id = kb["id"]
            print(f"Reindexing KB '{kb['name']}' (id={kb_id})...")

            reindex_resp = client.post(
                f"/api/knowledge-bases/{kb_id}/reindex",
                json={"embedding_model": "text-embedding-3-large", "openai_api_key": OPENAI_API_KEY}
            )
            reindex_resp.raise_for_status()
            print(f"Reindex started for KB '{kb['name']}'.")

            # 3️⃣Fine tuning a specific assistant.
            if ASSISTANT_ID:
                attach_resp = client.post(
                    f"/api/assistants/{ASSISTANT_ID}/knowledge-bases",
                    json={"kb_ids": [kb_id]}
                )
                attach_resp.raise_for_status()
                print(f"KB '{kb['name']}' attached to assistant {ASSISTANT_ID}.")

    print("Done. All KBs reindex triggered, and attached to assistant if specified.")


if __name__ == '__main__':
    main()
