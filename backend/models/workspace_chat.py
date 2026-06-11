"""
AIRA — Workspace Chat Model
MongoDB document for project-specific workspace chat.
"""

from datetime import datetime, timezone
from bson import ObjectId
from services.database import get_collection
from utils.logger import get_logger

logger = get_logger("models.workspace_chat")

class WorkspaceChat:
    COLLECTION = "workspace_chats"

    @staticmethod
    def _collection():
        return get_collection(WorkspaceChat.COLLECTION)

    @staticmethod
    def get_or_create(project_id, user_id):
        """Get the workspace chat for a project, or create it if missing."""
        query = {"projectId": str(project_id), "userId": str(user_id)}
        chat = WorkspaceChat._collection().find_one(query)
        
        if not chat:
            chat = {
                "projectId": str(project_id),
                "userId": str(user_id),
                "messages": [],
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
            }
            result = WorkspaceChat._collection().insert_one(chat)
            chat["_id"] = result.inserted_id
            
        return WorkspaceChat._serialize(chat)

    @staticmethod
    def add_message(project_id, user_id, role, content, agent=None):
        """Append a message to the workspace chat."""
        query = {"projectId": str(project_id), "userId": str(user_id)}
        message = {
            "id": str(ObjectId()),
            "role": role,
            "content": content,
            "agent": agent,
            "timestamp": datetime.now(timezone.utc),
        }
        
        result = WorkspaceChat._collection().find_one_and_update(
            query,
            {
                "$push": {"messages": message},
                "$set": {"updatedAt": datetime.now(timezone.utc)}
            },
            return_document=True
        )
        return WorkspaceChat._serialize(result)

    @staticmethod
    def clear_messages(project_id, user_id):
        """Clear all messages from the workspace chat."""
        query = {"projectId": str(project_id), "userId": str(user_id)}
        result = WorkspaceChat._collection().find_one_and_update(
            query,
            {
                "$set": {
                    "messages": [],
                    "updatedAt": datetime.now(timezone.utc)
                }
            },
            return_document=True
        )
        return WorkspaceChat._serialize(result)

    @staticmethod
    def _serialize(chat):
        if chat is None:
            return None
        chat["id"] = str(chat.pop("_id"))
        
        # Serialize datetime fields
        chat["createdAt"] = chat["createdAt"].isoformat() if isinstance(chat.get("createdAt"), datetime) else chat.get("createdAt")
        chat["updatedAt"] = chat["updatedAt"].isoformat() if isinstance(chat.get("updatedAt"), datetime) else chat.get("updatedAt")
        
        # Serialize nested messages
        for msg in chat.get("messages", []):
            if isinstance(msg.get("timestamp"), datetime):
                msg["timestamp"] = msg["timestamp"].isoformat()
                
        return chat
