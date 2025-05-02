"""
LLM Interface for Auto Documentation Generator
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLMInterface(ABC):
    """
    Abstract base class for LLM interactions
    """
    
    def __init__(self, model_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM interface
        
        Args:
            model_path (str): Path to the model file
            config (dict, optional): Configuration dictionary
        """
        self.model_path = model_path
        self.config = config or {}
        self.model = None
        self.tokenizer = None
        
        # Common LLM parameters
        self.max_tokens = self.config.get('max_tokens', 1024)
        self.temperature = self.config.get('temperature', 0.2)
        self.top_p = self.config.get('top_p', 0.9)
        self.context_length = self.config.get('context_length', 4096)
        
        # Cache settings
        self.cache_dir = self.config.get('cache_dir', 'cache')
        self.use_cache = self.config.get('use_cache', True)
        
        if self.use_cache and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        logger.debug(f"Initialized {self.__class__.__name__} with config: {self.config}")
        
    @abstractmethod
    def load_model(self):
        """
        Load the LLM model and tokenizer
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate text based on the prompt
        
        Args:
            prompt (str): Input prompt for the LLM
            
        Returns:
            str: Generated text
        """
        pass
    
    def get_cached_response(self, prompt: str) -> Optional[str]:
        """
        Get a cached response for a prompt if it exists
        
        Args:
            prompt (str): Input prompt
            
        Returns:
            str or None: Cached response or None if not found
        """
        if not self.use_cache:
            return None
        
        import hashlib
        
        # Create a hash of the prompt for the cache key
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{prompt_hash}.txt")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    logger.debug(f"Found cached response for prompt")
                    return f.read()
            except Exception as e:
                logger.warning(f"Error reading cache file: {e}")
        
        return None
    
    def save_to_cache(self, prompt: str, response: str) -> None:
        """
        Save a response to the cache
        
        Args:
            prompt (str): Input prompt
            response (str): Generated response
        """
        if not self.use_cache:
            return
        
        import hashlib
        
        # Create a hash of the prompt for the cache key
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{prompt_hash}.txt")
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(response)
            logger.debug(f"Saved response to cache")
        except Exception as e:
            logger.warning(f"Error writing to cache file: {e}")
    
    def cleanup(self):
        """
        Clean up resources
        """
        # Release model resources if needed
        self.model = None
        self.tokenizer = None


class LLMFactory:
    """
    Factory class to create appropriate LLM instances
    """
    
    def get_llm(self, llm_type: str, model_path: str, config: Optional[Dict[str, Any]] = None) -> LLMInterface:
        """
        Get an LLM instance for the specified type
        
        Args:
            llm_type (str): Type of LLM ('llama', 'mistral', etc.)
            model_path (str): Path to the model file
            config (dict, optional): Configuration dictionary
            
        Returns:
            LLMInterface: Appropriate LLM instance
            
        Raises:
            ValueError: If LLM type is not supported
        """
        llm_type = llm_type.lower()
        
        if llm_type == 'llama':
            from src.llm.llama_handler import LlamaHandler
            return LlamaHandler(model_path, config)
        elif llm_type == 'mistral':
            from src.llm.mistral_handler import MistralHandler
            return MistralHandler(model_path, config)
        else:
            raise ValueError(f"Unsupported LLM type: {llm_type}")