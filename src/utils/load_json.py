import json
import os

from aws_lambda_powertools import Logger

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


def load_json_from_relative_path(relative_path: str) -> dict:
    """
    Loads a JSON file using a path relative to this project’s base directory.

    Example:
        load_json_from_relative_path("balances/superstar_martini.json")

    Args:
        relative_path (str): Relative path from the project root to the JSON file.

    Returns:
        dict: The loaded JSON content, or an empty dict if the file cannot be read.
    """
    # Compute the absolute base directory two levels up from this utils file
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    json_path = os.path.join(base_dir, relative_path)

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            logger.info(f"Loaded JSON file: {json_path}")
            return data
    except Exception as e:
        logger.exception(f"Failed to load JSON file: {json_path} — {e}")
        return {}
