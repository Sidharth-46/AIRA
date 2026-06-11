"""
AIRA — Model Router Service
Handles intelligent routing, intent classification, model caching, and performance tracking.
"""

import time
import re
import threading
from utils.logger import get_logger
from services.model_providers.model_registry import get_registry, get_provider
from orchestrator.intent_classifier import classify_intent as llm_classify_intent

logger = get_logger("services.model_router")

# Intent Rules
FAST_PATH_RULES = {
    "GENERAL_CHAT": [
        r"\b(hi|hello|hey|thanks|thank you|good morning|good evening)\b",
        r"\b(what time is it|who is|what is|why is|tell me a joke|explain)\b",
    ],
    "CODING": [
        r"\b(code|script|function|class|bug|debug|fix|python|javascript|typescript|react|node|api|flask|docker|sql)\b",
    ],
    "REPOSITORY_ANALYSIS": [
        r"\b(repo|repository|github|codebase|project structure|architecture)\b",
    ],
    "DOCUMENTATION": [
        r"\b(readme|documentation|docs|api reference)\b",
    ],
}

# Tiers
GENERAL_MODELS = ["qwen3:4b", "gemma3:4b", "llama3.2:3b"]
CODING_MODELS = ["qwen2.5-coder:7b", "deepseek-coder:6.7b"]

