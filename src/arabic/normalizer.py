"""
Arabic Text Normalization and Language Detection Module.
Provides functions for normalizing Arabic text (Alef, Hamza, Tashkeel, Tatweel, Punctuation)
and detecting language script distribution (Arabic-first policy).
"""

import re
import unicodedata
from typing import List, Optional

# Regular expressions for Arabic characters and diacritics
TASHKEEL_REGEX = re.compile(r"[\u0617-\u061A\u064B-\u065F\u0670]")
TATWEEL_REGEX = re.compile(r"\u0640")

# Arabic Alef variations mapped to plain Alef (ا)
ALEF_VARIATIONS_REGEX = re.compile(r"[\u0622\u0623\u0625\u0671]")  # آ, أ, إ, ٱ -> ا

# Alef Maqsura (ى) to Ya (ي)
ALEF_MAQSURA_REGEX = re.compile(r"\u0649")  # ى -> ي

# Teh Marbuta (ة) to Heh (ه)
TEH_MARBUTA_REGEX = re.compile(r"\u0629")  # ة -> ه

# Arabic Unicode range regex for script identification
ARABIC_CHAR_REGEX = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
LATIN_CHAR_REGEX = re.compile(r"[a-zA-Z]")

# Arabic punctuation translation table
ARABIC_PUNCTUATION_TABLE = str.maketrans({
    "،": ",",
    "؛": ";",
    "؟": "?",
    "٪": "%",
    "٫": ".",
    "٬": ",",
})


def remove_tashkeel(text: str) -> str:
    """
    Strips all Arabic diacritical marks (Tashkeel / Harakat):
    fatha, damma, kasra, tanween, sukun, shadda, etc.
    """
    if not text:
        return text
    return TASHKEEL_REGEX.sub("", text)


def remove_tatweel(text: str) -> str:
    """
    Strips Arabic kashida / tatweel (ـ) elongation characters.
    """
    if not text:
        return text
    return TATWEEL_REGEX.sub("", text)


def normalize_alef(text: str) -> str:
    """
    Normalizes all variations of Alef (أ, إ, آ, ٱ) into a bare Alef (ا).
    """
    if not text:
        return text
    return ALEF_VARIATIONS_REGEX.sub("ا", text)


def normalize_alef_maqsura(text: str) -> str:
    """
    Normalizes Alef Maqsura (ى) to standard Dotless/Dotted Ya (ي).
    """
    if not text:
        return text
    return ALEF_MAQSURA_REGEX.sub("ي", text)


def normalize_teh_marbuta(text: str) -> str:
    """
    Converts Teh Marbuta (ة) to Heh (ه).
    """
    if not text:
        return text
    return TEH_MARBUTA_REGEX.sub("ه", text)


def normalize_arabic_punctuation(text: str) -> str:
    """
    Converts Arabic punctuation marks (،, ؛, ؟, ٪, ٫, ٬) to Western equivalents.
    """
    if not text:
        return text
    return text.translate(ARABIC_PUNCTUATION_TABLE)


def contains_arabic(text: str) -> bool:
    """
    Checks if the given text contains any Arabic characters.
    """
    if not text:
        return False
    return bool(ARABIC_CHAR_REGEX.search(text))


def normalize_arabic(
    text: str,
    strip_tashkeel: bool = True,
    strip_tatweel: bool = True,
    norm_alef: bool = True,
    norm_alef_maqsura: bool = True,
    norm_teh_marbuta: bool = False,
    norm_punctuation: bool = True,
) -> str:
    """
    Full Arabic text normalization pipeline.

    Args:
        text (str): Input text containing Arabic or mixed characters.
        strip_tashkeel (bool): Remove diacritics (Harakat). Defaults to True.
        strip_tatweel (bool): Remove kashida elongation. Defaults to True.
        norm_alef (bool): Convert أ/إ/آ/ٱ to ا. Defaults to True.
        norm_alef_maqsura (bool): Convert ى to ي. Defaults to True.
        norm_teh_marbuta (bool): Convert ة to ه. Defaults to False (preserves spelling).
        norm_punctuation (bool): Convert Arabic punctuation to Western. Defaults to True.

    Returns:
        str: Normalized text.
    """
    if not text:
        return text

    # Standard Unicode NFC normalization first
    result = unicodedata.normalize("NFC", str(text))

    if strip_tashkeel:
        result = remove_tashkeel(result)

    if strip_tatweel:
        result = remove_tatweel(result)

    if norm_alef:
        result = normalize_alef(result)

    if norm_alef_maqsura:
        result = normalize_alef_maqsura(result)

    if norm_teh_marbuta:
        result = normalize_teh_marbuta(result)

    if norm_punctuation:
        result = normalize_arabic_punctuation(result)

    return result


def detect_language(text: str) -> str:
    """
    Detects the dominant script/language of the text: "ar", "en", or "mixed".
    
    Arabic-First Policy:
    - If both Arabic and Latin characters are present with substantial ratio -> "mixed"
    - If only Arabic characters present -> "ar"
    - If only Latin characters present -> "en"
    - If ambiguous, empty, or purely numerical -> defaults to "ar"
    
    Args:
        text (str): Input text to analyze.
        
    Returns:
        str: "ar", "en", or "mixed"
    """
    if not text or not text.strip():
        return "ar"

    arabic_chars = len(ARABIC_CHAR_REGEX.findall(text))
    latin_chars = len(LATIN_CHAR_REGEX.findall(text))
    total_letters = arabic_chars + latin_chars

    if total_letters == 0:
        # Ambiguous / only numbers or symbols -> Arabic-first default
        return "ar"

    arabic_ratio = arabic_chars / total_letters
    latin_ratio = latin_chars / total_letters

    if arabic_chars > 0 and latin_chars > 0:
        # If both exist and each represents at least 15% of alphabetical content -> mixed
        if arabic_ratio >= 0.15 and latin_ratio >= 0.15:
            return "mixed"
        elif arabic_ratio > latin_ratio:
            return "ar"
        else:
            return "en"

    if arabic_chars > 0:
        return "ar"

    return "en"


def extract_arabic_text_blocks(text: str) -> List[str]:
    """
    Extracts continuous blocks/sequences of Arabic text from mixed content.
    
    Args:
        text (str): The input text.
        
    Returns:
        List[str]: List of continuous Arabic segments stripped of leading/trailing whitespace.
    """
    if not text:
        return []

    # Matches continuous sequences of Arabic characters and internal spaces/diacritics
    arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+(?:\s+[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+)*")
    matches = arabic_pattern.findall(text)
    return [m.strip() for m in matches if m.strip()]
