"""
AIRA — Ollama Service
High-level service wrapping the ModelRegistry.
This is what the service layer imports — never providers directly.
"""

from services.model_providers.model_registry import get_registry, get_provider
from utils.hardware_detector import detect_hardware
from utils.logger import get_logger

logger = get_logger("services.ollama")


class OllamaService:
    """
    High-level Ollama integration service.
    Routes → Services → OllamaService → ModelRegistry → OllamaProvider
    """

    @staticmethod
    def chat(messages, temperature=0.7, max_tokens=4096, system_prompt=None, model=None):
        """Synchronous chat completion."""
        provider = get_provider(model)
        return provider.chat(messages, temperature, max_tokens, system_prompt)

    @staticmethod
    def stream_chat(messages, temperature=0.7, max_tokens=4096, system_prompt=None, model=None):
        """Streaming chat completion — yields tokens."""
        provider = get_provider(model)
        return provider.stream_chat(messages, temperature, max_tokens, system_prompt)



    @staticmethod
    def list_models():
        """List available models."""
        registry = get_registry()
        return registry.list_models()

    @staticmethod
    def get_active_model():
        """Get the active model name and info."""
        registry = get_registry()
        model_name = registry.get_active_model()
        provider = get_provider()
        try:
            info = provider.get_model_info()
        except Exception:
            info = {"name": model_name}
        return {"name": model_name, "info": info}

    @staticmethod
    def switch_model(model_name):
        """Switch the active model."""
        registry = get_registry()
        return registry.switch_model(model_name)

    @staticmethod
    def get_status():
        """Get Ollama status + hardware info."""
        provider = get_provider()
        connected = provider.health_check()
        hardware = detect_hardware()

        result = {
            "ollama": {
                "connected": connected,
                "model": provider.get_model_name() if connected else None,
                "url": provider.base_url if hasattr(provider, 'base_url') else None,
            },
            "hardware": hardware,
        }

        if connected:
            try:
                result["ollama"]["info"] = provider.get_model_info()
            except Exception:
                pass

        return result

    @staticmethod
    def pull_model(model_name):
        """Pull a model from Ollama registry."""
        provider = get_provider()
        return provider.pull_model(model_name)

    @staticmethod
    def get_diagnostics():
        """Get model resolution diagnostics."""
        registry = get_registry()
        return registry.get_diagnostics()