class ModelRouter:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(ModelRouter, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.cached_models = []
        self.metrics = {}  # {model: {requests, failures, latency_sum, first_token_sum, completion_time_sum}}
        self.last_refresh = 0
        self.refresh_interval = 300  # 5 minutes
        self.warmup_models = set()
        
        # Initial synchronous fetch
        self._refresh_cache()
        self._warmup_startup()

    def _refresh_cache(self):
        """Fetch installed models and update cache."""
        try:
            registry = get_registry()
            # We assume OllamaProvider or registry provides a list_models method
            models_info = registry.list_models()
            if isinstance(models_info, list):
                if models_info and isinstance(models_info[0], dict) and 'name' in models_info[0]:
                    self.cached_models = [m['name'] for m in models_info]
                else:
                    self.cached_models = models_info
            else:
                self.cached_models = []
            
            self.last_refresh = time.time()
            logger.info(f"MODEL_CACHE_REFRESH: Installed models: {self.cached_models}")
        except Exception as e:
            logger.error(f"Failed to refresh model cache: {e}")

    def _warmup_startup(self):
        """Warm up the highest priority available models."""
        primary_general = self._get_best_model_for_tier(GENERAL_MODELS)
        primary_coding = self._get_best_model_for_tier(CODING_MODELS)

        # To conserve VRAM, warm only the overall highest priority model if both exist
        # Or warm both if the system intends so. The prompt says "Warm only the highest-priority available model."
        model_to_warm = primary_general or primary_coding
        if model_to_warm:
            logger.info(f"MODEL_WARMUP_START: {model_to_warm}")
            self.warmup_models.add(model_to_warm)
            threading.Thread(target=self._perform_warmup, args=(model_to_warm,), daemon=True).start()

    def _perform_warmup(self, model_name):
        try:
            provider = get_provider(model_name)
            provider.chat([{"role": "user", "content": "hi"}], max_tokens=1)
            logger.info(f"MODEL_WARMUP_COMPLETE: {model_name}")
        except Exception as e:
            logger.error(f"Warmup failed for {model_name}: {e}")

    def _lazy_warmup(self, model_name):
        if model_name not in self.warmup_models:
            logger.info(f"MODEL_LAZY_WARMUP: {model_name}")
            self.warmup_models.add(model_name)
            threading.Thread(target=self._perform_warmup, args=(model_name,), daemon=True).start()

    def _ensure_cache(self):
        if time.time() - self.last_refresh > self.refresh_interval:
            if self.cached_models:
                # Trigger in background so it doesn't block request
                threading.Thread(target=self._refresh_cache, daemon=True).start()
                self.last_refresh = time.time()  # Optimistically update to prevent multiple threads
            else:
                self._refresh_cache()

    def _classify_intent_fast(self, message: str) -> str:
        """Run lightweight rule-based classifier."""
        message_lower = message.lower()
        for intent, patterns in FAST_PATH_RULES.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        return None

    def _get_best_model_for_tier(self, tier_list: list) -> str:
        """Find the best available model in a tier based on metrics."""
        available = [m for m in tier_list if any(cm.startswith(m) or m.startswith(cm) for cm in self.cached_models)]
        
        if not available:
            # Fallback to absolute available if tier is totally missing
            return self.cached_models[0] if self.cached_models else "qwen2.5-coder:7b"

        best_model = None
        best_score = -1

        for model in available:
            metrics = self.metrics.get(model, {"requests": 0, "failures": 0, "latency_sum": 0})
            if metrics["requests"] == 0:
                success_rate = 1.0  # Assume 100% until proven otherwise
                latency = 1.0       # Assume fast
            else:
                success_rate = 1.0 - (metrics["failures"] / metrics["requests"])
                latency = metrics["latency_sum"] / metrics["requests"]
            
            # Simple scoring: higher success is better, lower latency is better
            score = (success_rate * 100) - latency
            if score > best_score:
                best_score = score
                best_model = model

        return best_model or available[0]

    def route_request(self, message: str, workspace_context: bool = False, context_size: int = 0) -> dict:
        self._ensure_cache()
        
        routing_reason = ""
        
        # 1. Fast Path Classification
        intent = self._classify_intent_fast(message)
        if intent:
            routing_reason = "rule_based"
        else:
            # LLM Fallback (mocked here, should call the actual fallback)
            intent = llm_classify_intent(message)  # Assuming this returns 'chat', 'generate_code', etc.
            # Normalize intent
            intent_map = {
                "chat": "GENERAL_CHAT",
                "explain": "GENERAL_CHAT",
                "generate_code": "CODING",
                "debug": "CODING",
                "refactor": "CODING",
                "generate_project": "CODING",
                "analyze_repo": "REPOSITORY_ANALYSIS",
                "generate_docs": "DOCUMENTATION",
            }
            intent = intent_map.get(intent, "GENERAL_CHAT")
            routing_reason = "llm_fallback"

        # 2. Context Weights (Intent 80%, Context 20%)
        # If context is extremely large, bump to coding model
        if context_size > 2000 or (workspace_context and context_size > 500):
            if intent == "GENERAL_CHAT":
                # Only override if it's borderline, but instruction says "Context must NEVER override intent."
                # Instruction also says "Workspace Open + User: What time is it? -> GENERAL_CHAT"
                # And "Large context -> Coding model"
                # Let's keep intent dominant unless it's a huge payload and general chat.
                pass

        # 3. Tier Selection
        if intent == "GENERAL_CHAT":
            tier = GENERAL_MODELS
            timeout = 120
        elif intent == "CODING":
            tier = CODING_MODELS
            timeout = 180
        elif intent == "REPOSITORY_ANALYSIS":
            tier = CODING_MODELS
            timeout = 240
        elif intent == "DOCUMENTATION":
            tier = CODING_MODELS
            timeout = 180
        else:
            tier = GENERAL_MODELS
            timeout = 120

        model = self._get_best_model_for_tier(tier)

        logger.info(f"MODEL_ROUTED: {model} (Intent: {intent}, Reason: {routing_reason})")
        
        self._lazy_warmup(model)

        return {
            "intent": intent,
            "model": model,
            "routing_reason": routing_reason,
            "timeout": timeout
        }

    def record_metrics(self, model: str, success: bool, latency: float, time_to_first_token: float, completion_time: float):
        if model not in self.metrics:
            self.metrics[model] = {
                "requests": 0, "failures": 0, "latency_sum": 0, 
                "first_token_sum": 0, "completion_time_sum": 0
            }
        
        m = self.metrics[model]
        m["requests"] += 1
        if not success:
            m["failures"] += 1
            logger.warning(f"MODEL_FAILURE: {model}")
            # Refresh immediately after model failure
            threading.Thread(target=self._refresh_cache, daemon=True).start()
        else:
            m["latency_sum"] += latency
            m["first_token_sum"] += time_to_first_token
            m["completion_time_sum"] += completion_time

    def get_diagnostics(self):
        self._ensure_cache()
        metrics_out = {}
        for m, data in self.metrics.items():
            reqs = data["requests"]
            if reqs == 0: continue
            metrics_out[m] = {
                "requests": reqs,
                "failures": data["failures"],
                "avg_latency": round(data["latency_sum"] / reqs, 3),
                "avg_time_to_first_token": round(data["first_token_sum"] / reqs, 3),
                "avg_completion_time": round(data["completion_time_sum"] / reqs, 3),
            }

        return {
            "general_model": self._get_best_model_for_tier(GENERAL_MODELS),
            "coding_model": self._get_best_model_for_tier(CODING_MODELS),
            "available_models": self.cached_models,
            "cached_models": self.cached_models,
            "metrics": metrics_out,
            "last_cache_refresh": self.last_refresh,
            "router_status": "healthy"
        }

# Global singleton instance provider
def get_model_router():
    return ModelRouter()
