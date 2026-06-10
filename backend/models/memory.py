from datetime import datetime

from services.database import get_db

class MemoryModel:
    """
    MongoDB model for storing long-term memory and user preferences.
    """
    collection_name = "memory"

    @classmethod
    def get_collection(cls):
        return get_db()[cls.collection_name]

    @classmethod
    def create_memory(cls, user_id: str, memory_type: str, key: str, value: any):
        """
        Create or update a memory record.
        Types: 'preference', 'project_context', 'technology', 'interaction'
        """
        memory = {
            "user_id": user_id,
            "memory_type": memory_type,
            "key": key,
            "value": value,
            "updated_at": datetime.utcnow()
        }
        
        # Upsert based on user_id, type, and key
        cls.get_collection().update_one(
            {"user_id": user_id, "memory_type": memory_type, "key": key},
            {"$set": memory},
            upsert=True
        )
        return memory

    @classmethod
    def get_user_memories(cls, user_id: str, memory_type: str = None) -> list:
        query = {"user_id": user_id}
        if memory_type:
            query["memory_type"] = memory_type
            
        cursor = cls.get_collection().find(query, {"_id": 0})
        return list(cursor)

