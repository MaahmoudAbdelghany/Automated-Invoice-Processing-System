"""
Unit tests for src/arabic/currencies.py — MENA currency detection, amount parsing, and VAT rate resolution.
"""

from decimal import Decimal
import pytest

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


class TestCurrencyDetection:
    """Tests for detect_currency function across MENA and international currencies."""

    @pytest.mark.parametrize(
        "text, expected_code",
        [
            # Saudi Arabia (SAR)
            ("المجموع الكلي: 1500.00 ر.س", "SAR"),
            ("1500 ر.س", "SAR"),
            ("1500 ر . س", "SAR"),
            ("1500 رس", "SAR"),
            ("1500 ريال سعودي", "SAR"),
            ("المبلغ: 1500 SAR", "SAR"),
            ("Total: 1500 SR", "SAR"),
            ("Total: 1500 S.R.", "SAR"),
            # UAE (AED)
            ("المبلغ الإجمالي: 2500 د.إ", "AED"),
            ("2500 د.ا", "AED"),
            ("2500 دا", "AED"),
            ("2500 دإ", "AED"),
            ("2500 درهم إماراتي", "AED"),
            ("2500 درهم اماراتي", "AED"),
            ("2500 AED", "AED"),
            ("2500 DHS", "AED"),
            ("2500 DH", "AED"),
            # Egypt (EGP)
            ("القيمة: 3200 ج.م", "EGP"),
            ("3200 جم", "EGP"),
            ("3200 جنيه مصري", "EGP"),
            ("3200 جنية مصرية", "EGP"),
            ("3200 EGP", "EGP"),
            ("3200 LE", "EGP"),
            ("3200 L.E.", "EGP"),
            # Kuwait (KWD)
            ("150 د.ك", "KWD"),
            ("150 دك", "KWD"),
            ("150 دينار كويتي", "KWD"),
            ("150 KWD", "KWD"),
            ("150 KD", "KWD"),
            # Qatar (QAR)
            ("800 ر.ق", "QAR"),
            ("800 رق", "QAR"),
            ("800 ريال قطري", "QAR"),
            ("800 QAR", "QAR"),
            ("800 QR", "QAR"),
            # Bahrain (BHD)
            ("45 د.ب", "BHD"),
            ("45 دب", "BHD"),
            ("45 دينار بحريني", "BHD"),
            ("45 BHD", "BHD"),
            ("45 BD", "BHD"),
            # Oman (OMR)
            ("95 ر.ع", "OMR"),
            ("95 رع", "OMR"),
            ("95 ريال عماني", "OMR"),
            ("95 OMR", "OMR"),
            ("95 RO", "OMR"),
            # Jordan (JOD)
            ("60 د.أ", "JOD"),
            ("60 دأ", "JOD"),
            ("60 دينار أردني", "JOD"),
            ("60 دينار اردني", "JOD"),
            ("60 JOD", "JOD"),
            ("60 JD", "JOD"),
            # US Dollar (USD)
            ("Amount: $1200", "USD"),
            ("1200 دولار أمريكي", "USD"),
            ("1200 دولار امريكي", "USD"),
            ("1200 دولار", "USD"),
            ("1200 USD", "USD"),
            ("1200 US$", "USD"),
            # Euro (EUR)
            ("1200 €", "EUR"),
            ("1200 يورو", "EUR"),
            ("1200 EUR", "EUR"),
            # British Pound (GBP)
            ("1200 £", "GBP"),
            ("1200 جنيه إسترليني", "GBP"),
            ("1200 GBP", "GBP"),
        ],
    )
    def test_detect_specific_currency(self, text: str, expected_code: str):
        assert detect_currency(text) == expected_code

    @pytest.mark.parametrize(
        "text, expected_code",
        [
            ("المجموع: 500 ريال", "SAR"),
            ("500 درهم", "AED"),
            ("500 جنيه", "EGP"),
            ("500 دينار", "KWD"),
        ],
    )
    def test_detect_generic_currency_defaults(self, text: str, expected_code: str):
        assert detect_currency(text) == expected_code

    def test_detect_currency_fallback(self):
        assert detect_currency("لا توجد عملة هنا") is None
        assert detect_currency("لا توجد عملة هنا", default="SAR") == "SAR"
        assert detect_currency("", default="SAR") == "SAR"
        assert detect_currency(None, default="SAR") == "SAR"


