"""
AIRA — Project Model
MongoDB document for repository/project management.
"""

from datetime import datetime, timezone
from bson import ObjectId

from services.database import get_collection
from utils.logger import get_logger

logger = get_logger("models.project")


class Project:
    """Project model — uploaded or generated project repositories."""

    COLLECTION = "projects"

    @staticmethod
    def _collection():
        return get_collection(Project.COLLECTION)

    @staticmethod
    def create(user_id, name, project_type, path, structure=None):
        """Create a new project record."""
        doc = {
            "user_id": str(user_id),
            "name": name,
            "type": project_type,  # "uploaded" or "generated"
            "path": path,
            "structure": structure or {},
            "analysis": None,
            "languages": [],
            "files_count": 0,
            "total_size": 0,
            "status": "ready",  # "processing", "ready", "error"
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        result = Project._collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info(f"Project created: {name} ({project_type})")
        return Project._serialize(doc)

    @staticmethod
    def find_by_user(user_id, page=1, limit=20):
        """Find projects for a user."""
        query = {"user_id": str(user_id)}
        cursor = (
            Project._collection()
            .find(query)
            .sort("created_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        total = Project._collection().count_documents(query)
        return [Project._serialize(p) for p in cursor], total

    @staticmethod
    def find_by_id(project_id, user_id=None):
        """Find a project by ID."""
        query = {"_id": ObjectId(project_id)}
        if user_id:
            query["user_id"] = str(user_id)
        doc = Project._collection().find_one(query)
        return Project._serialize(doc) if doc else None

    @staticmethod
    def update_analysis(project_id, analysis, languages=None, files_count=None, total_size=None):
        """Update project analysis results."""
        updates = {
            "analysis": analysis,
            "status": "ready",
            "updated_at": datetime.now(timezone.utc),
        }
        if languages is not None:
            updates["languages"] = languages
        if files_count is not None:
            updates["files_count"] = files_count
        if total_size is not None:
            updates["total_size"] = total_size

        Project._collection().update_one(
            {"_id": ObjectId(project_id)},
            {"$set": updates},
        )

    @staticmethod
    def update_status(project_id, status):
        """Update project status."""
        Project._collection().update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        )

    @staticmethod
    def delete(project_id, user_id):
        """Delete a project record."""
        result = Project._collection().delete_one(
            {"_id": ObjectId(project_id), "user_id": str(user_id)}
        )
        return result.deleted_count > 0

    @staticmethod
    def count_by_user(user_id):
        """Count projects for a user."""
        return Project._collection().count_documents({"user_id": str(user_id)})

    @staticmethod
    def _serialize(doc):
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        doc["created_at"] = doc["created_at"].isoformat()
        doc["updated_at"] = doc["updated_at"].isoformat()
        return doc
