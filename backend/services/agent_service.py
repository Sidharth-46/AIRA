"""
AIRA — Agent Service
Bridge between routes and the agent orchestrator.
Service layer pattern: Routes → AgentService → Orchestrator → Agents → ModelProvider
"""

from models.chat import Message
from orchestrator.orchestrator import AgentOrchestrator
from services.chat_service import ChatService
from utils.logger import get_logger

logger = get_logger("services.agent")


class AgentService:
    """
    Agent service layer — the bridge between HTTP routes and the agent system.
    This is what ChatService calls for AI responses.
    """

    _orchestrator = None

    @classmethod
    def _get_orchestrator(cls):
        """Lazy-initialize the orchestrator."""
        if cls._orchestrator is None:
            try:
                from services.model_providers.model_registry import get_registry
                registry = get_registry()
                registry.initialize()
                cls._orchestrator = AgentOrchestrator()
                logger.info("Agent orchestrator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize orchestrator: {e}")
                raise
        return cls._orchestrator

    @classmethod
    def process_message(cls, user_id, chat_id, message, workspace_context=None):
        """
        Process a user message through the agent pipeline.
        Returns a generator that yields SSE events.
        
        Events:
            {"event": "agent_status", "data": "planner|research|coder|reviewer"}
            {"event": "token", "data": "..."}
            {"event": "done", "data": "full_response"}
        """
        
        # Check identity fallback
        from utils.identity import check_identity_fallback
        fallback_response = check_identity_fallback(message)
        if fallback_response:
            def stream_fallback():
                yield {"event": "agent_status", "data": "general"}
                yield {"event": "token", "data": fallback_response}
                
                try:
                    Message.create(
                        chat_id=chat_id,
                        role="assistant",
                        content=fallback_response,
                        agent="general",
                        metadata={"model": "identity_fallback"},
                    )
                except Exception as e:
                    logger.error(f"Fallback save failed: {e}")
                    
                yield {"event": "done", "data": ""}
            return stream_fallback()
            
        try:
            orchestrator = cls._get_orchestrator()
        except Exception as exc:
            error_msg = str(exc)
            # Orchestrator initialization failed — return error
            def error_gen():
                yield {"event": "token", "data": f"AIRA is unable to process your request. Please ensure Ollama is running. Error: {error_msg}"}
                yield {"event": "done", "data": ""}
            return error_gen()

        # Get conversation history for context
        history = ChatService.get_conversation_history(chat_id)

        # Get user preferences from memory (if available)
        user_preferences = None
        try:
            from memory.memory_manager import MemoryManager
            prefs = MemoryManager.get_preferences(user_id)
            if prefs:
                user_preferences = str(prefs)
        except (ImportError, Exception):
            pass

        # Build workspace context if provided
        workspace_context_string = None
        if workspace_context and workspace_context.get("projectId"):
            from services.workspace_context_builder import WorkspaceContextBuilder
            try:
                workspace_context_string = WorkspaceContextBuilder.get_context(
                    project_id=workspace_context.get("projectId"),
                    current_file=workspace_context.get("currentFile", ""),
                    prompt=message
                )
            except Exception as e:
                logger.error(f"Failed to build workspace context: {e}")

        # Create generator that processes and saves response
        def stream_and_save():
            full_response = ""
            current_agent = None
            message_saved = False

            try:
                for event in orchestrator.process(
                    message=message,
                    history=history,
                    user_preferences=user_preferences,
                    workspace_context_string=workspace_context_string,
                ):
                    event_type = event.get("event")

                    if event_type == "agent_status":
                        current_agent = event.get("data")

                    elif event_type == "token":
                        full_response += event.get("data", "")

                    if event_type == "done":
                        # GUARANTEE: Save message and verify before yielding done
                        if full_response and not message_saved:
                            try:
                                logger.info(f"MESSAGE_SAVE_START: chat={chat_id}")
                                Message.create(
                                    chat_id=chat_id,
                                    role="assistant",
                                    content=full_response,
                                    agent=current_agent,
                                    metadata={
                                        "model": orchestrator.coder.provider.get_model_name() if hasattr(orchestrator, 'coder') and orchestrator.coder else "unknown",
                                    },
                                )
                                message_saved = True
                                
                                # Notify registry of successful generation
                                from services.model_providers.model_registry import get_registry
                                get_registry().mark_successful_generation()
                                
                                logger.info(f"MESSAGE_SAVE_SUCCESS: chat={chat_id}")
                            except Exception as e:
                                logger.error(f"MESSAGE_SAVE_FAILURE: chat={chat_id}, error={e}")
                                yield {"event": "error", "data": f"Failed to save message: {str(e)}"}

                        # Title Generation (if first message)
                        if len(history) <= 1:
                            def generate_title():
                                try:
                                    logger.info(f"Generating smart title for chat {chat_id}")
                                    prompt = f"Generate a concise 2-5 word title for this chat. Use Title Case. No punctuation. Prefer: General Conversation, Coding Help, Project Discussion, Repository Analysis. Avoid: Hi, Hello, Test. Message: {message}"
                                    # Create a separate provider instance or use the existing one if thread-safe
                                    from services.model_providers.model_registry import get_provider
                                    from services.model_router import get_model_router
                                    router = get_model_router()
                                    model = router.get_diagnostics().get("general_model", "qwen2.5-coder:7b")
                                    provider = get_provider(model)
                                    title = provider.chat([{"role": "user", "content": prompt}], max_tokens=15, temperature=0.3).strip('"\'. ')
                                    
                                    from models.chat import Chat
                                    Chat.update(chat_id, user_id, {"title": title})
                                    # We cannot yield the SSE event from a thread, but the frontend can poll or we can just send it before the thread starts if we wanted.
                                    # But since we can't yield from thread, we'll yield a generic title update now, and let the thread update the DB for next time.
                                    # Wait, SSE stream can't be yielded from a thread to the same generator.
                                except Exception as exc:
                                    logger.error(f"Title generation failed: {exc}")
                                    from models.chat import Chat
                                    chat = Chat.find_by_id(chat_id)
                                    if chat and chat.get("title") == "New Chat":
                                        Chat.update(chat_id, user_id, {"title": "General Conversation"})

                            import threading
                            threading.Thread(target=generate_title, daemon=True).start()
                            yield {"event": "title_update", "data": "Processing..."}

                    # Yield the event to frontend
                    yield event
                    
            finally:
                # Fallback safeguard: Save response if generator aborted abruptly
                if full_response and not message_saved:
                    try:
                        logger.info(f"MESSAGE_SAVE_START (Fallback): chat={chat_id}")
                        Message.create(
                            chat_id=chat_id,
                            role="assistant",
                            content=full_response,
                            agent=current_agent,
                            metadata={
                                "model": orchestrator.coder.provider.get_model_name() if hasattr(orchestrator, 'coder') and orchestrator.coder else "unknown",
                            },
                        )
                        logger.info(f"MESSAGE_SAVE_SUCCESS (Fallback): chat={chat_id}")
                    except Exception as e:
                        logger.error(f"MESSAGE_SAVE_FAILURE (Fallback): chat={chat_id}, error={e}")

        return stream_and_save()

    @classmethod
    def reset_orchestrator(cls):
        """Reset the orchestrator (e.g., after model switch)."""
        cls._orchestrator = None
        logger.info("Orchestrator reset")
