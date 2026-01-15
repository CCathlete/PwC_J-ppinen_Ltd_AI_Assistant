from dataclasses import dataclass
from typing import Protocol
from returns.future import FutureResult, future_safe
from returns.result import Result, Success, Failure
from open_webui import OpenWebUI

# ---- AIProvider Protocol ----
class AIProvider(Protocol):
    def embed_text(self, texts: list[str], top_k: int = 5) -> FutureResult[list[list[float]], Exception]:
        ...

    def query(self, prompt: str) -> FutureResult[str, Exception]:
        ...

# ---- Implementation using OpenWebUI ----
@dataclass
class OpenWebUIProvider(AIProvider):
    model: str = "gpt-4o"

    def __post_init__(self):
        self.client = OpenWebUI(model=self.model)

    def embed_text(self, texts: list[str], top_k: int = 5) -> FutureResult[list[list[float]], Exception]:
        @future_safe
        def _embed() -> list[list[float]]:
            return [self.client.embed(text, top_k=top_k) for text in texts]
        return _embed()

    def query(self, prompt: str) -> FutureResult[str, Exception]:
        @future_safe
        def _query() -> str:
            return self.client.complete(prompt)
        return _query()

