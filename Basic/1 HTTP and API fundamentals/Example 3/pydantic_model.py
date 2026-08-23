from pydantic import BaseModel

class DocumentJobRequest(BaseModel):
    document_id: str
