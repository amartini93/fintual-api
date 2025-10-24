import os

from aws_lambda_powertools import Logger

from clients.dynamodb_client import DynamoDBClient
from models.transactions_models import Transaction

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class TransactionRepository:
    _dynamodb_client = DynamoDBClient(table_name='transactions')

    @classmethod
    def _put_transaction(cls, transaction: Transaction) -> bool:
        try:
            response = cls._dynamodb_client.put_item(
                item=transaction.model_dump()
            )
            if response is None:
                return False
            return True
        except Exception as e:
            logger.exception(f"Exception raised in _put_transaction: {e}")
            raise e
