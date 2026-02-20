import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import init_db, async_session_maker
from src.database.repository import UserRepository, OrderRepository, InventoryRepository
from src.services.email import EmailService
from src.handlers import UserCreatedHandler, OrderPlacedHandler
from src.listener.message_router import MessageRouter
from src.listener.sqs_listener import SQSListener

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Configuration
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789/test-queue"
DLQ_URL = None  # Set if you have a DLQ

async def setup_handlers() -> MessageRouter:
    """Setup message router with all handlers"""
    router = MessageRouter()
    
    # Note: In production, you'd use proper DI container
    # For demo, we create a session that handlers will use
    # Each message processing creates a new session
    session = async_session_maker()
    
    # Create repositories with session
    user_repo = UserRepository(session)
    order_repo = OrderRepository(session)
    inventory_repo = InventoryRepository(session)
    
    # Create services
    email_service = EmailService()
    
    # Register handlers
    router.register(
        "user.created",
        UserCreatedHandler(user_repo, email_service)
    )
    router.register(
        "order.placed",
        OrderPlacedHandler(order_repo, inventory_repo)
    )
    
    return router

async def main():
    """Main entry point"""
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Setup handlers
    router = await setup_handlers()
    logger.info("Handlers registered")
    
    # Create and run listener
    listener = SQSListener(
        queue_url=QUEUE_URL,
        router=router,
        dlq_url=DLQ_URL
    )
    
    logger.info("Starting SQS listener (harness approach)...")
    await listener.run()

if __name__ == "__main__":
    asyncio.run(main())
