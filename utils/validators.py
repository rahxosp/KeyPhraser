import re
from typing import Tuple, Optional

def validate_shortcut(shortcut: str) -> Tuple[bool, Optional[str]]:
    """Validate shortcut string"""
    if not shortcut:
        return False, "Shortcut cannot be empty"
        
    if len(shortcut) > 50:
        return False, "Shortcut must be less than 50 characters"
        
    # Check for valid characters
    if not re.match(r'^[\w-]+$', shortcut):
        return False, "Shortcut can only contain letters, numbers, and hyphens"
        
    return True, None

def validate_content(content: str) -> Tuple[bool, Optional[str]]:
    """Validate content string"""
    if not content:
        return False, "Content cannot be empty"
        
    if len(content) > 10000:
        return False, "Content must be less than 10,000 characters"
        
    return True, None

def validate_file_path(path: str) -> Tuple[bool, Optional[str]]:
    """Validate file path"""
    if not path:
        return False, "Path cannot be empty"
        
    # Check for invalid characters
    invalid_chars = '<>:"|?*'
    if any(char in path for char in invalid_chars):
        return False, "Path contains invalid characters"
        
    # Check path length
    if len(path) > 260:
        return False, "Path is too long"
        
    return True, None

def validate_json_data(data: dict) -> Tuple[bool, Optional[str]]:
    """Validate JSON data structure"""
    required_fields = ['keyword', 'replacement']
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
            
    # Validate field types
    if not isinstance(data['keyword'], str):
        return False, "Keyword must be a string"
        
    if not isinstance(data['replacement'], str):
        return False, "Replacement must be a string"
        
    # Validate field contents
    valid, error = validate_shortcut(data['keyword'])
    if not valid:
        return False, f"Invalid keyword: {error}"
        
    valid, error = validate_content(data['replacement'])
    if not valid:
        return False, f"Invalid replacement: {error}"
        
    return True, None
