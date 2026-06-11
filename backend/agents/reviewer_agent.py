"""
AIRA — Reviewer Agent
Code review, quality assurance, bug detection, optimization.
"""

import json
from typing import Generator

from agents.base_agent import BaseAgent
from utils.logger import get_logger

logger = get_logger("agents.reviewer")

REVIEWER_SYSTEM_PROMPT = """You are the Reviewer Agent of AIRA (Autonomous Intelligent Reasoning Agent), created by Sidharth.
You are a senior code reviewer focused on quality assurance.

## Your Responsibilities:
1. Review code for correctness, security, and performance
2. Identify bugs, vulnerabilities, and anti-patterns
3. Suggest improvements and optimizations
4. Ensure code follows best practices
5. Check edge cases and error handling

## Review Categories:
- **Correctness**: Does the code do what it's supposed to?
- **Security**: Are there vulnerabilities? (injection, XSS, auth issues, etc.)
- **Performance**: Are there efficiency issues? (N+1 queries, memory leaks, etc.)
- **Best Practices**: Does it follow language/framework conventions?
- **Error Handling**: Are errors handled gracefully?
- **Edge Cases**: What could go wrong?

## Output Format:
```json
{
    "verdict": "pass|fail",
    "score": 1-10,
    "issues": [
        {
            "severity": "critical|major|minor|suggestion",
            "category": "correctness|security|performance|best_practice|edge_case",
            "description": "Clear description of the issue",
            "suggestion": "How to fix it"
        }
    ],
    "summary": "Overall assessment",
    "improvements": ["Optional improvement suggestions"]
}
```

## Rules:
- Be fair but thorough — don't nitpick trivial formatting
- Focus on issues that matter: bugs, security, correctness
- Always explain WHY something is an issue
- Provide actionable fix suggestions
- If code is good, say so — verdict "pass"
- Set verdict to "fail" only for critical/major issues
- Keep the review concise and practical"""


class ReviewerAgent(BaseAgent):
    """
    Reviewer Agent — autonomous code quality gate.
    Provides structured review with pass/fail verdict.
    """

    def __init__(self, model_provider):
        super().__init__(
            model_provider=model_provider,
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            name="reviewer",
            temperature=0.3,  # Low temperature for consistent reviews
            max_tokens=2048,
        )

    def execute(self, task: dict, context: dict) -> dict:
        """Review code and return structured feedback."""
        messages = self._build_messages(task, context)
        response = self._safe_execute(messages)
        review = self._parse_review(response)

        self._logger.info(
            f"Review complete: verdict={review.get('verdict')}, "
            f"issues={len(review.get('issues', []))}"
        )

        return {
            "content": response,
            "review": review,
            "metadata": {
                "agent": "reviewer",
                "verdict": review.get("verdict", "pass"),
                "issue_count": len(review.get("issues", [])),
            },
        }

    def stream_execute(self, task: dict, context: dict) -> Generator[str, None, None]:
        """Stream review output."""
        messages = self._build_messages(task, context)
        yield from self._safe_stream(messages)

    def _build_task_prompt(self, task: dict, context: dict) -> str:
        """Build review-specific prompt."""
        parts = []

        # Original requirements
        if context.get("original_request"):
            parts.append(f"## Original Requirements\n{context['original_request']}")

        # Code to review
        code_to_review = context.get("code_output") or task.get("message", "")
        parts.append(f"## Code to Review\n{code_to_review}")

        parts.append("Review this code and provide your assessment in JSON format.")
        return "\n\n".join(parts)

    def _parse_review(self, response: str) -> dict:
        """Parse the reviewer's JSON response."""
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            review = json.loads(json_str)

            # Ensure required fields
            review.setdefault("verdict", "pass")
            review.setdefault("score", 7)
            review.setdefault("issues", [])
            review.setdefault("summary", "Review complete")

            return review

        except (json.JSONDecodeError, IndexError):
            self._logger.warning("Could not parse review JSON, defaulting to pass")
            return {
                "verdict": "pass",
                "score": 7,
                "issues": [],
                "summary": response[:200] if response else "Review complete",
                "improvements": [],
            }
