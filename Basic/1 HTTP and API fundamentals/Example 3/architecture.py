from fastapi import FastAPI, HTTPException, status, Header
from typing import Annotated
from .pydantic_model import DocumentJobRequest

app = FastAPI()


processed_requests: dict[str, dict[str, str]] = {}

@app.post("/document-job", status_code=status.HTTP_201_CREATED)
def create_document_job(payload: DocumentJobRequest, 
                        idempotency_key: Annotated[str, Header(alias="Idempotency-Key")]) -> dict[str, str]:
    existing_result = processed_requests.get(idempotency_key)

    if existing_result is not None:
        return existing_result

    result =  {
        "job_id": f"job-{len(processed_requests) + 1}",
        "document_id": payload.document_id,
        "status": "accepted",
    }

    processed_requests[idempotency_key] = result
    return result


