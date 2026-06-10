"""
AIRA — MongoDB Connection Manager
Handles connection pooling, index creation, and health checks.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from utils.logger import get_logger

logger = get_logger("database")

# Module-level client and db references
_client = None
_db = None


def init_db(app):
    """Initialize MongoDB connection and create indexes."""
    global _client, _db

    uri = app.config.get("MONGODB_URI", "mongodb://localhost:27017/aira")
    db_name = app.config.get("MONGODB_DB_NAME", "aira")

    try:
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50,
            minPoolSize=5,
        )
        # Force connection check
        _client.admin.command("ping")
        _db = _client[db_name]

        _create_indexes()
        logger.info(f"MongoDB connected: {db_name}")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise


def get_db():
    """Get the database instance."""
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db(app) first.")
    return _db


def get_collection(name):
    """Get a collection by name."""
    return get_db()[name]


def _create_indexes():
    """Create database indexes for optimal query performance."""
    db = get_db()

    # Users collection
    db.users.create_index("email", unique=True)
    db.users.create_index("username")

    # Chats collection
    db.chats.create_index([("user_id", 1), ("created_at", -1)])
    db.chats.create_index([("user_id", 1), ("folder", 1)])
    db.chats.create_index([("user_id", 1), ("pinned", -1)])

    # Messages collection
    db.messages.create_index([("chat_id", 1), ("timestamp", 1)])

    # Projects collection
    db.projects.create_index([("user_id", 1), ("created_at", -1)])

    # Documents collection
    db.documents.create_index([("user_id", 1), ("uploaded_at", -1)])
    db.documents.create_index("collection_id")

    # Memory collection
    db.memory.create_index([("user_id", 1), ("key", 1)], unique=True)

    # Activity collection
    db.activity.create_index([("user_id", 1), ("timestamp", -1)])

    logger.info("Database indexes created")


def health_check():
    """Check MongoDB health. Returns (healthy, info)."""
    try:
        if _client is None:
            return False, {"status": "disconnected"}

        result = _client.admin.command("ping")
        db_stats = _db.command("dbstats") if _db else {}

        return True, {
            "status": "connected",
            "ping": result.get("ok", 0),
            "database": _db.name if _db else None,
            "collections": _db.list_collection_names() if _db else [],
            "storage_size": db_stats.get("storageSize", 0),
        }
    except Exception as e:
        return False, {"status": "error", "error": str(e)}


def close_db():
    """Close the database connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
