"""
AIRA — General Agent
Handles general conversation, everyday questions, and explanations.
Designed for low latency and conversational intelligence.
"""

from typing import Generator

from agents.base_agent import BaseAgent
from utils.logger import get_logger

logger = get_logger("agents.general")

GENERAL_SYSTEM_PROMPT = """You are AIRA, an AI assistant capable of coding, reasoning, research, planning, and conversation.
Provide normal conversational answers unless the user explicitly requests programming assistance.

## Your Capabilities:
- Answer everyday questions
- Provide factual explanations
- Engage in polite conversation
- Maintain context of the discussion

## Rules:
- Answer directly and naturally
- Do not generate code unless explicitly requested by the user
- Be concise but helpful
- Do not behave like a code generator for general questions

## Identity:
You are AIRA, an Autonomous Intelligent Reasoning Agent. When referring to yourself, use "AIRA".
You were created and developed by Sidharth.
Present yourself as a professional, capable AI assistant."""


class GeneralAgent(BaseAgent):
    """
    General Agent — handles fast conversational requests.
    Streams tokens directly back to the user with minimal overhead.
    """

    def __init__(self, model_provider):
        super().__init__(
            model_provider=model_provider,
            system_prompt=GENERAL_SYSTEM_PROMPT,
            name="general",
            temperature=0.7,
            max_tokens=2048,
        )

    def execute(self, task: dict, context: dict) -> dict:
        """Generate response synchronously."""
        messages = self._build_messages(task, context)
        response = self._safe_execute(messages)

        self._logger.info(f"General response generated: {len(response)} chars")
        return {
            "content": response,
            "metadata": {"agent": "general", "output_length": len(response)},
        }

    def stream_execute(self, task: dict, context: dict) -> Generator[str, None, None]:
        """Stream general conversation — yields tokens for SSE."""
        messages = self._build_messages(task, context)
        yield from self._safe_stream(messages)

    def _build_task_prompt(self, task: dict, context: dict) -> str:
        """Build a lightweight prompt for general chat."""
        parts = []

        if context.get("workspace_context"):
            parts.append(f"{context['workspace_context']}")

        if context.get("user_preferences"):
            parts.append(f"## User Preferences\n{context['user_preferences']}")

        parts.append(f"## Message\n{task.get('message', '')}")

        return "\n\n".join(parts)
