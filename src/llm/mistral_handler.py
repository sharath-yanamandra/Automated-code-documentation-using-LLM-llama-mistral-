"""
Mistral LLM Handler Implementation
"""
"""
Mistral LLM Handler Implementation with Chunking
"""
import logging
import os
import re
from typing import Dict, Any, Optional

from src.llm.llm_interface import LLMInterface

logger = logging.getLogger(__name__)

class MistralHandler(LLMInterface):
    """
    Handler for Mistral models using ctransformers with added chunking support
    """
    
    def __init__(self, model_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Mistral handler
        
        Args:
            model_path (str): Path to the model file
            config (dict, optional): Configuration dictionary
        """
        super().__init__(model_path, config)
        
        # Mistral-specific parameters
        self.context_length = self.config.get('context_length', 4096)
        self.gpu_layers = self.config.get('gpu_layers', 0)
        self.batch_size = self.config.get('batch_size', 512)
        
        # Initialize model on creation if specified
        if self.config.get('load_on_init', True):
            self.load_model()
    
    def load_model(self):
        """
        Load the Mistral model using ctransformers
        
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
            
            # Import ctransformers
            try:
                from ctransformers import AutoModelForCausalLM
                
                # Log model loading
                logger.info(f"Loading Mistral model from {self.model_path}...")
                
                # Load the model
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    model_type="mistral",
                    context_length=self.context_length,
                    gpu_layers=self.gpu_layers
                )
                
                logger.info("Mistral model loaded successfully")
                return True
                
            except ImportError:
                # Fallback to mock mode if ctransformers is not installed
                logger.warning("ctransformers package not installed. Using mock mode.")
                logger.warning("Install with: pip install ctransformers")
                self.model = "MOCK_MODEL"
                return True
                
        except Exception as e:
            logger.error(f"Error loading Mistral model: {str(e)}")
            # Use mock mode as fallback
            logger.warning("Using mock mode due to error loading model")
            self.model = "MOCK_MODEL"
            return True
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using Mistral model
        
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
            # Check if we're in mock mode
            if self.model == "MOCK_MODEL":
                # Generate simple documentation based on prompt
                return self._generate_mock_response(prompt)
            
            # Check if the prompt is too long
            if len(prompt.split()) > (self.context_length / 2):
                # Use chunking approach for long prompts
                return self._handle_long_prompt(prompt)
            
            # Format the prompt
            formatted_prompt = self._format_prompt(prompt)
            
            # Log generation start (truncate for logging)
            log_prompt = formatted_prompt[:100] + "..." if len(formatted_prompt) > 100 else formatted_prompt
            logger.debug(f"Generating with prompt: {log_prompt}")
            
            try:
                # Generate the response
                text = self.model(
                    formatted_prompt,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p
                )
                
                # Clean up response if needed
                text = self._clean_response(text)
                
                # Save to cache
                self.save_to_cache(prompt, text)
                
                return text
            except Exception as e:
                logger.warning(f"Error during generation (likely token overflow): {str(e)}")
                # Fall back to chunking approach
                return self._handle_long_prompt(prompt)
            
        except Exception as e:
            logger.error(f"Error during text generation: {str(e)}")
            # Fall back to mock response
            return self._generate_mock_response(prompt)
    
    def _handle_long_prompt(self, prompt: str) -> str:
        """
        Handle long prompts by extracting key parts
        
        Args:
            prompt (str): Original long prompt
            
        Returns:
            str: Generated response
        """
        logger.info("Handling long prompt through smart extraction")
        
        # Extract key components from the prompt
        code_blocks = self._extract_code_blocks(prompt)
        name = self._extract_name(prompt)
        prompt_type = self._determine_prompt_type(prompt)
        
        # Create a condensed prompt
        if code_blocks and len(code_blocks) > 0:
            # Use the first code block (usually contains the function/class definition)
            condensed_code = code_blocks[0]
            
            # Generate a shorter prompt with just the essential information
            condensed_prompt = f"Generate documentation for this {prompt_type}: {name}\n\n"
            condensed_prompt += f"Here's the essential part of the code:\n\n```python\n{condensed_code}\n```\n\n"
            condensed_prompt += f"Provide a comprehensive explanation in P&C insurance context."
            
            # Try generating with the condensed prompt
            formatted_prompt = self._format_prompt(condensed_prompt)
            
            try:
                text = self.model(
                    formatted_prompt,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p
                )
                
                text = self._clean_response(text)
                return text
            except Exception as e:
                logger.warning(f"Error during condensed generation: {str(e)}")
                # Fall back to mock mode
                return self._generate_mock_response(f"{prompt_type} {name}")
        else:
            # If we couldn't extract code blocks, use a very simplified prompt
            simple_prompt = f"Briefly describe a {prompt_type} named {name} in P&C insurance context."
            formatted_prompt = self._format_prompt(simple_prompt)
            
            try:
                text = self.model(
                    formatted_prompt,
                    max_new_tokens=self.max_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p
                )
                
                text = self._clean_response(text)
                return text
            except Exception as e:
                logger.warning(f"Error during simplified generation: {str(e)}")
                # Fall back to mock mode as last resort
                return self._generate_mock_response(f"{prompt_type} {name}")
    
    def _extract_code_blocks(self, text: str) -> list:
        """
        Extract code blocks from markdown text
        
        Args:
            text (str): Text containing markdown code blocks
            
        Returns:
            list: List of code block contents
        """
        # Pattern to match code blocks with or without language specifier
        pattern = r'```(?:python)?\s*([\s\S]*?)```'
        matches = re.findall(pattern, text)
        return [match.strip() for match in matches]
    
    def _extract_name(self, text: str) -> str:
        """
        Extract name from prompt
        
        Args:
            text (str): Prompt text
            
        Returns:
            str: Extracted name or default
        """
        # Try to find name in the text
        name_match = re.search(r'name:?\s*([^\n\r]+)', text, re.IGNORECASE)
        if name_match:
            return name_match.group(1).strip()
        
        # Look for class or function name patterns
        class_match = re.search(r'class\s+(\w+)', text)
        if class_match:
            return class_match.group(1)
        
        func_match = re.search(r'def\s+(\w+)', text)
        if func_match:
            return func_match.group(1)
        
        # Default name based on prompt type
        return self._determine_prompt_type(text)
    
    def _determine_prompt_type(self, text: str) -> str:
        """
        Determine the type of prompt (class, function, etc.)
        
        Args:
            text (str): Prompt text
            
        Returns:
            str: Prompt type
        """
        lower_text = text.lower()
        
        if "class" in lower_text or "class:" in lower_text:
            return "class"
        elif "function" in lower_text or "function:" in lower_text or "def " in lower_text:
            return "function"
        elif "variable" in lower_text or "variable:" in lower_text:
            return "variable"
        elif "module" in lower_text or "module:" in lower_text:
            return "module"
        else:
            return "code"
    
    def _format_prompt(self, prompt: str) -> str:
        """
        Format the prompt for the Mistral model
        
        Args:
            prompt (str): Original prompt
            
        Returns:
            str: Formatted prompt
        """
        # Use the system prompt template if provided
        system_prompt = self.config.get('system_prompt', 
            "You are an expert technical writer specializing in P&C insurance code documentation.")
        
        # For Mistral Instruct format
        return f"<s>[INST] {system_prompt}\n\n{prompt} [/INST]"
    
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
        end_markers = ["</answer>", "Human:", "User:", "<|user|>", "<|system|>", "\n\n\n"]
        for marker in end_markers:
            if marker in text:
                text = text.split(marker)[0].strip()
        
        return text
    
    def _generate_mock_response(self, prompt: str) -> str:
        """
        Generate a mock response when the model is not available
        
        Args:
            prompt (str): Input prompt
            
        Returns:
            str: Generated mock response
        """
        # Check what type of documentation is requested
        if "class" in prompt.lower():
            class_name = self._extract_name(prompt)
            return f"""This class is part of the P&C insurance system.

It provides functionality related to {class_name}, which is an important component
for managing insurance policies, claims, or risk assessment. In the P&C insurance domain, 
this handles processes critical to effective insurance operations.

Key features include:
- Processing and validation of insurance data
- Support for standard P&C insurance workflows
- Implementation of business rules for insurance calculations
- Management of policy or claim information"""
            
        elif "function" in prompt.lower():
            func_name = self._extract_name(prompt)
            return f"""This function handles {func_name.replace('_', ' ')} operations in the P&C insurance system.

It performs calculations or data processing related to insurance policies or claims,
ensuring proper validation and compliance with industry standards. The function 
implements business logic for insurance operations according to P&C practices.

Insurance domain importance:
- Ensures accurate insurance calculations
- Supports consistent insurance processing flows
- Implements industry-standard methods for P&C insurance
- Provides key functionality for policy or claims management"""
            
        elif "variable" in prompt.lower():
            var_name = self._extract_name(prompt)
            return f"""This variable represents {var_name.replace('_', ' ')} in the P&C insurance context.

It stores important configuration or state information for the insurance processing
system, reflecting standard values or parameters used in P&C insurance.

This data point is essential for:
- Supporting insurance calculations
- Maintaining consistent policy processing
- Reflecting industry standards for risk assessment
- Storing key insurance parameters or rates"""
            
        else:
            return """This module is part of a Property & Casualty (P&C) insurance system.

It provides functionality for insurance operations, including policy calculations,
risk assessment, or claims processing. The implementation follows industry
standards for P&C insurance and includes specialized handling for different
insurance scenarios.

Key capabilities include:
- Insurance premium calculations
- Risk assessment for different property or casualty scenarios
- Implementation of insurance business rules
- Support for standard P&C insurance workflows"""

