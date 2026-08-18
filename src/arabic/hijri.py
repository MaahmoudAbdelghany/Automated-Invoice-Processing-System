"""
Hijri Date Detection and Gregorian Conversion Module.
Provides functions for detecting Hijri dates in various Arabic and numeric formats,
converting them to Gregorian ISO dates (and vice-versa), and handling MENA invoice date standards.
"""

import datetime
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

try:
    from hijridate import Gregorian, Hijri
except ImportError:
    from hijri_converter import Gregorian, Hijri  # type: ignore

from src.arabic.normalizer import normalize_arabic
from src.arabic.numerals import to_western_numerals

# Heuristic bounds for identifying Hijri vs Gregorian years
HIJRI_YEAR_MIN = 1300
HIJRI_YEAR_MAX = 1500
GREGORIAN_YEAR_MIN = 1900
GREGORIAN_YEAR_MAX = 2100

# Base definitions for all 12 Hijri months and their diverse spelling variations
_BASE_MONTH_VARIATIONS: Dict[int, List[str]] = {
    1: ["محرم", "المحرم"],
    2: ["صفر", "الصفر"],
    3: ["ربيع الأول", "ربيع الاول", "ربيع أول", "ربيع اول", "ربيع 1", "ربيع ١"],
    4: [
        "ربيع الثاني",
        "ربيع الآخر",
        "ربيع الاخر",
        "ربيع الآخرة",
        "ربيع الاخرة",
        "ربيع الاخره",
        "ربيع ثان",
        "ربيع ثاني",
        "ربيع اخير",
        "ربيع 2",
        "ربيع ٢",
    ],
    5: [
        "جمادى الأولى",
        "جمادى الاولى",
        "جمادي الاولي",
        "جمادي الأولى",
        "جمادي الاولى",
        "جمادى اول",
        "جمادي اول",
        "جمادى أول",
        "جمادي أول",
        "جمادى 1",
        "جمادى ١",
    ],
    6: [
        "جمادى الآخرة",
        "جمادى الاخرة",
        "جمادى الاخره",
        "جمادي الاخره",
        "جمادي الآخرة",
        "جمادي الاخرة",
        "جمادى الثانية",
        "جمادى الثانيه",
        "جمادي الثاني",
        "جمادي الثانيه",
        "جمادي الثانية",
        "جمادى 2",
        "جمادى ٢",
    ],
    7: ["رجب", "الرجب"],
    8: ["شعبان", "الشعبان"],
    9: ["رمضان", "شهر رمضان المبارك", "الرمضان"],
    10: ["شوال", "الشوال"],
    11: [
        "ذو القعدة",
        "ذو القعده",
        "ذي القعدة",
        "ذي القعده",
        "ذوالقعدة",
        "ذوالقعده",
    ],
    12: [
        "ذو الحجة",
        "ذو الحجه",
        "ذي الحجة",
        "ذي الحجه",
        "ذوالحجة",
        "ذوالحجه",
    ],
}


def _build_month_dictionary_and_regex() -> Tuple[Dict[str, int], str]:
    """
    Constructs a comprehensive lookup map and matching regex for all Hijri month variations.
    Includes variations prefixed with 'شهر' (Month of).
    """
    lookup: Dict[str, int] = {}

    for month_num, variations in _BASE_MONTH_VARIATIONS.items():
        for var in variations:
            lookup[var] = month_num
            lookup[f"شهر {var}"] = month_num
            # Also store normalized version for robust lookup
            norm = normalize_arabic(
                var,
                strip_tashkeel=True,
                strip_tatweel=True,
                norm_alef=True,
                norm_alef_maqsura=True,
                norm_teh_marbuta=True,
            )
            lookup[norm] = month_num
            lookup[f"شهر {norm}"] = month_num

    # Sort descending by length so longer patterns (e.g. 'ربيع الأول') match before shorter ('ربيع')
    sorted_patterns = sorted(lookup.keys(), key=len, reverse=True)
    escaped_patterns = [re.escape(p) for p in sorted_patterns]
    regex_pattern = r"(?:" + "|".join(escaped_patterns) + r")"

    return lookup, regex_pattern


