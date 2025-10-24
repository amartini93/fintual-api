import os

from aws_lambda_powertools import Logger

from clients.sqs_client import SQSClient
from models.transactions_models import Transaction
from repositories.transactions_repository import TransactionRepository

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

QUEUE_URL = os.getenv("TRANSACTION_QUEUE_URL")


class TransactionService:
    @classmethod
    def create_transaction(cls, transaction: Transaction) -> bool:
        try:
            sqs_client = SQSClient(queue_url=QUEUE_URL)
            # Save transaction with status pending
            repository_response = TransactionRepository._put_transaction(transaction)
            if not repository_response:
                raise Exception("Failed transaction dynamodb save")

            # Send to SQS
            sqs_response = sqs_client.send_message(transaction.model_dump(), message_group_id=transaction.user_id)
            if not sqs_response:
                raise Exception("Failed transaction sqs queue")

            return True
        except Exception as e:
            logger.exception(f"Exception raised in service.create_transaction: {e}")
            raise e
