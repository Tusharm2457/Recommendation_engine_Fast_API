"""
Helper utilities for Phase 3 rulesets.
"""

from typing import Tuple, Any


def parse_yes_no_with_followup(data: Any) -> Tuple[bool, str]:
    """
    Parse yes/no question with optional followup text.
    
    This is a standardized helper for fields that follow the pattern:
    1. Yes/No question
    2. If Yes, free-text followup
    
    Supported formats:
    - String: "Yes; Melatonin 3mg, helps with sleep"
    - String: "No"
    - Dict (legacy): {"answer": "Yes", "followup": "Melatonin 3mg"}
    
    Args:
        data: Input data (string or dict)
    
    Returns:
        Tuple of (is_yes: bool, followup_text: str)
        - is_yes: True if answer is "Yes", False otherwise
        - followup_text: The followup text (empty string if No or not provided)
    
    Examples:
        >>> parse_yes_no_with_followup("Yes; Melatonin 3mg")
        (True, "Melatonin 3mg")
        
        >>> parse_yes_no_with_followup("No")
        (False, "")
        
        >>> parse_yes_no_with_followup({"answer": "Yes", "followup": "Melatonin"})
        (True, "Melatonin")
    """
    is_yes = False
    followup_text = ""
    
    if isinstance(data, dict):
        # Legacy dict format
        answer = str(data.get("answer", "")).strip().lower()
        is_yes = answer in ["yes", "y", "true", "1"]
        
        if is_yes:
            followup_text = str(data.get("followup", "")).strip()
    
    elif isinstance(data, str):
        # String format
        data_str = data.strip()
        
        # Try to split by common separators
        if ";" in data_str:
            parts = data_str.split(";", 1)
            answer = parts[0].strip().lower()
            is_yes = answer in ["yes", "y", "true", "1"]
            
            if is_yes and len(parts) > 1:
                followup_text = parts[1].strip()
        
        elif "," in data_str:
            parts = data_str.split(",", 1)
            answer = parts[0].strip().lower()
            is_yes = answer in ["yes", "y", "true", "1"]
            
            if is_yes and len(parts) > 1:
                followup_text = parts[1].strip()
        
        else:
            # No separator - just yes/no
            answer = data_str.lower()
            is_yes = answer in ["yes", "y", "true", "1"]
    
    return is_yes, followup_text

