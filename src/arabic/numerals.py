"""
Module for handling conversion between Eastern Arabic numerals and standard Western numerals.
"""

# Eastern Arabic Numerals used primarily in Egypt and Levant
EASTERN_ARABIC_NUMERALS = "٠١٢٣٤٥٦٧٨٩"

# Persian/Urdu variants of Eastern Arabic Numerals (sometimes encountered in diverse MENA environments)
PERSIAN_NUMERALS = "۰۱۲۳۴۵۶۷۸۹"

WESTERN_NUMERALS = "0123456789"

# Translation tables
_TO_WESTERN_TABLE = str.maketrans(
    EASTERN_ARABIC_NUMERALS + PERSIAN_NUMERALS,
    WESTERN_NUMERALS + WESTERN_NUMERALS,
)

_TO_EASTERN_TABLE = str.maketrans(
    WESTERN_NUMERALS,
    EASTERN_ARABIC_NUMERALS,
)


def to_western_numerals(text: str) -> str:
    """
    Converts Eastern Arabic and Persian numerals in a string to Western numerals.
    Leaves other characters intact.
    
    Args:
        text (str): The input string containing mixed text and numerals.
        
    Returns:
        str: The converted string with Western numerals.
    """
    if not text:
        return text
    return str(text).translate(_TO_WESTERN_TABLE)


def to_eastern_numerals(text: str) -> str:
    """
    Converts Western numerals in a string to Eastern Arabic numerals.
    Leaves other characters intact.
    
    Args:
        text (str): The input string containing mixed text and numerals.
        
    Returns:
        str: The converted string with Eastern Arabic numerals.
    """
    if not text:
        return text
    return str(text).translate(_TO_EASTERN_TABLE)
