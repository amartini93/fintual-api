import os
from typing import List

from aws_lambda_powertools import Logger

from clients.dynamodb_client import DynamoDBClient
from models.orders_models import Order

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class OrderRepository:
    _dynamodb_client = DynamoDBClient(table_name='orders')

    @classmethod
    def _put_order(cls, order: Order) -> bool:
        try:
            response = cls._dynamodb_client.put_item(
                item=order.model_dump()
            )
            if response is None:
                return False
            return True
        except Exception as e:
            logger.exception(f"Exception raised in _put_order: {e}")
            raise e

    @classmethod
    def _get_recent_orders(cls, user_id) -> List[Order]:
        try:
            logger.info("Getting recent orders for user_id", user_id=user_id)
            orders = cls._dynamodb_client.query_by_partition_key_and_sort_key(
                key_name="user_id",
                key_value=user_id,
                index_name="UserIdIndex"
            )
            if not orders:
                logger.info("No orders found for user_id", user_id=user_id)
                return []
            return [Order.model_validate(order) for order in orders]
        except Exception as e:
            logger.exception(f"Exception raised in _get_recent_orders: {e}")
            raise e
