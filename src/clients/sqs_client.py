import json
import os

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
import boto3

logger = Logger(service=os.getenv("AWS_LAMBDA_FUNCTION_NAME"))


class SQSClient:
    def __init__(self, queue_url):
        logger.info("Initializing SQSClient...")

        stage = os.getenv("STAGE") or "dev"
        self.queue_url = queue_url
        logger.info(f"Stage: {stage}")
        logger.info(f"Queue URL from env: {self.queue_url}")

        if not self.queue_url:
            raise ValueError("Environment variable QUEUE_URL not set")

        if stage == "dev":
            logger.info("Using local SQS")
            self._sqs = boto3.client(
                "sqs",
                endpoint_url="http://localhost:9324",
                aws_access_key_id="anything",
                aws_secret_access_key="anything",
                region_name="us-west-2",
            )
        else:
            self._sqs = boto3.client("sqs")

        logger.info("SQS client initialized successfully")

    def send_message(self, message_body: dict, message_group_id: str = None) -> dict:
        try:
            logger.info("Sending message to SQS", extra={"queue_url": self.queue_url, "message_body": message_body})

            params = {
                "QueueUrl": self.queue_url,
                "MessageBody": json.dumps(message_body),
            }

            # FIFO queues require MessageGroupId
            if message_group_id is not None:
                params["MessageGroupId"] = message_group_id

            response = self._sqs.send_message(**params)

            logger.info("Message sent to SQS successfully", extra={"response": response})
            return response

        except ClientError as e:
            logger.error("Error sending message to SQS", extra={"error": str(e), "queue_url": self.queue_url})
            raise e

    def receive_messages(self, max_number: int = 10, wait_time_seconds: int = 0, visibility_timeout: int = None):
        """
        Optionally implement this if you want to poll messages from the queue.
        """
        try:
            params = {
                "QueueUrl": self.queue_url,
                "MaxNumberOfMessages": max_number,
                "WaitTimeSeconds": wait_time_seconds,
            }
            if visibility_timeout is not None:
                params["VisibilityTimeout"] = visibility_timeout

            response = self._sqs.receive_message(**params)

            messages = response.get("Messages", [])
            logger.info(f"Received {len(messages)} messages from SQS")
            return messages
        except ClientError as e:
            logger.error("Error receiving messages from SQS", extra={"error": str(e), "queue_url": self.queue_url})
            raise e

    def delete_message(self, receipt_handle: str):
        try:
            response = self._sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info("Deleted message from SQS", extra={"receipt_handle": receipt_handle})
            return response
        except ClientError as e:
            logger.error("Error deleting message from SQS", extra={"error": str(e), "receipt_handle": receipt_handle})
            raise e
