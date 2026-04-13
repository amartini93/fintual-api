from typing import Optional
import os

from aws_lambda_powertools import Logger

from clients.alpaca_client import AlpacaBrokerClient
from repositories.user_repository import UserRepository

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME", "brokerage_service"))

class BrokerageService:
    @classmethod
    def onboard_user(cls, user_id: str, kyc_data: Optional[dict] = None) -> Optional[str]:
        """
        Links a local user to an Alpaca account.
        If the user already has an alpaca_account_id, it returns it.
        Otherwise, it creates a new one via AlpacaBrokerClient.
        """
        try:
            # 1. Check if user exists
            user = UserRepository._get_user(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return None

            # 2. Check if already onboarded
            if user.alpaca_account_id:
                logger.info(f"User {user_id} already has Alpaca account: {user.alpaca_account_id}")
                return user.alpaca_account_id

            # 3. Prepare Alpaca account request
            # For this challenge/API, we use a default set of mock KYC data if not provided
            alpaca_request = kyc_data or cls._get_default_kyc_data(user.name, user.email)

            # 4. Call Alpaca Client
            alpaca_client = AlpacaBrokerClient()
            alpaca_account_id = alpaca_client.create_account(alpaca_request)

            if alpaca_account_id:
                # 5. Save Alpaca ID to user record
                UserRepository._update_user(user_id, updates={"alpaca_account_id": alpaca_account_id})
                logger.info(f"User {user_id} successfully onboarded to Alpaca with ID: {alpaca_account_id}")
                return alpaca_account_id
            
            return None

        except Exception as e:
            logger.exception(f"Exception raised in BrokerageService.onboard_user: {e}")
            raise e

    @staticmethod
    def _get_default_kyc_data(name: str, email: str) -> dict:
        """
        Generates mandatory (mock) KYC data required by Alpaca Broker API.
        """
        # Split name for first/last
        parts = name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else "User"

        return {
            "contact": {
                "email_address": email,
                "phone_number": "+15555555555",
                "street_address": ["123 Broker Way"],
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "USA"
            },
            "identity": {
                "given_name": first_name,
                "family_name": last_name,
                "date_of_birth": "1990-01-01",
                "tax_id": "123-456-789",
                "tax_id_type": "USA_SSN",
                "country_of_citizenship": "USA",
                "country_of_birth": "USA",
                "country_of_tax_residence": "USA",
                "funding_source": ["employment_income"]
            },
            "disclosures": {
                "is_control_person": False,
                "is_affiliated_exchange_or_finra": False,
                "is_politically_exposed": False,
                "immediate_family_exposed": False
            },
            "agreements": [
                {
                    "agreement": "customer_agreement",
                    "signed_at": "2024-01-01T00:00:00Z",
                    "ip_address": "127.0.0.1"
                },
                {
                    "agreement": "margin_agreement",
                    "signed_at": "2024-01-01T00:00:00Z",
                    "ip_address": "127.0.0.1"
                }
            ],
            "config": {
                "trading_class": "paper" # Defaulting to paper for safety in sandbox
            }
        }