HIJRI_MONTH_MAP, _MONTH_PATTERN = _build_month_dictionary_and_regex()

# Regex pattern matching any Arabic, Eastern, or Western digit
_DIGIT_CHAR = r"[\d\u0660-\u0669\u06F0-\u06F9]"

# Textual Hijri date regex: e.g. "15 صفر 1446", "١٥ محرم ١٤٤٦ هـ", "15 من ربيع الأول 1446"
_TEXTUAL_HIJRI_REGEX = re.compile(
    rf"(?P<day>{_DIGIT_CHAR}{{1,2}})\s+(?:من\s+)?(?P<month>{_MONTH_PATTERN})\s+(?P<year>{_DIGIT_CHAR}{{4}})(?:\s*(?P<suffix>هـ|ه\b|AH|H))?",
    re.IGNORECASE,
)

# Numeric YYYY/MM/DD regex: e.g. "1446/02/15", "١٤٤٦-٠٢-١٥", "1446.02.15"
_NUMERIC_HIJRI_YMD_REGEX = re.compile(
    rf"(?P<year>{_DIGIT_CHAR}{{4}})[\/\.\-](?P<month>{_DIGIT_CHAR}{{1,2}})[\/\.\-](?P<day>{_DIGIT_CHAR}{{1,2}})(?:\s*(?P<suffix>هـ|ه\b|AH|H))?"
)

# Numeric DD/MM/YYYY regex: e.g. "15/02/1446", "١٥-٠٢-١٤٤٦", "15.02.1446"
_NUMERIC_HIJRI_DMY_REGEX = re.compile(
    rf"(?P<day>{_DIGIT_CHAR}{{1,2}})[\/\.\-](?P<month>{_DIGIT_CHAR}{{1,2}})[\/\.\-](?P<year>{_DIGIT_CHAR}{{4}})(?:\s*(?P<suffix>هـ|ه\b|AH|H))?"
)


@dataclass(frozen=True)
class HijriMatch:
    """Represents a detected Hijri date match within text."""
    original_text: str
    hijri_year: int
    hijri_month: int
    hijri_day: int
    gregorian_date: datetime.date
    gregorian_iso: str
    start_pos: int
    end_pos: int


def is_likely_hijri(year: int) -> bool:
    """
    Heuristic check to determine if a 4-digit year is in the Hijri range.
    Years between 1300 and 1500 are considered Hijri.
    Years between 1900 and 2100 are considered Gregorian.
    
    Args:
        year (int): The year to evaluate.
        
    Returns:
        bool: True if the year falls within the Hijri epoch window.
    """
    return HIJRI_YEAR_MIN <= year <= HIJRI_YEAR_MAX


def hijri_to_gregorian(year: int, month: int, day: int) -> datetime.date:
    """
    Converts a Hijri date (year, month, day) to a Python datetime.date (Gregorian).
    Handles edge cases like 30th day in 29-day Hijri months safely by clamping.
    
    Args:
        year (int): Hijri year (e.g., 1446)
        month (int): Hijri month (1-12)
        day (int): Hijri day (1-30)
        
    Returns:
        datetime.date: The corresponding Gregorian date.
        
    Raises:
        ValueError: If year/month are invalid or cannot be converted.
    """
    if not (HIJRI_YEAR_MIN <= year <= HIJRI_YEAR_MAX):
        raise ValueError(f"Hijri year {year} is outside supported range [{HIJRI_YEAR_MIN}, {HIJRI_YEAR_MAX}]")
    if not (1 <= month <= 12):
        raise ValueError(f"Hijri month {month} must be between 1 and 12")

    # Hijri months are either 29 or 30 days. Handle possible day overflow gracefully
    clamped_day = max(1, min(day, 30))
    
    try:
        greg_obj = Hijri(year, month, clamped_day).to_gregorian()
        return datetime.date(greg_obj.year, greg_obj.month, greg_obj.day)
    except (ValueError, OverflowError):
        # Fallback to day 29 if month has only 29 days
        if clamped_day == 30:
            greg_obj = Hijri(year, month, 29).to_gregorian()
            return datetime.date(greg_obj.year, greg_obj.month, greg_obj.day)
        raise


