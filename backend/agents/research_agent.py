"""
AIRA — Research Agent
Context retrieval, repository understanding, knowledge gathering.
"""

from typing import Generator

from agents.base_agent import BaseAgent
from utils.logger import get_logger

logger = get_logger("agents.research")

RESEARCH_SYSTEM_PROMPT = """You are the Research Agent of AIRA (Autonomous Intelligent Reasoning Agent).

Your role is to gather, analyze, and summarize relevant context for other agents.

## Your Responsibilities:
1. Analyze provided files, code, and documents
2. Understand project structure and architecture
3. Identify relevant patterns, dependencies, and relationships
4. Summarize findings concisely for the Coder and Reviewer agents
5. Provide citations and references to source files

## Output Format:
Structure your research as:

### Key Findings
- Bullet points of important discoveries

### Relevant Code
- Code snippets with file references

### Architecture Notes
- How the codebase is structured
- Design patterns used
- Dependencies and relationships

### Recommendations
- Suggestions for the Coder agent

## Rules:
- Be thorough but concise
- Always cite source files and line numbers when referencing code
- Focus on information relevant to the current task
- Highlight potential issues or concerns
- If no relevant context is found, state that clearly"""


class ResearchAgent(BaseAgent):
    """
    Research Agent — gathers and analyzes context for downstream agents.
    Queries RAG, reads files, analyzes project structure.
    """

    def __init__(self, model_provider):
        super().__init__(
            model_provider=model_provider,
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            name="research",
            temperature=0.3,
            max_tokens=2048,
        )

    def execute(self, task: dict, context: dict) -> dict:
        """Gather and analyze context."""
        messages = self._build_messages(task, context)
        response = self._safe_execute(messages)

        self._logger.info(f"Research complete: {len(response)} chars")
        return {
            "content": response,
            "metadata": {"agent": "research", "context_length": len(response)},
        }

    def stream_execute(self, task: dict, context: dict) -> Generator[str, None, None]:
        """Stream research results."""
        messages = self._build_messages(task, context)
        yield from self._safe_stream(messages)

    def _build_task_prompt(self, task: dict, context: dict) -> str:
        """Build research-specific prompt with available context."""
        parts = []

        # Project information
        if context.get("project_info"):
            parts.append(f"## Project Context\n{context['project_info']}")

        # File contents
        if context.get("file_contents"):
            parts.append(f"## Available Files\n{context['file_contents']}")

        # RAG results
        if context.get("rag_results"):
            parts.append(f"## Document Search Results\n{context['rag_results']}")

        # Repository structure
        if context.get("repo_structure"):
            parts.append(f"## Repository Structure\n{context['repo_structure']}")

        # The actual task
        action = task.get("action", "Analyze the provided context")
        message = task.get("message", "")
        parts.append(f"## Research Task\n{action}\n\nOriginal user request: {message}")

        return "\n\n".join(parts) if parts else f"Research the following: {message}"
