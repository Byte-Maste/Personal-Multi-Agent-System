from pydantic import BaseModel

class UploadResponse(BaseModel):
    statement_id: str
    file_name: str
    status: str
    transactions_count: int = 0
    message: str = ""
