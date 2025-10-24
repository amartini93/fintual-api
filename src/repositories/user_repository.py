from datetime import datetime, timezone
import os
from typing import Optional

from aws_lambda_powertools import Logger

from clients.dynamodb_client import DynamoDBClient
from models.user_models import User

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class UserRepository:
    _dynamodb_client = DynamoDBClient(table_name='users')

    @classmethod
    def _get_user(cls, user_id: str) -> Optional[User]:
        try:
            response = cls._dynamodb_client.get_item_by_hash_key(
                key_name="user_id",
                key_value=user_id
            )
            if not response:
                return None
            return User.model_validate(response)
        except Exception as e:
            logger.exception(f"Exception raised in get_user: {e}")
            raise e

    @classmethod
    def _put_user(cls, user: User) -> bool:
        try:
            response = cls._dynamodb_client.put_item(
                item=user.model_dump()
            )
            if response is None:
                return False
            return True

        except Exception as e:
            logger.exception(f"Exception raised in _put_user: {e}")
            raise e

    @classmethod
    def _update_user(cls, user_id: str, updates: dict) -> bool:
        try:
            if not updates:
                logger.warning("No updates provided")
                return False
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()

            update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
            expression_attribute_names = {f"#{k}": k for k in updates}
            expression_attribute_values = {f":{k}": v for k, v in updates.items()}

            response = cls._dynamodb_client.update_item(
                key={"user_id": user_id},
                update_expression=update_expression,
                expression_attribute_names=expression_attribute_names,
                expression_attribute_values=expression_attribute_values,
                return_values="UPDATED_NEW"
            )

            return "Attributes" in response

        except Exception as e:
            logger.exception(f"Exception raised in _update_user: {e}")
            raise e
