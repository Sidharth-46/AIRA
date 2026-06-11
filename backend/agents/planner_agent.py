"""
AIRA — Planner Agent
Goal understanding, task decomposition, execution planning.
"""

import json
from typing import Generator

from agents.base_agent import BaseAgent
from utils.logger import get_logger

logger = get_logger("agents.planner")

PLANNER_SYSTEM_PROMPT = """You are the Planner Agent of AIRA (Autonomous Intelligent Reasoning Agent), created by Sidharth.

Your role is to understand the user's intent and create a structured execution plan.

## Your Responsibilities:
1. Analyze the user's request
2. Classify the intent
3. Decompose complex tasks into subtasks
4. Determine which agents should handle each subtask
5. Output a clear, structured plan

## Available Agents:
- **research**: Gathers context, reads files, searches documents, analyzes repositories
- **coder**: Generates code, fixes bugs, refactors, creates projects, writes documentation
- **reviewer**: Reviews code quality, checks for bugs, suggests improvements

## Output Format:
Always respond with a JSON object:
```json
{
    "intent": "chat|generate_code|debug|explain|review|refactor|generate_project|analyze_repo|generate_docs",
    "complexity": "simple|moderate|complex",
    "plan": [
        {"step": 1, "agent": "research|coder|reviewer", "action": "description of what to do"},
        {"step": 2, "agent": "coder", "action": "description"}
    ],
    "requires_context": true/false,
    "summary": "Brief summary of what you'll do"
}
```

## Rules:
- For simple questions/chat: set intent="chat", plan=[{"step": 1, "agent": "coder", "action": "respond directly"}]
- For code generation: include research step if context is needed, then coder, then reviewer
- For debugging: always include research → coder → reviewer
- For code review: set agent="reviewer" only
- Keep plans concise — max 4 steps
- Always output valid JSON only, no other text"""


class PlannerAgent(BaseAgent):
    """
    Planner Agent — decomposes user requests into execution plans.
    Determines intent and routes to appropriate agents.
    """

    def __init__(self, model_provider):
        super().__init__(
            model_provider=model_provider,
            system_prompt=PLANNER_SYSTEM_PROMPT,
            name="planner",
            temperature=0.3,  # Low temperature for structured output
            max_tokens=1024,
        )

    def execute(self, task: dict, context: dict) -> dict:
        """Create an execution plan for the user's request."""
        messages = self._build_messages(task, context)
        response = self._safe_execute(messages)
        plan = self._parse_plan(response)

        self._logger.info(f"Plan created: intent={plan.get('intent')}, steps={len(plan.get('plan', []))}")
        return {
            "content": json.dumps(plan),
            "plan": plan,
            "metadata": {"agent": "planner", "intent": plan.get("intent")},
        }

    def stream_execute(self, task: dict, context: dict) -> Generator[str, None, None]:
        """Planner doesn't stream — returns plan synchronously."""
        result = self.execute(task, context)
        yield result.get("content", "{}")

    def _build_task_prompt(self, task: dict, context: dict) -> str:
        """Build planner-specific prompt."""
        parts = ["Analyze this request and create an execution plan:"]
        parts.append(f"\nUser Request: {task.get('message', '')}")

        if context.get("history"):
            recent = context["history"][-3:]
            history_text = "\n".join([f"- {m['role']}: {m['content'][:100]}" for m in recent])
            parts.append(f"\nRecent conversation:\n{history_text}")

        return "\n".join(parts)

    def _parse_plan(self, response: str) -> dict:
        """Parse the planner's JSON response."""
        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            plan = json.loads(json_str)

            # Validate required fields
            if "intent" not in plan:
                plan["intent"] = "chat"
            if "plan" not in plan:
                plan["plan"] = [{"step": 1, "agent": "coder", "action": "respond to user"}]
            if "complexity" not in plan:
                plan["complexity"] = "simple"

            return plan

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            self._logger.warning(f"Could not parse plan, using default: {e}")
            return {
                "intent": "chat",
                "complexity": "simple",
                "plan": [{"step": 1, "agent": "coder", "action": "respond to user"}],
                "requires_context": False,
                "summary": "Direct response",
            }
