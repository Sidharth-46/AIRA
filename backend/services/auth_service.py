"""
AIRA — Authentication Service
Handles signup, login, JWT token management.
Routes → Service → Model pattern.
"""

from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError

from models.user import User
from utils.logger import get_logger

logger = get_logger("services.auth")


class AuthService:
    """Authentication service layer."""

    @staticmethod
    def signup(data):
        """
        Register a new user.
        Returns (user_dict, error_message).
        """
        username = data["username"]
        email = data["email"]
        password = data["password"]

        # Check if email already exists
        existing = User.find_by_email(email)
        if existing:
            return None, "Email already registered"

        # Check if username already exists
        existing_username = User.find_by_username(username)
        if existing_username:
            return None, "Username already taken"

        try:
            user = User.create(username, email, password)
            logger.info(f"User registered: {email}")
            return user, None
        except DuplicateKeyError:
            return None, "Email already registered"
        except Exception as e:
            logger.error(f"Signup error: {e}")
            return None, "Registration failed. Please try again."

    @staticmethod
    def login(data):
        """
        Authenticate a user.
        Returns (user_dict, error_message).
        """
        email = data["email"]
        password = data["password"]

        user = User.find_by_email(email)
        if not user:
            return None, "Invalid email or password"

        if not User.verify_password(user["password_hash"], password):
            return None, "Invalid email or password"

        # Update last login
        User.update_last_login(user["_id"])

        # Sanitize for response
        user_data = User._sanitize(user)
        logger.info(f"User logged in: {email}")
        return user_data, None

    @staticmethod
    def get_profile(user_id):
        """Get user profile by ID."""
        user = User.find_by_id(user_id)
        if not user:
            return None, "User not found"
        return user, None

    @staticmethod
    def update_preferences(user_id, preferences):
        """Update user preferences."""
        User.update_preferences(user_id, preferences)
        user = User.find_by_id(user_id)
        return user, None
