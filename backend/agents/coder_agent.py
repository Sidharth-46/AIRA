"""
AIRA — Coder Agent
Code generation, bug fixing, refactoring, project creation.
The primary output agent — streams responses to the user.
"""

from typing import Generator

from agents.base_agent import BaseAgent
from utils.logger import get_logger

logger = get_logger("agents.coder")

CODER_SYSTEM_PROMPT = """You are the Coder Agent of AIRA (Autonomous Intelligent Reasoning Agent).
You are an expert software engineer capable of writing production-quality code.

## Your Capabilities:
- Generate clean, well-structured code in any language
- Fix bugs with clear explanations
- Refactor code following best practices
- Create complete project scaffolds
- Write comprehensive tests
- Generate API documentation
- Explain code clearly

## Code Quality Standards:
- Follow language-specific conventions and best practices
- Include meaningful comments for complex logic
- Handle errors gracefully
- Use descriptive variable and function names
- Apply SOLID principles where appropriate
- Optimize for readability and maintainability

## Output Format:
- Use markdown code blocks with language tags (```python, ```javascript, etc.)
- Include file paths as comments when generating multi-file code
- Explain your approach before showing code
- After code, explain key decisions and trade-offs

## Rules:
- Always provide complete, working code — never leave placeholders like "// TODO" or "..."
- If you're unsure about requirements, state your assumptions
- When fixing bugs, explain the root cause
- When refactoring, explain what changed and why
- Include import statements and dependencies
- For projects, include setup instructions

## Identity:
You are AIRA, an Autonomous Intelligent Reasoning Agent. When referring to yourself, use "AIRA".
You were created and developed by Sidharth.
Present yourself as a professional AI Software Engineering Agent, not a chatbot."""


class CoderAgent(BaseAgent):
    """
    Coder Agent — the primary code generation engine.
    Streams tokens in real-time for responsive UX.
    """

    def __init__(self, model_provider):
        super().__init__(
            model_provider=model_provider,
            system_prompt=CODER_SYSTEM_PROMPT,
            name="coder",
            temperature=0.7,
            max_tokens=4096,
        )

    def execute(self, task: dict, context: dict) -> dict:
        """Generate code synchronously."""
        messages = self._build_messages(task, context)
        response = self._safe_execute(messages)

        self._logger.info(f"Code generated: {len(response)} chars")
        return {
            "content": response,
            "metadata": {"agent": "coder", "output_length": len(response)},
        }

    def stream_execute(self, task: dict, context: dict) -> Generator[str, None, None]:
        """Stream code generation — yields tokens for SSE."""
        messages = self._build_messages(task, context)
        yield from self._safe_stream(messages)

    def _build_task_prompt(self, task: dict, context: dict) -> str:
        """Build coder-specific prompt with research context and plan."""
        parts = []

        # Workspace Context
        if context.get("workspace_context"):
            parts.append(f"{context['workspace_context']}")

        # Include plan from planner
        if context.get("plan"):
            plan_str = context["plan"]
            if isinstance(plan_str, dict):
                import json
                plan_str = json.dumps(plan_str, indent=2)
            parts.append(f"## Execution Plan\n{plan_str}")

        # Include research findings
        if context.get("research"):
            parts.append(f"## Research Context\n{context['research']}")

        # Include relevant file contents
        if context.get("file_contents"):
            parts.append(f"## Referenced Code\n{context['file_contents']}")

        # Include review feedback for iteration
        if context.get("review_feedback"):
            parts.append(
                "## ⚠️ Review Feedback — Address These Issues\n"
                f"{context['review_feedback']}"
            )

        # User preferences
        if context.get("user_preferences"):
            parts.append(f"## User Preferences\n{context['user_preferences']}")

        # The actual request
        parts.append(f"## Request\n{task.get('message', '')}")

        return "\n\n".join(parts)
