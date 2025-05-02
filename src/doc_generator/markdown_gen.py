"""
Markdown Documentation Generator
"""
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.doc_generator.generator import DocGenerator

logger = logging.getLogger(__name__)

class MarkdownGenerator(DocGenerator):
    """
    Generator for Markdown documentation
    """
    
    def __init__(self, output_dir: str, template_dir: Optional[str] = None):
        """
        Initialize the Markdown generator
        
        Args:
            output_dir (str): Directory to output generated documentation
            template_dir (str, optional): Directory containing templates
        """
        super().__init__(output_dir, template_dir)
        
        # Load templates if available
        self.file_template = self._load_template('file.md') or self._default_file_template()
        self.index_template = self._load_template('index.md') or self._default_index_template()
        self.class_template = self._load_template('class.md') or self._default_class_template()
        self.function_template = self._load_template('function.md') or self._default_function_template()
    
    def generate(self, file_path: str, documentation: Dict[str, Any]) -> str:
        """
        Generate markdown documentation for a file
        
        Args:
            file_path (str): Path to the source file (relative to input dir)
            documentation (dict): Documentation data
            
        Returns:
            str: Path to the generated documentation file
        """
        output_path = self._get_output_path(file_path)
        
        # Get module information
        module_info = documentation.get('module', {})
        module_name = module_info.get('name', os.path.basename(file_path))
        
        # Prepare module documentation
        module_doc = module_info.get('docstring', '')
        
        # Process classes
        classes_md = ""
        for cls in documentation.get('classes', []):
            classes_md += self._generate_class_doc(cls) + "\n\n"
        
        # Process functions
        functions_md = ""
        for func in documentation.get('functions', []):
            if not func.get('class_name'):  # Only include module-level functions
                functions_md += self._generate_function_doc(func) + "\n\n"
        
        # Process variables
        variables_md = ""
        for var in documentation.get('variables', []):
            if not var.get('class_name'):  # Only include module-level variables
                variables_md += self._generate_variable_doc(var) + "\n\n"
        
        # Process imports
        imports_md = self._generate_imports_doc(documentation.get('imports', []))
        
        # Format the file documentation
        file_doc = self.file_template.format(
            file_path=file_path,
            module_name=module_name,
            date=datetime.now().strftime('%Y-%m-%d'),
            module_doc=module_doc,
            classes=classes_md,
            functions=functions_md,
            variables=variables_md,
            imports=imports_md
        )
        
        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(file_doc)
            logger.info(f"Generated documentation for {file_path} at {output_path}")
        except Exception as e:
            logger.error(f"Error writing documentation file {output_path}: {str(e)}")
        
        return output_path
    
    def generate_index(self, project_name: str, source_files: List[str]) -> str:
        """
        Generate an index file for the project
        
        Args:
            project_name (str): Name of the project
            source_files (list): List of source files that were documented
            
        Returns:
            str: Path to the generated index file
        """
        index_path = os.path.join(self.output_dir, 'index.md')
        
        # Organize files by directory
        file_tree = {}
        for file_path in source_files:
            directory = os.path.dirname(file_path)
            if directory not in file_tree:
                file_tree[directory] = []
            file_tree[directory].append(file_path)
        
        # Generate file links
        files_md = ""
        
        for directory, files in sorted(file_tree.items()):
            if directory:
                files_md += f"### {directory}/\n\n"
            else:
                files_md += "### Root\n\n"
            
            for file_path in sorted(files):
                base_name = os.path.basename(file_path)
                doc_path = self._get_output_path(file_path)
                rel_path = os.path.relpath(doc_path, self.output_dir)
                
                files_md += f"- [{base_name}]({rel_path})\n"
            
            files_md += "\n"
        
        # Format the index file
        index_doc = self.index_template.format(
            project_name=project_name,
            date=datetime.now().strftime('%Y-%m-%d'),
            files=files_md
        )
        
        # Write to file
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_doc)
            logger.info(f"Generated index file at {index_path}")
        except Exception as e:
            logger.error(f"Error writing index file {index_path}: {str(e)}")
        
        return index_path
    
    def _get_extension(self) -> str:
        """
        Get the file extension for Markdown
        
        Returns:
            str: Markdown file extension
        """
        return '.md'
    
    def _generate_class_doc(self, cls: Dict[str, Any]) -> str:
        """
        Generate documentation for a class
        
        Args:
            cls (dict): Class information
            
        Returns:
            str: Markdown documentation
        """
        # Process class documentation
        class_name = cls.get('name', '')
        doc = cls.get('documentation', cls.get('docstring', ''))
        
        # Process methods
        methods_md = ""
        for method in cls.get('methods', []):
            methods_md += self._generate_function_doc(method, is_method=True) + "\n\n"
        
        # Process attributes
        attributes_md = ""
        for attr in cls.get('attributes', []):
            attributes_md += self._generate_variable_doc(attr, is_attribute=True) + "\n\n"
        
        # Format the class documentation
        return self.class_template.format(
            class_name=class_name,
            bases=", ".join(cls.get('bases', [])),
            doc=doc,
            methods=methods_md,
            attributes=attributes_md
        )
    
    def _generate_function_doc(self, func: Dict[str, Any], is_method: bool = False) -> str:
        """
        Generate documentation for a function
        
        Args:
            func (dict): Function information
            is_method (bool): Whether this is a class method
            
        Returns:
            str: Markdown documentation
        """
        # Process function documentation
        func_name = func.get('name', '')
        class_name = func.get('class_name', '')
        doc = func.get('documentation', func.get('docstring', ''))
        
        # Process parameters
        params_md = ""
        for param in func.get('parameters', []):
            param_name = param.get('name', '')
            param_type = param.get('annotation', '')
            param_default = param.get('default', '')
            
            if param_type:
                if param_default:
                    params_md += f"- **{param_name}** (*{param_type}*, default: `{param_default}`)\n"
                else:
                    params_md += f"- **{param_name}** (*{param_type}*)\n"
            else:
                if param_default:
                    params_md += f"- **{param_name}** (default: `{param_default}`)\n"
                else:
                    params_md += f"- **{param_name}**\n"
        
        # Process return type
        returns = func.get('returns', '')
        if returns:
            returns_md = f"**Returns**: *{returns}*"
        else:
            returns_md = ""
        
        # Format the function documentation
        prefix = "Method" if is_method else "Function"
        qualified_name = f"{class_name}.{func_name}" if class_name and is_method else func_name
        
        return self.function_template.format(
            prefix=prefix,
            qualified_name=qualified_name,
            func_name=func_name,
            doc=doc,
            parameters=params_md,
            returns=returns_md
        )
    
    def _generate_variable_doc(self, var: Dict[str, Any], is_attribute: bool = False) -> str:
        """
        Generate documentation for a variable
        
        Args:
            var (dict): Variable information
            is_attribute (bool): Whether this is a class attribute
            
        Returns:
            str: Markdown documentation
        """
        # Process variable documentation
        var_name = var.get('name', '')
        class_name = var.get('class_name', '')
        annotation = var.get('annotation', '')
        value = var.get('value', '')
        
        # Format type and value
        if annotation:
            type_info = f"*{annotation}*"
        else:
            type_info = ""
        
        if value and str(value) != "None":
            value_info = f"= `{value}`"
        else:
            value_info = ""
        
        prefix = "Attribute" if is_attribute else "Variable"
        qualified_name = f"{class_name}.{var_name}" if class_name and is_attribute else var_name
        
        # Format the variable documentation
        return f"### {prefix}: `{qualified_name}`\n\n" + \
               (f"**Type**: {type_info}\n\n" if type_info else "") + \
               (f"**Default**: {value_info}\n\n" if value_info else "") + \
               (var.get('documentation', '') if 'documentation' in var else "")
    
    def _generate_imports_doc(self, imports: List[Dict[str, Any]]) -> str:
        """
        Generate documentation for imports
        
        Args:
            imports (list): List of import information
            
        Returns:
            str: Markdown documentation
        """
        if not imports:
            return ""
        
        imports_md = "## Imports\n\n"
        
        for imp in imports:
            if imp.get('type') == 'from':
                module = imp.get('module', '')
                name = imp.get('name', '')
                asname = imp.get('asname', '')
                
                if asname:
                    imports_md += f"- `from {module} import {name} as {asname}`\n"
                else:
                    imports_md += f"- `from {module} import {name}`\n"
            else:
                name = imp.get('name', '')
                asname = imp.get('asname', '')
                
                if asname:
                    imports_md += f"- `import {name} as {asname}`\n"
                else:
                    imports_md += f"- `import {name}`\n"
        
        return imports_md
    
    def _default_file_template(self) -> str:
        """
        Get the default file template
        
        Returns:
            str: Default template
        """
        return """# {module_name}

*File: {file_path}*

*Generated: {date}*

{module_doc}

{imports}

{classes}

{functions}

{variables}
"""
    
    def _default_index_template(self) -> str:
        """
        Get the default index template
        
        Returns:
            str: Default template
        """
        return """# {project_name} Documentation

*Generated: {date}*

## Files

{files}
"""
    
    def _default_class_template(self) -> str:
        """
        Get the default class template
        
        Returns:
            str: Default template
        """
        return """## Class: `{class_name}`

{doc}

{attributes}

{methods}
"""
    
    def _default_function_template(self) -> str:
        """
        Get the default function template
        
        Returns:
            str: Default template
        """
        return """### {prefix}: `{qualified_name}`

{doc}

**Parameters**:
{parameters}

{returns}
"""