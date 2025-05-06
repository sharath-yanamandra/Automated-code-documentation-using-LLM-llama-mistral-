# Automated-code-documentation-using-LLM-llama-mistral-models
# Automated Code Documentation Generator for P&C Insurance

A specialized documentation generator that uses local Large Language Models (LLMs) to automatically create comprehensive documentation for Property & Casualty (P&C) insurance codebases.

## Overview

This tool analyzes Python and Java source code, extracts the structure (classes, functions, parameters, etc.), and uses a local LLM to generate insurance domain-specific documentation. The system is designed to run entirely offline, without requiring API calls to external services.

## Features

- **Code Analysis**: Automatically extracts code structure from Python and Java files
- **Domain-Specific Documentation**: Generates documentation with P&C insurance context and terminology
- **Local LLM Integration**: Uses offline models (Mistral, Llama) for faster, more private operation
- **Multiple Output Formats**: Generates documentation in Markdown or HTML
- **Extensible Architecture**: Modular design for adding new languages or output formats

## Requirements

- Python 3.8 or higher
- 8GB+ RAM (for running the LLM)
- LLM model file (e.g., Mistral 7B instruct model)
- Please download the Mistral 7B model from "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF" and paste the model into the folder named models.
- Required Python packages (see Installation section)

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/auto-doc-generator.git
cd auto-doc-generator
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Download the model file**

Download a compatible GGUF model file and place it in the `models/` directory. This project is configured to use Mistral 7B, but you can use any compatible model:

