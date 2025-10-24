import json
import os
from uuid import uuid4
from datetime import datetime, timezone

from aws_lambda_powertools import Logger

from models.portfolio_models import Portfolio
from repositories.portfolio_repository import PortfolioRepository
from services.portfolio_service import PortfolioService
from utils.http_response import create_http_response
from utils.load_json import load_json_from_relative_path

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

REBALANCE_DISTRIBUTION = "balances/superstar_martini.json"


def create_portfolio(event: dict, context) -> dict:
    """
    Handler function to create a portfolio.
    """
    try:
        logger.info(f"Received event: {event}")

        payload = json.loads(event.get('body', {})) if isinstance(event.get('body'), str) else event.get('body', {})
        portfolio_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        payload["portfolio_id"] = portfolio_id
        payload["created_at"] = now
        payload["updated_at"] = now
        payload["total_value"] = 0.0

        portfolio = Portfolio.model_validate(payload)

        service_response = PortfolioService.create_portfolio(portfolio)
        if not service_response:
            return create_http_response(500, "Failed to create portfolio")
        logger.info(f"Portfolio {portfolio.portfolio_id} created")
        return create_http_response(200, "Portfolio created successfully")

    except Exception as e:
        logger.exception(f"Exception raised in handler.create_portfolio: {e}")
        return create_http_response(500, "Internal server error")


def update_portfolio(event: dict, context) -> dict:
    try:
        logger.info(f"Received event: {event}")

        portfolio_id = event['pathParameters']['portfolio_id']
        payload = json.loads(event.get('body', {})) if isinstance(event.get('body'), str) else event.get('body', {})

        service_response = PortfolioService.update_portfolio(portfolio_id, payload)
        if not service_response:
            return create_http_response(404, "Portfolio not found or no changes applied")
        return create_http_response(200, "Portfolio updated successfully")

    except Exception as e:
        logger.exception(f"Exception raised in handler.update_portfolio: {e}")
        return create_http_response(500, "Internal server error")


def portfolio_value(event: dict, context) -> dict:
    try:
        logger.info(f"Received event: {event}")

        portfolio_id = event["pathParameters"]["portfolio_id"]
        portfolio = PortfolioRepository._get_portfolio(portfolio_id)
        if not portfolio:
            return create_http_response(404, "Portfolio not found")
        service_response = PortfolioService.portfolio_value(portfolio)

        return create_http_response(
            status_code=200,
            message="Success",
            data={
                "Value": float(service_response)
            }
        )

    except Exception as e:
        logger.exception(f"Exception raised in handler.portfolio_value: {e}")
        return create_http_response(500, "Internal server error")


def portfolio_rebalance(event: dict, context) -> dict:
    try:
        logger.info(f"Received event: {event}")

        portfolio_id = event["pathParameters"]["portfolio_id"]
        portfolio = PortfolioRepository._get_portfolio(portfolio_id)
        if not portfolio:
            return create_http_response(404, "Portfolio not found")

        service_response = PortfolioService.portfolio_rebalance(
            portfolio=portfolio,
            target_allocations=load_json_from_relative_path(REBALANCE_DISTRIBUTION)
            )

        return create_http_response(
            status_code=200,
            message="Success",
            data=service_response
        )

    except Exception as e:
        logger.exception(f"Exception raised in handler.portfolio_value: {e}")
        return create_http_response(500, "Internal server error")
