from dependency_injector.wiring import Provide, inject
from returns.pipeline import flow
from returns.result import Result, Success, Failure
from control.dependency_container import ApplicationContainer
from application.auditor_service import get_grounded_answer, validate_grounding
from domain.models import AuditedResponse, SafetyStatus
from httpx import Client

@inject
def run_cli(client: Client = Provide[ApplicationContainer.http_client]) -> None:
    print("--- Jäppinen Ltd Maintenance Auditor ---")
    query: str = input("Mechanic Question: ")
    
    result: Result[AuditedResponse, Exception] = flow(
        query,
        lambda q: get_grounded_answer(client, q),
        lambda a: validate_grounding(client, a)
    )
    
    match result:
        case Success(val) if val.status == SafetyStatus.VERIFIED:
            print(f"\n[AUDITED]: {val.answer}")
        case Success(val):
            print(f"\n[UNVERIFIED]: {val.answer}")
        case Failure(err):
            print(f"\n[SYSTEM ERROR]: {err}")

if __name__ == "__main__":
    container = ApplicationContainer()
    container.wire(modules=[__name__])
    run_cli()
