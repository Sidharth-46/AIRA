"""
AIRA — Model Registry
Singleton that manages provider instances.
Supports runtime model switching without restart.
"""

import os
from services.model_providers.base_provider import BaseModelProvider
from services.model_providers.ollama_provider import OllamaProvider
from utils.logger import get_logger

logger = get_logger("model_registry")


import datetime
import ollama

class ModelResolutionError(Exception):
    """Raised when no suitable Ollama model can be resolved."""
    def __init__(self, message, installed_models=None):
        super().__init__(message)
        self.installed_models = installed_models or []

class ModelRegistry:
    """
    Central registry for model providers.
    All AI interactions get their provider from here.
    """

    _instance = None
    _active_provider: BaseModelProvider = None
    _configured_model: str = None
    _resolved_model: str = None
    _providers: dict = {}
    _installed_models: list = []
    _last_successful_generation: str = None

    _last_models_fetch: float = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
            cls._instance._last_models_fetch = 0
        return cls._instance

    def initialize(self, default_model: str = None, base_url: str = None,
                   embedding_model: str = None, timeout: int = None):
        """Initialize the registry with defaults from config."""
        if self._initialized:
            return

        self._base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._embedding_model = embedding_model or os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        self._timeout = timeout or int(os.getenv("OLLAMA_REQUEST_TIMEOUT", 60))
        self._configured_model = default_model or os.getenv("OLLAMA_DEFAULT_MODEL", "qwen3-coder")

        # Resolve the actual model dynamically based on priority
        try:
            self._resolved_model = self._resolve_model_name(self._configured_model)
        except ModelResolutionError as e:
            logger.error(f"Startup Model Resolution Failed: {e}")
            self._resolved_model = self._configured_model  # Keep it so we can show diagnostics

        # Create default provider
        self._get_or_create_provider(self._resolved_model)
        self._active_provider = self._providers.get(self._resolved_model)

        self._initialized = True
        logger.info(f"ModelRegistry initialized: configured={self._configured_model}, resolved={self._resolved_model}")

    def _resolve_model_name(self, configured_name: str) -> str:
        """
        Dynamically resolve the best matching model based on priority:
        1. Exact Match
        2. Prefix Match
        3. Same Family Match
        4. Coding Model Match
        5. Fail with User Selection Required
        """
        import time
        if not self._installed_models or (time.time() - self._last_models_fetch > 300):
            client = ollama.Client(host=self._base_url, timeout=self._timeout)
            try:
                response = client.list()
                models_list = getattr(response, 'models', None)
                if models_list is None and isinstance(response, dict):
                    models_list = response.get("models", [])
                
                names = []
                for m in (models_list or []):
                    name = getattr(m, 'model', None) or getattr(m, 'name', None)
                    if not name and isinstance(m, dict):
                        name = m.get('model') or m.get('name')
                    if name:
                        names.append(name)
                self._installed_models = names
                self._last_models_fetch = time.time()
            except Exception as exc:
                logger.warning(f"Could not connect to Ollama to list models: {exc}")
                return configured_name
            
        installed = self._installed_models
        if not installed:
            raise ModelResolutionError("No models installed in Ollama.", installed_models=[])

        # 1. Exact Match
        if configured_name in installed:
            return configured_name
            
        # 2. Prefix Match (e.g. qwen3-coder -> qwen3-coder:7b)
        for m in installed:
            if m.startswith(configured_name):
                logger.info(f"Model Resolution: Prefix match found for {configured_name} -> {m}")
                return m
                
        # 3. Same Family Match (e.g. qwen, llama, mistral)
        family = configured_name.split("-")[0].lower() if "-" in configured_name else configured_name.lower()
        for m in installed:
            if family in m.lower():
                logger.info(f"Model Resolution: Family match found for {configured_name} ({family}) -> {m}")
                return m
                
        # 4. Coding Model Match
        is_coding = "code" in configured_name.lower()
        if is_coding:
            for m in installed:
                if "code" in m.lower():
                    logger.info(f"Model Resolution: Coding model match found for {configured_name} -> {m}")
                    return m

        # 5. Fail gracefully
        raise ModelResolutionError(
            f"Could not resolve a suitable model for '{configured_name}'.",
            installed_models=installed
        )

    def get_provider(self, model_name: str = None) -> BaseModelProvider:
        """
        Get a model provider instance.
        If model_name is None, returns the active provider.
        """
        if not self._initialized:
            self.initialize()

        if model_name is None:
            return self._active_provider

        try:
            resolved_name = self._resolve_model_name(model_name)
            return self._get_or_create_provider(resolved_name)
        except ModelResolutionError as e:
            logger.error(str(e))
            # Return a failing provider or let it raise?
            # The prompt says: "Never fail chat requests because of a missing model alias."
            # Wait, prompt says: "Do NOT automatically select arbitrary unrelated models. If no suitable model exists: Return clear diagnostic information, ask user to choose."
            # If we raise here, it will bubble up. We will let it raise.
            raise

    def switch_model(self, model_name: str) -> dict:
        """Switch the active model at runtime."""
        resolved_name = self._resolve_model_name(model_name)
        provider = self._get_or_create_provider(resolved_name)

        if not provider.health_check():
            raise RuntimeError(f"Cannot reach Ollama for model: {resolved_name}")

        self._configured_model = model_name
        self._resolved_model = resolved_name
        self._active_provider = provider

        logger.info(f"Active model switched to: {resolved_name}")
        return {
            "model": resolved_name,
            "info": provider.get_model_info(),
        }

    def get_active_model(self) -> str:
        """Get the name of the currently active model."""
        return self._resolved_model or self._configured_model

    def list_models(self) -> list:
        """List all models available on the Ollama instance."""
        if not self._initialized:
            self.initialize()
        return self._active_provider.list_available_models() if self._active_provider else []

    def _get_or_create_provider(self, model_name: str) -> BaseModelProvider:
        """Get existing provider or create a new one."""
        if model_name not in self._providers:
            provider = OllamaProvider(
                model_name=model_name,
                base_url=self._base_url,
                embedding_model=self._embedding_model,
                timeout=self._timeout,
            )
            self._providers[model_name] = provider
            logger.info(f"Provider created for model: {model_name}")

        return self._providers[model_name]
        
    def mark_successful_generation(self):
        """Track the last successful generation timestamp."""
        self._last_successful_generation = datetime.datetime.utcnow().isoformat() + "Z"

    def get_diagnostics(self) -> dict:
        """Return full diagnostics state for model resolution."""
        running = False
        try:
            client = ollama.Client(host=self._base_url, timeout=self._timeout)
            response = client.list()
            
            models_list = getattr(response, 'models', None)
            if models_list is None and isinstance(response, dict):
                models_list = response.get("models", [])
                
            names = []
            for m in (models_list or []):
                name = getattr(m, 'model', None) or getattr(m, 'name', None)
                if not name and isinstance(m, dict):
                    name = m.get('model') or m.get('name')
                if name:
                    names.append(name)
                    
            self._installed_models = names
            running = True
        except Exception:
            pass

        # Check if resolved model actually matches anything in installed
        is_healthy = running and (self._resolved_model in self._installed_models)

        return {
            "ollama_running": running,
            "configured_model": self._configured_model,
            "resolved_model": self._resolved_model,
            "installed_models": self._installed_models,
            "last_successful_generation": self._last_successful_generation,
            "status": "healthy" if is_healthy else "degraded"
        }

# Module-level singleton access
_registry = ModelRegistry()

def get_registry() -> ModelRegistry:
    return _registry

def get_provider(model_name: str = None) -> BaseModelProvider:
    return _registry.get_provider(model_name)

