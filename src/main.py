#!/usr/bin/env python3
"""
Auto Documentation Generator for P&C Insurance Codebases
Main entry point for the application
"""
import argparse
import os
import sys
import yaml
import logging
from datetime import datetime

from src.code_parser.parser import CodeParserFactory
from src.llm.llm_interface import LLMFactory
from src.doc_generator.generator import DocGeneratorFactory
from src.utils.file_utils import get_files_by_extension, ensure_dir
from src.utils.logging_utils import setup_logging

def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Automated Code Documentation Generator')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                        help='Path to configuration file')
    parser.add_argument('--input', type=str, help='Path to input code directory')
    parser.add_argument('--output', type=str, help='Path to output documentation directory')
    parser.add_argument('--format', type=str, choices=['markdown', 'html'], 
                        help='Output documentation format')
    parser.add_argument('--model', type=str, help='LLM model to use')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    return parser.parse_args()

def main():
    """Main execution function"""
    # Parse arguments and load configuration
    args = parse_arguments()
    
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file not found: {args.config}")
        print("Creating default configuration file...")
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(args.config), exist_ok=True)
        
        # Write default config
        default_config = {
            "project_name": "P&C Insurance Code Documentation",
            "project_description": "Automated documentation for P&C Insurance codebase",
            "input_dir": "data/input",
            "output_dir": "data/output",
            "template_dir": "config/templates",
            "log_file": "logs/auto_doc.log",
            "code_language": "python",
            "file_extensions": [".py", ".java"],
            "output_format": "markdown",
            "generate_index": True,
            "include_examples": True,
            "include_type_hints": True,
            "include_source_links": True,
            "llm": {
                "type": "llama",
                "model_path": "models/llama-2-7b-code-instruct.gguf",
                "context_length": 4096,
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": 1024,
                "cache_dir": "cache"
            },
            "prompt_templates": "config/prompt_templates.yaml"
        }
        
        with open(args.config, 'w') as file:
            yaml.dump(default_config, file, default_flow_style=False)
        
        config = default_config
    
    # Override config with command line arguments if provided
    if args.input:
        config['input_dir'] = args.input
    if args.output:
        config['output_dir'] = args.output
    if args.format:
        config['output_format'] = args.format
    if args.model:
        config['llm']['model_path'] = args.model
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(config.get('log_file', 'logs/auto_doc.log'))
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level, config.get('log_file'))
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting documentation generation at {datetime.now()}")
    
    # Ensure output directory exists
    ensure_dir(config['output_dir'])
    
    # Create prompt_templates.yaml if it doesn't exist
    if not os.path.exists(config['prompt_templates']):
        logger.warning(f"Prompt templates file not found: {config['prompt_templates']}")
        logger.info("Creating default prompt templates file...")
        
        os.makedirs(os.path.dirname(config['prompt_templates']), exist_ok=True)
        
        default_prompts = {
            "class": "Generate documentation for this class: {name}\n\nCode:\n```python\n{code}\n```\n\nProvide a comprehensive explanation of this class's purpose in P&C insurance context.",
            "function": "Generate documentation for this function: {name}\n\nCode:\n```python\n{code}\n```\n\nProvide a comprehensive explanation with parameters and return values in P&C insurance context.",
            "module": "Generate documentation for this module:\n\nCode:\n```python\n{code}\n```\n\nProvide a comprehensive explanation of this module's purpose in P&C insurance context.",
            "variable": "Generate documentation for this variable: {name}\n\nCode:\n```python\n{code}\n```\n\nExplain the purpose and usage in P&C insurance context."
        }
        
        with open(config['prompt_templates'], 'w') as file:
            yaml.dump(default_prompts, file, default_flow_style=False)
        
        prompts = default_prompts
    else:
        # Load prompt templates
        with open(config['prompt_templates'], 'r') as file:
            prompts = yaml.safe_load(file)
    
    # Initialize components
    try:
        # Initialize code parser based on language
        parser_factory = CodeParserFactory()
        parser = parser_factory.get_parser(config['code_language'])
        
        # Initialize LLM
        llm_factory = LLMFactory()
        llm = llm_factory.get_llm(
            config['llm']['type'],
            model_path=config['llm']['model_path'],
            config=config['llm']
        )
        
        # Initialize documentation generator
        generator_factory = DocGeneratorFactory()
        doc_generator = generator_factory.get_generator(
            config['output_format'],
            output_dir=config['output_dir'],
            template_dir=config.get('template_dir')
        )
        
        # Get all source files
        source_files = get_files_by_extension(
            config['input_dir'], 
            extensions=config['file_extensions']
        )
        
        logger.info(f"Found {len(source_files)} source files to process")
        
        # Process each file
        for file_path in source_files:
            logger.info(f"Processing file: {file_path}")
            
            # Parse code structure
            code_structure = parser.parse_file(file_path)
            
            # Generate documentation using the LLM
            documentation = {}
            
            # Process module documentation
            module_info = code_structure.get('module', {})
            module_code = module_info.get('code', '')
            module_name = module_info.get('name', os.path.basename(file_path))
            
            # Generate module documentation
            if module_code:
                prompt = prompts.get('module', '').format(
                    code=module_code,
                    name=module_name,
                    context=''
                )
                
                module_doc = llm.generate(prompt)
                module_info['documentation'] = module_doc
            
            documentation['module'] = module_info
            documentation['imports'] = code_structure.get('imports', [])
            
            # Process classes
            classes = []
            for cls in code_structure.get('classes', []):
                # Generate documentation for this class
                prompt = prompts.get('class', '').format(
                    code=cls.get('code', ''),
                    name=cls.get('name', ''),
                    context=cls.get('context', '')
                )
                
                doc_content = llm.generate(prompt)
                cls['documentation'] = doc_content
                
                # Process methods
                for method in cls.get('methods', []):
                    method_prompt = prompts.get('function', '').format(
                        code=method.get('code', ''),
                        name=method.get('name', ''),
                        context=method.get('context', '')
                    )
                    
                    method_doc = llm.generate(method_prompt)
                    method['documentation'] = method_doc
                
                # Process attributes
                for attr in cls.get('attributes', []):
                    attr_prompt = prompts.get('variable', '').format(
                        code=attr.get('code', ''),
                        name=attr.get('name', ''),
                        context=attr.get('context', '')
                    )
                    
                    attr_doc = llm.generate(attr_prompt)
                    attr['documentation'] = attr_doc
                
                classes.append(cls)
            
            documentation['classes'] = classes
            
            # Process functions
            functions = []
            for func in code_structure.get('functions', []):
                # Skip class methods (already processed)
                if func.get('class_name'):
                    continue
                
                # Generate documentation for this function
                prompt = prompts.get('function', '').format(
                    code=func.get('code', ''),
                    name=func.get('name', ''),
                    context=func.get('context', '')
                )
                
                doc_content = llm.generate(prompt)
                func['documentation'] = doc_content
                functions.append(func)
            
            documentation['functions'] = functions
            
            # Process variables
            variables = []
            for var in code_structure.get('variables', []):
                # Skip class attributes (already processed)
                if var.get('class_name'):
                    continue
                
                # Generate documentation for this variable
                prompt = prompts.get('variable', '').format(
                    code=var.get('code', ''),
                    name=var.get('name', ''),
                    context=var.get('context', '')
                )
                
                doc_content = llm.generate(prompt)
                var['documentation'] = doc_content
                variables.append(var)
            
            documentation['variables'] = variables
            
            # Generate the output documentation
            relative_path = os.path.relpath(file_path, config['input_dir'])
            doc_generator.generate(relative_path, documentation)
        
        # Generate index file if needed
        if config.get('generate_index', True):
            doc_generator.generate_index(config['project_name'], source_files)
        
        logger.info(f"Documentation generation completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())