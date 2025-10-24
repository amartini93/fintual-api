from datetime import datetime, timezone
from uuid import uuid4
import json
import os

from aws_lambda_powertools import Logger

from models.transactions_models import Transaction, TransactionStatus
from services.transactions_service import TransactionService
from services.user_service import UserService
from utils.http_response import create_http_response

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def create_transaction(event: dict, context) -> dict:
    """
    Handler function to create a transaction.
    """
    try:
        logger.info(f"Received event: {event}")

        payload = json.loads(event.get('body', {})) if isinstance(event.get('body'), str) else event.get('body', {})
        transaction_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        created_at = str(now)
        updated_at = str(now)
        status = TransactionStatus.PENDING

        payload["transaction_id"] = transaction_id
        payload["status"] = status
        payload["created_at"] = created_at
        payload["updated_at"] = updated_at

        transaction = Transaction.model_validate(payload)

        service_response = TransactionService.create_transaction(transaction)
        if not service_response:
            create_http_response(status_code=500, message="Transaction failed")
        logger.info(f"Transaction {transaction.transaction_id} created")
        return create_http_response(status_code=200, message="Success")

    except Exception as e:
        logger.exception(f"Exception raised in handler.create_transaction: {e}")
        return create_http_response(status_code=500, message="Internal server error")


def process_transaction(event: dict, context):
    """
    SQS-triggered function to process transaction.
    Updates user balance based on transaction type.
    """
    logger.info(f"Received SQS event: {json.dumps(event)}")

    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            logger.info(f"Processing transaction: {body}")

            transaction = Transaction.model_validate(body)
            service_response = UserService.update_balance(transaction)
            if not service_response:
                logger.error(f"Failed to process {transaction.transaction_id}")
            logger.info(f"Processed transaction {transaction.transaction_id} successfully")

        except Exception as e:
            logger.exception(f"Failed to process transaction message: {e}")
            # Optionally: move to DLQ or log permanently failed message
    return create_http_response(status_code=200, message="Success")
