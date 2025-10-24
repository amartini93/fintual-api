import os

from aws_lambda_powertools import Logger

from clients.sqs_client import SQSClient
from models.orders_models import Order
from repositories.orders_repository import OrderRepository

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

QUEUE_URL = os.getenv("ORDER_QUEUE_URL")


class OrderService:
    @classmethod
    def create_order(cls, order: Order) -> bool:
        try:
            sqs_client = SQSClient(queue_url=QUEUE_URL)
            # Save order with status pending
            repository_response = OrderRepository._put_order(order)
            if not repository_response:
                raise Exception("Failed order dynamodb save")

            # Send to SQS
            sqs_response = sqs_client.send_message(order.model_dump(), message_group_id=order.user_id)
            if not sqs_response:
                raise Exception("Failed order sqs queue")

            return True
        except Exception as e:
            logger.exception(f"Exception raised in service.create_order: {e}")
            raise e
