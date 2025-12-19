"""
Text Processing Utilities

Helper functions for processing free-text responses in Phase 3 rulesets.
"""

import re
from typing import List


def split_by_delimiters(text: str, delimiters: List[str] = None) -> List[str]:
    """
    Split text by multiple delimiters and return non-empty items.
    
    Args:
        text: The text to split
        delimiters: List of delimiter strings (default: [',', ';', '\n', '|'])
    
    Returns:
        List of non-empty, stripped strings
    
    Examples:
        >>> split_by_delimiters("weight loss, better sleep; more energy")
        ['weight loss', 'better sleep', 'more energy']
        
        >>> split_by_delimiters("goal1|goal2|goal3", delimiters=['|'])
        ['goal1', 'goal2', 'goal3']
    """
    if not text:
        return []
    
    if delimiters is None:
        delimiters = [',', ';', '\n', '|', '•', '-']
    
    # Create regex pattern from delimiters
    # Escape special regex characters
    escaped_delimiters = [re.escape(d) for d in delimiters]
    pattern = '|'.join(escaped_delimiters)
    
    # Split by any delimiter
    items = re.split(pattern, text)
    
    # Clean up: strip whitespace, remove empty strings, remove numbering
    cleaned_items = []
    for item in items:
        item = item.strip()
        # Remove leading numbers like "1.", "2)", etc.
        item = re.sub(r'^\d+[\.\)]\s*', '', item)
        if item:
            cleaned_items.append(item)
    
    return cleaned_items

