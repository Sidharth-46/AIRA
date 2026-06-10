"""
AIRA — Intent Classifier
Classifies user messages into categories for agent routing.
Uses keyword matching + optional LLM for ambiguous cases.
"""

import re
from utils.logger import get_logger

logger = get_logger("orchestrator.intent")

# Intent categories and their keyword patterns
INTENT_PATTERNS = {
    "generate_code": [
        r"\b(write|create|generate|build|make|implement|code|develop)\b.*\b(function|class|api|app|component|module|script|program|code|endpoint|route|service)\b",
        r"\b(can you|please|help me)\b.*\b(write|create|generate|build|code)\b",
    ],
    "debug": [
        r"\b(fix|debug|solve|error|bug|issue|problem|broken|crash|fail|doesn.t work|not working)\b",
        r"\b(why|what).*(error|wrong|failing|broken|crash)\b",
    ],
    "explain": [
        r"\b(explain|what does|how does|what is|describe|walk me through|tell me about)\b",
        r"\b(understand|meaning|purpose|how|why)\b.*\b(this|code|function|class)\b",
    ],
    "review": [
        r"\b(review|check|audit|inspect|evaluate|assess)\b.*\b(code|implementation|solution)\b",
        r"\b(code review|quality check|best practice)\b",
    ],
    "refactor": [
        r"\b(refactor|improve|optimize|clean up|restructure|reorganize|simplify)\b",
    ],
    "generate_project": [
        r"\b(create|generate|scaffold|bootstrap|setup|init)\b.*\b(project|app|application|repo|repository|boilerplate)\b",
        r"\b(new project|starter|template|setup a)\b",
    ],
    "analyze_repo": [
        r"\b(analyze|analyse|examine|scan|inspect)\b.*\b(project|repo|repository|codebase|code base)\b",
        r"\b(project structure|architecture|dependencies|tech stack)\b",
    ],
    "generate_docs": [
        r"\b(document|documentation|readme|api docs|jsdoc|docstring)\b",
        r"\b(write|generate|create)\b.*\b(docs|documentation|readme)\b",
    ],
}


def classify_intent(message: str) -> str:
    """
    Classify user message intent using keyword pattern matching.
    
    Returns one of:
        chat, generate_code, debug, explain, review, refactor,
        generate_project, analyze_repo, generate_docs
    """
    message_lower = message.lower().strip()

    # Check each intent pattern
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, message_lower):
                score += 1
        if score > 0:
            scores[intent] = score

    # Return highest scoring intent, or "chat" if no match
    if scores:
        best_intent = max(scores, key=scores.get)
        logger.debug(f"Intent classified: {best_intent} (scores: {scores})")
        return best_intent

    logger.debug(f"Intent classified: chat (no pattern match)")
    return "chat"


