from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
from datetime import datetime

from .models import User, Order, Inventory

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, data: dict) -> User:
        """Create a new user"""
        user = User(
            email=data["email"],
            name=data["name"]
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, data: dict) -> Order:
        """Create a new order"""
        order = Order(
            user_id=data["user_id"],
            total=data["total"]
        )
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order

class InventoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def decrement(self, product_id: int, quantity: int) -> None:
        """Decrement inventory quantity"""
        await self.db.execute(
            update(Inventory)
            .where(Inventory.product_id == product_id)
            .values(quantity=Inventory.quantity - quantity)
        )
