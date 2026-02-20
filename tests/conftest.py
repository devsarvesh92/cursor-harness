import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.database.models import Base
from src.database.repository import UserRepository, OrderRepository, InventoryRepository
from src.services.email import EmailService
from src.handlers import UserCreatedHandler, OrderPlacedHandler

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    """Create a test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session_maker() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
def user_repo(db_session):
    """Create a user repository"""
    return UserRepository(db_session)

@pytest.fixture
def order_repo(db_session):
    """Create an order repository"""
    return OrderRepository(db_session)

@pytest.fixture
def inventory_repo(db_session):
    """Create an inventory repository"""
    return InventoryRepository(db_session)

@pytest.fixture
def email_service():
    """Create a mock email service"""
    return EmailService()

@pytest.fixture
def user_created_handler(user_repo, email_service):
    """Create a user created handler"""
    return UserCreatedHandler(user_repo, email_service)

@pytest.fixture
def order_placed_handler(order_repo, inventory_repo):
    """Create an order placed handler"""
    return OrderPlacedHandler(order_repo, inventory_repo)
