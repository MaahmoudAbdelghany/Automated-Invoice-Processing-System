"""
Unit tests for src/arabic/field_mapper.py — Arabic field label to schema mapping.
"""

import pytest

from src.arabic.field_mapper import (
    FIELD_BUYER_ADDRESS,
    FIELD_BUYER_NAME,
    FIELD_BUYER_VAT_NUMBER,
    FIELD_CURRENCY,
    FIELD_DUE_DATE,
    FIELD_INVOICE_DATE,
    FIELD_INVOICE_NUMBER,
    FIELD_SUBTOTAL,
    FIELD_TAX_AMOUNT,
    FIELD_TAX_RATE,
    FIELD_TOTAL_AMOUNT,
    FIELD_VENDOR_ADDRESS,
    FIELD_VENDOR_NAME,
    FIELD_VENDOR_VAT_NUMBER,
    ITEM_AMOUNT,
    ITEM_DESCRIPTION,
    ITEM_QUANTITY,
    ITEM_UNIT_PRICE,
    get_canonical_arabic_label,
    map_arabic_fields,
    map_arabic_label,
    map_line_item,
    map_line_item_key,
)


class TestArabicFieldLabelMapping:
    """Tests mapping individual raw Arabic labels to canonical schema keys."""

    @pytest.mark.parametrize(
        "raw_label, expected_field",
        [
            # Invoice Number
            ("رقم الفاتورة", FIELD_INVOICE_NUMBER),
            ("رقم الفاتوره", FIELD_INVOICE_NUMBER),
            ("الرقم المرجعي", FIELD_INVOICE_NUMBER),
            ("كود الفاتورة:", FIELD_INVOICE_NUMBER),
            ("Invoice Number", FIELD_INVOICE_NUMBER),
            ("INV #", FIELD_INVOICE_NUMBER),
            # Invoice Date
            ("تاريخ الفاتورة", FIELD_INVOICE_DATE),
            ("تاريخ الإصدار", FIELD_INVOICE_DATE),
            ("تاريخ الاصدار", FIELD_INVOICE_DATE),
            ("التاريخ:", FIELD_INVOICE_DATE),
            ("تحريرا في", FIELD_INVOICE_DATE),
            # Due Date
            ("تاريخ الاستحقاق", FIELD_DUE_DATE),
            ("ميعاد السداد", FIELD_DUE_DATE),
            ("تاريخ السداد", FIELD_DUE_DATE),
            # Vendor Information
            ("اسم المورد", FIELD_VENDOR_NAME),
            ("اسم البائع", FIELD_VENDOR_NAME),
            ("اسم الشركة", FIELD_VENDOR_NAME),
            ("المورد:", FIELD_VENDOR_NAME),
            ("عنوان المورد", FIELD_VENDOR_ADDRESS),
            ("المقر", FIELD_VENDOR_ADDRESS),
            ("الرقم الضريبي", FIELD_VENDOR_VAT_NUMBER),
            ("رقم التسجيل الضريبي", FIELD_VENDOR_VAT_NUMBER),
            ("الرقم الضريبي للمنشأة", FIELD_VENDOR_VAT_NUMBER),
            ("VAT Registration No", FIELD_VENDOR_VAT_NUMBER),
            ("TRN", FIELD_VENDOR_VAT_NUMBER),
            # Buyer Information
            ("اسم المشتري", FIELD_BUYER_NAME),
            ("اسم العميل", FIELD_BUYER_NAME),
            ("العميل:", FIELD_BUYER_NAME),
            ("الفاتورة إلى", FIELD_BUYER_NAME),
            ("عنوان العميل", FIELD_BUYER_ADDRESS),
            ("الرقم الضريبي للمشتري", FIELD_BUYER_VAT_NUMBER),
            ("الرقم الضريبي للعميل", FIELD_BUYER_VAT_NUMBER),
            # Financial Amounts
            ("المجموع الفرعي", FIELD_SUBTOTAL),
            ("المجموع قبل الضريبة", FIELD_SUBTOTAL),
            ("المبلغ الخاضع للضريبة", FIELD_SUBTOTAL),
            ("مبلغ الضريبة", FIELD_TAX_AMOUNT),
            ("ضريبة القيمة المضافة", FIELD_TAX_AMOUNT),
            ("VAT", FIELD_TAX_AMOUNT),
            ("نسبة الضريبة", FIELD_TAX_RATE),
            ("معدل الضريبة", FIELD_TAX_RATE),
            ("المجموع الكلي", FIELD_TOTAL_AMOUNT),
            ("الإجمالي", FIELD_TOTAL_AMOUNT),
            ("المجموع شامل الضريبة", FIELD_TOTAL_AMOUNT),
            ("صافي المبلغ المطلوب", FIELD_TOTAL_AMOUNT),
            ("الصافي", FIELD_TOTAL_AMOUNT),
            ("العملة", FIELD_CURRENCY),
        ],
    )
    def test_map_standard_labels(self, raw_label: str, expected_field: str):
        assert map_arabic_label(raw_label) == expected_field

    def test_fuzzy_matching_and_typos(self):
        # Slight typos or alternate forms
        assert map_arabic_label("رقم الفاتوره الضريبه") == FIELD_INVOICE_NUMBER
        assert map_arabic_label("تاريخ الفاتوره الضريبيه") == FIELD_INVOICE_DATE
        assert map_arabic_label("المجموع الفرعى") == FIELD_SUBTOTAL
        assert map_arabic_label("اسم المشترى") == FIELD_BUYER_NAME

    def test_empty_or_unmapped_labels(self):
        assert map_arabic_label("") is None
        assert map_arabic_label(None) is None
        assert map_arabic_label("شروط الدفع العامة للمورد") is None


