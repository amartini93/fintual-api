from datetime import datetime, timezone
from decimal import Decimal
import os
from typing import List

from aws_lambda_powertools import Logger

from models.orders_models import Order
from models.transactions_models import Transaction, TransactionStatus, TransactionType
from models.user_models import User
from repositories.orders_repository import OrderRepository
from repositories.transactions_repository import TransactionRepository
from repositories.user_repository import UserRepository

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class UserService:
    @classmethod
    def create_user(cls, user: User) -> bool:
        try:
            # Save user with status pending
            repository_response = UserRepository._put_user(user)
            if not repository_response:
                raise Exception("Failed user dynamodb save")

            return True
        except Exception as e:
            logger.exception(f"Exception raised in service.create_user: {e}")
            raise e

    @classmethod
    def update_user(cls, user_id: str, updates: dict) -> bool:
        try:
            repository_response = UserRepository._update_user(user_id, updates)
            if not repository_response:
                logger.warning(f"User {user_id} not found or not updated")
                return False
            return True
        except Exception as e:
            logger.exception(f"Exception raised in service.update_user: {e}")
            raise e

    @classmethod
    def update_balance(cls, transaction: Transaction) -> bool:
        try:
            user = UserRepository._get_user(transaction.user_id)
            if not user:
                logger.error(f"User {transaction.user_id} not found")
                return False

            # Calculate new balance
            logger.info("Updating balance for user", user_id=transaction.user_id)
            logger.info("With transaction", transaction_id=transaction.transaction_id, transaction_type=transaction.transaction_type, amount=transaction.amount)
            new_balance = user.balance
            transaction.updated_at = str(datetime.now(timezone.utc).isoformat())
            if transaction.transaction_type == TransactionType.DEPOSIT:
                new_balance += transaction.amount
            elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                if transaction.amount > user.balance:
                    logger.warning(f"Insufficient funds for user {transaction.user_id}")
                    transaction.status = TransactionStatus.FAILED
                    TransactionRepository._put_transaction(transaction)
                    return False
                new_balance -= transaction.amount

            update_response = UserRepository._update_user(
                transaction.user_id,
                updates={"balance": Decimal(new_balance)}
            )
            if not update_response:
                logger.error("Error at user_update")
                transaction.status = TransactionStatus.FAILED

            # Update transaction in dynamodb
            transaction.status = TransactionStatus.COMPLETED
            TransactionRepository._put_transaction(transaction)
            logger.info(f"Balance updated {transaction.user_id}: {user.balance} -> {new_balance}")

            return True

        except Exception as e:
            logger.exception(f"Exception raised in service.update_balance: {e}")
            transaction.status = "failed"
            raise e

    @classmethod
    def get_recent_orders(cls, user_id) -> List[Order]:
        try:
            user = UserRepository._get_user(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False

            recent_orders = OrderRepository._get_recent_orders(user_id)
            return recent_orders[:10] if recent_orders else []

        except Exception as e:
            logger.exception(f"Exception raised in service.update_balance: {e}")
            raise e
