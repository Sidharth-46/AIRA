"""
AIRA — Token Manager
Token budget management for multi-agent pipelines.
"""

from utils.logger import get_logger

logger = get_logger("orchestrator.tokens")


class TokenManager:
    """
    Manages token budgets across the multi-agent pipeline.
    Ensures agents don't exceed context windows.
    """

    # Approximate chars per token (conservative estimate)
    CHARS_PER_TOKEN = 4

    # Budget allocation (percentage of context window)
    BUDGET_ALLOCATION = {
        "system_prompt": 0.15,
        "context": 0.40,
        "conversation": 0.25,
        "generation": 0.20,
    }

    def __init__(self, context_window=8192):
        self.context_window = context_window
        self.usage = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "agent_usage": {},
        }

    def get_budget(self, component="context"):
        """Get token budget for a component."""
        allocation = self.BUDGET_ALLOCATION.get(component, 0.25)
        return int(self.context_window * allocation)

    def get_max_chars(self, component="context"):
        """Get max characters for a component."""
        return self.get_budget(component) * self.CHARS_PER_TOKEN

    def estimate_tokens(self, text):
        """Estimate token count for text."""
        if isinstance(text, str):
            return len(text) // self.CHARS_PER_TOKEN
        elif isinstance(text, list):
            return sum(
                len(m.get("content", "")) // self.CHARS_PER_TOKEN
                for m in text
            )
        return 0

    def track_usage(self, agent_name, input_tokens, output_tokens):
        """Track token usage per agent."""
        self.usage["total_input_tokens"] += input_tokens
        self.usage["total_output_tokens"] += output_tokens

        if agent_name not in self.usage["agent_usage"]:
            self.usage["agent_usage"][agent_name] = {"input": 0, "output": 0}

        self.usage["agent_usage"][agent_name]["input"] += input_tokens
        self.usage["agent_usage"][agent_name]["output"] += output_tokens

    def get_usage(self):
        """Get current usage statistics."""
        return self.usage

    def within_budget(self, text, component="context"):
        """Check if text fits within component budget."""
        estimated = self.estimate_tokens(text)
        budget = self.get_budget(component)
        return estimated <= budget

    def truncate_to_budget(self, text, component="context"):
        """Truncate text to fit within component budget."""
        max_chars = self.get_max_chars(component)
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n[...truncated to fit context window]"
