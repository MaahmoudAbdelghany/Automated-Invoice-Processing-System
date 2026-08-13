import pytest
from src.arabic.numerals import to_western_numerals, to_eastern_numerals

def test_to_western_numerals():
    assert to_western_numerals("١٢٣٤٥٦٧٨٩٠") == "1234567890"
    assert to_western_numerals("۱۱۲۲") == "1122"  # Persian
    assert to_western_numerals("رقم الفاتورة: ١٥٠.٥٠") == "رقم الفاتورة: 150.50"
    assert to_western_numerals("1234") == "1234"
    assert to_western_numerals("") == ""
    assert to_western_numerals(None) == None

def test_to_eastern_numerals():
    assert to_eastern_numerals("1234567890") == "١٢٣٤٥٦٧٨٩٠"
    assert to_eastern_numerals("رقم الفاتورة: 150.50") == "رقم الفاتورة: ١٥٠.٥٠"
    assert to_eastern_numerals("١٢٣٤") == "١٢٣٤"
    assert to_eastern_numerals("") == ""
    assert to_eastern_numerals(None) == None
