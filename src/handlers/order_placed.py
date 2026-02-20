from typing import TYPE_CHECKING
import logging

from .base import MessageHandler

if TYPE_CHECKING:
    from src.database.repository import OrderRepository, InventoryRepository

logger = logging.getLogger(__name__)

class OrderPlacedHandler(MessageHandler):
    """Handler for order.placed events"""
    
    def __init__(
        self,
        order_repo: "OrderRepository",
        inventory_repo: "InventoryRepository"
    ):
        self.order_repo = order_repo
        self.inventory_repo = inventory_repo
    
    async def handle(self, message: dict) -> None:
        """
        Handle order.placed event.
        
        Creates an order and updates inventory in a transaction.
        If inventory update fails, order creation is rolled back.
        """
        order_data = message.get("data", {})
        
        # Validate required fields
        required_fields = ["user_id", "total", "product_id", "quantity"]
        missing = [field for field in required_fields if not order_data.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        
        # Use transaction to ensure both operations succeed or both fail
        async with self.order_repo.db.begin():
            order = await self.order_repo.create(order_data)
            logger.info(f"Created order: {order.id} for user {order.user_id}")
            
            # Update inventory - if this fails, order creation rolls back
            await self.inventory_repo.decrement(
                product_id=order_data["product_id"],
                quantity=order_data["quantity"]
            )
            logger.info(
                f"Updated inventory for product {order_data['product_id']}, "
                f"decremented {order_data['quantity']}"
            )
