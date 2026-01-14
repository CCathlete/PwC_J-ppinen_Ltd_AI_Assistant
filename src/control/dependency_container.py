import os
from dependency_injector import containers, providers
from httpx import Client

class ApplicationContainer(containers.DeclarativeContainer):
    http_client = providers.Singleton(
        Client,
        base_url="http://localhost:4000/v1",
        headers={"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"},
        timeout=60.0
    )