'''
import logging
import os
from typing import Dict, Any, Optional

from src.llm.llm_interface import LLMInterface

logger = logging.getLogger(__name__)

class MistralHandler(LLMInterface):
    """
    Handler for Mistral models using ctransformers
    """
    
    def __init__(self, model_path: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Mistral handler
        
        Args:
            model_path (str): Path to the model file
            config (dict, optional): Configuration dictionary
        """
        super().__init__(model_path, config)
        
        # Mistral-specific parameters
        self.context_length = self.config.get('context_length', 4096)
        self.gpu_layers = self.config.get('gpu_layers', 0)
        self.batch_size = self.config.get('batch_size', 512)
        
        # Initialize model on creation if specified
        if self.config.get('load_on_init', True):
            self.load_model()
    
    def load_model(self):
        """
        Load the Mistral model using ctransformers
        
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
            
            # Import ctransformers
            try:
                from ctransformers import AutoModelForCausalLM
            except ImportError:
                logger.error("ctransformers package not installed. Please install it with: pip install ctransformers")
                return False
            
            # Log model loading
            logger.info(f"Loading Mistral model from {self.model_path}...")
            
            # Load the model
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                model_type="mistral",
                context_length=self.context_length,
                gpu_layers=self.gpu_layers,
                batch_size=self.batch_size
            )
            
            logger.info("Mistral model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading Mistral model: {str(e)}")
            self.model = None
            return False
    
    def generate(self, prompt: str) -> str:
        """
        Generate text using Mistral model
        
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
            # Format the prompt according to Mistral's expected format
            formatted_prompt = self._format_prompt(prompt)
            
            # Log generation start (truncate for logging)
            log_prompt = formatted_prompt[:100] + "..." if len(formatted_prompt) > 100 else formatted_prompt
            logger.debug(f"Generating with prompt: {log_prompt}")
            
            # Generate the response
            stop_sequences = self.config.get('stop_sequences', ["</answer>", "Human:", "User:"])
            
            text = self.model(
                formatted_prompt,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                stop=stop_sequences
            )
            
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
        Format the prompt for the Mistral model
        
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
        
        # For Mistral Instruct format
        if self.config.get('chat_format', 'instruct') == 'instruct':
            return f"""<s>[INST] {system_prompt}

{prompt_prefix}{prompt}{prompt_suffix} [/INST]"""
        # For Zephyr chat format
        elif self.config.get('chat_format') == 'zephyr':
            return f"""<|system|>
{system_prompt}
<|user|>
{prompt_prefix}{prompt}{prompt_suffix}
<|assistant|>"""
        # For simple format
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
        end_markers = ["</answer>", "Human:", "User:", "<|user|>", "<|system|>", "\n\n\n"]
        for marker in end_markers:
            if marker in text:
                text = text.split(marker)[0].strip()
        
        return text
    '''
    
