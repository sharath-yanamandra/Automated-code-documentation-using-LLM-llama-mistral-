"""
Code Parser Interface for Auto Documentation Generator
"""
import os
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class CodeParser(ABC):
    """
    Abstract base class for code parsers
    """
    
    def __init__(self, config=None):
        """
        Initialize the code parser
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        self.config = config or {}
        logger.debug(f"Initialized {self.__class__.__name__} with config: {self.config}")
    
    @abstractmethod
    def parse_file(self, file_path):
        """
        Parse a source code file
        
        Args:
            file_path (str): Path to the source code file
            
        Returns:
            dict: Structured representation of the code
        """
        pass
    
    @abstractmethod
    def parse_code(self, code, file_name=None):
        """
        Parse source code from a string
        
        Args:
            code (str): Source code as string
            file_name (str, optional): Name of the file for context
            
        Returns:
            dict: Structured representation of the code
        """
        pass
    
    def extract_context(self, code, line_num, max_lines=50):
        """
        Extract context around a specific line of code
        
        Args:
            code (str): Source code
            line_num (int): Line number to extract context around
            max_lines (int): Maximum number of context lines
            
        Returns:
            str: Context code
        """
        lines = code.split('\n')
        start = max(0, line_num - max_lines // 2)
        end = min(len(lines), line_num + max_lines // 2)
        
        return '\n'.join(lines[start:end])


class CodeParserFactory:
    """
    Factory class to create appropriate code parser instances
    """
    
    def get_parser(self, language, config=None):
        """
        Get a parser for the specified language
        
        Args:
            language (str): Programming language ('python', 'java', etc.)
            config (dict, optional): Configuration dictionary
            
        Returns:
            CodeParser: Appropriate parser instance
            
        Raises:
            ValueError: If language is not supported
        """
        language = language.lower()
        
        if language == 'python':
            from src.code_parser.python_parser import PythonParser
            return PythonParser(config)
        elif language == 'java':
            from src.code_parser.java_parser import JavaParser
            return JavaParser(config)
        else:
            raise ValueError(f"Unsupported language: {language}")