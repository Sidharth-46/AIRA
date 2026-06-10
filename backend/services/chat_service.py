"""
AIRA — Chat Service
Handles chat CRUD, message management, and agent orchestration.
"""

from models.chat import Chat, Message
from utils.logger import get_logger

logger = get_logger("services.chat")


class ChatService:
    """Chat service layer."""

    @staticmethod
    def create_chat(user_id, title="New Chat", folder=None):
        """Create a new chat."""
        chat = Chat.create(user_id, title=title, folder=folder)
        logger.info(f"Chat created: {chat['id']} for user {user_id}")
        return chat, None

    @staticmethod
    def get_chats(user_id, search=None, folder=None, page=1, limit=50):
        """Get user's chats with optional filters."""
        chats, total = Chat.find_by_user(
            user_id, search=search, folder=folder, page=page, limit=limit
        )
        return {
            "chats": chats,
            "total": total,
            "page": page,
            "limit": limit,
        }, None

    @staticmethod
    def get_chat(chat_id, user_id):
        """Get a chat with its messages."""
        chat = Chat.find_by_id(chat_id, user_id=user_id)
        if not chat:
            return None, "Chat not found"

        messages = Message.find_by_chat(chat_id)
        chat["messages"] = messages
        return chat, None

    @staticmethod
    def update_chat(chat_id, user_id, updates):
        """Update a chat."""
        chat = Chat.update(chat_id, user_id, updates)
        if not chat:
            return None, "Chat not found"
        return chat, None

    @staticmethod
    def delete_chat(chat_id, user_id):
        """Delete a chat and its messages."""
        deleted = Chat.delete(chat_id, user_id)
        if not deleted:
            return False, "Chat not found"
        return True, None



    @staticmethod
    def get_conversation_history(chat_id, limit=20):
        """Get recent conversation history for context building."""
        messages = Message.find_by_chat(chat_id, limit=limit)
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

    @staticmethod
    def get_folders(user_id):
        """Get user's chat folders."""
        return Chat.get_folders(user_id)

    @staticmethod
    def send_message(chat_id, user_id, content, workspace_context=None):
        """
        Send a user message and generate AI response.
        Returns a generator that yields SSE events.
        """
        # Verify chat ownership
        chat = Chat.find_by_id(chat_id, user_id=user_id)
        if not chat:
            return None, "Chat not found"

        # Save user message
        Message.create(chat_id=chat_id, role="user", content=content)

        # Auto-title on first message logic has been moved to agent_service.py
        # where it intelligently generates a concise title using the LLM.

        # Generate AI response via agent service
        # This import is deferred to avoid circular imports
        try:
            from services.agent_service import AgentService
            generator = AgentService.process_message(
                user_id=user_id,
                chat_id=chat_id,
                message=content,
                workspace_context=workspace_context,
            )
            return generator, None
        except ImportError:
            # Agent service not yet available — return placeholder
            def placeholder_generator():
                yield {
                    "event": "agent_status",
                    "data": "coder",
                }
                yield {
                    "event": "token",
                    "data": "AIRA is initializing. The agent system will be available once Ollama is configured. "
                            "Please ensure Ollama is running and a model is pulled.",
                }
                yield {
                    "event": "done",
                    "data": "",
                }

            # Save placeholder response
            Message.create(
                chat_id=chat_id,
                role="assistant",
                content="AIRA is initializing. The agent system will be available once Ollama is configured. "
                        "Please ensure Ollama is running and a model is pulled.",
                agent="system",
            )
            return placeholder_generator(), None
