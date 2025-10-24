from enum import Enum

from pydantic import BaseModel


class OrderType(str, Enum):
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Order(BaseModel):
    order_id: str
    user_id: str
    portfolio_id: str
    symbol: str
    quantity: float
    price: float  # precio por acción
    order_type: OrderType
    created_at: str
    updated_at: str
    status: OrderStatus
