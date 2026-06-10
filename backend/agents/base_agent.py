"""
AIRA — Base Agent
Abstract base class for all agents (Planner, Research, Coder, Reviewer).
All AI calls go through BaseModelProvider.
"""

from abc import ABC, abstractmethod
from typing import Generator

from services.model_providers.base_provider import BaseModelProvider
from utils.logger import get_logger

logger = get_logger("agents.base")


class BaseAgent(ABC):
    """
    Abstract base for all AIRA agents.
    Each agent has a specialized system prompt and execution logic.
    """

    def __init__(self, model_provider: BaseModelProvider, system_prompt: str,
                 name: str = "agent", temperature: float = 0.7, max_tokens: int = 4096):
        self.provider = model_provider
        self.system_prompt = system_prompt
        self.name = name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._logger = get_logger(f"agents.{name}")

    @abstractmethod
    def execute(self, task: dict, context: dict) -> dict:
        """
        Execute agent task synchronously.
        
        Args:
            task: {"message": str, "intent": str, ...}
            context: {"history": [...], "files": [...], "project": {...}, ...}
            
        Returns:
            {"content": str, "metadata": dict}
        """
        pass

    @abstractmethod
    def stream_execute(self, task: dict, context: dict) -> Generator[str, None, None]:
        """
        Execute agent task with streaming output.
        Yields tokens one at a time for SSE.
        """
        pass

    def _build_messages(self, task: dict, context: dict) -> list:
        """
        Build message list for the model provider.
        Combines conversation history with current task.
        """
        messages = []

        # Add conversation history (if any)
        history = context.get("history", [])
        for msg in history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        # Build current task message
        task_content = self._build_task_prompt(task, context)
        messages.append({"role": "user", "content": task_content})

        return messages

    def _build_task_prompt(self, task: dict, context: dict) -> str:
        """
        Build the task-specific prompt with context.
        Override in subclasses for specialized prompts.
        """
        parts = []

        # Add context if available
        if context.get("rag_results"):
            parts.append("## Relevant Context\n" + context["rag_results"])

        if context.get("file_contents"):
            parts.append("## Referenced Files\n" + context["file_contents"])

        if context.get("project_info"):
            parts.append("## Project Information\n" + context["project_info"])

        if context.get("plan"):
            parts.append("## Execution Plan\n" + context["plan"])

        if context.get("review_feedback"):
            parts.append("## Review Feedback (Address These Issues)\n" + context["review_feedback"])

        # Add the user's request
        parts.append("## User Request\n" + task.get("message", ""))

        return "\n\n".join(parts)

    def _safe_execute(self, messages: list) -> str:
        """Execute with retry logic (max 2 retries)."""
        last_error = None

        for attempt in range(3):
            try:
                return self.provider.chat(
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    system_prompt=self.system_prompt,
                )
            except Exception as e:
                last_error = e
                self._logger.warning(f"Attempt {attempt + 1} failed: {e}")

        self._logger.error(f"All attempts failed: {last_error}")
        raise RuntimeError(f"{self.name} agent failed after 3 attempts: {last_error}")

    def _safe_stream(self, messages: list) -> Generator[str, None, None]:
        """Stream with error handling."""
        try:
            yield from self.provider.stream_chat(
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                system_prompt=self.system_prompt,
            )
        except Exception as e:
            self._logger.error(f"Stream error: {e}")
            yield f"\n\n[Error: {self.name} agent streaming failed — {e}]"
