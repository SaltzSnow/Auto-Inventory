"""Text normalization utilities for Thai language."""
import re
from typing import Dict


# Common Thai word variations that should be normalized
THAI_WORD_VARIATIONS: Dict[str, str] = {
    # Strawberry variations - normalize to simplest form
    "สตรอว์เบอร์รี่": "สตอเบอรี่",
    "สตรอเบอร์รี่": "สตอเบอรี่",
    "สตอเบอร์รี่": "สตอเบอรี่",
    "สตรอเบอรี่": "สตอเบอรี่",
    "สตอว์เบอร์รี่": "สตอเบอรี่",
    "สตอเบอรี่": "สตอเบอรี่",
    "สตรอว์เบอรี่": "สตอเบอรี่",
    "สตรอเบอรี": "สตอเบอรี่",
    "สตอเบอร์รี": "สตอเบอรี่",
    
    # Blueberry variations
    "บลูเบอร์รี่": "บลูเบอรี่",
    "บลูเบอรี่": "บลูเบอรี่",
    
    # Tomato variations
    "มะเขือเทศ": "มะเขือเทศ",
    "มะเขือ": "มะเขือเทศ",
    
    # Corn variations
    "ข้าวโพดหวาน": "ข้าวโพด",
    "ข้าวโพดอ่อน": "ข้าวโพด",
    
    # Milk variations
    "นมสด": "นม",
    "นมจืด": "นม",
    "นมพาสเจอร์ไรส์": "นม",
    
    # Water variations
    "น้ำเปล่า": "น้ำดื่ม",
    "น้ำดื่ม": "น้ำดื่ม",
    "น้ำแร่": "น้ำดื่ม",
    
    # Coke variations
    "โค้ก": "โคก",
    "โค๊ก": "โคก",
    "โคก": "โคก",
    
    # Pepsi variations
    "เป๊ปซี่": "เปปซี่",
    "เป๊ปซี": "เปปซี่",
    "เปปซี": "เปปซี่",
}


def normalize_thai_text(text: str) -> str:
    """
    Normalize Thai text for better matching.
    
    This function:
    1. Removes extra whitespace
    2. Converts to lowercase for English characters
    3. Removes some punctuation marks (. , - etc)
    4. Normalizes common Thai word variations
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text
        
    Examples:
        >>> normalize_thai_text("สตรอว์เบอร์รี่ 500 กรัม")
        'สตอเบอรี 500 กรัม'
        >>> normalize_thai_text("โค้ก 325 มล.")
        'โคก 325 มล'
    """
    if not text:
        return ""
    
    # Remove leading/trailing whitespace and normalize internal whitespace
    normalized = " ".join(text.split())
    
    # Convert English to lowercase first
    normalized = normalized.lower()
    
    # Remove common punctuation marks that don't affect meaning
    # Keep Thai characters (including tone marks), English, numbers, and spaces
    normalized = re.sub(r'[.,\-_/\\()[\]{}!?@#$%^&*+=|~`"\'<>]', '', normalized)
    
    # Replace known variations with standard forms
    for variation, standard in THAI_WORD_VARIATIONS.items():
        # Case-insensitive replacement for English parts
        normalized = normalized.replace(variation.lower(), standard.lower())
    
    # Remove extra whitespace again after cleaning
    normalized = " ".join(normalized.split())
    
    return normalized


def add_word_variation(variation: str, standard: str) -> None:
    """
    Add a new word variation to the normalization dictionary.
    
    This allows dynamic addition of new variations at runtime.
    
    Args:
        variation: The variation to normalize
        standard: The standard form to normalize to
        
    Example:
        >>> add_word_variation("สตรอเบอรี่", "สตอเบอรี่")
    """
    THAI_WORD_VARIATIONS[variation] = standard


def get_all_variations() -> Dict[str, str]:
    """
    Get all registered word variations.
    
    Returns:
        Dictionary of variations and their standard forms
    """
    return THAI_WORD_VARIATIONS.copy()
