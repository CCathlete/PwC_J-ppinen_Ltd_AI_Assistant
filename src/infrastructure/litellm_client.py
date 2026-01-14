from httpx import Client
from returns.result import Success, Failure, Result
from domain.models import MODEL_NAME

def post_to_gateway(client: Client, messages: list[dict[str, str]]) -> Result[str, Exception]:
    try:
        response = client.post(
            "/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0
            }
        )
        response.raise_for_status()
        return Success(response.json()["choices"][0]["message"]["content"])
    except Exception as e:
        return Failure(e)
