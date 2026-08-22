"""
MENA and International Currency Detection, Parsing, and Formatting Module.
Provides robust detection of Arabic and Latin currency symbols/names,
parsing of Arabic/mixed amount representations to Python Decimal,
and standard VAT rates for target Middle East markets.
"""

from decimal import Decimal, InvalidOperation
import re
from typing import Dict, List, Optional, Tuple, Union

from src.arabic.normalizer import normalize_arabic
from src.arabic.numerals import to_eastern_numerals, to_western_numerals

# Standard VAT Rates for MENA countries (as percentage)
VAT_RATES: Dict[str, Decimal] = {
    "SAR": Decimal("15.0"),  # Saudi Arabia (ZATCA standard)
    "AED": Decimal("5.0"),   # UAE (FTA standard)
    "EGP": Decimal("14.0"),  # Egypt (ETA standard)
    "BHD": Decimal("10.0"),  # Bahrain (NBR standard)
    "OMR": Decimal("5.0"),   # Oman (OTA standard)
    "JOD": Decimal("16.0"),  # Jordan (ISTD standard)
    "KWD": Decimal("0.0"),   # Kuwait (No VAT currently)
    "QAR": Decimal("0.0"),   # Qatar (No VAT currently)
    "USD": Decimal("0.0"),
    "EUR": Decimal("0.0"),
    "GBP": Decimal("0.0"),
}

# Arabic Currency Display Symbols (canonical)
ARABIC_CURRENCY_SYMBOLS: Dict[str, str] = {
    "SAR": "ر.س",
    "AED": "د.إ",
    "EGP": "ج.م",
    "KWD": "د.ك",
    "QAR": "ر.ق",
    "BHD": "د.ب",
    "OMR": "ر.ع",
    "JOD": "د.أ",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}

# Unicode boundary anchors for Arabic and Latin words/symbols
_AR_L = r"(?<![\u0600-\u06FF\w])"
_AR_R = r"(?![\u0600-\u06FF\w])"
_LAT_L = r"(?<![A-Za-z])"
_LAT_R = r"(?![A-Za-z])"


# Currency metadata definition
class CurrencyInfo:
    """Metadata container for currency definitions."""
    def __init__(
        self,
        code: str,
        country: str,
        arabic_symbol: str,
        arabic_name: str,
        vat_rate: Decimal,
        patterns: List[str],
        decimal_places: int = 2,
    ):
        self.code = code
        self.country = country
        self.arabic_symbol = arabic_symbol
        self.arabic_name = arabic_name
        self.vat_rate = vat_rate
        self.patterns = patterns
        self.decimal_places = decimal_places


