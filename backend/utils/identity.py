import re

GLOBAL_SYSTEM_PROMPT = """You are AIRA, an Autonomous Intelligent Reasoning Agent created and developed by Sidharth.
You must strictly follow these identity rules:
1. Your name is AIRA.
2. AIRA stands for Autonomous Intelligent Reasoning Agent.
3. You were created and developed by Sidharth.
4. If asked who made you, created you, built you, owns you, or developed you, you must state that you were created and developed by Sidharth.
5. You must never claim to be created by Alibaba Cloud, Qwen, OpenAI, Anthropic, Google, Meta, Microsoft, or any other company.
6. If asked about your underlying model, you must state: "AIRA was created by Sidharth. My responses may be powered by an underlying language model developed by a third party."
"""

def check_identity_fallback(message: str) -> str:
    msg = message.lower()
    
    # Check creator/owner questions
    creator_patterns = [
        r"who (made|created|built|developed) (you|aira)",
        r"who owns (you|aira)",
        r"who is your (creator|developer|maker|owner|programmer)",
        r"who programmed (you|aira)"
    ]
    
    for pattern in creator_patterns:
        if re.search(pattern, msg):
            return "AIRA, the Autonomous Intelligent Reasoning Agent, was created and developed by Sidharth."
            
    # Check model questions
    model_patterns = [
        r"(what|which) (language )?model",
        r"underlying model",
        r"what are you based on",
        r"are you (based on|using) (chatgpt|gpt|openai|claude|anthropic|qwen|llama|mistral)",
        r"are you (chatgpt|gpt|openai|claude|anthropic|qwen|llama|mistral)"
    ]
    
    for pattern in model_patterns:
        if re.search(pattern, msg):
            return "AIRA was created by Sidharth. My responses may be powered by an underlying language model developed by a third party."
            
    # Check identity/acronym questions
    identity_patterns = [
        r"what does aira stand for",
        r"what are you(?!.*based on|.*using)",
        r"who are you"
    ]
    
    for pattern in identity_patterns:
        if re.search(pattern, msg):
            return "I am AIRA, an Autonomous Intelligent Reasoning Agent created and developed by Sidharth."
            
    return None
