import boto3
import json
import asyncio
import logging
import random
from typing import Optional
from botocore.exceptions import ClientError

from .message_router import MessageRouter, UnknownEventTypeError

logger = logging.getLogger(__name__)

BASE_BACKOFF_SECONDS = 2.0
MAX_BACKOFF_SECONDS = 900


class SQSListener:
    """SQS message listener with proper error handling and retry logic"""
    
    def __init__(
        self,
        queue_url: str,
        router: MessageRouter,
        dlq_url: Optional[str] = None,
        max_retries: int = 3
    ):
        self.sqs = boto3.client('sqs')
        self.queue_url = queue_url
        self.dlq_url = dlq_url
        self.router = router
        self.max_retries = max_retries
    
    async def _change_visibility(self, receipt_handle: str, timeout: int) -> None:
        """Set visibility timeout so SQS redelivers after the backoff period."""
        try:
            self.sqs.change_message_visibility(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=timeout,
            )
        except ClientError as e:
            logger.error(f"Failed to change message visibility: {e}")

    def _calculate_backoff(self, attempt: int) -> float:
        """Exponential backoff with jitter, capped at MAX_BACKOFF_SECONDS."""
        delay = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
        jitter = random.uniform(0, BASE_BACKOFF_SECONDS)
        return min(delay + jitter, MAX_BACKOFF_SECONDS)

    def _get_receive_count(self, message: dict) -> int:
        """Extract ApproximateReceiveCount, defaulting to 1 if absent."""
        try:
            return int(message.get("Attributes", {}).get("ApproximateReceiveCount", "1"))
        except (ValueError, TypeError):
            return 1

    async def process_message(self, message: dict) -> bool:
        """
        Process a single message with retry-aware error handling.

        Returns:
            True if message processed successfully, False otherwise.
        """
        receipt_handle = message["ReceiptHandle"]
        message_body = json.loads(message["Body"])
        receive_count = self._get_receive_count(message)

        try:
            await self.router.route(message_body)
            await self.acknowledge_message(receipt_handle)
            return True
        except UnknownEventTypeError as e:
            logger.warning(f"Unknown event type: {e}")
            await self.acknowledge_message(receipt_handle)
            return False
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            await self.send_to_dlq(message_body, str(e))
            await self.acknowledge_message(receipt_handle)
            return False
        except Exception as e:
            if receive_count >= self.max_retries:
                logger.error(
                    f"Retries exhausted ({receive_count}/{self.max_retries}): {e}"
                )
                await self.send_to_dlq(message_body, str(e))
                await self.acknowledge_message(receipt_handle)
            else:
                backoff = int(self._calculate_backoff(receive_count))
                logger.warning(
                    f"Transient error (attempt {receive_count}/{self.max_retries}), "
                    f"retrying in {backoff}s: {e}"
                )
                await self._change_visibility(receipt_handle, backoff)
            return False
    
    async def acknowledge_message(self, receipt_handle: str) -> None:
        """Delete message from queue after successful processing"""
        try:
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
        except ClientError as e:
            logger.error(f"Failed to acknowledge message: {e}")
            raise
    
    async def send_to_dlq(self, message_body: dict, error: str) -> None:
        """Send failed message to dead letter queue"""
        if not self.dlq_url:
            logger.warning("DLQ not configured, message will be lost")
            return
        
        try:
            self.sqs.send_message(
                QueueUrl=self.dlq_url,
                MessageBody=json.dumps({
                    **message_body,
                    "error": error,
                    "original_queue": self.queue_url
                })
            )
            logger.info(f"Sent message to DLQ: {self.dlq_url}")
        except ClientError as e:
            logger.error(f"Failed to send message to DLQ: {e}")
    
    async def poll(self) -> None:
        """Long-poll for messages from SQS"""
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                MessageAttributeNames=['All'],
                AttributeNames=['ApproximateReceiveCount'],
            )
            
            messages = response.get('Messages', [])
            if messages:
                logger.info(f"Received {len(messages)} messages")
            
            for message in messages:
                await self.process_message(message)
                
        except ClientError as e:
            logger.error(f"SQS polling error: {e}")
            # Wait before retrying
            await asyncio.sleep(5)
    
    async def run(self) -> None:
        """Main loop for polling messages"""
        logger.info(f"Starting SQS listener for queue: {self.queue_url}")
        while True:
            await self.poll()
