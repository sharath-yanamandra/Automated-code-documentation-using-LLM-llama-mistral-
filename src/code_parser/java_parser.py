"""
Java Code Parser Implementation
"""
import re
import logging
import os
from src.code_parser.parser import CodeParser

logger = logging.getLogger(__name__)

class JavaParser(CodeParser):
    """
    Parser for Java source code
    
    Note: This is a simplified implementation that uses regex patterns
    for parsing instead of a full-fledged Java parser. For production use,
    consider using libraries like javalang or a JDT-based parser.
    """
    
    def __init__(self, config=None):
        """
        Initialize the Java parser
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        super().__init__(config)
        self.include_comments = self.config.get('include_comments', True)
        self.include_javadoc = self.config.get('include_docstrings', True)
        self.parse_dependencies = self.config.get('parse_dependencies', True)
        self.max_context_lines = self.config.get('max_context_lines', 50)
        
        # Regex patterns for Java elements
        self.patterns = {
            'package': re.compile(r'package\s+([a-zA-Z0-9_.]+)\s*;'),
            'import': re.compile(r'import\s+(?:static\s+)?([a-zA-Z0-9_.]+(?:\*)?)\s*;'),
            'class': re.compile(r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*class\s+([a-zA-Z0-9_]+)(?:\s+extends\s+([a-zA-Z0-9_<>.]+))?(?:\s+implements\s+([a-zA-Z0-9_<>.,\s]+))?'),
            'method': re.compile(r'(?:public|private|protected)?\s*(?:static)?\s*(?:final|abstract|synchronized)?\s*(?:<[^>]+>)?\s*(?:([a-zA-Z0-9_<>[\],\s]+))\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*(?:throws\s+([a-zA-Z0-9_,\s]+))?\s*(?:\{|;)'),
            'field': re.compile(r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*([a-zA-Z0-9_<>[\],\s]+)\s+([a-zA-Z0-9_]+)(?:\s*=\s*([^;]+))?\s*;'),
            'javadoc': re.compile(r'/\*\*(.*?)\*/', re.DOTALL),
            'line_comment': re.compile(r'//(.*)$', re.MULTILINE),
        }
    
    def parse_file(self, file_path):
        """
        Parse a Java source file
        
        Args:
            file_path (str): Path to Java file
            
        Returns:
            dict: Structured representation of the Java code
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                code = file.read()
            
            return self.parse_code(code, file_path)
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            raise
    
    def parse_code(self, code, file_name=None):
        """
        Parse Java code from a string
        
        Args:
            code (str): Java source code
            file_name (str, optional): Name of the file for context
            
        Returns:
            dict: Structured representation of the Java code
        """
        try:
            # Extract comments if needed
            comments = {}
            if self.include_comments:
                comments = self._extract_comments(code)
            
            # Extract javadoc comments if needed
            javadocs = {}
            if self.include_javadoc:
                javadocs = self._extract_javadocs(code)
            
            # Get package declaration
            package_match = self.patterns['package'].search(code)
            package = package_match.group(1) if package_match else ""
            
            # Prepare result structure
            result = {
                'module': {
                    'name': file_name,
                    'package': package,
                    'code': code,
                    'comments': comments
                },
                'imports': self._extract_imports(code),
                'classes': self._extract_classes(code, javadocs),
                'interfaces': [],  # To be implemented
                'enums': [],       # To be implemented
                'annotations': []  # To be implemented
            }
            
            logger.debug(f"Successfully parsed Java code{' from ' + file_name if file_name else ''}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing Java code: {str(e)}")
            raise
    
    def _extract_comments(self, code):
        """
        Extract line comments from Java code
        
        Args:
            code (str): Java source code
            
        Returns:
            dict: Comments mapped to line numbers
        """
        comments = {}
        lines = code.split('\n')
        
        # Find all line comments
        for i, line in enumerate(lines):
            match = self.patterns['line_comment'].search(line)
            if match:
                comments[i + 1] = match.group(1).strip()
        
        return comments
    
    def _extract_javadocs(self, code):
        """
        Extract JavaDoc comments from Java code
        
        Args:
            code (str): Java source code
            
        Returns:
            dict: JavaDoc comments mapped to their positions
        """
        javadocs = {}
        
        # Find all JavaDoc comments
        for match in self.patterns['javadoc'].finditer(code):
            start_pos = match.start()
            
            # Find the line number
            line_num = code[:start_pos].count('\n') + 1
            
            # Clean up the JavaDoc comment
            javadoc = match.group(1)
            javadoc = re.sub(r'\n\s*\*\s?', '\n', javadoc)
            javadoc = javadoc.strip()
            
            javadocs[line_num] = javadoc
        
        return javadocs
    
    def _extract_imports(self, code):
        """
        Extract import statements from Java code
        
        Args:
            code (str): Java source code
            
        Returns:
            list: List of import information
        """
        imports = []
        
        for match in self.patterns['import'].finditer(code):
            import_path = match.group(1)
            is_static = 'static' in match.group(0)
            is_wildcard = import_path.endswith('*')
            
            imports.append({
                'path': import_path,
                'is_static': is_static,
                'is_wildcard': is_wildcard
            })
        
        return imports
    
    def _extract_classes(self, code, javadocs):
        """
        Extract classes from Java code
        
        Args:
            code (str): Java source code
            javadocs (dict): JavaDoc comments
            
        Returns:
            list: List of class information
        """
        classes = []
        
        for class_match in self.patterns['class'].finditer(code):
            class_name = class_match.group(1)
            parent_class = class_match.group(2) if class_match.group(2) else None
            
            # Find interfaces if any
            interfaces = []
            if class_match.group(3):
                interfaces = [i.strip() for i in class_match.group(3).split(',')]
            
            # Get the class start position
            class_start = class_match.start()
            
            # Find the class end (this is a simplification)
            class_end = self._find_block_end(code, class_start)
            
            # Extract class body
            class_body = code[class_start:class_end+1] if class_end else code[class_start:]
            
            # Find JavaDoc for this class
            class_line = code[:class_start].count('\n') + 1
            class_javadoc = None
            
            # Look for closest javadoc above the class
            for line in sorted(javadocs.keys(), reverse=True):
                if line < class_line:
                    class_javadoc = javadocs[line]
                    break
            
            # Extract methods and fields
            methods = self._extract_methods(class_body, javadocs)
            fields = self._extract_fields(class_body, javadocs)
            
            # Add class info to result
            classes.append({
                'name': class_name,
                'parent_class': parent_class,
                'interfaces': interfaces,
                'javadoc': class_javadoc,
                'code': class_body,
                'methods': methods,
                'fields': fields,
                'start_line': class_line,
                'end_line': code[:class_end].count('\n') + 1 if class_end else None
            })
        
        return classes
    
    def _extract_methods(self, class_body, javadocs):
        """
        Extract methods from class body
        
        Args:
            class_body (str): Java class code
            javadocs (dict): JavaDoc comments
            
        Returns:
            list: List of method information
        """
        methods = []
        
        for method_match in self.patterns['method'].finditer(class_body):
            return_type = method_match.group(1).strip()
            method_name = method_match.group(2)
            parameters_str = method_match.group(3)
            throws = method_match.group(4)
            
            # Parse parameters
            parameters = []
            if parameters_str.strip():
                for param in parameters_str.split(','):
                    param = param.strip()
                    if not param:
                        continue
                    
                    # Handle varargs
                    is_vararg = '...' in param
                    param = param.replace('...', '')
                    
                    # Split parameter type and name
                    parts = param.strip().split()
                    param_type = ' '.join(parts[:-1])
                    param_name = parts[-1]
                    
                    parameters.append({
                        'type': param_type,
                        'name': param_name,
                        'is_vararg': is_vararg
                    })
            
            # Get method start position
            method_start = method_match.start()
            
            # Find method end (simplified)
            method_end = self._find_block_end(class_body, method_start)
            
            # Get method body
            method_body = class_body[method_start:method_end+1] if method_end else class_body[method_start:]
            
            # Find JavaDoc for this method
            method_line = class_body[:method_start].count('\n') + 1
            method_javadoc = None
            
            # Look for closest javadoc above the method
            for line in sorted(javadocs.keys(), reverse=True):
                if line <= method_line and line > method_line - 10:  # Look within 10 lines
                    method_javadoc = javadocs[line]
                    break
            
            # Parse throws clause
            throws_list = []
            if throws:
                throws_list = [t.strip() for t in throws.split(',')]
            
            # Add method info to result
            methods.append({
                'name': method_name,
                'return_type': return_type,
                'parameters': parameters,
                'throws': throws_list,
                'javadoc': method_javadoc,
                'code': method_body,
                'start_line': method_line
            })
        
        return methods
    
    def _extract_fields(self, class_body, javadocs):
        """
        Extract fields from class body
        
        Args:
            class_body (str): Java class code
            javadocs (dict): JavaDoc comments
            
        Returns:
            list: List of field information
        """
        fields = []
        
        for field_match in self.patterns['field'].finditer(class_body):
            field_type = field_match.group(1).strip()
            field_name = field_match.group(2)
            field_value = field_match.group(3).strip() if field_match.group(3) else None
            
            # Get field start position
            field_start = field_match.start()
            
            # Find JavaDoc for this field
            field_line = class_body[:field_start].count('\n') + 1
            field_javadoc = None
            
            # Look for closest javadoc above the field
            for line in sorted(javadocs.keys(), reverse=True):
                if line <= field_line and line > field_line - 5:  # Look within 5 lines
                    field_javadoc = javadocs[line]
                    break
            
            # Add field info to result
            fields.append({
                'name': field_name,
                'type': field_type,
                'value': field_value,
                'javadoc': field_javadoc,
                'line': field_line
            })
        
        return fields
    
    def _find_block_end(self, code, start_pos):
        """
        Find the end of a code block (simplistic implementation)
        
        Args:
            code (str): Source code
            start_pos (int): Starting position
            
        Returns:
            int: Position of the closing bracket or None if not found
        """
        # Find opening bracket
        bracket_pos = code.find('{', start_pos)
        if bracket_pos == -1:
            return None
        
        # Count brackets
        level = 1
        pos = bracket_pos + 1
        
        while pos < len(code) and level > 0:
            if code[pos] == '{':
                level += 1
            elif code[pos] == '}':
                level -= 1
                if level == 0:
                    return pos
            pos += 1
        
        return None