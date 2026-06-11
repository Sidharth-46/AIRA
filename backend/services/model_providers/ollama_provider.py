"""
AIRA — Ollama Model Provider
Concrete implementation of BaseModelProvider for Ollama.
Handles streaming, embeddings, hardware detection, and model management.
"""

import ollama as ollama_sdk
from typing import Generator

from services.model_providers.base_provider import BaseModelProvider
from utils.logger import get_logger

logger = get_logger("providers.ollama")


class OllamaProvider(BaseModelProvider):
    """
    Ollama model provider — runs models locally via Ollama server.
    Supports: qwen3-coder, deepseek-coder-v2, and any Ollama model.
    """

    # Default context windows per model family
    CONTEXT_WINDOWS = {
        "qwen3-coder": 32768,
        "deepseek-coder-v2": 16384,
        "codellama": 16384,
        "llama3": 8192,
        "mistral": 32768,
    }

    def __init__(self, model_name: str, base_url: str = "http://localhost:11434",
                 embedding_model: str = "nomic-embed-text", timeout: int = 60):
        self.model_name = model_name
        self.base_url = base_url
        self.embedding_model = embedding_model
        self.timeout = timeout

        # Configure Ollama client
        self._client = ollama_sdk.Client(host=base_url, timeout=timeout)
        logger.info(f"OllamaProvider initialized: model={model_name}, url={base_url}")

    def chat(self, messages: list, temperature: float = 0.7,
             max_tokens: int = 4096, system_prompt: str = None) -> str:
        """Synchronous chat completion via Ollama."""
        formatted = self._format_messages(messages, system_prompt)

        try:
            response = self._client.chat(
                model=self.model_name,
                messages=formatted,
                keep_alive="1h",
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )
            content = response.get("message", {}).get("content", "")
            logger.debug(f"Chat completion: {len(content)} chars")
            return content

        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"Ollama chat error: {error_msg}")
            raise RuntimeError(f"Ollama chat failed: {error_msg}") from exc

    def stream_chat(self, messages: list, temperature: float = 0.7,
                    max_tokens: int = 4096, system_prompt: str = None) -> Generator[str, None, None]:
        """Streaming chat — yields tokens one at a time."""
        formatted = self._format_messages(messages, system_prompt)

        try:
            stream = self._client.chat(
                model=self.model_name,
                messages=formatted,
                stream=True,
                keep_alive="1h",
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )

            for chunk in stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token

        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"Ollama stream error: {error_msg}")
            yield f"\n\n[Error: Ollama streaming failed — {error_msg}]"

    def generate_embeddings(self, texts: list) -> list:
        """Generate embeddings via Ollama's embedding model."""
        embeddings = []
        for text in texts:
            try:
                response = self._client.embeddings(
                    model=self.embedding_model,
                    prompt=text,
                )
                embeddings.append(response.get("embedding", []))
            except Exception as e:
                logger.error(f"Embedding error: {e}")
                embeddings.append([])

        return embeddings

    def get_model_info(self) -> dict:
        """Get information about the current model."""
        try:
            info = self._client.show(self.model_name)
            return {
                "name": self.model_name,
                "size": info.get("size", 0),
                "format": info.get("details", {}).get("format", "unknown"),
                "family": info.get("details", {}).get("family", "unknown"),
                "parameter_size": info.get("details", {}).get("parameter_size", "unknown"),
                "quantization": info.get("details", {}).get("quantization_level", "unknown"),
                "context_window": self.get_context_window(),
            }
        except Exception as e:
            logger.warning(f"Could not get model info: {e}")
            return {
                "name": self.model_name,
                "context_window": self.get_context_window(),
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            self._client.list()
            return True
        except Exception:
            return False

    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.model_name

    def get_context_window(self) -> int:
        """Get context window size."""
        for key, window in self.CONTEXT_WINDOWS.items():
            if key in self.model_name.lower():
                return window
        return 8192  # Conservative default

    def list_available_models(self) -> list:
        """List all models available on the Ollama instance."""
        try:
            response = self._client.list()
            
            models_list = getattr(response, 'models', None)
            if models_list is None and isinstance(response, dict):
                models_list = response.get("models", [])
                
            models = []
            for m in (models_list or []):
                # Handle dictionary format
                if isinstance(m, dict):
                    models.append({
                        "name": m.get("name", m.get("model", "")),
                        "size": m.get("size", 0),
                        "modified_at": str(m.get("modified_at", "")),
                        "details": m.get("details", {}),
                    })
                # Handle object format
                else:
                    models.append({
                        "name": getattr(m, 'model', getattr(m, 'name', "")),
                        "size": getattr(m, 'size', 0),
                        "modified_at": str(getattr(m, 'modified_at', "")),
                        "details": getattr(m, 'details', {}),
                    })
            return models
        except Exception as exc:
            logger.error(f"Error listing models: {str(exc)}")
            return []

    def pull_model(self, model_name: str) -> bool:
        """Pull/download a model from Ollama registry."""
        try:
            logger.info(f"Pulling model: {model_name}")
            self._client.pull(model_name)
            logger.info(f"Model pulled: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False

    def _format_messages(self, messages: list, system_prompt: str = None) -> list:
        """Format messages for Ollama API, prepending system prompt if given."""
        from utils.identity import GLOBAL_SYSTEM_PROMPT
        
        formatted = []

        # Always inject global identity prompt first
        final_system_prompt = GLOBAL_SYSTEM_PROMPT
        
        if system_prompt:
            final_system_prompt += "\n\n" + system_prompt

        formatted.append({"role": "system", "content": final_system_prompt})

        for msg in messages:
            formatted.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        return formatted
