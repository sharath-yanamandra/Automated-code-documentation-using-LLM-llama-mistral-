"""
File Utility Functions
"""
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def get_files_by_extension(directory: str, extensions: List[str]) -> List[str]:
    """
    Get all files with specific extensions in a directory (recursive)
    
    Args:
        directory (str): Directory to search
        extensions (list): List of file extensions to include
        
    Returns:
        list: List of file paths
    """
    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    # Normalize extensions
    normalized_exts = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]
    logger.debug(f"Looking for files with extensions: {normalized_exts}")
    
    files = []
    
    # Walk through directory
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext.lower() in normalized_exts:
                file_path = os.path.join(root, filename)
                files.append(file_path)
    
    logger.debug(f"Found {len(files)} files with specified extensions")
    return files

def ensure_dir(directory: str) -> None:
    """
    Ensure a directory exists, create it if it doesn't
    
    Args:
        directory (str): Directory path
    """
    if not os.path.exists(directory):
        logger.debug(f"Creating directory: {directory}")
        os.makedirs(directory, exist_ok=True)

def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Read a file and return its contents
    
    Args:
        file_path (str): Path to the file
        encoding (str): File encoding
        
    Returns:
        str or None: File contents or None if error
    """
    if not os.path.exists(file_path):
        logger.warning(f"File does not exist: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None

def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Write content to a file
    
    Args:
        file_path (str): Path to the file
        content (str): Content to write
        encoding (str): File encoding
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        directory = os.path.dirname(file_path)
        if directory:
            ensure_dir(directory)
        
        with open(file_path, 'w', encoding=encoding) as file:
            file.write(content)
        
        logger.debug(f"Successfully wrote to file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {str(e)}")
        return False

def copy_file(src_path: str, dst_path: str) -> bool:
    """
    Copy a file from source to destination
    
    Args:
        src_path (str): Source file path
        dst_path (str): Destination file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    import shutil
    
    if not os.path.exists(src_path):
        logger.warning(f"Source file does not exist: {src_path}")
        return False
    
    try:
        # Ensure destination directory exists
        directory = os.path.dirname(dst_path)
        if directory:
            ensure_dir(directory)
        
        shutil.copy2(src_path, dst_path)
        logger.debug(f"Successfully copied {src_path} to {dst_path}")
        return True
    except Exception as e:
        logger.error(f"Error copying file from {src_path} to {dst_path}: {str(e)}")
        return False

def get_relative_path(file_path: str, base_dir: str) -> str:
    """
    Get the relative path of a file to a base directory
    
    Args:
        file_path (str): File path
        base_dir (str): Base directory
        
    Returns:
        str: Relative path
    """
    return os.path.relpath(file_path, base_dir)

def get_file_size(file_path: str) -> Optional[int]:
    """
    Get the size of a file in bytes
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        int or None: File size in bytes or None if error
    """
    if not os.path.exists(file_path):
        logger.warning(f"File does not exist: {file_path}")
        return None
    
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {str(e)}")
        return None