def gregorian_to_hijri(date_val: Union[datetime.date, datetime.datetime, str]) -> Tuple[int, int, int]:
    """
    Converts a Gregorian date to a Hijri date tuple (year, month, day).
    
    Args:
        date_val: Gregorian date as datetime.date, datetime.datetime, or ISO string (YYYY-MM-DD).
        
    Returns:
        Tuple[int, int, int]: (hijri_year, hijri_month, hijri_day)
    """
    if isinstance(date_val, str):
        date_val = datetime.date.fromisoformat(date_val.strip()[:10])
    elif isinstance(date_val, datetime.datetime):
        date_val = date_val.date()

    hijri_obj = Gregorian(date_val.year, date_val.month, date_val.day).to_hijri()
    return hijri_obj.year, hijri_obj.month, hijri_obj.day


def detect_hijri_date(text: str) -> List[HijriMatch]:
    """
    Scans text to detect Hijri dates in various formats (numeric and textual),
    converts Eastern numerals to Western, normalizes Arabic text, and converts
    each matched date into its Gregorian equivalent.
    
    Preserves exact character offsets (`start_pos`, `end_pos`) on the original text.
    
    Supported formats:
    - Textual Arabic months: `15 صفر 1446`, `١٥ محرم ١٤٤٦ هـ`, `15 من ربيع الأول 1446`
    - Numeric YYYY/MM/DD: `1446/02/15`, `١٤٤٦-٠٢-١٥`
    - Numeric DD/MM/YYYY: `15/02/1446`, `١٥/٠٢/١٤٤٦`
    
    Args:
        text (str): Input text (e.g. invoice OCR output).
        
    Returns:
        List[HijriMatch]: List of detected Hijri date matches with Gregorian conversions.
    """
    if not text:
        return []

    matches: List[HijriMatch] = []
    seen_spans: List[Tuple[int, int]] = []

    def _is_overlapping(start: int, end: int) -> bool:
        for s, e in seen_spans:
            if not (end <= s or start >= e):
                return True
        return False

    # 1. Match textual month names directly on raw text: "15 صفر 1446", "١٥ محرم ١٤٤٦ هـ"
    for match in _TEXTUAL_HIJRI_REGEX.finditer(text):
        start, end = match.span()
        if _is_overlapping(start, end):
            continue

        raw_day = match.group("day")
        raw_month = match.group("month")
        raw_year = match.group("year")

        day_val = int(to_western_numerals(raw_day))
        year_val = int(to_western_numerals(raw_year))

        # Look up month from exact match or normalized match
        month_val = HIJRI_MONTH_MAP.get(raw_month)
        if not month_val:
            norm_month = normalize_arabic(
                raw_month,
                strip_tashkeel=True,
                strip_tatweel=True,
                norm_alef=True,
                norm_alef_maqsura=True,
                norm_teh_marbuta=True,
            )
            month_val = HIJRI_MONTH_MAP.get(norm_month)

        if not month_val:
            continue

        if not is_likely_hijri(year_val):
            continue

        try:
            greg_date = hijri_to_gregorian(year_val, month_val, day_val)
            original_slice = text[start:end]
            matches.append(
                HijriMatch(
                    original_text=original_slice,
                    hijri_year=year_val,
                    hijri_month=month_val,
                    hijri_day=day_val,
                    gregorian_date=greg_date,
                    gregorian_iso=greg_date.isoformat(),
                    start_pos=start,
                    end_pos=end,
                )
            )
            seen_spans.append((start, end))
        except (ValueError, OverflowError):
            continue

    # 2. Match numeric YYYY/MM/DD Hijri dates: "1446/02/15", "١٤٤٦/٠٢/١٥"
    for match in _NUMERIC_HIJRI_YMD_REGEX.finditer(text):
        start, end = match.span()
        if _is_overlapping(start, end):
            continue

        raw_year = match.group("year")
        raw_month = match.group("month")
        raw_day = match.group("day")

        year_val = int(to_western_numerals(raw_year))
        month_val = int(to_western_numerals(raw_month))
        day_val = int(to_western_numerals(raw_day))

        if not is_likely_hijri(year_val):
            continue
        if not (1 <= month_val <= 12) or not (1 <= day_val <= 30):
            continue

        try:
            greg_date = hijri_to_gregorian(year_val, month_val, day_val)
            original_slice = text[start:end]
            matches.append(
                HijriMatch(
                    original_text=original_slice,
                    hijri_year=year_val,
                    hijri_month=month_val,
                    hijri_day=day_val,
                    gregorian_date=greg_date,
                    gregorian_iso=greg_date.isoformat(),
                    start_pos=start,
                    end_pos=end,
                )
            )
            seen_spans.append((start, end))
        except (ValueError, OverflowError):
            continue

    # 3. Match numeric DD/MM/YYYY Hijri dates: "15/02/1446", "١٥/٠٢/١٤٤٦"
    for match in _NUMERIC_HIJRI_DMY_REGEX.finditer(text):
        start, end = match.span()
        if _is_overlapping(start, end):
            continue

        raw_day = match.group("day")
        raw_month = match.group("month")
        raw_year = match.group("year")

        day_val = int(to_western_numerals(raw_day))
        month_val = int(to_western_numerals(raw_month))
        year_val = int(to_western_numerals(raw_year))

        if not is_likely_hijri(year_val):
            continue
        if not (1 <= month_val <= 12) or not (1 <= day_val <= 30):
            continue

        try:
            greg_date = hijri_to_gregorian(year_val, month_val, day_val)
            original_slice = text[start:end]
            matches.append(
                HijriMatch(
                    original_text=original_slice,
                    hijri_year=year_val,
                    hijri_month=month_val,
                    hijri_day=day_val,
                    gregorian_date=greg_date,
                    gregorian_iso=greg_date.isoformat(),
                    start_pos=start,
                    end_pos=end,
                )
            )
            seen_spans.append((start, end))
        except (ValueError, OverflowError):
            continue

    # Sort matches by position in text
    matches.sort(key=lambda m: m.start_pos)
    return matches