class TestArabicAmountParsing:
    """Tests for parse_arabic_amount handling diverse formatting, separators, and numerals."""

    @pytest.mark.parametrize(
        "raw_text, expected_amount",
        [
            # Standard Western formatting
            ("1234.56", Decimal("1234.56")),
            ("1,234.56", Decimal("1234.56")),
            ("1,234,567.89", Decimal("1234567.89")),
            ("500", Decimal("500")),
            ("0.75", Decimal("0.75")),
            # Eastern Arabic Numerals (٠١٢٣٤٥٦٧٨٩)
            ("١٢٣٤٫٥٦", Decimal("1234.56")),
            ("١٬٢٣٤٫٥٦", Decimal("1234.56")),
            ("٥٠٠", Decimal("500")),
            ("٠٫٧٥", Decimal("0.75")),
            ("١٬٢٣٤٬٥٦٧٫٨٩", Decimal("1234567.89")),
            # Persian / Urdu Numerals (۰۱۲۳۴۵۶۷۸۹)
            ("۱۲۳۴٫۵۶", Decimal("1234.56")),
            ("۵۰۰", Decimal("500")),
            # Egyptian / European comma decimal notation
            ("1234,56", Decimal("1234.56")),
            ("1.234,56", Decimal("1234.56")),
            ("10,5", Decimal("10.5")),
            # Amounts embedded in Arabic text and currency markers
            ("المجموع: ١٬٥٠٠٫٥٠ ر.س", Decimal("1500.50")),
            ("الإجمالي شامل الضريبة 2,345.75 AED", Decimal("2345.75")),
            ("ج.م 1.250,00", Decimal("1250.00")),
            ("  ر.س  1000.00  ", Decimal("1000.00")),
            # Spaced thousand separators
            ("10 000.50", Decimal("10000.50")),
            # Negative numbers (accounting or standard)
            ("-150.00", Decimal("-150.00")),
            ("(150.00)", Decimal("-150.00")),
            ("-١٥٠٫٠٠", Decimal("-150.00")),
            ("150.00-", Decimal("-150.00")),
        ],
    )
    def test_parse_arabic_amount_success(self, raw_text: str, expected_amount: Decimal):
        parsed = parse_arabic_amount(raw_text)
        assert parsed == expected_amount

    @pytest.mark.parametrize(
        "invalid_text",
        [
            "",
            "   ",
            "لا يوجد أرقام",
            "None",
            "N/A",
        ],
    )
    def test_parse_arabic_amount_invalid(self, invalid_text: str):
        assert parse_arabic_amount(invalid_text) is None


class TestCountryVATRates:
    """Tests for get_country_vat_rate."""

    @pytest.mark.parametrize(
        "currency_code, expected_vat",
        [
            ("SAR", Decimal("15.0")),
            ("sar", Decimal("15.0")),
            ("AED", Decimal("5.0")),
            ("EGP", Decimal("14.0")),
            ("BHD", Decimal("10.0")),
            ("OMR", Decimal("5.0")),
            ("JOD", Decimal("16.0")),
            ("KWD", Decimal("0.0")),
            ("QAR", Decimal("0.0")),
            ("USD", Decimal("0.0")),
            ("EUR", Decimal("0.0")),
            ("GBP", Decimal("0.0")),
        ],
    )
    def test_get_country_vat_rate(self, currency_code: str, expected_vat: Decimal):
        assert get_country_vat_rate(currency_code) == expected_vat

    def test_get_country_vat_rate_unknown(self):
        assert get_country_vat_rate("XYZ") is None
        assert get_country_vat_rate("") is None
        assert get_country_vat_rate(None) is None


class TestArabicCurrencySymbols:
    """Tests for get_currency_symbol_arabic."""

    @pytest.mark.parametrize(
        "currency_code, expected_symbol",
        [
            ("SAR", "ر.س"),
            ("AED", "د.إ"),
            ("EGP", "ج.م"),
            ("KWD", "د.ك"),
            ("QAR", "ر.ق"),
            ("BHD", "د.ب"),
            ("OMR", "ر.ع"),
            ("JOD", "د.أ"),
            ("USD", "$"),
            ("EUR", "€"),
            ("GBP", "£"),
        ],
    )
    def test_get_currency_symbol_arabic(self, currency_code: str, expected_symbol: str):
        assert get_currency_symbol_arabic(currency_code) == expected_symbol


class TestFormatArabicCurrency:
    """Tests for format_arabic_currency."""

    def test_format_western_numerals(self):
        result = format_arabic_currency(Decimal("1500.50"), "SAR")
        assert result == "1,500.50 ر.س"

    def test_format_eastern_numerals(self):
        result = format_arabic_currency(
            Decimal("1500.50"), "SAR", use_eastern_numerals=True
        )
        assert result == "١٬٥٠٠٫٥٠ ر.س"

    def test_format_three_decimal_currencies(self):
        result = format_arabic_currency(Decimal("12.345"), "KWD")
        assert result == "12.345 د.ك"

    def test_format_without_symbol(self):
        result = format_arabic_currency(
            Decimal("1500.50"), "SAR", include_symbol=False
        )
        assert result == "1,500.50"


class TestExtractCurrencyAndAmount:
    """Tests for extract_currency_and_amount."""

    def test_extract_both(self):
        currency, amount = extract_currency_and_amount("المبلغ الإجمالي: ١٬٥٠٠٫٥٠ ر.س")
        assert currency == "SAR"
        assert amount == Decimal("1500.50")

    def test_extract_with_fallback_currency(self):
        currency, amount = extract_currency_and_amount("المبلغ: 500", default_currency="SAR")
        assert currency == "SAR"
        assert amount == Decimal("500")

    def test_extract_empty_string(self):
        currency, amount = extract_currency_and_amount("")
        assert currency is None
        assert amount is None


class TestIsValidCurrencyCode:
    """Tests for is_valid_currency_code."""

    def test_valid_codes(self):
        assert is_valid_currency_code("SAR") is True
        assert is_valid_currency_code("sar") is True
        assert is_valid_currency_code("AED") is True
        assert is_valid_currency_code("EGP") is True
        assert is_valid_currency_code("USD") is True

    def test_invalid_codes(self):
        assert is_valid_currency_code("XYZ") is False
        assert is_valid_currency_code("") is False
        assert is_valid_currency_code(None) is False
