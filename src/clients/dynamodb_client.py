from decimal import Decimal
from typing import Any
import json
import os

from aws_lambda_powertools import Logger
from boto3.dynamodb.conditions import Key
import boto3

from exceptions.dynamodb_exceptions import DynamoDBItemNotFoundException

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class DynamoDBClient:
    def __init__(self, table_name: str) -> None:
        stage = os.getenv("STAGE") or "dev"
        if stage == 'dev':  # Only for offline development
            print('Using local DynamoDB')
            self._dynamodb = boto3.resource('dynamodb',
                                            endpoint_url='http://localhost:8000',
                                            aws_access_key_id='anything',
                                            aws_secret_access_key='anything',
                                            region_name='us-west-2').Table(table_name)
        else:
            self._dynamodb = boto3.resource('dynamodb').Table(table_name)

    def get_item_by_hash_key(self, key_name: str, key_value: str) -> dict:
        response = self._dynamodb.get_item(
            Key={
                key_name: key_value
            }
        )

        if response.get('Item') is None:
            raise DynamoDBItemNotFoundException('Item not found')
        return response['Item']

    def get_by_composite_primary_key(self, hash_key, range_key, hash_name, range_name):
        response = self._dynamodb.get_item(
            Key={
                hash_name: hash_key,
                range_name: range_key
            }
        )

        if response.get('Item') is None:
            return None
        return response['Item']

    def put_item(self, item: dict) -> None:
        try:
            logger.info("Attempting to put item in DynamoDB", extra={
                "table": self._dynamodb.table_name,
                "item": item
            })

            response = self._dynamodb.put_item(
                Item=json.loads(json.dumps(item), parse_float=Decimal)
            )

            logger.info("DynamoDB put_item successful", extra={
                "response": response
            })

            return response
        except Exception as e:
            logger.error("Error in DynamoDB put_item", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "table": self._dynamodb.table_name
            })
            raise e

    def query_by_partition_key_and_sort_key(self, key_name: str, key_value: Any, index_name: str = None, sort_key: str = None, sort_value: Any = None, operator: str = "=", filter_expression: str = None) -> dict:
        query_params = {'KeyConditionExpression': Key(key_name).eq(key_value)}
        if sort_key is not None:
            query_params['KeyConditionExpression'] = Key(
                key_name).eq(key_value) & Key(sort_key).eq(sort_value)
        if filter_expression:
            query_params['FilterExpression'] = filter_expression
        if index_name is not None:
            query_params['IndexName'] = index_name
        response = self._dynamodb.query(**query_params)
        if response.get('Items') is None or len(response['Items']) == 0:
            return None
        return response['Items']

    def scan_table(self):
        response = self._dynamodb.scan()
        if response.get('Items') is None:
            raise DynamoDBItemNotFoundException('Items not found')
        return response.get('Items')

    def update_item(self, key: dict, update_expression: str, expression_attribute_names: dict,
                    expression_attribute_values: dict, return_values: str = "UPDATED_NEW") -> dict:
        try:
            logger.info(f"Updating item in DynamoDB table {self._dynamodb.table_name}")
            response = self._dynamodb.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues=return_values
            )
            logger.info(f"DynamoDB update_item response: {response}")
            return response
        except Exception as e:
            logger.error("Error in DynamoDB update_item", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "key": key,
                "update_expression": update_expression,
                "table": self._dynamodb.table_name
            })
            raise e