MENA_CURRENCY_DEFINITIONS: List[CurrencyInfo] = [
    # Saudi Arabia (SAR) — Primary target market
    CurrencyInfo(
        code="SAR",
        country="Saudi Arabia",
        arabic_symbol="ر.س",
        arabic_name="ريال سعودي",
        vat_rate=Decimal("15.0"),
        patterns=[
            _AR_L + r"ر\s*\.?\s*س\.?" + _AR_R,
            _AR_L + r"ريال\s*سعودي" + _AR_R,
            _AR_L + r"ريالات\s*سعودية" + _AR_R,
            _AR_L + r"رس" + _AR_R,
            r"\bSAR\b",
            r"\bSR\b",
            _LAT_L + r"S\.R\." + _LAT_R,
        ],
    ),
    # UAE (AED)
    CurrencyInfo(
        code="AED",
        country="United Arab Emirates",
        arabic_symbol="د.إ",
        arabic_name="درهم إماراتي",
        vat_rate=Decimal("5.0"),
        patterns=[
            _AR_L + r"د\s*\.?\s*[إا]\.?" + _AR_R,
            _AR_L + r"درهم\s*[إا]ماراتي" + _AR_R,
            _AR_L + r"دراهم\s*[إا]ماراتية" + _AR_R,
            _AR_L + r"درهم\s*اماراتي" + _AR_R,
            _AR_L + r"دا" + _AR_R,
            _AR_L + r"دإ" + _AR_R,
            r"\bAED\b",
            r"\bDHS\b",
            r"\bDH\b",
        ],
    ),
    # Egypt (EGP)
    CurrencyInfo(
        code="EGP",
        country="Egypt",
        arabic_symbol="ج.م",
        arabic_name="جنيه مصري",
        vat_rate=Decimal("14.0"),
        patterns=[
            _AR_L + r"ج\s*\.?\s*م\.?" + _AR_R,
            _AR_L + r"جنيه\s*مصري" + _AR_R,
            _AR_L + r"جنية\s*مصرية" + _AR_R,
            _AR_L + r"جنيهات\s*مصرية" + _AR_R,
            _AR_L + r"جم" + _AR_R,
            r"\bEGP\b",
            r"\bLE\b",
            _LAT_L + r"L\.E\." + _LAT_R,
            _LAT_L + r"E\.G\.P\." + _LAT_R,
        ],
    ),
    # Kuwait (KWD)
    CurrencyInfo(
        code="KWD",
        country="Kuwait",
        arabic_symbol="د.ك",
        arabic_name="دينار كويتي",
        vat_rate=Decimal("0.0"),
        patterns=[
            _AR_L + r"د\s*\.?\s*ك\.?" + _AR_R,
            _AR_L + r"دينار\s*كويتي" + _AR_R,
            _AR_L + r"دنانير\s*كويتية" + _AR_R,
            _AR_L + r"دك" + _AR_R,
            r"\bKWD\b",
            r"\bKD\b",
        ],
        decimal_places=3,
    ),
    # Qatar (QAR)
    CurrencyInfo(
        code="QAR",
        country="Qatar",
        arabic_symbol="ر.ق",
        arabic_name="ريال قطري",
        vat_rate=Decimal("0.0"),
        patterns=[
            _AR_L + r"ر\s*\.?\s*ق\.?" + _AR_R,
            _AR_L + r"ريال\s*قطري" + _AR_R,
            _AR_L + r"ريالات\s*قطرية" + _AR_R,
            _AR_L + r"رق" + _AR_R,
            r"\bQAR\b",
            r"\bQR\b",
        ],
    ),
    # Bahrain (BHD)
    CurrencyInfo(
        code="BHD",
        country="Bahrain",
        arabic_symbol="د.ب",
        arabic_name="دينار بحريني",
        vat_rate=Decimal("10.0"),
        patterns=[
            _AR_L + r"د\s*\.?\s*ب\.?" + _AR_R,
            _AR_L + r"دينار\s*بحريني" + _AR_R,
            _AR_L + r"دنانير\s*بحرينية" + _AR_R,
            _AR_L + r"دب" + _AR_R,
            r"\bBHD\b",
            r"\bBD\b",
        ],
        decimal_places=3,
    ),
    # Oman (OMR)
    CurrencyInfo(
        code="OMR",
        country="Oman",
        arabic_symbol="ر.ع",
        arabic_name="ريال عماني",
        vat_rate=Decimal("5.0"),
        patterns=[
            _AR_L + r"ر\s*\.?\s*ع\.?" + _AR_R,
            _AR_L + r"ريال\s*عماني" + _AR_R,
            _AR_L + r"ريالات\s*عمانية" + _AR_R,
            _AR_L + r"رع" + _AR_R,
            r"\bOMR\b",
            r"\bRO\b",
        ],
        decimal_places=3,
    ),
    # Jordan (JOD)
    CurrencyInfo(
        code="JOD",
        country="Jordan",
        arabic_symbol="د.أ",
        arabic_name="دينار أردني",
        vat_rate=Decimal("16.0"),
        patterns=[
            _AR_L + r"د\s*\.?\s*[أا]\.?" + _AR_R,
            _AR_L + r"دينار\s*[أا]ردني" + _AR_R,
            _AR_L + r"دنانير\s*[أا]ردنية" + _AR_R,
            _AR_L + r"دأ" + _AR_R,
            r"\bJOD\b",
            r"\bJD\b",
        ],
        decimal_places=3,
    ),
    # US Dollar (USD)
    CurrencyInfo(
        code="USD",
        country="United States",
        arabic_symbol="$",
        arabic_name="دولار أمريكي",
        vat_rate=Decimal("0.0"),
        patterns=[
            _AR_L + r"دولار\s*[أا]مريكي" + _AR_R,
            _AR_L + r"دولار\s*امريكي" + _AR_R,
            _AR_L + r"دولارات" + _AR_R,
            _AR_L + r"دولار" + _AR_R,
            r"\bUSD\b",
            _LAT_L + r"US\$" + _LAT_R,
            r"\$",
        ],
    ),
    # Euro (EUR)
    CurrencyInfo(
        code="EUR",
        country="European Union",
        arabic_symbol="€",
        arabic_name="يورو",
        vat_rate=Decimal("0.0"),
        patterns=[
            _AR_L + r"يورو" + _AR_R,
            r"\bEUR\b",
            r"€",
        ],
    ),
    # British Pound (GBP)
    CurrencyInfo(
        code="GBP",
        country="United Kingdom",
        arabic_symbol="£",
        arabic_name="جنيه إسترليني",
        vat_rate=Decimal("0.0"),
        patterns=[
            _AR_L + r"جنيه\s*[إا]سترليني" + _AR_R,
            _AR_L + r"جنيه\s*استرليني" + _AR_R,
            r"\bGBP\b",
            r"£",
        ],
    ),
]

