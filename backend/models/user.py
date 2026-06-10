"""
AIRA — User Model
MongoDB user document with password hashing.
"""

from datetime import datetime, timezone
from bson import ObjectId
import bcrypt

from services.database import get_collection
from utils.logger import get_logger

logger = get_logger("models.user")


class User:
    """User model for authentication and profile management."""

    COLLECTION = "users"

    @staticmethod
    def _collection():
        return get_collection(User.COLLECTION)

    @staticmethod
    def create(username, email, password):
        """Create a new user. Returns user dict or raises on duplicate."""
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        user_doc = {
            "username": username,
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "role": "user",
            "preferences": {
                "theme": "dark",
                "default_model": None,
                "coding_language": None,
            },
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
        }

        result = User._collection().insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        logger.info(f"User created: {email}")
        return User._sanitize(user_doc)

    @staticmethod
    def find_by_email(email):
        """Find user by email. Returns full user dict including password_hash."""
        return User._collection().find_one({"email": email.lower().strip()})

    @staticmethod
    def find_by_id(user_id):
        """Find user by ID. Returns sanitized user dict."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        user = User._collection().find_one({"_id": user_id})
        return User._sanitize(user) if user else None

    @staticmethod
    def find_by_username(username):
        """Find user by username."""
        return User._collection().find_one({"username": username})

    @staticmethod
    def verify_password(stored_hash, password):
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8"),
        )

    @staticmethod
    def update_last_login(user_id):
        """Update the last login timestamp."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        User._collection().update_one(
            {"_id": user_id},
            {"$set": {"last_login": datetime.now(timezone.utc)}},
        )

    @staticmethod
    def update_preferences(user_id, preferences):
        """Update user preferences."""
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        User._collection().update_one(
            {"_id": user_id},
            {"$set": {f"preferences.{k}": v for k, v in preferences.items()}},
        )

    @staticmethod
    def count():
        """Get total user count."""
        return User._collection().count_documents({})

    @staticmethod
    def _sanitize(user):
        """Remove sensitive fields from user dict."""
        if user is None:
            return None
        user["id"] = str(user.pop("_id"))
        user.pop("password_hash", None)
        return user
