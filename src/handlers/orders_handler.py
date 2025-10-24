from datetime import datetime, timezone
from uuid import uuid4
import json
import os

from aws_lambda_powertools import Logger

from models.orders_models import Order, OrderStatus
from services.orders_service import OrderService
from services.portfolio_service import PortfolioService
from utils.http_response import create_http_response

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def create_order(event: dict, context) -> dict:
    """
    Handler function to create a order.
    """
    try:
        logger.info(f"Received event: {event}")

        payload = json.loads(event.get('body', {})) if isinstance(event.get('body'), str) else event.get('body', {})
        order_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        created_at = str(now)
        updated_at = str(now)
        status = OrderStatus.PENDING

        payload["order_id"] = order_id
        payload["status"] = status
        payload["created_at"] = created_at
        payload["updated_at"] = updated_at

        order = Order.model_validate(payload)

        service_response = OrderService.create_order(order)
        if not service_response:
            create_http_response(status_code=500, message="Order failed")
        logger.info(f"Order {order.order_id} created")
        return create_http_response(status_code=200, message="Success")

    except Exception as e:
        logger.exception(f"Exception raised in handler.create_order: {e}")
        return create_http_response(status_code=500, message="Internal server error")


def process_order(event: dict, context):
    """
    SQS-triggered function to process investment orders.
    Updates user balance based on order type.
    """
    logger.info(f"Received SQS event: {json.dumps(event)}")

    for record in event.get("Records", []):
        try:
            body = json.loads(record["body"])
            logger.info(f"Processing order: {body}")

            order = Order.model_validate(body)
            service_response = PortfolioService.process_order(order)
            if not service_response:
                logger.error(f"Failed to process {order.order_id}")
            logger.info(f"Processed order {order.order_id} successfully")

        except Exception as e:
            logger.exception(f"Failed to process order message: {e}")
            # Optionally: move to DLQ or log permanently failed message
    return create_http_response(status_code=200, message="Success")