# Generic Arabic Currency Names (Fallback when country is not explicitly specified)
# Maps isolated generic currency words to the most likely regional ISO code
GENERIC_ARABIC_CURRENCY_MAP: Dict[str, str] = {
    "ريال": "SAR",       # Default Riyal -> Saudi Riyal
    "ريالات": "SAR",
    "درهم": "AED",       # Default Dirham -> UAE Dirham
    "دراهم": "AED",
    "جنيه": "EGP",       # Default Pound -> Egyptian Pound
    "جنية": "EGP",
    "جنيهات": "EGP",
    "دينار": "KWD",      # Default Dinar -> Kuwaiti Dinar
    "دنانير": "KWD",
}

# Compiled regex patterns cache
_COMPILED_PATTERNS: List[Tuple[str, re.Pattern]] = []
for _curr in MENA_CURRENCY_DEFINITIONS:
    for _pattern in _curr.patterns:
        _COMPILED_PATTERNS.append(
            (_curr.code, re.compile(_pattern, re.IGNORECASE | re.UNICODE))
        )

# Precompile generic fallback patterns with safe Arabic boundaries
_GENERIC_PATTERNS: List[Tuple[str, re.Pattern]] = [
    (code, re.compile(rf"{_AR_L}{word}{_AR_R}", re.UNICODE))
    for word, code in GENERIC_ARABIC_CURRENCY_MAP.items()
]


def detect_currency(text: str, default: Optional[str] = None) -> Optional[str]:
    """
    Scans input text for Arabic currency symbols, names, or ISO codes.
    Uses priority matching:
    1. Specific national currency markers (e.g. 'ر.س', 'درهم إماراتي', 'EGP')
    2. Generic currency words (e.g. 'ريال', 'درهم', 'جنيه') mapped to regional defaults
    3. Provided default fallback

    Args:
        text (str): Raw or preprocessed text string from an invoice snippet or OCR block.
        default (Optional[str]): Fallback ISO code if no currency is found (e.g. "SAR").

    Returns:
        Optional[str]: ISO 4217 currency code (e.g. 'SAR', 'AED', 'EGP') or default.
    """
    if not text:
        return default

    # 1. Match specific national currency symbols/patterns
    for code, regex in _COMPILED_PATTERNS:
        if regex.search(text):
            return code

    # Also test on normalized text to handle missing dots, hamza variations, or tashkeel
    norm_text = normalize_arabic(text)
    for code, regex in _COMPILED_PATTERNS:
        if regex.search(norm_text):
            return code

    # 2. Match generic terms (e.g., 'ريال', 'درهم', 'جنيه')
    for code, regex in _GENERIC_PATTERNS:
        if regex.search(text):
            return code

    for code, regex in _GENERIC_PATTERNS:
        if regex.search(norm_text):
            return code

    return default


