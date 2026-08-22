"""
Arabic Preprocessing Module (الوحدة الرئيسية).
Provides Eastern/Western numeral conversion, text normalization,
Hijri date handling, Arabic field mapping, and MENA currency detection/parsing.
"""

from src.arabic.currencies import (
    ARABIC_CURRENCY_SYMBOLS,
    VAT_RATES,
    detect_currency,
    extract_currency_and_amount,
    format_arabic_currency,
    get_country_vat_rate,
    get_currency_symbol_arabic,
    is_valid_currency_code,
    parse_arabic_amount,
)
from src.arabic.field_mapper import (
    get_canonical_arabic_label,
    map_arabic_fields,
    map_arabic_label,
    map_line_item,
    map_line_item_key,
)
from src.arabic.hijri import (
    HijriMatch,
    detect_hijri_date,
    gregorian_to_hijri,
    hijri_to_gregorian,
    is_likely_hijri,
    parse_hijri_date_string,
    replace_hijri_with_gregorian,
)
from src.arabic.normalizer import (
    detect_language,
    extract_arabic_text_blocks,
    normalize_alef,
    normalize_arabic,
    normalize_arabic_punctuation,
    normalize_teh_marbuta,
    remove_tashkeel,
    remove_tatweel,
)
from src.arabic.numerals import (
    to_eastern_numerals,
    to_western_numerals,
)

__all__ = [
    # Numerals
    "to_western_numerals",
    "to_eastern_numerals",
    # Normalizer
    "remove_tashkeel",
    "remove_tatweel",
    "normalize_alef",
    "normalize_teh_marbuta",
    "normalize_arabic_punctuation",
    "normalize_arabic",
    "detect_language",
    "extract_arabic_text_blocks",
    # Hijri
    "HijriMatch",
    "detect_hijri_date",
    "hijri_to_gregorian",
    "gregorian_to_hijri",
    "replace_hijri_with_gregorian",
    "is_likely_hijri",
    "parse_hijri_date_string",
    # Field Mapper
    "map_arabic_label",
    "map_arabic_fields",
    "map_line_item_key",
    "map_line_item",
    "get_canonical_arabic_label",
    # Currencies
    "detect_currency",
    "parse_arabic_amount",
    "get_country_vat_rate",
    "get_currency_symbol_arabic",
    "format_arabic_currency",
    "extract_currency_and_amount",
    "is_valid_currency_code",
    "VAT_RATES",
    "ARABIC_CURRENCY_SYMBOLS",
]
