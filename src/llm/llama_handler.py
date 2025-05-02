"""
Llama LLM Handler Implementation
"""
import logging
import os
from typing import Dict, Any, Optional

from src.llm.llm_interface import LLMInterface

logger = logging.getLogger(__name__)

class LlamaHandler(LLMInterface):
    """
    Handler for Llama models using llama-cpp-python
    """
    
    def __init__(self, model_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Llama handler
        
        Args:
            model_path (str): Path to the model file
            config (dict, optional): Configuration dictionary
        """
        super().__init__(model_path, config)
        
        # Llama-specific parameters
        self.n_ctx = self.config.get('context_length', 4096)
        self.n_batch = self.config.get('batch_size', 512)
        self.n_gpu_layers = self.config.get('gpu_layers', -1)  # -1 means auto-detect
        self.quantization = self.config.get('quantization', 'q4_0')
        
        # Initialize model on creation if specified
        if self.config.get('load_on_init', True):
            self.load_model()
    
    def load_model(self):
        """
        Load the Llama model
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.model is not None:
            logger.debug("Model already loaded.")
            return True
        
        try:
            # Check if model file exists
            if not os.path.exists(self.model_path):
                logger.error(f"Model file not found: {self.model_path}")
                return False
            
            # Import llama-cpp-python
            try:
                from llama_cpp import Llama
            except ImportError:
                logger.error("llama-cpp-python package not installed. Please install it with: pip install llama-cpp-python")
                return False
            
            # Log model loading
            logger.info(f"Loading Llama model from {self.model_path}...")
            logger.info(f"Context length: {self.n_ctx}, Batch size: {self.n_batch}")
            
            # Load the model
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                n_gpu_layers=self.n_gpu_layers,
                seed=self.config.get('seed', -1),
                verbose=self.config.get('verbose', False)
            )
            
            logger.info("Llama model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading Llama model: {str(e)}")
            self.model = None
            return False
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using Llama model
        
        Args:
            prompt (str): Input prompt
            
        Returns:
            str: Generated text
        """
        # Check for cached response
        cached_response = self.get_cached_response(prompt)
        if cached_response is not None:
            return cached_response
        
        # Ensure model is loaded
        if self.model is None:
            success = self.load_model()
            if not success:
                return "Error: Failed to load model."
        
        try:
            # Format the prompt according to Llama's expected format
            formatted_prompt = self._format_prompt(prompt)
            
            # Log generation start (truncate for logging)
            log_prompt = formatted_prompt[:100] + "..." if len(formatted_prompt) > 100 else formatted_prompt
            logger.debug(f"Generating with prompt: {log_prompt}")
            
            # Generate the response
            response = self.model.create_completion(
                formatted_prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                stop=self.config.get('stop_sequences', ["</answer>", "Human:", "User:"]),
                echo=self.config.get('echo', False)
            )
            
            # Extract the text from the response
            if response and "choices" in response and len(response["choices"]) > 0:
                text = response["choices"][0]["text"].strip()
            else:
                text = ""
            
            # Clean up response if needed
            text = self._clean_response(text)
            
            # Save to cache
            self.save_to_cache(prompt, text)
            
            return text
            
        except Exception as e:
            logger.error(f"Error during text generation: {str(e)}")
            return f"Error generating documentation: {str(e)}"
    
    def _format_prompt(self, prompt: str) -> str:
        """
        Format the prompt for the Llama model
        
        Args:
            prompt (str): Original prompt
            
        Returns:
            str: Formatted prompt
        """
        # Use the system prompt template if provided
        system_prompt = self.config.get('system_prompt', 
            "You are an expert technical writer specializing in code documentation.")
        
        # Optional prefix and suffix
        prompt_prefix = self.config.get('prompt_prefix', "")
        prompt_suffix = self.config.get('prompt_suffix', "")
        
        # For Llama 2 Chat models
        if self.config.get('chat_format', 'llama2') == 'llama2':
            return f"""<s>[INST] <<SYS>>
{system_prompt}
<</SYS>>

{prompt_prefix}{prompt}{prompt_suffix} [/INST]
"""
        # For simpler format
        else:
            return f"{system_prompt}\n\n{prompt_prefix}{prompt}{prompt_suffix}\n"
    
    def _clean_response(self, text: str) -> str:
        """
        Clean up the generated response
        
        Args:
            text (str): Raw generated text
            
        Returns:
            str: Cleaned response text
        """
        # Remove any model formatting artifacts
        text = text.replace("[/INST]", "").strip()
        
        # Remove common completion endings
        end_markers = ["</answer>", "Human:", "User:", "Assistant:", "\n\n\n"]
        for marker in end_markers:
            if marker in text:
                text = text.split(marker)[0].strip()
        
        return text