def parse_arabic_amount(text: str) -> Optional[Decimal]:
    """
    Parses a monetary amount from a raw Arabic or bilingual string into a Python Decimal.
    
    Handles:
    - Eastern Arabic numerals (٠١٢٣٤٥٦٧٨٩) and Persian numerals (۰۱۲۳۴۵۶۷۸۹)
    - Western numerals (0123456789)
    - Arabic decimal comma (٫ / U+066B) and Arabic thousands separator (٬ / U+066C)
    - Western formatting: 1,234.56 or 1.234,56 or 1234.56
    - Accounting format negative numbers (e.g. '(1,234.50)' or '-1,234.50' or '1234-')
    - Embedded currency symbols, spaces, and text surrounding the amount

    Args:
        text (str): String containing the amount.

    Returns:
        Optional[Decimal]: Parsed amount as Decimal, or None if no valid numeric value found.
    """
    if not text:
        return None

    # Step 1: Convert all Eastern Arabic / Persian numerals to Western
    cleaned = to_western_numerals(str(text).strip())

    # Step 2: Check for negative notation
    is_negative = False
    if re.search(r"\(.*\)", cleaned):
        is_negative = True
        cleaned = re.sub(r"[\(\)]", "", cleaned)
    elif "-" in cleaned:
        is_negative = True
        cleaned = cleaned.replace("-", "")

    # Step 3: Handle explicit Arabic decimal and thousands separators
    # Arabic Thousands Separator (U+066C '٬')
    cleaned = cleaned.replace("٬", "")
    # Arabic Decimal Separator (U+066B '٫')
    cleaned = cleaned.replace("٫", ".")

    # Step 4: Strip known currency symbols, letters, and extraneous characters
    # Preserve digits, dots, commas, and whitespace
    cleaned = re.sub(r"[^\d.,\s]", " ", cleaned).strip()

    # If empty after removing non-numeric characters, return None
    if not cleaned or not re.search(r"\d", cleaned):
        return None

    # Step 5: Extract the primary numeric sequence
    # Find sequence of digits, dots, commas, spaces
    match = re.search(r"(\d[\d\s.,]*\d|\d)", cleaned)
    if not match:
        return None

    num_str = match.group(1).strip()
    # Remove internal spaces between digits (e.g., "1 500.00" -> "1500.00")
    num_str = re.sub(r"\s+", "", num_str)

    # Step 6: Normalize decimal and thousands separators
    has_comma = "," in num_str
    has_dot = "." in num_str

    if has_comma and has_dot:
        # Both exist: whichever appears last is the decimal separator
        last_comma = num_str.rfind(",")
        last_dot = num_str.rfind(".")
        if last_dot > last_comma:
            # 1,234.56 -> commas are thousands separators
            num_str = num_str.replace(",", "")
        else:
            # 1.234,56 -> dots are thousands separators, comma is decimal
            num_str = num_str.replace(".", "").replace(",", ".")
    elif has_comma:
        # Only comma exists
        comma_parts = num_str.split(",")
        # If last part is 1 or 2 digits (e.g. 1234,56 or 10,5) -> decimal separator
        # If multiple commas (e.g. 1,000,000) or last part is 3 digits (e.g. 1,234) -> thousands separator
        if len(comma_parts) > 2:
            # Multiple commas: thousands separators (e.g. 1,000,000)
            num_str = num_str.replace(",", "")
        elif len(comma_parts) == 2:
            if len(comma_parts[1]) in (1, 2):
                num_str = comma_parts[0] + "." + comma_parts[1]
            elif len(comma_parts[1]) == 3 and len(comma_parts[0]) <= 3:
                # Could be 1,000 or 1,234 -> thousands separator
                num_str = num_str.replace(",", "")
            else:
                num_str = comma_parts[0] + "." + comma_parts[1]
    elif has_dot:
        # Only dot exists
        dot_parts = num_str.split(".")
        if len(dot_parts) > 2:
            # Multiple dots: thousands separators (e.g. 1.000.000)
            num_str = num_str.replace(".", "")
        # Single dot is standard decimal (e.g. 1234.56 or 1000.0)

    try:
        amount = Decimal(num_str)
        if is_negative:
            amount = -amount
        return amount
    except InvalidOperation:
        return None


