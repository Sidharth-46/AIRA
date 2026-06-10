"""
AIRA — Context Manager
Builds and compresses context for agent calls.
"""

from utils.logger import get_logger

logger = get_logger("orchestrator.context")


class ContextManager:
    """
    Manages context assembly for multi-agent pipeline.
    Ensures each agent gets relevant, token-efficient context.
    """

    def __init__(self, max_context_tokens=8000):
        self.max_context_tokens = max_context_tokens

    def build_context(self, history=None, rag_results=None, file_contents=None,
                      project_info=None, plan=None, research=None,
                      review_feedback=None, user_preferences=None,
                      original_request=None, code_output=None,
                      workspace_context_string=None):
        """
        Build a context dict for agent consumption.
        Compresses content if it exceeds token budget.
        """
        context = {}

        # Conversation history (sliding window)
        if history:
            context["history"] = self._compress_history(history)

        # RAG search results
        if rag_results:
            context["rag_results"] = self._truncate(rag_results, 2000)

        # File contents
        if file_contents:
            context["file_contents"] = self._truncate(file_contents, 3000)

        # Project information
        if project_info:
            context["project_info"] = self._truncate(project_info, 1000)

        # Execution plan from Planner
        if plan:
            context["plan"] = plan

        # Research findings
        if research:
            context["research"] = self._truncate(research, 3000)

        # Review feedback for iteration
        if review_feedback:
            context["review_feedback"] = self._truncate(review_feedback, 1500)

        # User preferences from memory
        if user_preferences:
            context["user_preferences"] = self._truncate(user_preferences, 500)

        # Workspace context
        if workspace_context_string:
            context["workspace_context"] = workspace_context_string

        # Original request (for reviewer)
        if original_request:
            context["original_request"] = original_request

        # Code output (for reviewer)
        if code_output:
            context["code_output"] = self._truncate(code_output, 4000)

        return context

    def _compress_history(self, history, max_messages=10):
        """
        Compress conversation history to fit token budget.
        Keeps recent messages, summarizes older ones.
        """
        if len(history) <= max_messages:
            return history

        # Keep last N messages
        recent = history[-max_messages:]

        # Summarize older messages (simple truncation for now)
        older = history[:-max_messages]
        if older:
            summary = {
                "role": "system",
                "content": f"[Earlier conversation: {len(older)} messages summarized] "
                           + " | ".join([m.get("content", "")[:50] for m in older[-3:]]),
            }
            return [summary] + recent

        return recent

    def _truncate(self, text, max_chars):
        """Truncate text to approximate token limit (4 chars ≈ 1 token)."""
        if isinstance(text, dict):
            import json
            text = json.dumps(text, indent=2)

        if len(text) <= max_chars:
            return text

        truncated = text[:max_chars]
        return truncated + f"\n\n[... truncated, {len(text) - max_chars} chars omitted]"
