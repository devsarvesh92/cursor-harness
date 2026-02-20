import boto3
import json
import asyncio
import logging
from typing import Optional
from botocore.exceptions import ClientError

from .message_router import MessageRouter, UnknownEventTypeError

logger = logging.getLogger(__name__)

class SQSListener:
    """SQS message listener with proper error handling and retry logic"""
    
    MAX_RETRIES = 1
    BASE_DELAY_SECONDS = 1.0

    def __init__(
        self,
        queue_url: str,
        router: MessageRouter,
        dlq_url: Optional[str] = None,
    ):
        self.sqs = boto3.client('sqs')
        self.queue_url = queue_url
        self.dlq_url = dlq_url
        self.router = router
    
    async def process_message(self, message: dict) -> bool:
        """
        Process a single message with error handling.
        
        Returns:
            True if message processed successfully, False otherwise
        """
        receipt_handle = message['ReceiptHandle']
        message_body = json.loads(message['Body'])
        
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
            logger.error(f"Error processing message: {e}")
            return await self._retry_or_dlq(message_body, receipt_handle, e)

    async def _retry_or_dlq(
        self, message_body: dict, receipt_handle: str, original_error: Exception
    ) -> bool:
        for attempt in range(1, self.MAX_RETRIES + 1):
            delay = self.BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.info(
                f"Retrying message, attempt {attempt}/{self.MAX_RETRIES}"
            )
            await asyncio.sleep(delay)
            try:
                await self.router.route(message_body)
                await self.acknowledge_message(receipt_handle)
                return True
            except Exception as e:
                logger.error(f"Retry {attempt}/{self.MAX_RETRIES} failed: {e}")
                original_error = e

        await self.send_to_dlq(message_body, str(original_error))
        await self.acknowledge_message(receipt_handle)
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
