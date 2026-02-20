from typing import Dict
import logging

from src.handlers.base import MessageHandler

logger = logging.getLogger(__name__)

class UnknownEventTypeError(Exception):
    """Raised when message type is not registered"""
    pass

class MessageRouter:
    """Routes messages to appropriate handlers"""
    
    def __init__(self):
        self.handlers: Dict[str, MessageHandler] = {}
    
    def register(self, event_type: str, handler: MessageHandler) -> None:
        """Register a handler for an event type"""
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")
    
    async def route(self, message: dict) -> None:
        """
        Route a message to the appropriate handler.
        
        Args:
            message: Message dictionary with 'type' and 'data' keys
            
        Raises:
            UnknownEventTypeError: If no handler is registered for the event type
            ValueError: If message is missing required fields
        """
        event_type = message.get("type")
        if not event_type:
            raise ValueError("Message missing 'type' field")
        
        handler = self.handlers.get(event_type)
        if not handler:
            raise UnknownEventTypeError(f"Unknown event type: {event_type}")
        
        logger.debug(f"Routing {event_type} to {handler.__class__.__name__}")
        await handler.handle(message)
