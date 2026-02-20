import asyncio
import json
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from .message_router import MessageRouter, UnknownEventTypeError
from .retry import RetryPolicy, calculate_delay, is_transient_error

logger = logging.getLogger(__name__)


class SQSListener:
    """SQS message listener with exponential-backoff retry for transient errors."""

    def __init__(
        self,
        queue_url: str,
        router: MessageRouter,
        dlq_url: Optional[str] = None,
        retry_policy: Optional[RetryPolicy] = None,
    ):
        self.sqs = boto3.client("sqs")
        self.queue_url = queue_url
        self.dlq_url = dlq_url
        self.router = router
        self.retry_policy = retry_policy or RetryPolicy()

    async def process_message(self, message: dict) -> bool:
        receipt_handle = message["ReceiptHandle"]
        message_body = json.loads(message["Body"])

        last_error: Optional[Exception] = None
        max_attempts = 1 + self.retry_policy.max_retries

        for attempt in range(max_attempts):
            try:
                await self.router.route(message_body)
                await self.acknowledge_message(receipt_handle)
                return True
            except Exception as e:
                last_error = e

                if not is_transient_error(e):
                    return await self._handle_permanent_error(
                        e, receipt_handle, message_body
                    )

                if attempt < self.retry_policy.max_retries:
                    delay = calculate_delay(self.retry_policy, attempt)
                    logger.warning(
                        f"Retry {attempt + 1}/{self.retry_policy.max_retries} "
                        f"in {delay:.2f}s — {e}"
                    )
                    self._extend_visibility(receipt_handle, delay)
                    await asyncio.sleep(delay)

        logger.error(
            f"Exhausted {self.retry_policy.max_retries} retries — {last_error}"
        )
        await self.send_to_dlq(message_body, str(last_error))
        await self.acknowledge_message(receipt_handle)
        return False

    async def _handle_permanent_error(
        self,
        error: Exception,
        receipt_handle: str,
        message_body: dict,
    ) -> bool:
        if isinstance(error, UnknownEventTypeError):
            logger.warning(f"Unknown event type: {error}")
            await self.acknowledge_message(receipt_handle)
        else:
            logger.error(f"Permanent error: {error}")
            await self.send_to_dlq(message_body, str(error))
            await self.acknowledge_message(receipt_handle)
        return False
    
    def _extend_visibility(self, receipt_handle: str, delay: float) -> None:
        """Best-effort extension of SQS visibility timeout to cover the retry delay."""
        timeout = int(delay) + 30
        try:
            self.sqs.change_message_visibility(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=timeout,
            )
        except ClientError as e:
            logger.warning(f"Failed to extend visibility timeout: {e}")

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
                WaitTimeSeconds=20,  # Long polling
                MessageAttributeNames=['All']
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
