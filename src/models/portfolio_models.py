from decimal import Decimal
from typing import Dict, Optional

from clients.alpaca_client import AlpacaBrokerClient
from pydantic import BaseModel, model_validator


class StockPosition(BaseModel):
    symbol: str  # e.g. AAPL, TSLA
    quantity: float
    avg_price: float  # promedio de compra
    current_price: Optional[float] = None

    @classmethod
    def get_current_price(cls, symbol: str) -> Decimal:
        alpaca_client = AlpacaBrokerClient()
        
        if alpaca_client.enabled:
            prices = alpaca_client.get_latest_prices([symbol])
            if symbol in prices:
                return prices[symbol]

        mock_prices = {
            "AAPL": 262.82,
            "TSLA": 433.55,
            "FTEC": 227.04,
            "QQQM": 252.35,
            "ESGV": 117.96,
            "SOXX": 291.06,
            "GLD": 379.38,
            "SIVR": 46.85,
            "LEU": 383
        }
        return Decimal(str(mock_prices.get(symbol, 0.0)))

    @model_validator(mode='before')
    def set_current_price(cls, values: dict) -> dict:
        if 'current_price' not in values or values['current_price'] is None:
            values['current_price'] = cls.get_current_price(values['symbol'])
        return values


class Portfolio(BaseModel):
    portfolio_id: str
    user_id: str
    created_at: str
    updated_at: str
    total_value: float  # TODO: realtime of sum all its StocksPositions current_price * quantity
    stocks: Dict[str, StockPosition] = {}

    class Config:
        from_attributes = True
