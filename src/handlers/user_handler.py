from datetime import datetime, timezone
from uuid import uuid4
import json
import os

from aws_lambda_powertools import Logger

from models.user_models import User
from services.user_service import UserService
from utils.http_response import create_http_response

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def create_user(event: dict, context) -> dict:
    """
    Handler function to create a user.
    """
    try:
        logger.info(f"Received event: {event}")

        payload = json.loads(event.get('body', {})) if isinstance(event.get('body'), str) else event.get('body', {})
        user_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        created_at = str(now)
        updated_at = str(now)
        balance = 0.0

        payload["user_id"] = user_id
        payload["created_at"] = created_at
        payload["updated_at"] = updated_at
        payload["balance"] = balance

        user = User.model_validate(payload)

        service_response = UserService.create_user(user)
        if not service_response:
            create_http_response(status_code=500, message="User create failed")
        logger.info(f"User {user.user_id} created")
        return create_http_response(status_code=200, message="Success")

    except Exception as e:
        logger.exception(f"Exception raised in handler.create_user: {e}")
        return create_http_response(status_code=500, message="Internal server error")


def update_user(event: dict, context) -> dict:
    """
    Handler function to update a user.
    """
    try:
        logger.info(f"Received event: {event}")

        user_id = event["pathParameters"].get("user_id")
        if not user_id:
            return create_http_response(status_code=400, message="Missing user_id in path")

        payload: dict = json.loads(event.get('body', {})) if isinstance(event.get('body'), str) else event.get('body', {})
        if not payload:
            return create_http_response(status_code=400, message="Missing params")
        payload["user_id"] = user_id
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Validate only the fields that are being updated
        allowed_fields = {"name", "email", "updated_at"}  # balance can be changed via transactions
        updates = {k: v for k, v in payload.items() if k in allowed_fields}

        if not updates:
            return create_http_response(status_code=400, message="No valid fields to update")

        service_response = UserService.update_user(user_id, updates)
        if not service_response:
            return create_http_response(status_code=404, message="User not found or update failed")

        return create_http_response(status_code=200, message="User updated successfully")

    except Exception as e:
        logger.exception(f"Exception raised in handler.update_user: {e}")
        return create_http_response(status_code=500, message="Internal server error")


def get_recent_orders(event: dict, context) -> dict:
    """
    Handler function to get user last 10 orders.
    """
    try:
        logger.info(f"Received event: {event}")

        user_id = event["pathParameters"]["user_id"]
        orders = UserService.get_recent_orders(user_id)
        return create_http_response(
            status_code=200,
            message="User updated successfully",
            data={
                "orders": [order.model_dump() for order in orders]
            }
        )
    except Exception as e:
        logger.exception(f"Exception raised in handler.get_recent_orders: {e}")
        return create_http_response(status_code=500, message="Internal server error")
