"""
AIRA — Base Model Provider
Abstract interface that ALL AI interactions go through.
No hardcoded model logic anywhere in the application.
"""

from abc import ABC, abstractmethod
from typing import Generator


class BaseModelProvider(ABC):
    """
    Abstract base class for all model providers.
    Every AI interaction in AIRA flows through this interface.
    
    Supported implementations:
        - OllamaProvider (default, local)
        - Future providers can extend this
    """

    @abstractmethod
    def chat(self, messages: list, temperature: float = 0.7,
             max_tokens: int = 4096, system_prompt: str = None) -> str:
        """
        Synchronous chat completion.
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt override
            
        Returns:
            Generated text string
        """
        pass

    @abstractmethod
    def stream_chat(self, messages: list, temperature: float = 0.7,
                    max_tokens: int = 4096, system_prompt: str = None) -> Generator[str, None, None]:
        """
        Streaming chat completion — yields tokens one at a time.
        
        Args:
            Same as chat()
            
        Yields:
            Individual tokens/chunks as strings
        """
        pass

    @abstractmethod
    def generate_embeddings(self, texts: list) -> list:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of strings to embed
            
        Returns:
            List of embedding vectors (list of floats)
        """
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """
        Get information about the current model.
        
        Returns:
            Dict with: name, size, context_window, quantization, etc.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the model provider is healthy and reachable.
        
        Returns:
            True if healthy, False otherwise
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the current model name."""
        pass

    @abstractmethod
    def get_context_window(self) -> int:
        """Get the model's context window size in tokens."""
        pass