- Mistral 7B Instruct: [mistral-7b-instruct-v0.1.Q2_K.gguf](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF)
- Other options: [Llama 2 Code](https://huggingface.co/TheBloke/Llama-2-7B-GGUF)

5. **Create required directories**

```bash
mkdir -p models config/templates data/input data/output cache logs
```

## Project Structure

```
auto-doc-generator/
├── config/                 # Configuration files
│   ├── config.yaml         # Main configuration
│   ├── prompt_templates.yaml  # LLM prompting templates
│   └── templates/          # Documentation templates
├── data/
│   ├── input/              # Place source code here
│   └── output/             # Generated documentation
├── models/                 # LLM model files
├── src/                    # Source code
│   ├── code_parser/        # Code parsing components
│   │   ├── parser.py       # Parser interface
│   │   ├── python_parser.py # Python language parser
│   │   └── java_parser.py  # Java language parser
│   ├── doc_generator/      # Documentation generator
│   │   ├── generator.py    # Generator interface
│   │   ├── markdown_gen.py # Markdown generator
│   │   └── html_gen.py     # HTML generator
│   ├── llm/                # LLM integration
│   │   ├── llm_interface.py # LLM interface
│   │   ├── llama_handler.py # Llama integration
│   │   └── mistral_handler.py # Mistral integration
│   ├── utils/              # Utilities
│   │   ├── file_utils.py   # File handling utilities
│   │   └── logging_utils.py # Logging utilities
│   └── main.py             # Main entry point
├── examples/               # Example P&C insurance code
│   └── claims_processor/   # Example claims processing module
├── requirements.txt        # Dependencies
├── setup.py                # Package setup
└── README.md               # This file
```

## Usage

### Basic Usage

To generate documentation for your code:

1. Place your Python or Java files in the `data/input` directory
2. Run the generator:

```bash
python -m src.main
```

The documentation will be generated in the `data/output` directory.

### Command Line Options

```
python -m src.main [OPTIONS]

Options:
  --config CONFIG        Path to configuration file
  --input INPUT          Path to input code directory
  --output OUTPUT        Path to output documentation directory
  --format {markdown,html}  Output documentation format
  --model MODEL          Path to LLM model file
  --verbose              Enable verbose logging
```

### Examples

Generate documentation for a specific file:

```bash
python -m src.main --input data/input/mini_insurance.py --output docs/mini
```

Generate HTML documentation:

```bash
python -m src.main --format html
```

Use verbose logging for troubleshooting:

```bash
python -m src.main --verbose
```

## Component Descriptions

### Code Parsers

- **parser.py**: Base interface for all code parsers
- **python_parser.py**: Extracts classes, functions, parameters, and docstrings from Python files using the AST module
- **java_parser.py**: Extracts structure from Java files using regex patterns

### LLM Integration

- **llm_interface.py**: Abstract interface for integrating with different LLM backends
- **llama_handler.py**: Integration with Llama models using llama-cpp-python
- **mistral_handler.py**: Integration with Mistral models using ctransformers

### Documentation Generators

- **generator.py**: Base interface for documentation generators
- **markdown_gen.py**: Generates Markdown documentation
- **html_gen.py**: Generates HTML documentation with CSS styling

### Utilities

- **file_utils.py**: Utilities for file operations (reading, writing, finding files)
- **logging_utils.py**: Logging configuration and utilities

### Main Application

- **main.py**: Entry point that orchestrates the documentation generation process

## Configuration

The system is configured through YAML files in the `config` directory:

### config.yaml

The main configuration file defines input/output paths, LLM settings, and more:

```yaml
# Project information
project_name: "P&C Insurance Code Documentation"

# Directories
input_dir: "data/input"
output_dir: "data/output"
template_dir: "config/templates"
log_file: "logs/auto_doc.log"

# Files to process
code_language: "python"  # supported: python, java
file_extensions: [".py", ".java"]

# Documentation options
output_format: "markdown"  # supported: markdown, html

# LLM Configuration
llm:
  type: "mistral"  # supported: llama, mistral
  model_path: "models/mistral-7b-instruct-v0.1.Q2_K.gguf"
  context_length: 4096
  temperature: 0.2
  top_p: 0.9
  max_tokens: 1024
  cache_dir: "cache"
```

### prompt_templates.yaml

Defines prompts for different code elements:

```yaml
class: "Generate documentation for this class: {name}\n\nCode:\n```python\n{code}\n```\n\nProvide a comprehensive explanation of this class's purpose in P&C insurance context."
function: "Generate documentation for this function: {name}\n\nCode:\n```python\n{code}\n```\n\nProvide a comprehensive explanation with parameters and return values in P&C insurance context."
module: "Generate documentation for this module:\n\nCode:\n```python\n{code}\n```\n\nProvide a comprehensive explanation of this module's purpose in P&C insurance context."
variable: "Generate documentation for this variable: {name}\n\nCode:\n```python\n{code}\n```\n\nExplain the purpose and usage in P&C insurance context."
```

## Troubleshooting

### Token Length Errors

If you see "Number of tokens exceeded maximum context length" warnings:

1. Use smaller input files (mini_insurance.py is a good example)
2. Increase the context_length in config.yaml if your hardware supports it:
   ```yaml
   llm:
     context_length: 8192  # Increase if your hardware allows
   ```
3. Process files individually rather than entire directories

### Model Loading Issues

If you have trouble loading the model:

1. Ensure the model file exists in the models directory
2. Check you have the correct packages installed:
   ```bash
   pip install ctransformers  # For Mistral models
   # or
   pip install llama-cpp-python  # For Llama models
   ```
3. Try a smaller quantized model (Q4_0 or Q2_K versions) if memory is limited

### Template Issues

If you see template warnings:

1. Ensure the `config/templates` directory exists
2. Check that template files match the expected names (file.md, index.md, etc.)
3. The system will auto-create default templates if they're missing

## Models

This system is designed to work with multiple LLM backends, but has been primarily tested with:

### Mistral 7B Instruct

- **File**: mistral-7b-instruct-v0.1.Q2_K.gguf
- **Size**: ~4GB
- **Quantization**: 2-bit (Q2_K) for efficient memory usage
- **Context Length**: 4096 tokens by default
- **Strengths**: Good understanding of code, efficient operation
- **Source**: [HuggingFace - TheBloke/Mistral-7B-Instruct-v0.1-GGUF](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF)

### Alternative: Llama 2 7B Code

- **File**: llama-2-7b-code-instruct.gguf
- **Size**: ~4GB
- **Quantization**: 4-bit (Q4_0) recommended
- **Context Length**: 4096 tokens by default
- **Strengths**: Specialized for code understanding
- **Source**: [HuggingFace - TheBloke/Llama-2-7B-GGUF](https://huggingface.co/TheBloke/Llama-2-7B-GGUF)

## Performance Considerations

- **Memory Usage**: 4-8GB RAM depending on model size and quantization
- **Processing Time**: 15-30 seconds per file on CPU (faster with GPU)
- **GPU Acceleration**: Enabled by setting `gpu_layers` in config.yaml
- **Caching**: Generated documentation is cached to avoid repeated processing

## Contributing

Contributions are welcome! Here are some areas where the project could be extended:

1. Additional language parsers (C#, JavaScript, etc.)
2. Support for more LLM backends
3. Additional output formats (PDF, DocBook, etc.)
4. Improved prompt templates for specific P&C insurance domains
5. Integration with development tools and IDEs
