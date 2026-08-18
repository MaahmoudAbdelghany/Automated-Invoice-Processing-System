"""
Unit tests for src/arabic/hijri.py — Hijri date detection & Gregorian conversion.
"""

import datetime
import pytest

from src.arabic.hijri import (
    HijriMatch,
    detect_hijri_date,
    gregorian_to_hijri,
    hijri_to_gregorian,
    is_likely_hijri,
    parse_hijri_date_string,
    replace_hijri_with_gregorian,
)


class TestIsLikelyHijri:
    """Tests for the is_likely_hijri heuristic function."""

    @pytest.mark.parametrize(
        "year, expected",
        [
            (1445, True),
            (1446, True),
            (1300, True),
            (1500, True),
            (2024, False),
            (2025, False),
            (1999, False),
            (1299, False),
            (1501, False),
            (0, False),
        ],
    )
    def test_is_likely_hijri(self, year: int, expected: bool):
        assert is_likely_hijri(year) is expected


class TestHijriConversionCore:
    """Tests for direct date conversion between Hijri and Gregorian."""

    def test_hijri_to_gregorian_standard(self):
        # 1446-02-15 Hijri corresponds to 2024-08-19 Gregorian
        greg = hijri_to_gregorian(1446, 2, 15)
        assert isinstance(greg, datetime.date)
        assert greg == datetime.date(2024, 8, 19)

    def test_hijri_to_gregorian_day_clamping(self):
        # Even if day 30 is passed for a 29-day month, it converts gracefully
        greg = hijri_to_gregorian(1446, 2, 30)
        assert isinstance(greg, datetime.date)

    def test_hijri_to_gregorian_invalid_ranges(self):
        with pytest.raises(ValueError, match="outside supported range"):
            hijri_to_gregorian(2024, 1, 1)

        with pytest.raises(ValueError, match="must be between 1 and 12"):
            hijri_to_gregorian(1446, 13, 1)

        with pytest.raises(ValueError, match="must be between 1 and 12"):
            hijri_to_gregorian(1446, 0, 1)

    def test_gregorian_to_hijri_types(self):
        # Date object
        d = datetime.date(2024, 8, 19)
        h_year, h_month, h_day = gregorian_to_hijri(d)
        assert (h_year, h_month, h_day) == (1446, 2, 15)

        # Datetime object
        dt = datetime.datetime(2024, 8, 19, 14, 30, 0)
        assert gregorian_to_hijri(dt) == (1446, 2, 15)

        # ISO String
        assert gregorian_to_hijri("2024-08-19") == (1446, 2, 15)


class TestDetectHijriDate:
    """Tests for detecting Hijri dates across diverse invoice formats."""

    def test_textual_month_names_all_twelve(self):
        months_test = [
            ("1 محرم 1446", 1),
            ("15 صفر 1446", 2),
            ("10 ربيع الأول 1446", 3),
            ("12 ربيع الثاني 1446", 4),
            ("5 جمادى الأولى 1446", 5),
            ("20 جمادى الآخرة 1446", 6),
            ("27 رجب 1446", 7),
            ("15 شعبان 1446", 8),
            ("1 رمضان 1446", 9),
            ("1 شوال 1446", 10),
            ("10 ذو القعدة 1446", 11),
            ("9 ذو الحجة 1446", 12),
        ]
        for text, expected_month in months_test:
            matches = detect_hijri_date(text)
            assert len(matches) == 1, f"Failed to match: {text}"
            assert matches[0].hijri_month == expected_month
            assert matches[0].hijri_year == 1446

    def test_eastern_numerals_and_variations(self):
        text = "تاريخ الفاتورة: ١٥ صفر ١٤٤٦ هـ"
        matches = detect_hijri_date(text)
        assert len(matches) == 1
        assert matches[0].hijri_year == 1446
        assert matches[0].hijri_month == 2
        assert matches[0].hijri_day == 15
        assert matches[0].gregorian_iso == "2024-08-19"
        assert matches[0].original_text == "١٥ صفر ١٤٤٦ هـ"

    def test_numeric_hijri_ymd(self):
        text = "رقم الفاتورة: INV-99 - التاريخ: 1446/02/15 - الرياض"
        matches = detect_hijri_date(text)
        assert len(matches) == 1
        assert matches[0].hijri_year == 1446
        assert matches[0].hijri_month == 2
        assert matches[0].hijri_day == 15
        assert matches[0].gregorian_iso == "2024-08-19"

    def test_numeric_hijri_dmy_eastern(self):
        text = "فاتورة ضريبية بتاريخ ١٥-٠٢-١٤٤٦"
        matches = detect_hijri_date(text)
        assert len(matches) == 1
        assert matches[0].hijri_year == 1446
        assert matches[0].hijri_month == 2
        assert matches[0].hijri_day == 15
        assert matches[0].gregorian_iso == "2024-08-19"

    def test_ignore_gregorian_dates(self):
        text = "Invoice Date: 2024-08-19 and Due Date: 19/08/2024"
        matches = detect_hijri_date(text)
        assert len(matches) == 0

    def test_empty_or_none_text(self):
        assert detect_hijri_date("") == []
        assert detect_hijri_date(None) == []


class TestReplaceHijriWithGregorian:
    """Tests for replacing/augmenting Hijri dates with Gregorian equivalents."""

    def test_replace_single_hijri_date(self):
        text = "حرر في ١٥ صفر ١٤٤٦ هـ بالرياض"
        result = replace_hijri_with_gregorian(text)
        assert "2024-08-19" in result
        assert "١٥ صفر ١٤٤٦ هـ (2024-08-19)" in result

    def test_replace_multiple_hijri_dates(self):
        text = "تاريخ الإصدار: 1446/02/15 وتاريخ الاستحقاق: 1446/03/15"
        result = replace_hijri_with_gregorian(text)
        assert "(2024-08-19)" in result
        assert "(2024-09-18)" in result

    def test_no_change_when_no_hijri(self):
        text = "المبلغ الإجمالي: 1500 ر.س"
        assert replace_hijri_with_gregorian(text) == text


class TestParseHijriDateString:
    """Tests for the parse_hijri_date_string utility."""

    def test_parse_valid_strings(self):
        assert parse_hijri_date_string("1446/02/15") == datetime.date(2024, 8, 19)
        assert parse_hijri_date_string("١٥ صفر ١٤٤٦") == datetime.date(2024, 8, 19)
        assert parse_hijri_date_string("15-02-1446") == datetime.date(2024, 8, 19)

    def test_parse_invalid_or_empty_string(self):
        assert parse_hijri_date_string("") is None
        assert parse_hijri_date_string("2024-08-19") is None
        assert parse_hijri_date_string("مرحبا") is None