class TestLineItemMapping:
    """Tests mapping Arabic line item headers and structured item dictionaries."""

    @pytest.mark.parametrize(
        "raw_label, expected_key",
        [
            ("الوصف", ITEM_DESCRIPTION),
            ("البيان", ITEM_DESCRIPTION),
            ("اسم الصنف", ITEM_DESCRIPTION),
            ("الخدمة", ITEM_DESCRIPTION),
            ("الكمية", ITEM_QUANTITY),
            ("العدد", ITEM_QUANTITY),
            ("سعر الوحدة", ITEM_UNIT_PRICE),
            ("السعر", ITEM_UNIT_PRICE),
            ("المبلغ", ITEM_AMOUNT),
            ("القيمة", ITEM_AMOUNT),
            ("الإجمالي للسطر", ITEM_AMOUNT),
        ],
    )
    def test_map_line_item_key(self, raw_label: str, expected_key: str):
        assert map_line_item_key(raw_label) == expected_key

    def test_map_line_item_dict(self):
        raw_item = {
            "البيان": "خدمات استشارية تقنية",
            "الكمية": 2,
            "سعر الوحدة": 500.0,
            "الإجمالي للسطر": 1000.0,
        }
        mapped = map_line_item(raw_item)
        assert mapped == {
            "description": "خدمات استشارية تقنية",
            "quantity": 2,
            "unit_price": 500.0,
            "amount": 1000.0,
        }


class TestBatchFieldMapping:
    """Tests the high-level map_arabic_fields function on full invoice dictionaries."""

    def test_map_full_saudi_invoice_dict(self):
        raw_invoice_data = {
            "رقم الفاتورة": "INV-2024-001",
            "تاريخ الإصدار": "2024-08-19",
            "اسم المورد": "شركة التقنية المتقدمة المحدودة",
            "الرقم الضريبي للمنشأة": "300123456700003",
            "اسم العميل": "مؤسسة الأفق للتجارة",
            "الرقم الضريبي للعميل": "310987654300003",
            "المجموع قبل الضريبة": "1000.00",
            "ضريبة القيمة المضافة": "150.00",
            "نسبة الضريبة": "15%",
            "المجموع شامل الضريبة": "1150.00",
            "العملة": "SAR",
            "البنود": [
                {
                    "الوصف": "تطوير برمجيات",
                    "الكمية": "1",
                    "سعر الوحدة": "1000.00",
                    "المبلغ": "1000.00",
                }
            ],
        }

        mapped = map_arabic_fields(raw_invoice_data)

        assert mapped["invoice_number"] == "INV-2024-001"
        assert mapped["invoice_date"] == "2024-08-19"
        assert mapped["vendor_name"] == "شركة التقنية المتقدمة المحدودة"
        assert mapped["vendor_vat_number"] == "300123456700003"
        assert mapped["buyer_name"] == "مؤسسة الأفق للتجارة"
        assert mapped["buyer_vat_number"] == "310987654300003"
        assert mapped["subtotal"] == "1000.00"
        assert mapped["tax_amount"] == "150.00"
        assert mapped["tax_rate"] == "15%"
        assert mapped["total_amount"] == "1150.00"
        assert mapped["currency"] == "SAR"
        assert len(mapped["line_items"]) == 1
        assert mapped["line_items"][0]["description"] == "تطوير برمجيات"
        assert mapped["line_items"][0]["amount"] == "1000.00"

    def test_get_canonical_arabic_label(self):
        assert get_canonical_arabic_label("invoice_number") == "رقم الفاتورة"
        assert get_canonical_arabic_label("total_amount") == "المجموع الكلي"
        assert get_canonical_arabic_label("vendor_vat_number") == "الرقم الضريبي للمورد"
        assert get_canonical_arabic_label("unknown_field") == "unknown_field"
