"""
AIRA — Dashboard Service
Aggregation queries for user statistics and activity.
"""

from datetime import datetime, timezone, timedelta
from bson import ObjectId

from services.database import get_db
from models.chat import Chat, Message
from models.project import Project
from models.document import Document
from utils.logger import get_logger

logger = get_logger("services.dashboard")


class DashboardService:
    """Dashboard analytics service."""

    @staticmethod
    def get_stats(user_id):
        """Get user dashboard statistics."""
        db = get_db()

        total_chats = Chat.count_by_user(user_id)
        total_projects = Project.count_by_user(user_id)
        total_documents = Document.count_by_user(user_id)
        total_messages = Message.count_by_user_chats(user_id)

        # Count agent calls from message metadata
        agent_calls = db.messages.count_documents({
            "chat_id": {"$in": [
                str(c["_id"]) for c in db.chats.find(
                    {"user_id": str(user_id)}, {"_id": 1}
                )
            ]},
            "role": "assistant",
            "agent": {"$ne": None},
        })

        return {
            "totalChats": total_chats,
            "uploadedRepos": total_projects,
            "generatedFiles": total_documents,
            "total_messages": total_messages,
            "agentCalls": agent_calls,
        }

    @staticmethod
    def get_activity(user_id, limit=10):
        """Get recent user activity."""
        db = get_db()

        activities = list(
            db.activity.find(
                {"user_id": str(user_id)}
            ).sort("timestamp", -1).limit(limit)
        )

        for a in activities:
            a["id"] = str(a.pop("_id"))
            a["timestamp"] = a["timestamp"].isoformat()

        return activities

    @staticmethod
    def get_usage_chart(user_id, days=7):
        """Get message count per day for the last N days."""
        db = get_db()
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)

        # Get user's chat IDs
        chat_ids = [
            str(c["_id"]) for c in db.chats.find(
                {"user_id": str(user_id)}, {"_id": 1}
            )
        ]

        if not chat_ids:
            return [{"date": (now - timedelta(days=i)).strftime("%Y-%m-%d"), "count": 0} for i in range(days - 1, -1, -1)]

        # Aggregate messages per day
        pipeline = [
            {
                "$match": {
                    "chat_id": {"$in": chat_ids},
                    "timestamp": {"$gte": start},
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = list(db.messages.aggregate(pipeline))
        counts = {r["_id"]: r["count"] for r in results}

        # Fill in missing days
        chart = []
        for i in range(days - 1, -1, -1):
            date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            chart.append({"date": date, "count": counts.get(date, 0)})

        return chart


