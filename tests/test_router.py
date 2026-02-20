import pytest
from unittest.mock import AsyncMock
from src.listener.message_router import MessageRouter, UnknownEventTypeError
from src.handlers import UserCreatedHandler

@pytest.mark.asyncio
async def test_router_unknown_event_type():
    """Test router with unknown event type"""
    router = MessageRouter()
    message = {"type": "unknown.event", "data": {}}
    
    with pytest.raises(UnknownEventTypeError):
        await router.route(message)

@pytest.mark.asyncio
async def test_router_missing_type():
    """Test router with missing type field"""
    router = MessageRouter()
    message = {"data": {}}
    
    with pytest.raises(ValueError, match="missing 'type' field"):
        await router.route(message)
