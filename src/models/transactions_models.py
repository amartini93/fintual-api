from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class TransactionStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"


class Transaction(BaseModel):
    amount: int = Field(..., example=100.0)
    created_at: str = Field(..., example="2025-07-01T00:00:00")
    status: TransactionStatus
    transaction_id: str = Field(..., example="uuid4")
    transaction_type: TransactionType = Field(..., example="deposit")
    updated_at: str = Field(..., example="2025-07-01T00:00:00")
    user_id: str = Field(..., example="user_123")
