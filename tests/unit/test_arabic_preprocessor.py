"""
Unit tests for src/arabic/preprocessor.py — Unified Arabic Preprocessing Pipeline.
"""

from decimal import Decimal
import pytest

from src.arabic.preprocessor import (
    ArabicPreprocessor,
    PreprocessedInvoiceData,
    preprocess,
    preprocess_arabic_invoice,
)


class TestArabicPreprocessorSaudiInvoice:
    """Tests full preprocessing on a representative Saudi ZATCA Arabic invoice."""

    @pytest.fixture
    def saudi_ocr_output(self):
        return {
            "raw_text": (
                "شَرِكَةُ التَّقْنِيَّةِ الْمُتَقَدِّمَةِ لِتِقْنِيَّةِ الْمَعْلُومَاتِ\n"
                "فاتورة ضريبية\n"
                "رقم الفاتورة: INV-2024-001\n"
                "تاريخ الفاتورة: ١٥ صفر ١٤٤٦\n"
                "الرقم الضريبي للمنشأة: ٣٠٠١٢٣٤٥٦٧٠٠٠٠٣\n"
                "اسم العميل: شركة الأمل للتجارة\n"
                "المجموع قبل الضريبة: ١٬٠٠٠٫٠٠ ر.س\n"
                "ضريبة القيمة المضافة: ١٥٠٫٠٠ ر.س\n"
                "المجموع الكلي: ١٬١٥٠٫٠٠ ر.س\n"
            ),
            "expense_fields": {
                "رقم الفاتورة": "INV-2024-001",
                "تاريخ الفاتورة": "١٥ صفر ١٤٤٦",
                "اسم المورد": "شَرِكَةُ التَّقْنِيَّةِ الْمُتَقَدِّمَةِ",
                "الرقم الضريبي للمنشأة": "٣٠٠١٢٣٤٥٦٧٠٠٠٠٣",
                "اسم العميل": "شركة الأمل للتجارة",
                "المجموع الفرعي": "١٬٠٠٠٫٠٠ ر.س",
                "مبلغ الضريبة": "١٥٠٫٠٠ ر.س",
                "المجموع الكلي": "١٬١٥٠٫٠٠ ر.س",
                "العملة": "ر.س",
            },
            "tables": [
                {
                    "الوصف": "خدمات استشارات سحابية",
                    "الكمية": "٢",
                    "سعر الوحدة": "٥٠٠٫٠٠",
                    "المبلغ": "١٬٠٠٠٫٠٠",
                }
            ],
            "confidence_scores": {"total": 0.95},
        }

    def test_preprocess_saudi_invoice(self, saudi_ocr_output):
        preprocessor = ArabicPreprocessor()
        result = preprocessor.preprocess(saudi_ocr_output)

        assert isinstance(result, PreprocessedInvoiceData)
        assert result.detected_language == "ar"
        assert result.detected_currency == "SAR"
        assert result.statutory_vat_rate == Decimal("15.0")

        # Verify mapped fields
        fields = result.mapped_fields
        assert fields["invoice_number"] == "INV-2024-001"
        assert fields["invoice_date"] == "2024-08-19"  # Hijri 15 Safar 1446 -> Gregorian
        assert fields["vendor_vat_number"] == "300123456700003"  # Eastern -> Western
        assert "شركة التقنية المتقدمة" in fields["vendor_name"]  # Tashkeel removed
        assert fields["buyer_name"] == "شركة الامل للتجارة"  # Normalized
        assert fields["subtotal"] == Decimal("1000.00")
        assert fields["tax_amount"] == Decimal("150.00")
        assert fields["total_amount"] == Decimal("1150.00")
        assert fields["currency"] == "SAR"

        # Verify table items
        assert len(result.mapped_tables) == 1
        item = result.mapped_tables[0]
        assert item["description"] == "خدمات استشارات سحابية"
        assert item["quantity"] == Decimal("2")
        assert item["unit_price"] == Decimal("500.00")
        assert item["amount"] == Decimal("1000.00")

        # Verify Hijri conversions recorded
        assert len(result.hijri_conversions) >= 1
        assert result.hijri_conversions[0]["hijri_year"] == 1446
        assert result.hijri_conversions[0]["hijri_month"] == 2
        assert result.hijri_conversions[0]["hijri_day"] == 15
        assert result.hijri_conversions[0]["gregorian_iso"] == "2024-08-19"


