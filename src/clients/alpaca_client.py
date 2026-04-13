from decimal import Decimal
from typing import Dict, List, Optional
import os

from alpaca.broker.client import BrokerClient
from alpaca.broker.requests import CreateAccountRequest
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest
from aws_lambda_powertools import Logger

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME", "alpaca_client"))


class AlpacaBrokerClient:
    def __init__(self):
        self.api_key = os.getenv("ALPACA_BROKER_API_KEY")
        self.secret_key = os.getenv("ALPACA_BROKER_SECRET_KEY")
        self.base_url = os.getenv("ALPACA_API_BASE_URL", "https://broker-api.sandbox.alpaca.markets")
        self.enabled = os.getenv("ALPACA_ENABLED", "false").lower() == "true"

        if self.enabled:
            # Using BrokerClient for account management and trading on behalf of users
            self.broker_client = BrokerClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                sandbox=True if "sandbox" in self.base_url else False
            )
            # Market Data Client
            self.data_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key
            )
        else:
            self.broker_client = None
            self.data_client = None
            logger.info("Alpaca Client is disabled (offline-friendly mode)")

    def create_account(self, request_params: dict) -> Optional[str]:
        """
        Creates an Alpaca account for an end-user.
        """
        if not self.enabled:
            logger.info("Skipping Alpaca account creation (disabled)")
            return "mock_alpaca_id_" + request_params.get("email", "unknown")

        try:
            # Simplified request construction for the integration logic
            # In a real scenario, request_params must match CreateAccountRequest fields
            request = CreateAccountRequest(**request_params)
            account = self.broker_client.create_account(request)
            return account.id
        except Exception as e:
            logger.exception(f"Error creating Alpaca account: {e}")
            raise e

    def get_latest_prices(self, symbols: List[str]) -> Dict[str, Decimal]:
        """
        Fetase latest quotes for a list of symbols.
        """
        if not self.enabled:
            return {}

        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbols)
            quotes = self.data_client.get_stock_latest_quote(request)
            return {symbol: Decimal(str(quote.ask_price)) for symbol, quote in quotes.items()}
        except Exception as e:
            logger.exception(f"Error fetching latest prices from Alpaca: {e}")
            return {}

    def place_market_order(self, account_id: str, symbol: str, qty: float, side: str) -> Optional[dict]:
        """
        Places a market order for a specific end-user account.
        """
        if not self.enabled:
            logger.info(f"Mocking {side} order for {qty} shares of {symbol} on account {account_id}")
            return {"id": "mock_order_id", "status": "accepted"}

        try:
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL,
                time_in_force=TimeInForce.GTC
            )
            order = self.broker_client.create_order_for_account_id(account_id, order_request)
            return order.model_dump()
        except Exception as e:
            logger.exception(f"Error placing order on Alpaca for account {account_id}: {e}")
            raise e

    def place_limit_order(self, account_id: str, symbol: str, qty: float, limit_price: float, side: str) -> Optional[dict]:
        """
        Places a limit order for a specific end-user account.
        """
        if not self.enabled:
            logger.info(f"Mocking {side} LIMIT order for {qty} shares of {symbol} at ${limit_price} on account {account_id}")
            return {"id": "mock_limit_order_id", "status": "accepted"}

        try:
            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=qty,
                limit_price=limit_price,
                side=OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL,
                time_in_force=TimeInForce.GTC
            )
            order = self.broker_client.create_order_for_account_id(account_id, order_request)
            return order.model_dump()
        except Exception as e:
            logger.exception(f"Error placing limit order on Alpaca for account {account_id}: {e}")
            raise e
