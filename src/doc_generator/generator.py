"""
Documentation Generator Interface
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DocGenerator(ABC):
    """
    Abstract base class for documentation generators
    """
    
    def __init__(self, output_dir: str, template_dir: Optional[str] = None):
        """
        Initialize the documentation generator
        
        Args:
            output_dir (str): Directory to output generated documentation
            template_dir (str, optional): Directory containing templates
        """
        self.output_dir = output_dir
        self.template_dir = template_dir
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        logger.debug(f"Initialized {self.__class__.__name__} with output_dir: {output_dir}")
    
    @abstractmethod
    def generate(self, file_path: str, documentation: Dict[str, Any]) -> str:
        """
        Generate documentation for a file
        
        Args:
            file_path (str): Path to the source file (relative to input dir)
            documentation (dict): Documentation data
            
        Returns:
            str: Path to the generated documentation file
        """
        pass
    
    @abstractmethod
    def generate_index(self, project_name: str, source_files: List[str]) -> str:
        """
        Generate an index file for the project
        
        Args:
            project_name (str): Name of the project
            source_files (list): List of source files that were documented
            
        Returns:
            str: Path to the generated index file
        """
        pass
    
    def _get_output_path(self, file_path: str) -> str:
        """
        Get the output file path for a source file
        
        Args:
            file_path (str): Relative path to the source file
            
        Returns:
            str: Path to the output documentation file
        """
        # Replace file extension with the appropriate one
        name, ext = os.path.splitext(file_path)
        output_path = os.path.join(self.output_dir, f"{name}{self._get_extension()}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        return output_path
    
    @abstractmethod
    def _get_extension(self) -> str:
        """
        Get the file extension for the documentation format
        
        Returns:
            str: File extension (including the dot)
        """
        pass
    
    def _load_template(self, template_name: str) -> Optional[str]:
        """
        Load a template file
        
        Args:
            template_name (str): Name of the template file
            
        Returns:
            str or None: Template content or None if not found
        """
        if not self.template_dir:
            return None
        
        template_path = os.path.join(self.template_dir, template_name)
        
        if not os.path.exists(template_path):
            logger.warning(f"Template not found: {template_path}")
            return None
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading template {template_path}: {str(e)}")
            return None


class DocGeneratorFactory:
    """
    Factory class to create appropriate documentation generator instances
    """
    
    def get_generator(self, format_type: str, output_dir: str, template_dir: Optional[str] = None) -> DocGenerator:
        """
        Get a documentation generator for the specified format
        
        Args:
            format_type (str): Documentation format ('markdown', 'html', etc.)
            output_dir (str): Directory to output generated documentation
            template_dir (str, optional): Directory containing templates
            
        Returns:
            DocGenerator: Appropriate generator instance
            
        Raises:
            ValueError: If format type is not supported
        """
        format_type = format_type.lower()
        
        if format_type == 'markdown':
            from src.doc_generator.markdown_gen import MarkdownGenerator
            return MarkdownGenerator(output_dir, template_dir)
        elif format_type == 'html':
            from src.doc_generator.html_gen import HTMLGenerator
            return HTMLGenerator(output_dir, template_dir)
        else:
            raise ValueError(f"Unsupported documentation format: {format_type}")