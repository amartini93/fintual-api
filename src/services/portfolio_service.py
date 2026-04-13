from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict
import os

from aws_lambda_powertools import Logger

from clients.alpaca_client import AlpacaBrokerClient
from exceptions.dynamodb_exceptions import DynamoDBItemNotFoundException
from models.orders_models import Order, OrderStatus, OrderType
from models.portfolio_models import Portfolio, StockPosition
from repositories.orders_repository import OrderRepository
from repositories.portfolio_repository import PortfolioRepository
from repositories.user_repository import UserRepository

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class PortfolioService:
    @classmethod
    def create_portfolio(cls, portfolio: Portfolio) -> bool:
        try:
            # Check if user exists
            user = UserRepository._get_user(portfolio.user_id)
            if not user:
                logger.error(f"User not found {portfolio.user_id}")
                raise DynamoDBItemNotFoundException("User not found")
            return PortfolioRepository._put_portfolio(portfolio)
        except Exception as e:
            logger.exception(f"Exception raised in create_portfolio: {e}")
            raise e

    @classmethod
    def update_portfolio(cls, portfolio_id: str, updates: dict) -> bool:
        try:
            repository_response = UserRepository._update_user(portfolio_id, updates)
            if not repository_response:
                logger.warning(f"Portfolio {portfolio_id} not found or not updated")
                return False
        except Exception as e:
            logger.exception(f"Exception raised in update_portfolio: {e}")
            raise e

    @classmethod
    def process_order(cls, order: Order) -> bool:
        try:
            logger.info("Processing order", order_id=order.order_id, type=order.order_type)

            order.updated_at = str(datetime.now(timezone.utc).isoformat())
            user = UserRepository._get_user(order.user_id)
            if not user:
                logger.error(f"User not found {order.user_id}")
                order.status = OrderStatus.FAILED
                OrderRepository._put_order(order)
                return False

            portfolio = PortfolioRepository._get_portfolio(order.portfolio_id)
            if not portfolio:
                logger.error(f"Portfolio not found {order.portfolio_id}")
                order.status = OrderStatus.FAILED
                OrderRepository._put_order(order)
                return False

            symbol = order.symbol
            quantity = Decimal(str(order.quantity))
            price = Decimal(str(order.price))
            total_cost = price * quantity

            if order.order_type == OrderType.BUY_LIMIT:
                if user.balance < total_cost:
                    logger.warning(f"Insufficient balance for user {order.user_id}")
                    order.status = OrderStatus.FAILED
                    OrderRepository._put_order(order)
                    return False

                # Update user balance
                new_balance = Decimal(user.balance) - total_cost
                UserRepository._update_user(user.user_id, updates={"balance": new_balance})

                # Update portfolio stocks
                current_position = portfolio.stocks.get(symbol)
                if current_position:
                    total_quantity = Decimal(str(current_position.quantity)) + quantity
                    total_invested = (
                        Decimal(str(current_position.avg_price)) * Decimal(str(current_position.quantity))
                        + price * quantity
                    )
                    new_avg_price = total_invested / total_quantity
                    current_position.quantity = float(total_quantity)
                    current_position.avg_price = float(new_avg_price)
                else:
                    current_position = StockPosition(
                        symbol=symbol,
                        quantity=float(quantity),
                        avg_price=float(price)
                    )

                portfolio.stocks[symbol] = current_position

            elif order.order_type == OrderType.SELL_LIMIT:
                current_position = portfolio.stocks.get(symbol)
                if not current_position or Decimal(str(current_position.quantity)) < quantity:
                    logger.warning(f"Insufficient stock holdings to sell {symbol}")
                    order.status = OrderStatus.FAILED
                    OrderRepository._put_order(order)
                    return False

                new_quantity = Decimal(str(current_position.quantity)) - quantity
                if new_quantity <= 0:
                    portfolio.stocks.pop(symbol)
                else:
                    current_position.quantity = float(new_quantity)
                    portfolio.stocks[symbol] = current_position

                # Add cash to user
                new_balance = Decimal(user.balance) + total_cost
                UserRepository._update_user(user.user_id, updates={"balance": new_balance})

            else:
                logger.error(f"Unsupported order type: {order.order_type}")
                order.status = OrderStatus.FAILED
                OrderRepository._put_order(order)
                return False

            # Update portfolio with serialized StockPosition dicts
            stocks_dict = {k: v.model_dump() for k, v in portfolio.stocks.items()}
            for stock in stocks_dict.values():
                for k, v in stock.items():
                    if isinstance(v, float):
                        stock[k] = Decimal(str(v))

            PortfolioRepository._update_portfolio(
                portfolio.portfolio_id,
                updates={"stocks": stocks_dict}
            )

            # Alpaca Synchronization (Enabled/Disabled inside client)
            if user.alpaca_account_id:
                alpaca_client = AlpacaBrokerClient()
                alpaca_client.place_limit_order(
                    account_id=user.alpaca_account_id,
                    symbol=symbol,
                    qty=float(quantity),
                    limit_price=float(price),
                    side="BUY" if order.order_type == OrderType.BUY_LIMIT else "SELL"
                )

            order.status = OrderStatus.COMPLETED
            OrderRepository._put_order(order)
            logger.info(f"Order {order.order_id} completed successfully")
            return True

        except Exception as e:
            logger.exception(f"Exception raised in PortfolioService.process_order: {e}")
            order.status = OrderStatus.FAILED
            OrderRepository._put_order(order)
            raise e

    @classmethod
    def portfolio_value(cls, portfolio: Portfolio) -> Decimal:
        try:
            logger.info("Calculating portfolio value", portfolio_id=portfolio.portfolio_id)
            total_value = Decimal("0")

            # Fetch real prices from Alpaca if enabled
            alpaca_client = AlpacaBrokerClient()
            symbols = list(portfolio.stocks.keys())
            real_prices = alpaca_client.get_latest_prices(symbols) if symbols else {}

            for stock in portfolio.stocks.values():
                quantity = Decimal(str(stock.quantity))
                # Use real price if available, fallback to current_price then avg_price
                price = real_prices.get(stock.symbol)
                if not price:
                    price = Decimal(str(stock.current_price)) if stock.current_price else Decimal(str(stock.avg_price))
                
                total_value += quantity * price
                logger.info(f"Stock {stock.symbol} value: {price}")
            
            logger.info(f"Total portfolio value: {total_value}")
            portfolio.total_value = float(total_value)
            PortfolioRepository._update_portfolio(
                portfolio.portfolio_id,
                updates={"total_value": Decimal(str(total_value))}
            )

            return total_value

        except Exception as e:
            logger.exception(f"Exception raised in PortfolioService.portfolio_value: {e}")
            raise e

    @classmethod
    def portfolio_rebalance(cls, portfolio: Portfolio, target_allocations: dict) -> dict:
        try:
            logger.info("Rebalancing portfolio", portfolio_id=portfolio.portfolio_id)
            logger.debug("Target allocations:", target_allocations=target_allocations)

            # Compute up-to-date total value
            total_value = cls.portfolio_value(portfolio)  # returns Decimal
            logger.debug("Total portfolio value computed", total_value=float(total_value))

            if total_value == Decimal("0") or total_value is None or total_value == 0:
                logger.warning("Portfolio total value is zero; nothing to rebalance.")
                return {"portfolio_id": portfolio.portfolio_id, "total_value": 0.0, "rebalance_plan": {}}

            # Build current values map for quick lookup (symbol -> Decimal(current_value))
            current_values: Dict[str, Decimal] = {}
            for symbol, position in portfolio.stocks.items():
                price = (
                    Decimal(str(position.current_price))
                    if position.current_price is not None
                    else Decimal(str(position.avg_price))
                )
                current_values[symbol] = Decimal(str(position.quantity)) * price
                logger.debug("Current position", symbol=symbol, quantity=str(position.quantity), price=str(price), value=str(current_values[symbol]))

            # Prepare set of all symbols to evaluate
            symbols_to_consider = set(target_allocations.keys()) | set(portfolio.stocks.keys())

            rebalance_plan: Dict[str, Decimal] = {}

            # For each symbol, compute required quantity change
            for symbol in sorted(symbols_to_consider):
                target_pct = Decimal(str(target_allocations.get(symbol, 0)))
                target_value = (total_value * target_pct).quantize(Decimal("0.0001"))
                current_value = current_values.get(symbol, Decimal("0"))

                # Determine price to use for converting value <-> shares:
                if symbol in portfolio.stocks:
                    pos = portfolio.stocks[symbol]
                    price = (
                        Decimal(str(pos.current_price))
                        if pos.current_price is not None
                        else Decimal(str(pos.avg_price))
                    )
                else:
                    # no current position -> use market lookup
                    price = StockPosition.get_current_price(symbol)

                # Avoid division by zero if price is zero
                if price == 0 or price is None or price == Decimal("0"):
                    logger.warning(f"Price for {symbol} is zero; skipping trade calculation.")
                    continue

                # positive difference => need to BUY; negative => SELL
                difference_value = target_value - current_value
                qty_to_trade = (difference_value / price).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

                if qty_to_trade != Decimal("0"):
                    rebalance_plan[symbol] = qty_to_trade
                    action = "BUY" if qty_to_trade > 0 else "SELL"
                    logger.info(f"{symbol}: {action} {abs(qty_to_trade)} shares @ {price} (target_value={target_value}, current_value={current_value})")

            logger.info("Rebalance plan computed", rebalance_plan=rebalance_plan)

            return {
                "portfolio_id": portfolio.portfolio_id,
                "total_value": float(total_value),
                "rebalance_plan": {sym: float(qty) for sym, qty in rebalance_plan.items()},
            }

        except Exception as e:
            logger.exception(f"Exception raised in PortfolioService.portfolio_rebalance: {e}")
            raise e
