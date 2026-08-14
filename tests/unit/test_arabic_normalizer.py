import pytest
from src.arabic.normalizer import (
    remove_tashkeel,
    remove_tatweel,
    normalize_alef,
    normalize_alef_maqsura,
    normalize_teh_marbuta,
    normalize_arabic_punctuation,
    normalize_arabic,
    detect_language,
    contains_arabic,
    extract_arabic_text_blocks,
)


def test_remove_tashkeel():
    assert remove_tashkeel("فَاتُورَةٌ ضَرِيبِيَّةٌ") == "فاتورة ضريبية"
    assert remove_tashkeel("مَرْحَبًا بِكُمْ") == "مرحبا بكم"
    assert remove_tashkeel("سِعْرُ الوَحْدَةِ") == "سعر الوحدة"
    assert remove_tashkeel("") == ""
    assert remove_tashkeel(None) is None


def test_remove_tatweel():
    assert remove_tatweel("فـــــاتـــورة") == "فاتورة"
    assert remove_tatweel("المـــورد") == "المورد"
    assert remove_tatweel("") == ""
    assert remove_tatweel(None) is None


def test_normalize_alef():
    assert normalize_alef("أحمد") == "احمد"
    assert normalize_alef("إبراهيم") == "ابراهيم"
    assert normalize_alef("آدم") == "ادم"
    assert normalize_alef("ٱستلام") == "استلام"
    assert normalize_alef("الإجمالي") == "الاجمالي"


def test_normalize_alef_maqsura():
    assert normalize_alef_maqsura("مستشفى") == "مستشفي"
    assert normalize_alef_maqsura("علي") == "علي"


def test_normalize_teh_marbuta():
    assert normalize_teh_marbuta("فاتورة ضريبية") == "فاتوره ضريبيه"
    assert normalize_teh_marbuta("شركة") == "شركه"


def test_normalize_arabic_punctuation():
    assert normalize_arabic_punctuation("المبلغ: ١٠٠،٥٠؛ النسبة: ١٥٪؟") == "المبلغ: ١٠٠,٥٠; النسبة: ١٥%?"


def test_normalize_arabic_pipeline():
    raw_text = "فَاتُـــــورَةٌ ضَرِيبِيَّةٌ: إِجْمَالِيُّ المَبْلَغِ ١٥٠،٠٠"
    normalized = normalize_arabic(raw_text)
    assert normalized == "فاتورة ضريبية: اجمالي المبلغ ١٥٠,٠٠"


def test_contains_arabic():
    assert contains_arabic("فاتورة") is True
    assert contains_arabic("Invoice #1234") is False
    assert contains_arabic("Invoice رقم 123") is True
    assert contains_arabic("") is False
    assert contains_arabic(None) is False


def test_detect_language():
    assert detect_language("فاتورة ضريبية مبسطة") == "ar"
    assert detect_language("Tax Invoice #1029") == "en"
    assert detect_language("Tax Invoice فاتورة ضريبية") == "mixed"
    # Arabic-first fallback for numbers/symbols or empty
    assert detect_language("123456 - 789") == "ar"
    assert detect_language("") == "ar"


def test_extract_arabic_text_blocks():
    text = "Invoice Number: رقم الفاتورة 12345 Vendor: شركة الأمل للتجارة"
    blocks = extract_arabic_text_blocks(text)
    assert "رقم الفاتورة" in blocks
    assert "شركة الأمل للتجارة" in blocks
