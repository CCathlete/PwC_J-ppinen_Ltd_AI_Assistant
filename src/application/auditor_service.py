from httpx import Client
from returns.result import Result, Success
from infrastructure.litellm_client import post_to_gateway
from domain.models import AuditedResponse, SafetyStatus

def get_grounded_answer(client: Client, question: str) -> Result[str, Exception]:
    messages = [
        {"role": "system", "content": "Answer ONLY using the technical knowledge base. If information is missing, reply 'DATA_MISSING'."},
        {"role": "user", "content": question}
    ]
    return post_to_gateway(client, messages)

def validate_grounding(client: Client, answer: str) -> Result[AuditedResponse, Exception]:
    if "DATA_MISSING" in answer.upper():
        return Success(AuditedResponse(answer="I cannot find that in the manuals.", status=SafetyStatus.NOT_FOUND, confidence_score=1.0))
    
    check_messages = [
        {"role": "system", "content": "Verify if the following text contains specific maintenance instructions. Reply 'VALID' or 'INVALID'."},
        {"role": "user", "content": answer}
    ]
    
    return post_to_gateway(client, check_messages).map(
        lambda res: AuditedResponse(
            answer=answer,
            status=SafetyStatus.VERIFIED if "VALID" in res.upper() else SafetyStatus.UNVERIFIED,
            confidence_score=0.99
        )
    )