def get_country_vat_rate(currency_code: str) -> Optional[Decimal]:
    """
    Returns the standard statutory VAT rate for the country associated with the given currency code.

    Args:
        currency_code (str): ISO 4217 code (e.g. 'SAR', 'AED', 'EGP').

    Returns:
        Optional[Decimal]: VAT rate percentage (e.g. Decimal("15.0") for SAR), or None if unknown.
    """
    if not currency_code:
        return None
    return VAT_RATES.get(currency_code.upper().strip())


def get_currency_symbol_arabic(currency_code: str) -> str:
    """
    Returns the canonical Arabic currency symbol for the given ISO code.

    Args:
        currency_code (str): ISO 4217 code (e.g. 'SAR', 'AED', 'EGP').

    Returns:
        str: Arabic symbol (e.g. 'ر.س', 'د.إ', 'ج.م') or original code if not found.
    """
    if not currency_code:
        return ""
    code_upper = currency_code.upper().strip()
    return ARABIC_CURRENCY_SYMBOLS.get(code_upper, code_upper)


def format_arabic_currency(
    amount: Union[Decimal, float, int, str],
    currency_code: str,
    use_eastern_numerals: bool = False,
    include_symbol: bool = True,
) -> str:
    """
    Formats a numeric amount with standard thousands grouping, appropriate decimal places,
    and optional Arabic currency symbol and numeral conversion.

    Args:
        amount (Union[Decimal, float, int, str]): The amount to format.
        currency_code (str): ISO 4217 currency code (e.g. 'SAR', 'KWD').
        use_eastern_numerals (bool): If True, formats digits as Eastern Arabic (٠-٩).
        include_symbol (bool): If True, appends the Arabic currency symbol.

    Returns:
        str: Formatted currency string (e.g. '1,500.00 ر.س' or '١٬٥٠٠٫٠٠ ر.س').
    """
    if amount is None:
        return ""

    if not isinstance(amount, Decimal):
        try:
            dec_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            return str(amount)
    else:
        dec_amount = amount

    # Determine decimal places (3 for KWD/BHD/OMR, 2 for others)
    code_upper = (currency_code or "").upper().strip()
    decimal_places = 3 if code_upper in ("KWD", "BHD", "OMR") else 2

    # Format with Western grouping first: e.g. 1,234,567.89
    formatted_western = f"{dec_amount:,.{decimal_places}f}"

    if use_eastern_numerals:
        # Convert separators to Arabic standard (٬ for thousands, ٫ for decimal)
        formatted_ar = (
            formatted_western.replace(",", "٬")
            .replace(".", "٫")
        )
        formatted_digits = to_eastern_numerals(formatted_ar)
    else:
        formatted_digits = formatted_western

    if include_symbol:
        symbol = get_currency_symbol_arabic(code_upper)
        if symbol:
            return f"{formatted_digits} {symbol}".strip()

    return formatted_digits


def extract_currency_and_amount(
    text: str, default_currency: Optional[str] = None
) -> Tuple[Optional[str], Optional[Decimal]]:
    """
    Extracts both the ISO currency code and the parsed numeric amount from a single string snippet.

    Args:
        text (str): Input text line or snippet (e.g. 'الإجمالي: ١٬٥٠٠٫٥٠ ر.س').
        default_currency (Optional[str]): Fallback currency if not detected.

    Returns:
        Tuple[Optional[str], Optional[Decimal]]: (currency_code, amount)
    """
    if not text:
        return default_currency, None

    currency = detect_currency(text, default=default_currency)
    amount = parse_arabic_amount(text)
    return currency, amount


def is_valid_currency_code(code: str) -> bool:
    """
    Checks if a currency code is one of the supported MENA or international currencies.

    Args:
        code (str): ISO 4217 currency code.

    Returns:
        bool: True if recognized, False otherwise.
    """
    if not code:
        return False
    return code.upper().strip() in VAT_RATES
