"""
AIRA — Workspace Chat Service
Handles workspace-specific chat operations and SSE message streaming.
"""

from models.workspace_chat import WorkspaceChat
from services.workspace_context_builder import WorkspaceContextBuilder
from utils.logger import get_logger

logger = get_logger("services.workspace_chat")

class WorkspaceChatService:
    """Service layer for workspace project-specific chats."""

    @staticmethod
    def get_chat(project_id, user_id):
        """Get or create the workspace chat for a project."""
        chat = WorkspaceChat.get_or_create(project_id, user_id)
        return chat, None

    @staticmethod
    def clear_chat(project_id, user_id):
        """Clear all messages from a workspace chat."""
        chat = WorkspaceChat.clear_messages(project_id, user_id)
        if not chat:
            return None, "Chat not found"
        return chat, None

    @staticmethod
    def get_conversation_history(project_id, user_id, limit=20):
        """Get recent conversation history for context building."""
        chat = WorkspaceChat.get_or_create(project_id, user_id)
        messages = chat.get("messages", [])[-limit:]
        return [
            {"role": m["role"], "content": m["content"]}
            for m in messages
        ]

    @staticmethod
    def send_message(project_id, user_id, content, current_file=None):
        """
        Send a user message, build workspace context, and generate AI response.
        Returns a generator that yields SSE events.
        """
        # Save user message
        WorkspaceChat.add_message(project_id=project_id, user_id=user_id, role="user", content=content)

        # Build workspace context
        workspace_context = WorkspaceContextBuilder.get_context(
            project_id=project_id,
            current_file=current_file,
            prompt=content
        )
        
        # Format the context block for AgentService exactly like regular chats, 
        # or we can pass it directly. AgentService.process_message expects a chat_id.
        # Since Workspace chats are 1-1 with project, we will use the WorkspaceChat ID as the chat_id.
        chat = WorkspaceChat.get_or_create(project_id, user_id)
        chat_id = chat["id"]

        try:
            from services.agent_service import AgentService
            
            # AgentService process_message takes chat_id to fetch history.
            # We must wrap process_message or modify it to know about workspace chats vs normal chats.
            # Wait, AgentService.process_message reads history from `Message.find_by_chat(chat_id)`.
            # If we pass a workspace chat_id, it will find NO history in `messages` collection!
            # Let's bypass AgentService or use ModelRouter directly here for simplicity,
            # or we can just call ModelRouter.stream_chat ourselves.
            from services.model_router import ModelRouter
            
            history = WorkspaceChatService.get_conversation_history(project_id, user_id)
            
            # Format messages for router
            # Inject context securely at the very end of history before the final user message, 
            # or into the system prompt.
            system_prompt = "You are AIRA, an expert AI programming assistant.\n"
            if workspace_context:
                system_prompt += f"\n\n{workspace_context}\n"
                
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(history)
            
            # Remove the last user message from history and re-append to ensure correct ordering if needed
            # Wait, history already includes the user message since we just saved it.
            
            def stream_generator():
                from services.model_router import get_model_router
                from services.model_providers.model_registry import get_provider
                
                router = get_model_router()
                route = router.route_request(content, workspace_context=True, context_size=len(workspace_context) if workspace_context else 0)
                model = route.get("model", "qwen2.5-coder:7b")
                
                accumulated = ""
                agent_name = "coder" # Default copilot agent
                
                yield {
                    "event": "agent_status",
                    "data": agent_name
                }
                
                try:
                    provider = get_provider(model)
                    for chunk in provider.stream_chat(messages):
                        accumulated += chunk
                        yield {
                            "event": "token",
                            "data": chunk
                        }
                except Exception as e:
                    logger.error(f"Router error: {e}")
                    yield {
                        "event": "error",
                        "data": str(e)
                    }
                    
                # Save assistant message
                if accumulated:
                    WorkspaceChat.add_message(
                        project_id=project_id,
                        user_id=user_id,
                        role="assistant",
                        content=accumulated,
                        agent=agent_name
                    )
                    
                yield {
                    "event": "done",
                    "data": ""
                }
                
            return stream_generator(), None
            
        except Exception as e:
            logger.error(f"Workspace chat error: {e}")
            return None, str(e)
