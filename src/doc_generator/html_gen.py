"""
HTML Documentation Generator
"""
import logging
import os
import re
import markdown
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.doc_generator.generator import DocGenerator

logger = logging.getLogger(__name__)

class HTMLGenerator(DocGenerator):
    """
    Generator for HTML documentation
    """
    
    def __init__(self, output_dir: str, template_dir: Optional[str] = None):
        """
        Initialize the HTML generator
        
        Args:
            output_dir (str): Directory to output generated documentation
            template_dir (str, optional): Directory containing templates
        """
        super().__init__(output_dir, template_dir)
        
        # Load templates if available
        self.page_template = self._load_template('page.html') or self._default_page_template()
        self.index_template = self._load_template('index.html') or self._default_index_template()
        
        # Copy static assets if available
        self._copy_static_assets()
    
    def generate(self, file_path: str, documentation: Dict[str, Any]) -> str:
        """
        Generate HTML documentation for a file
        
        Args:
            file_path (str): Path to the source file (relative to input dir)
            documentation (dict): Documentation data
            
        Returns:
            str: Path to the generated documentation file
        """
        output_path = self._get_output_path(file_path)
        
        # Create markdown content
        md_content = self._generate_markdown_content(file_path, documentation)
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'codehilite', 'toc']
        )
        
        # Get module information
        module_info = documentation.get('module', {})
        module_name = module_info.get('name', os.path.basename(file_path))
        
        # Format the HTML page
        title = f"Documentation: {module_name}"
        
        html_doc = self.page_template.format(
            title=title,
            content=html_content,
            file_path=file_path,
            date=datetime.now().strftime('%Y-%m-%d'),
            nav=self._generate_nav_html(file_path)
        )
        
        # Write to file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_doc)
            logger.info(f"Generated HTML documentation for {file_path} at {output_path}")
        except Exception as e:
            logger.error(f"Error writing HTML file {output_path}: {str(e)}")
        
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
        index_path = os.path.join(self.output_dir, 'index.html')
        
        # Create markdown content for file list
        md_content = f"# {project_name} Documentation\n\n"
        
        # Organize files by directory
        file_tree = {}
        for file_path in source_files:
            directory = os.path.dirname(file_path)
            if directory not in file_tree:
                file_tree[directory] = []
            file_tree[directory].append(file_path)
        
        # Generate file links
        for directory, files in sorted(file_tree.items()):
            if directory:
                md_content += f"## {directory}/\n\n"
            else:
                md_content += "## Root\n\n"
            
            for file_path in sorted(files):
                base_name = os.path.basename(file_path)
                doc_path = self._get_output_path(file_path)
                rel_path = os.path.relpath(doc_path, self.output_dir)
                
                md_content += f"- [{base_name}]({rel_path})\n"
            
            md_content += "\n"
        
        # Convert markdown to HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'codehilite', 'toc']
        )
        
        # Format the HTML page
        html_doc = self.index_template.format(
            title=f"{project_name} Documentation",
            project_name=project_name,
            content=html_content,
            date=datetime.now().strftime('%Y-%m-%d')
        )
        
        # Write to file
        try:
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html_doc)
            logger.info(f"Generated HTML index file at {index_path}")
        except Exception as e:
            logger.error(f"Error writing HTML index file {index_path}: {str(e)}")
        
        return index_path
    
    def _get_extension(self) -> str:
        """
        Get the file extension for HTML
        
        Returns:
            str: HTML file extension
        """
        return '.html'
    
    def _generate_markdown_content(self, file_path: str, documentation: Dict[str, Any]) -> str:
        """
        Generate markdown content for a file
        
        Args:
            file_path (str): Path to the source file
            documentation (dict): Documentation data
            
        Returns:
            str: Markdown content
        """
        # Get module information
        module_info = documentation.get('module', {})
        module_name = module_info.get('name', os.path.basename(file_path))
        
        # Prepare module documentation
        module_doc = module_info.get('docstring', '')
        
        # Create markdown content
        md_content = f"# {module_name}\n\n"
        md_content += f"*File: {file_path}*\n\n"
        md_content += f"{module_doc}\n\n"
        
        # Add table of contents
        md_content += "[TOC]\n\n"
        
        # Process imports
        imports = documentation.get('imports', [])
        if imports:
            md_content += "## Imports\n\n"
            
            for imp in imports:
                if imp.get('type') == 'from':
                    module = imp.get('module', '')
                    name = imp.get('name', '')
                    asname = imp.get('asname', '')
                    
                    if asname:
                        md_content += f"- `from {module} import {name} as {asname}`\n"
                    else:
                        md_content += f"- `from {module} import {name}`\n"
                else:
                    name = imp.get('name', '')
                    asname = imp.get('asname', '')
                    
                    if asname:
                        md_content += f"- `import {name} as {asname}`\n"
                    else:
                        md_content += f"- `import {name}`\n"
            
            md_content += "\n"
        
        # Process classes
        classes = documentation.get('classes', [])
        if classes:
            md_content += "## Classes\n\n"
            
            for cls in classes:
                md_content += self._generate_class_markdown(cls) + "\n\n"
        
        # Process functions
        functions = documentation.get('functions', [])
        module_functions = [f for f in functions if not f.get('class_name')]
        
        if module_functions:
            md_content += "## Functions\n\n"
            
            for func in module_functions:
                md_content += self._generate_function_markdown(func) + "\n\n"
        
        # Process variables
        variables = documentation.get('variables', [])
        module_vars = [v for v in variables if not v.get('class_name')]
        
        if module_vars:
            md_content += "## Variables\n\n"
            
            for var in module_vars:
                md_content += self._generate_variable_markdown(var) + "\n\n"
        
        return md_content
    
    def _generate_class_markdown(self, cls: Dict[str, Any]) -> str:
        """
        Generate markdown for a class
        
        Args:
            cls (dict): Class information
            
        Returns:
            str: Markdown content
        """
        class_name = cls.get('name', '')
        doc = cls.get('documentation', cls.get('docstring', ''))
        
        md = f"### Class: `{class_name}`\n\n"
        
        # Add bases if available
        bases = cls.get('bases', [])
        if bases:
            md += f"*Inherits from: {', '.join(bases)}*\n\n"
        
        # Add class documentation
        md += f"{doc}\n\n"
        
        # Add attributes
        attributes = cls.get('attributes', [])
        if attributes:
            md += "#### Attributes\n\n"
            
            for attr in attributes:
                md += self._generate_variable_markdown(attr, is_attribute=True) + "\n\n"
        
        # Add methods
        methods = cls.get('methods', [])
        if methods:
            md += "#### Methods\n\n"
            
            for method in methods:
                md += self._generate_function_markdown(method, is_method=True) + "\n\n"
        
        return md
    
    def _generate_function_markdown(self, func: Dict[str, Any], is_method: bool = False) -> str:
        """
        Generate markdown for a function
        
        Args:
            func (dict): Function information
            is_method (bool): Whether this is a class method
            
        Returns:
            str: Markdown content
        """
        func_name = func.get('name', '')
        class_name = func.get('class_name', '')
        doc = func.get('documentation', func.get('docstring', ''))
        
        prefix = "Method" if is_method else "Function"
        qualified_name = f"{class_name}.{func_name}" if class_name and is_method else func_name
        
        md = f"{'####' if is_method else '###'} {prefix}: `{qualified_name}`\n\n"
        
        # Add function documentation
        md += f"{doc}\n\n"
        
        # Add parameters
        params = func.get('parameters', [])
        if params:
            md += "**Parameters**:\n\n"
            
            for param in params:
                param_name = param.get('name', '')
                param_type = param.get('annotation', '')
                param_default = param.get('default', '')
                
                if param_type:
                    if param_default:
                        md += f"- **{param_name}** (*{param_type}*, default: `{param_default}`)\n"
                    else:
                        md += f"- **{param_name}** (*{param_type}*)\n"
                else:
                    if param_default:
                        md += f"- **{param_name}** (default: `{param_default}`)\n"
                    else:
                        md += f"- **{param_name}**\n"
            
            md += "\n"
        
        # Add return type
        returns = func.get('returns', '')
        if returns:
            md += f"**Returns**: *{returns}*\n\n"
        
        return md
    
    def _generate_variable_markdown(self, var: Dict[str, Any], is_attribute: bool = False) -> str:
        """
        Generate markdown for a variable
        
        Args:
            var (dict): Variable information
            is_attribute (bool): Whether this is a class attribute
            
        Returns:
            str: Markdown content
        """
        var_name = var.get('name', '')
        class_name = var.get('class_name', '')
        annotation = var.get('annotation', '')
        value = var.get('value', '')
        
        prefix = "Attribute" if is_attribute else "Variable"
        qualified_name = f"{class_name}.{var_name}" if class_name and is_attribute else var_name
        
        md = f"{'####' if is_attribute else '###'} {prefix}: `{qualified_name}`\n\n"
        
        # Add type if available
        if annotation:
            md += f"**Type**: *{annotation}*\n\n"
        
        # Add value if available
        if value and str(value) != "None":
            md += f"**Default**: `{value}`\n\n"
        
        # Add documentation
        if 'documentation' in var:
            md += f"{var['documentation']}\n\n"
        
        return md
    
    def _generate_nav_html(self, current_file: str) -> str:
        """
        Generate HTML navigation
        
        Args:
            current_file (str): Current file path
            
        Returns:
            str: HTML navigation content
        """
        nav = '<div class="navigation">\n'
        nav += '  <a href="index.html">Index</a>\n'
        
        # Add breadcrumbs
        parts = current_file.split('/')
        path = ""
        
        for i, part in enumerate(parts[:-1]):
            path += part + "/"
            nav += f'  > <a href="#">{part}</a>\n'
        
        nav += f'  > {parts[-1]}\n'
        nav += '</div>\n'
        
        return nav
    
    def _copy_static_assets(self):
        """
        Copy static assets (CSS, JS) to output directory
        """
        # Create css directory if it doesn't exist
        css_dir = os.path.join(self.output_dir, 'css')
        if not os.path.exists(css_dir):
            os.makedirs(css_dir)
        
        # Check if template directory has CSS files
        if self.template_dir and os.path.exists(os.path.join(self.template_dir, 'css')):
            # Copy CSS files from template directory
            src_css_dir = os.path.join(self.template_dir, 'css')
            for file in os.listdir(src_css_dir):
                if file.endswith('.css'):
                    src_file = os.path.join(src_css_dir, file)
                    dst_file = os.path.join(css_dir, file)
                    shutil.copy2(src_file, dst_file)
        else:
            # Create default CSS file
            with open(os.path.join(css_dir, 'style.css'), 'w', encoding='utf-8') as f:
                f.write(self._default_css())
        
        logger.debug("Copied static assets to output directory")
    
    def _default_page_template(self) -> str:
        """
        Get the default HTML page template
        
        Returns:
            str: Default template
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/code-highlight.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>{title}</h1>
            {nav}
        </div>
    </header>
    
    <main class="container">
        <div class="content">
            {content}
        </div>
    </main>
    
    <footer>
        <div class="container">
            <p>Documentation generated for {file_path} on {date}</p>
        </div>
    </footer>
</body>
</html>
"""
    
    def _default_index_template(self) -> str:
        """
        Get the default HTML index template
        
        Returns:
            str: Default template
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>{project_name} Documentation</h1>
        </div>
    </header>
    
    <main class="container">
        <div class="content">
            {content}
        </div>
    </main>
    
    <footer>
        <div class="container">
            <p>Documentation generated on {date}</p>
        </div>
    </footer>
</body>
</html>
"""
    
    def _default_css(self) -> str:
        """
        Get the default CSS
        
        Returns:
            str: Default CSS
        """
        return """/* Base Styles */
:root {
    --primary-color: #0066cc;
    --secondary-color: #f8f9fa;
    --text-color: #333333;
    --link-color: #0066cc;
    --code-bg: #f5f5f5;
    --border-color: #dddddd;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: white;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
header {
    background-color: var(--secondary-color);
    border-bottom: 1px solid var(--border-color);
    padding: 20px 0;
}

header h1 {
    color: var(--primary-color);
    font-size: 24px;
}

.navigation {
    margin-top: 10px;
    color: #666;
}

.navigation a {
    color: var(--link-color);
    text-decoration: none;
}

.navigation a:hover {
    text-decoration: underline;
}

/* Main Content */
main {
    padding: 30px 0;
}

.content {
    background-color: white;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    margin: 20px 0 10px;
    font-weight: 600;
    line-height: 1.2;
}

h1 {
    font-size: 28px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 10px;
}

h2 {
    font-size: 24px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 6px;
}

h3 {
    font-size: 20px;
}

h4 {
    font-size: 18px;
}

p {
    margin: 0 0 15px;
}

/* Links */
a {
    color: var(--link-color);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

/* Lists */
ul, ol {
    margin: 0 0 15px 20px;
}

li {
    margin-bottom: 5px;
}

/* Code */
code, pre {
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    background-color: var(--code-bg);
    border-radius: 3px;
}

code {
    padding: 2px 5px;
    font-size: 0.9em;
}

pre {
    padding: 15px;
    margin: 15px 0;
    overflow-x: auto;
    font-size: 0.9em;
    line-height: 1.4;
    border: 1px solid var(--border-color);
}

pre code {
    padding: 0;
    background-color: transparent;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
}

th, td {
    padding: 8px 12px;
    text-align: left;
    border: 1px solid var(--border-color);
}

th {
    background-color: var(--secondary-color);
    font-weight: 600;
}

/* Footer */
footer {
    background-color: var(--secondary-color);
    border-top: 1px solid var(--border-color);
    padding: 20px 0;
    text-align: center;
    color: #666;
    font-size: 14px;
}

/* Code highlighting */
.codehilite {
    background-color: var(--code-bg);
    border-radius: 3px;
    margin: 15px 0;
    overflow: auto;
}

/* TOC */
.toc {
    background-color: var(--secondary-color);
    border: 1px solid var(--border-color);
    border-radius: 3px;
    padding: 15px;
    margin: 15px 0;
}

.toc ul {
    list-style-type: none;
    margin-left: 15px;
}
"""