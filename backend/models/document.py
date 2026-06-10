"""
AIRA — Document Model
MongoDB document for RAG document management.
"""

from datetime import datetime, timezone
from bson import ObjectId

from services.database import get_collection
from utils.logger import get_logger

logger = get_logger("models.document")


class Document:
    """Document model — uploaded documents for RAG processing."""

    COLLECTION = "documents"

    @staticmethod
    def _collection():
        return get_collection(Document.COLLECTION)

    @staticmethod
    def create(user_id, filename, doc_type, size, collection_id=None):
        """Create a new document record."""
        doc = {
            "user_id": str(user_id),
            "filename": filename,
            "type": doc_type,  # "pdf", "docx", "txt", "md", "code"
            "size": size,
            "chunks_count": 0,
            "collection_id": collection_id,
            "status": "processing",  # "processing", "ready", "error"
            "uploaded_at": datetime.now(timezone.utc),
        }
        result = Document._collection().insert_one(doc)
        doc["_id"] = result.inserted_id
        logger.info(f"Document created: {filename}")
        return Document._serialize(doc)

    @staticmethod
    def find_by_user(user_id, page=1, limit=20):
        """Find documents for a user."""
        query = {"user_id": str(user_id)}
        cursor = (
            Document._collection()
            .find(query)
            .sort("uploaded_at", -1)
            .skip((page - 1) * limit)
            .limit(limit)
        )
        total = Document._collection().count_documents(query)
        return [Document._serialize(d) for d in cursor], total

    @staticmethod
    def find_by_id(doc_id, user_id=None):
        """Find a document by ID."""
        query = {"_id": ObjectId(doc_id)}
        if user_id:
            query["user_id"] = str(user_id)
        doc = Document._collection().find_one(query)
        return Document._serialize(doc) if doc else None

    @staticmethod
    def update_status(doc_id, status, chunks_count=None):
        """Update document processing status."""
        updates = {"status": status}
        if chunks_count is not None:
            updates["chunks_count"] = chunks_count
        Document._collection().update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": updates},
        )

    @staticmethod
    def delete(doc_id, user_id):
        """Delete a document record."""
        result = Document._collection().delete_one(
            {"_id": ObjectId(doc_id), "user_id": str(user_id)}
        )
        return result.deleted_count > 0

    @staticmethod
    def count_by_user(user_id):
        """Count documents for a user."""
        return Document._collection().count_documents({"user_id": str(user_id)})

    @staticmethod
    def _serialize(doc):
        if doc is None:
            return None
        doc["id"] = str(doc.pop("_id"))
        doc["uploaded_at"] = doc["uploaded_at"].isoformat()
        return doc
