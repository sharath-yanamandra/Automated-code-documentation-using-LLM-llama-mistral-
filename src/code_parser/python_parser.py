"""
Python Code Parser Implementation
"""
import ast
import logging
import os
import re
from typing import Dict, List, Any, Optional, Tuple

from src.code_parser.parser import CodeParser

logger = logging.getLogger(__name__)

class PythonParser(CodeParser):
    """
    Parser for Python source code
    """
    
    def __init__(self, config=None):
        """
        Initialize the Python parser
        
        Args:
            config (dict, optional): Configuration dictionary
        """
        super().__init__(config)
        self.include_comments = self.config.get('include_comments', True)
        self.include_docstrings = self.config.get('include_docstrings', True)
        self.parse_dependencies = self.config.get('parse_dependencies', True)
        self.max_context_lines = self.config.get('max_context_lines', 50)
    
    def parse_file(self, file_path):
        """
        Parse a Python source file
        
        Args:
            file_path (str): Path to Python file
            
        Returns:
            dict: Structured representation of the Python code
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
        Parse Python code from a string
        
        Args:
            code (str): Python source code
            file_name (str, optional): Name of the file for context
            
        Returns:
            dict: Structured representation of the Python code
        """
        try:
            # Parse the AST
            tree = ast.parse(code)
            
            # Extract module-level docstring
            module_doc = ast.get_docstring(tree)
            
            # Find comments
            comments = self._extract_comments(code) if self.include_comments else {}
            
            # Prepare result structure
            result = {
                'module': {
                    'name': file_name,
                    'code': code,
                    'docstring': module_doc,
                    'comments': comments
                },
                'imports': self._extract_imports(tree),
                'classes': [],
                'functions': [],
                'variables': []
            }
            
            # Process each node in the AST
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    result['classes'].append(self._process_class(node, code))
                elif isinstance(node, ast.FunctionDef):
                    result['functions'].append(self._process_function(node, code))
                elif isinstance(node, ast.Assign):
                    result['variables'].extend(self._process_assignment(node, code))
            
            logger.debug(f"Successfully parsed Python code{' from ' + file_name if file_name else ''}")
            return result
            
        except SyntaxError as e:
            logger.error(f"Syntax error in Python code: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error parsing Python code: {str(e)}")
            raise
    
    def _extract_comments(self, code):
        """
        Extract comments from Python code
        
        Args:
            code (str): Python source code
            
        Returns:
            dict: Comments mapped to line numbers
        """
        comments = {}
        lines = code.split('\n')
        comment_pattern = re.compile(r'^\s*#\s*(.*)$|^.*?#\s*(.*)$')
        
        for i, line in enumerate(lines):
            match = comment_pattern.match(line)
            if match:
                comment = match.group(1) if match.group(1) is not None else match.group(2)
                comments[i + 1] = comment
        
        return comments
    
    def _extract_imports(self, tree):
        """
        Extract import statements from AST
        
        Args:
            tree (ast.Module): AST root node
            
        Returns:
            list: List of import information
        """
        imports = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append({
                        'type': 'import',
                        'name': name.name,
                        'asname': name.asname,
                        'line': node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for name in node.names:
                    imports.append({
                        'type': 'from',
                        'module': module,
                        'name': name.name,
                        'asname': name.asname,
                        'line': node.lineno
                    })
        
        return imports
    
    def _process_class(self, node, code):
        """
        Process a class definition
        
        Args:
            node (ast.ClassDef): Class definition node
            code (str): Full source code
            
        Returns:
            dict: Structured representation of the class
        """
        class_code = self._get_node_source(node, code)
        docstring = ast.get_docstring(node)
        
        # Get line numbers
        start_line = node.lineno
        end_line = self._get_node_end_line(node)
        
        # Extract context
        context = self.extract_context(code, start_line, self.max_context_lines)
        
        # Process methods and attributes
        methods = []
        class_vars = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(self._process_function(item, code, class_name=node.name))
            elif isinstance(item, ast.Assign):
                class_vars.extend(self._process_assignment(item, code, class_name=node.name))
        
        # Build class inheritance
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._get_attribute_path(base)}")
        
        return {
            'name': node.name,
            'bases': bases,
            'docstring': docstring,
            'code': class_code,
            'methods': methods,
            'attributes': class_vars,
            'decorators': self._get_decorators(node),
            'start_line': start_line,
            'end_line': end_line,
            'context': context
        }
    
    def _process_function(self, node, code, class_name=None):
        """
        Process a function definition
        
        Args:
            node (ast.FunctionDef): Function definition node
            code (str): Full source code
            class_name (str, optional): Name of the class this function belongs to
            
        Returns:
            dict: Structured representation of the function
        """
        func_code = self._get_node_source(node, code)
        docstring = ast.get_docstring(node)
        
        # Get line numbers
        start_line = node.lineno
        end_line = self._get_node_end_line(node)
        
        # Extract context
        context = self.extract_context(code, start_line, self.max_context_lines)
        
        # Process parameters
        params = []
        returns = None
        
        # Get function arguments
        for arg in node.args.args:
            param = {
                'name': arg.arg,
                'annotation': self._get_annotation(arg.annotation) if hasattr(arg, 'annotation') else None
            }
            params.append(param)
        
        # Get default values
        defaults = node.args.defaults
        if defaults:
            default_offset = len(params) - len(defaults)
            for i, default in enumerate(defaults):
                params[default_offset + i]['default'] = self._get_value(default)
        
        # Get *args and **kwargs
        if node.args.vararg:
            params.append({
                'name': f"*{node.args.vararg.arg}",
                'annotation': self._get_annotation(node.args.vararg.annotation) if hasattr(node.args.vararg, 'annotation') else None
            })
        
        if node.args.kwarg:
            params.append({
                'name': f"**{node.args.kwarg.arg}",
                'annotation': self._get_annotation(node.args.kwarg.annotation) if hasattr(node.args.kwarg, 'annotation') else None
            })
        
        # Get return annotation
        if hasattr(node, 'returns') and node.returns:
            returns = self._get_annotation(node.returns)
        
        return {
            'name': node.name,
            'class_name': class_name,
            'docstring': docstring,
            'code': func_code,
            'parameters': params,
            'returns': returns,
            'decorators': self._get_decorators(node),
            'start_line': start_line,
            'end_line': end_line,
            'context': context
        }
    
    def _process_assignment(self, node, code, class_name=None):
        """
        Process a variable assignment
        
        Args:
            node (ast.Assign): Assignment node
            code (str): Full source code
            class_name (str, optional): Name of the class this variable belongs to
            
        Returns:
            list: List of variable information dictionaries
        """
        variables = []
        var_code = self._get_node_source(node, code)
        
        # Get line numbers
        start_line = node.lineno
        end_line = self._get_node_end_line(node)
        
        # Extract context
        context = self.extract_context(code, start_line, self.max_context_lines)
        
        # Get variable value
        value = self._get_value(node.value)
        
        # Get type annotation if available
        annotation = None
        if isinstance(node, ast.AnnAssign):
            annotation = self._get_annotation(node.annotation)
        
        # Process each target in the assignment
        for target in node.targets:
            if isinstance(target, ast.Name):
                variables.append({
                    'name': target.id,
                    'class_name': class_name,
                    'value': value,
                    'annotation': annotation,
                    'code': var_code,
                    'start_line': start_line,
                    'end_line': end_line,
                    'context': context
                })
            elif isinstance(target, ast.Tuple):
                # Handle multiple assignment (e.g., a, b = 1, 2)
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        variables.append({
                            'name': elt.id,
                            'class_name': class_name,
                            'value': "Part of tuple unpacking",
                            'annotation': None,
                            'code': var_code,
                            'start_line': start_line,
                            'end_line': end_line,
                            'context': context
                        })
            elif isinstance(target, ast.Attribute):
                # Handle attribute assignment (e.g., self.x = 1)
                attr_path = self._get_attribute_path(target)
                variables.append({
                    'name': attr_path,
                    'class_name': class_name,
                    'value': value,
                    'annotation': annotation,
                    'code': var_code,
                    'start_line': start_line,
                    'end_line': end_line,
                    'context': context
                })
        
        return variables
    
    def _get_node_source(self, node, code):
        """
        Get the source code for a node
        
        Args:
            node (ast.AST): AST node
            code (str): Full source code
            
        Returns:
            str: Source code for the node
        """
        try:
            lines = code.split('\n')
            start_line = node.lineno - 1  # Convert to 0-based indexing
            end_line = self._get_node_end_line(node)
            
            # Ensure we don't go out of bounds
            end_line = min(end_line, len(lines))
            
            return '\n'.join(lines[start_line:end_line])
        except Exception as e:
            logger.warning(f"Could not get source for node: {str(e)}")
            return ""
    
    def _get_node_end_line(self, node):
        """
        Get the end line of a node
        
        Args:
            node (ast.AST): AST node
            
        Returns:
            int: End line number
        """
        if hasattr(node, 'end_lineno'):
            return node.end_lineno
        
        # Fall back to finding the max line number in the subtree
        max_line = node.lineno
        for child in ast.iter_child_nodes(node):
            if hasattr(child, 'lineno'):
                child_end = self._get_node_end_line(child)
                max_line = max(max_line, child_end)
        
        return max_line
    
    def _get_decorators(self, node):
        """
        Get decorators for a node
        
        Args:
            node (ast.FunctionDef or ast.ClassDef): Node with decorators
            
        Returns:
            list: List of decorator names
        """
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(f"{decorator.func.id}(...)")
                elif isinstance(decorator.func, ast.Attribute):
                    decorators.append(f"{self._get_attribute_path(decorator.func)}(...)")
            elif isinstance(decorator, ast.Attribute):
                decorators.append(self._get_attribute_path(decorator))
        
        return decorators
    
    def _get_attribute_path(self, node):
        """
        Get the full path of an attribute
        
        Args:
            node (ast.Attribute): Attribute node
            
        Returns:
            str: Full attribute path
        """
        parts = []
        current = node
        
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            parts.append(current.id)
        
        return '.'.join(reversed(parts))
    
    def _get_annotation(self, node):
        """
        Get type annotation as string
        
        Args:
            node (ast.AST): Annotation node
            
        Returns:
            str: Annotation as string
        """
        if node is None:
            return None
        
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_path(node)
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation(node.value)
            slice_val = self._get_annotation(node.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(node, ast.Index):
            return self._get_annotation(node.value)
        elif isinstance(node, ast.Tuple):
            elts = [self._get_annotation(elt) for elt in node.elts]
            return f"({', '.join(elts)})"
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return f"'{node.value}'"
            return str(node.value)
        elif isinstance(node, ast.List):
            elts = [self._get_annotation(elt) for elt in node.elts]
            return f"[{', '.join(elts)}]"
        elif isinstance(node, ast.BinOp):
            # Handle Union types (X | Y in Python 3.10+)
            left = self._get_annotation(node.left)
            right = self._get_annotation(node.right)
            if isinstance(node.op, ast.BitOr):
                return f"{left} | {right}"
            return f"{left} ? {right}"
        else:
            return "unknown"
    
    def _get_value(self, node):
        """
        Get a simple representation of a value
        
        Args:
            node (ast.AST): Value node
            
        Returns:
            str: Value as string
        """
        if node is None:
            return None
        
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                if len(node.value) > 50:
                    return f"'{node.value[:47]}...'"
                return f"'{node.value}'"
            return str(node.value)
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"{node.func.id}(...)"
            elif isinstance(node.func, ast.Attribute):
                return f"{self._get_attribute_path(node.func)}(...)"
            return "function call"
        elif isinstance(node, ast.Dict):
            return "{...}"
        elif isinstance(node, ast.List):
            return "[...]"
        elif isinstance(node, ast.Tuple):
            return "(...)"
        elif isinstance(node, ast.Set):
            return "{...}"
        elif isinstance(node, ast.ListComp):
            return "[list comprehension]"
        elif isinstance(node, ast.DictComp):
            return "{dict comprehension}"
        elif isinstance(node, ast.SetComp):
            return "{set comprehension}"
        elif isinstance(node, ast.Lambda):
            return "lambda function"
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_path(node)
        else:
            return "complex expression"