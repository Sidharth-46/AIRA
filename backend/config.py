"""
AIRA — Configuration Module
Loads settings from environment variables with sensible defaults.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/aira")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "aira")

    # Ollama
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_DEFAULT_MODEL = os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3-coder")
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    OLLAMA_REQUEST_TIMEOUT = int(os.getenv("OLLAMA_REQUEST_TIMEOUT", 120))

    # ChromaDB
    CHROMADB_PATH = os.getenv("CHROMADB_PATH", "./data/embeddings")

    # Upload
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", 100))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./data/uploads")

    # Workspace
    WORKSPACE_FOLDER = os.getenv("WORKSPACE_FOLDER", "./data/workspace")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "./logs/aira.log")

    # CORS
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")

    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "100/hour")


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG = False
    FLASK_ENV = "production"

    def __init__(self):
        super().__init__()
        # Validate critical settings in production
        if self.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set in production!")
        if self.JWT_SECRET_KEY == "dev-jwt-secret-change-in-production":
            raise ValueError("JWT_SECRET_KEY must be set in production!")


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING = True
    MONGODB_DB_NAME = "aira_test"


# Config selector
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    """Get configuration based on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class()
