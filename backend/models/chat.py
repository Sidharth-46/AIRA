"""
AIRA — Chat & Message Models
MongoDB documents for conversation management.
"""

from datetime import datetime, timezone
from bson import ObjectId

from services.database import get_collection
from utils.logger import get_logger

logger = get_logger("models.chat")


class Chat:
    """Chat model — represents a conversation."""

    COLLECTION = "chats"

    @staticmethod
    def _collection():
        return get_collection(Chat.COLLECTION)

    @staticmethod
    def create(user_id, title="New Chat", folder=None):
        """Create a new chat."""
        chat_doc = {
            "user_id": str(user_id),
            "title": title,
            "folder": folder,
            "pinned": False,
            "message_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = Chat._collection().insert_one(chat_doc)
        chat_doc["_id"] = result.inserted_id
        return Chat._serialize(chat_doc)

    @staticmethod
    def find_by_user(user_id, search=None, folder=None, page=1, limit=50):
        """Find chats for a user with optional search and folder filter."""
        query = {"user_id": str(user_id)}

        if search:
            query["title"] = {"$regex": search, "$options": "i"}
        if folder is not None:
            query["folder"] = folder

        cursor = (
            Chat._collection()
            .find(query)
            .sort([("pinned", -1), ("updated_at", -1)])
            .skip((page - 1) * limit)
            .limit(limit)
        )

        total = Chat._collection().count_documents(query)
        chats = [Chat._serialize(c) for c in cursor]
        return chats, total

    @staticmethod
    def find_by_id(chat_id, user_id=None):
        """Find a chat by ID, optionally scoped to user."""
        query = {"_id": ObjectId(chat_id)}
        if user_id:
            query["user_id"] = str(user_id)
        chat = Chat._collection().find_one(query)
        return Chat._serialize(chat) if chat else None

    @staticmethod
    def update(chat_id, user_id, updates):
        """Update a chat. Returns updated chat or None."""
        allowed = {"title", "folder", "pinned"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed}
        safe_updates["updated_at"] = datetime.now(timezone.utc)

        result = Chat._collection().find_one_and_update(
            {"_id": ObjectId(chat_id), "user_id": str(user_id)},
            {"$set": safe_updates},
            return_document=True,
        )
        return Chat._serialize(result) if result else None

    @staticmethod
    def delete(chat_id, user_id):
        """Delete a chat and all its messages."""
        result = Chat._collection().delete_one(
            {"_id": ObjectId(chat_id), "user_id": str(user_id)}
        )
        if result.deleted_count > 0:
            Message._collection().delete_many({"chat_id": str(chat_id)})
            logger.info(f"Chat deleted: {chat_id}")
            return True
        return False

    @staticmethod
    def increment_message_count(chat_id):
        """Increment message count and update timestamp."""
        Chat._collection().update_one(
            {"_id": ObjectId(chat_id)},
            {
                "$inc": {"message_count": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )

    @staticmethod
    def count_by_user(user_id):
        """Count chats for a user."""
        return Chat._collection().count_documents({"user_id": str(user_id)})

    @staticmethod
    def get_folders(user_id):
        """Get distinct folder names for a user."""
        return Chat._collection().distinct("folder", {"user_id": str(user_id), "folder": {"$ne": None}})

    @staticmethod
    def _serialize(chat):
        if chat is None:
            return None
        chat["id"] = str(chat.pop("_id"))
        chat["created_at"] = chat["created_at"].isoformat()
        chat["updated_at"] = chat["updated_at"].isoformat()
        return chat


class Message:
    """Message model — individual messages within a chat."""

    COLLECTION = "messages"

    @staticmethod
    def _collection():
        return get_collection(Message.COLLECTION)

    @staticmethod
    def create(chat_id, role, content, agent=None, metadata=None):
        """Create a new message."""
        msg_doc = {
            "chat_id": str(chat_id),
            "role": role,  # "user", "assistant", "system"
            "content": content,
            "agent": agent,  # "planner", "research", "coder", "reviewer", None
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc),
        }
        result = Message._collection().insert_one(msg_doc)
        msg_doc["_id"] = result.inserted_id

        # Update chat
        Chat.increment_message_count(chat_id)

        return Message._serialize(msg_doc)

    @staticmethod
    def find_by_chat(chat_id, limit=100):
        """Find messages for a chat, ordered by timestamp."""
        cursor = (
            Message._collection()
            .find({"chat_id": str(chat_id)})
            .sort("timestamp", 1)
            .limit(limit)
        )
        return [Message._serialize(m) for m in cursor]



    @staticmethod
    def count_by_user_chats(user_id):
        """Count total messages across all user's chats."""
        # Get all chat IDs for user
        chat_ids = [
            str(c["_id"])
            for c in get_collection("chats").find(
                {"user_id": str(user_id)}, {"_id": 1}
            )
        ]
        if not chat_ids:
            return 0
        return Message._collection().count_documents(
            {"chat_id": {"$in": chat_ids}}
        )

    @staticmethod
    def _serialize(msg):
        if msg is None:
            return None
        msg["id"] = str(msg.pop("_id"))
        msg["timestamp"] = msg["timestamp"].isoformat()
        return msg
