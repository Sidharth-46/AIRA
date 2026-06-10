from models.memory import MemoryModel
from utils.logger import get_logger

logger = get_logger("memory.manager")

class MemoryManager:
    """
    Manages long-term and short-term memory operations.
    """
    
    @staticmethod
    def save_preference(user_id: str, category: str, value: str):
        """
        Save a distinct user preference (e.g., 'uses_tailwind', 'prefers_typing').
        """
        MemoryModel.create_memory(
            user_id=user_id,
            memory_type="preference",
            key=category,
            value=value
        )
        logger.info(f"Saved preference for {user_id}: {category}={value}")