class TestArabicPreprocessorBilingualUAEInvoice:
    """Tests preprocessing on a bilingual UAE commercial invoice."""

    @pytest.fixture
    def uae_ocr_output(self):
        return {
            "raw_text": (
                "DUBAI TECH SOLUTIONS LLC\n"
                "فاتورة تجارية / Commercial Invoice\n"
                "Invoice Number: INV-DXB-9988\n"
                "Date / التاريخ: 2024-05-10\n"
                "TRN / الرقم الضريبي: 100234567800003\n"
                "Subtotal / المجموع الفرعي: 2,000.00 AED\n"
                "VAT (5%) / الضريبة: 100.00 د.إ\n"
                "Total Amount / المجموع الكلي: 2,100.00 AED\n"
            ),
            "expense_fields": {
                "Invoice Number": "INV-DXB-9988",
                "Date / التاريخ": "2024-05-10",
                "Vendor Name": "DUBAI TECH SOLUTIONS LLC",
                "TRN / الرقم الضريبي": "100234567800003",
                "Subtotal": "2,000.00 AED",
                "Tax Amount": "100.00 د.إ",
                "Total Amount": "2,100.00 AED",
            },
            "tables": [
                {
                    "Description / الوصف": "Software License",
                    "Qty": "1",
                    "Unit Price": "2,000.00",
                    "Total": "2,000.00",
                }
            ],
        }

    def test_preprocess_uae_invoice(self, uae_ocr_output):
        result = preprocess_arabic_invoice(uae_ocr_output)

        assert result.detected_language == "mixed"
        assert result.detected_currency == "AED"
        assert result.statutory_vat_rate == Decimal("5.0")

        fields = result.mapped_fields
        assert fields["invoice_number"] == "INV-DXB-9988"
        assert fields["invoice_date"] == "2024-05-10"
        assert fields["subtotal"] == Decimal("2000.00")
        assert fields["tax_amount"] == Decimal("100.00")
        assert fields["total_amount"] == Decimal("2100.00")


class TestArabicPreprocessorEgyptianInvoice:
    """Tests preprocessing on an Egyptian invoice with comma decimal notation."""

    @pytest.fixture
    def egypt_ocr_output(self):
        return {
            "raw_text": (
                "شركة القاهرة للخدمات الهندسية\n"
                "فاتورة مبيعات\n"
                "رقم الفاتورة: EGY-554\n"
                "تاريخ التحرير: 2024/03/01\n"
                "المجموع قبل الضريبة: 5.000,00 ج.م\n"
                "ضريبة القيمة المضافة 14%: 700,00 ج.م\n"
                "صافي المبلغ المطلوب: 5.700,00 ج.م\n"
            ),
            "expense_fields": {
                "رقم الفاتورة": "EGY-554",
                "تاريخ التحرير": "2024/03/01",
                "اسم المورد": "شركة القاهرة للخدمات الهندسية",
                "المجموع قبل الضريبة": "5.000,00 ج.م",
                "مبلغ الضريبة": "700,00 ج.م",
                "المجموع الكلي": "5.700,00 ج.م",
            },
            "tables": [],
        }

    def test_preprocess_egypt_invoice(self, egypt_ocr_output):
        result = preprocess_arabic_invoice(egypt_ocr_output)

        assert result.detected_language == "ar"
        assert result.detected_currency == "EGP"
        assert result.statutory_vat_rate == Decimal("14.0")

        fields = result.mapped_fields
        assert fields["subtotal"] == Decimal("5000.00")
        assert fields["tax_amount"] == Decimal("700.00")
        assert fields["total_amount"] == Decimal("5700.00")


class TestArabicPreprocessorEnglishFallback:
    """Tests preprocessing on an English invoice."""

    @pytest.fixture
    def english_ocr_output(self):
        return {
            "raw_text": (
                "Acme Corp Inc\n"
                "INVOICE\n"
                "Invoice Number: INV-900\n"
                "Invoice Date: 2024-01-15\n"
                "Total Amount: $500.00\n"
            ),
            "expense_fields": {
                "Invoice Number": "INV-900",
                "Invoice Date": "2024-01-15",
                "Total Amount": "$500.00",
            },
            "tables": [],
        }

    def test_preprocess_english_invoice(self, english_ocr_output):
        result = preprocess_arabic_invoice(english_ocr_output)

        assert result.detected_language == "en"
        assert result.detected_currency == "USD"
        fields = result.mapped_fields
        assert fields["invoice_number"] == "INV-900"
        assert fields["total_amount"] == Decimal("500.00")


class TestArabicPreprocessorLangGraphNode:
    """Tests the functional LangGraph node handler `preprocess()`."""

    def test_preprocess_node_output_format(self):
        ocr_input = {
            "raw_text": "فاتورة رقم 123 الإجمالي: 100 ر.س",
            "expense_fields": {"رقم الفاتورة": "123", "المجموع": "100 ر.س"},
            "tables": [],
        }
        output_dict = preprocess(ocr_input)

        assert isinstance(output_dict, dict)
        assert "detected_language" in output_dict
        assert "detected_currency" in output_dict
        assert "statutory_vat_rate" in output_dict
        assert "mapped_fields" in output_dict
        assert "preprocessed_text" in output_dict
        assert output_dict["detected_currency"] == "SAR"
        assert output_dict["statutory_vat_rate"] == 15.0
        assert output_dict["mapped_fields"]["invoice_number"] == "123"

    def test_preprocess_empty_input(self):
        output = preprocess({})
        assert isinstance(output, dict)
        assert output["detected_language"] == "ar"
        assert output["detected_currency"] == "SAR"
