from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Any

class MessageHandler(ABC):
    """Base class for message handlers"""
    
    @abstractmethod
    async def handle(self, message: dict[str, Any]) -> None:
        """
        Process a single message.
        
        Args:
            message: Message dictionary with 'type' and 'data' keys
            
        Raises:
            ValidationError: If message data is invalid
            DatabaseError: If database operation fails
            ExternalAPIError: If external service call fails
        """
        pass
