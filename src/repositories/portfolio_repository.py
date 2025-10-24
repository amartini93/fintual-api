import os
from typing import Optional

from aws_lambda_powertools import Logger

from clients.dynamodb_client import DynamoDBClient
from models.portfolio_models import Portfolio

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class PortfolioRepository:
    _dynamodb_client = DynamoDBClient(table_name='portfolios')

    @classmethod
    def _get_portfolio(cls, portfolio_id: str) -> Optional[Portfolio]:
        try:
            response = cls._dynamodb_client.get_item_by_hash_key(
                key_name="portfolio_id",
                key_value=portfolio_id
            )
            if not response:
                return None
            return Portfolio.model_validate(response)
        except Exception as e:
            logger.exception(f"Exception raised in get_user: {e}")
            raise e

    @classmethod
    def _put_portfolio(cls, portfolio: Portfolio) -> bool:
        try:
            response = cls._dynamodb_client.put_item(
                item=portfolio.model_dump()
            )
            return response is not None
        except Exception as e:
            logger.exception(f"Exception raised in put_portfolio: {e}")
            raise e

    @classmethod
    def _update_portfolio(cls, portfolio_id: str, updates: dict) -> bool:
        try:
            if not updates:
                return False

            update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in updates)
            expression_attribute_names = {f"#{k}": k for k in updates}
            expression_attribute_values = {f":{k}": v for k, v in updates.items()}

            response = cls._dynamodb_client.update_item(
                key={"portfolio_id": portfolio_id},
                update_expression=update_expression,
                expression_attribute_names=expression_attribute_names,
                expression_attribute_values=expression_attribute_values,
                return_values="UPDATED_NEW"
            )

            return "Attributes" in response
        except Exception as e:
            logger.exception(f"Exception raised in update_portfolio: {e}")
            raise e
