import pytest
from unittest.mock import AsyncMock, patch
from src.handlers import UserCreatedHandler, OrderPlacedHandler

@pytest.mark.asyncio
async def test_user_created_handler_success(user_created_handler):
    """Test successful user creation"""
    message = {
        "type": "user.created",
        "data": {
            "email": "test@example.com",
            "name": "Test User"
        }
    }
    
    with patch.object(user_created_handler.email_service, 'send_welcome', new_callable=AsyncMock) as mock_email:
        await user_created_handler.handle(message)
        mock_email.assert_called_once()

@pytest.mark.asyncio
async def test_user_created_handler_missing_fields(user_created_handler):
    """Test user creation with missing fields"""
    message = {
        "type": "user.created",
        "data": {
            "email": "test@example.com"
            # Missing 'name'
        }
    }
    
    with pytest.raises(ValueError, match="Missing required fields"):
        await user_created_handler.handle(message)

@pytest.mark.asyncio
async def test_order_placed_handler_success(order_placed_handler, inventory_repo):
    """Test successful order placement"""
    # Setup inventory
    from src.database.models import Inventory
    async with inventory_repo.db.begin():
        inventory_repo.db.add(Inventory(product_id=1, quantity=10))
    
    message = {
        "type": "order.placed",
        "data": {
            "user_id": 1,
            "total": 100.0,
            "product_id": 1,
            "quantity": 2
        }
    }
    
    await order_placed_handler.handle(message)
    
    # Verify inventory was decremented
    from sqlalchemy import select
    result = await order_placed_handler.inventory_repo.db.execute(
        select(Inventory).where(Inventory.product_id == 1)
    )
    inventory = result.scalar_one()
    assert inventory.quantity == 8  # 10 - 2

@pytest.mark.asyncio
async def test_order_placed_handler_missing_fields(order_placed_handler):
    """Test order placement with missing fields"""
    message = {
        "type": "order.placed",
        "data": {
            "user_id": 1,
            "total": 100.0
            # Missing product_id and quantity
        }
    }
    
    with pytest.raises(ValueError, match="Missing required fields"):
        await order_placed_handler.handle(message)