def replace_hijri_with_gregorian(
    text: str,
    template: str = "{original} ({gregorian})",
) -> str:
    """
    Finds all Hijri dates in text and appends/replaces them with Gregorian ISO equivalents.
    Preserves original text structure while providing Gregorian clarity for downstream models.
    
    Args:
        text (str): Input text containing Hijri dates.
        template (str): Format template with `{original}` and `{gregorian}` placeholders.
        
    Returns:
        str: Text with Gregorian conversions incorporated.
    """
    if not text:
        return text

    matches = detect_hijri_date(text)
    if not matches:
        return text

    # Process replacements in reverse order of position to avoid offset shifts
    result = text
    for match in reversed(matches):
        replacement = template.format(
            original=match.original_text,
            gregorian=match.gregorian_iso,
        )
        result = result[: match.start_pos] + replacement + result[match.end_pos :]

    return result


def parse_hijri_date_string(date_str: str) -> Optional[datetime.date]:
    """
    Attempts to parse a single string representing a Hijri date and returns the Gregorian date.
    
    Args:
        date_str (str): Date string (e.g. "1446/02/15", "15 صفر 1446", "١٤٤٦-٠٢-١٥").
        
    Returns:
        Optional[datetime.date]: Converted Gregorian date if valid Hijri date, else None.
    """
    if not date_str or not date_str.strip():
        return None

    matches = detect_hijri_date(date_str.strip())
    if matches:
        return matches[0].gregorian_date

    return None
