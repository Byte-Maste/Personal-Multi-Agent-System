from datetime import date, datetime
from pydantic import BaseModel

class TransactionResponse(BaseModel):
    id: str
    transaction_date: date
    description: str | None = None
    merchant: str | None = None
    amount: float
    currency: str = "INR"
    type: str
    category_id: str | None = None
    category_name: str | None = None
    subcategory: str | None = None
    is_recurring: bool = False
    is_anomaly: bool = False

    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
