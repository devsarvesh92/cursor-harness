from typing import TYPE_CHECKING
import logging

from .base import MessageHandler

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from src.database.repository import UserRepository
    from src.services.email import EmailService

logger = logging.getLogger(__name__)

class UserCreatedHandler(MessageHandler):
    """Handler for user.created events"""
    
    def __init__(
        self,
        user_repo: "UserRepository",
        email_service: "EmailService"
    ):
        self.user_repo = user_repo
        self.email_service = email_service
    
    async def handle(self, message: dict) -> None:
        """
        Handle user.created event.
        
        Creates a user record and sends welcome email in a transaction.
        If email fails, the user creation is rolled back.
        """
        user_data = message.get("data", {})
        
        # Validate required fields
        if not user_data.get("email") or not user_data.get("name"):
            raise ValueError("Missing required fields: email and name")
        
        # Use transaction to ensure both operations succeed or both fail
        # Note: In real implementation, session would be passed and managed at router level
        # For demo purposes, we show the pattern
        async with self.user_repo.db.begin():
            user = await self.user_repo.create(user_data)
            logger.info(f"Created user: {user.id} ({user.email})")
            
            # Send welcome email - if this fails, transaction rolls back
            await self.email_service.send_welcome(user.id)
            logger.info(f"Sent welcome email to user {user.id}")
            # Transaction commits automatically on context exit if no exception
