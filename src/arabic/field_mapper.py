"""
Arabic Field Label to Schema Field Mapper.
Maps diverse Arabic field labels across Saudi (ZATCA), UAE (FTA), and Egyptian (ETA)
invoices to standard canonical schema fields using normalized matching and fuzzy similarity.
"""

import difflib
import re
from typing import Any, Dict, List, Optional, Tuple

from src.arabic.normalizer import normalize_arabic

# Canonical English schema field names
FIELD_INVOICE_NUMBER = "invoice_number"
FIELD_INVOICE_DATE = "invoice_date"
FIELD_DUE_DATE = "due_date"
FIELD_VENDOR_NAME = "vendor_name"
FIELD_VENDOR_ADDRESS = "vendor_address"
FIELD_VENDOR_VAT_NUMBER = "vendor_vat_number"
FIELD_BUYER_NAME = "buyer_name"
FIELD_BUYER_ADDRESS = "buyer_address"
FIELD_BUYER_VAT_NUMBER = "buyer_vat_number"
FIELD_SUBTOTAL = "subtotal"
FIELD_TAX_AMOUNT = "tax_amount"
FIELD_TAX_RATE = "tax_rate"
FIELD_TOTAL_AMOUNT = "total_amount"
FIELD_CURRENCY = "currency"

# Line item schema fields
ITEM_DESCRIPTION = "description"
ITEM_QUANTITY = "quantity"
ITEM_UNIT_PRICE = "unit_price"
ITEM_AMOUNT = "amount"

# Primary canonical Arabic labels for UI display and reporting
CANONICAL_ARABIC_LABELS: Dict[str, str] = {
    FIELD_INVOICE_NUMBER: "رقم الفاتورة",
    FIELD_INVOICE_DATE: "تاريخ الفاتورة",
    FIELD_DUE_DATE: "تاريخ الاستحقاق",
    FIELD_VENDOR_NAME: "اسم المورد",
    FIELD_VENDOR_ADDRESS: "عنوان المورد",
    FIELD_VENDOR_VAT_NUMBER: "الرقم الضريبي للمورد",
    FIELD_BUYER_NAME: "اسم المشتري",
    FIELD_BUYER_ADDRESS: "عنوان المشتري",
    FIELD_BUYER_VAT_NUMBER: "الرقم الضريبي للمشتري",
    FIELD_SUBTOTAL: "المجموع الفرعي",
    FIELD_TAX_AMOUNT: "مبلغ الضريبة",
    FIELD_TAX_RATE: "نسبة الضريبة",
    FIELD_TOTAL_AMOUNT: "المجموع الكلي",
    FIELD_CURRENCY: "العملة",
    ITEM_DESCRIPTION: "الوصف",
    ITEM_QUANTITY: "الكمية",
    ITEM_UNIT_PRICE: "سعر الوحدة",
    ITEM_AMOUNT: "المبلغ",
}

# Comprehensive dialectal and regional variations for MENA invoices
_RAW_FIELD_VARIATIONS: Dict[str, List[str]] = {
    FIELD_INVOICE_NUMBER: [
        "رقم الفاتورة", "رقم الفاتوره", "رقم فاتورة", "رقم فاتوره",
        "الرقم المرجعي", "رقم المرجع", "رقم السند", "رقم الإشعار",
        "رقم الاشعار", "كود الفاتورة", "كود الفاتوره", "رقم الفاتورة الضريبية",
        "رقم الفاتوره الضريبيه", "فاتورة رقم", "فاتوره رقم", "سند رقم", "مرجع رقم", "invoice no",
        "invoice number", "inv no", "invoice #", "inv #",
    ],
    FIELD_INVOICE_DATE: [
        "تاريخ الفاتورة", "تاريخ الفاتوره", "تاريخ الإصدار", "تاريخ الاصدار",
        "التاريخ", "تاريخ التحرير", "تحريرا في", "تاريخ السند", "تاريخ المعاملة",
        "تاريخ البيع", "تاريخ الفاتورة الضريبية", "تاريخ الفاتوره الضريبيه",
        "تاريخ إصدار الفاتورة", "تاريخ اصدار الفاتورة",
        "date", "invoice date", "issue date", "bill date",
    ],
    FIELD_DUE_DATE: [
        "تاريخ الاستحقاق", "تاريخ استحقاق", "تاريخ السداد", "ميعاد السداد",
        "تاريخ الدفع", "تاريخ انتهاء الفاتورة", "مستحق في", "تاريخ الاستحقاق للسداد",
        "due date", "payment due date", "expiry date",
    ],
    FIELD_VENDOR_NAME: [
        "اسم المورد", "اسم البائع", "المورد", "البائع", "اسم الشركة",
        "اسم المؤسسة", "مقدم الخدمة", "اسم المنشأة", "المنشأة", "التاجر",
        "المصدر", "مقدم الفاتورة", "شركة", "مؤسسة",
        "vendor", "vendor name", "seller", "seller name", "supplier", "company name",
    ],
    FIELD_VENDOR_ADDRESS: [
        "عنوان المورد", "عنوان البائع", "عنوان الشركة", "المقر",
        "العنوان", "موقع المنشأة", "عنوان المنشأة", "الفرع", "عنوان الفرع",
        "المركز الرئيسي", "موقع الشركة",
        "vendor address", "seller address", "address", "supplier address",
    ],
    FIELD_VENDOR_VAT_NUMBER: [
        "الرقم الضريبي للمورد", "الرقم الضريبي للبائع", "الرقم الضريبي",
        "رقم التسجيل الضريبي", "الرقم الضريبي للمنشأة", "رقم ضريبة القيمة المضافة",
        "رقم التعريف الضريبي", "رقم ضريبي", "الرقم الضريبي للشركة",
        "رقم تسجيل ضريبة القيمة المضافة", "رقم المنشأة الضريبي",
        "vat number", "vat no", "vat registration no", "trn", "tin", "tax id",
    ],
    FIELD_BUYER_NAME: [
        "اسم المشتري", "اسم العميل", "المشتري", "العميل", "اسم الزبون",
        "الزبون", "المستلم", "السادة", "السيد", "الطرف الثاني", "الفاتورة إلى",
        "فاتورة إلى", "مرسل إليه", "إلى السادة", "المرسل إليه",
        "buyer", "buyer name", "customer", "customer name", "client", "bill to",
    ],
    FIELD_BUYER_ADDRESS: [
        "عنوان المشتري", "عنوان العميل", "عنوان الزبون", "موقع المستلم",
        "عنوان المستلم", "موقع العميل", "عنوان الشحن",
        "buyer address", "customer address", "client address", "ship to",
    ],
    FIELD_BUYER_VAT_NUMBER: [
        "الرقم الضريبي للمشتري", "الرقم الضريبي للعميل", "رقم التسجيل الضريبي للمشتري",
        "الرقم الضريبي للزبون", "رقم ضريبة العميل", "الرقم الضريبي للطرف الثاني",
        "buyer vat", "buyer vat no", "customer vat", "customer vat no",
    ],
    FIELD_SUBTOTAL: [
        "المجموع الفرعي", "المجموع قبل الضريبة", "الإجمالي قبل الضريبة",
        "المبلغ الخاضع للضريبة", "القيمة الخاضعة للضريبة", "القيمة قبل الضريبة",
        "صافي الفاتورة", "المبلغ بدون الضريبة", "المجموع بدون ضريبة",
        "إجمالي المبلغ الخاضع للضريبة", "المبلغ الخاضع لنسبة 15%", "المبلغ الخاضع لنسبة 5%",
        "subtotal", "sub-total", "sub total", "taxable amount", "amount before tax", "net amount",
    ],
    FIELD_TAX_AMOUNT: [
        "مبلغ الضريبة", "قيمة الضريبة", "الضريبة", "ضريبة القيمة المضافة",
        "إجمالي ضريبة القيمة المضافة", "مبلغ ضريبة القيمة المضافة",
        "قيمة ضريبة القيمة المضافة", "ض.ق.م", "م.الضريبة", "ضريبة",
        "tax", "tax amount", "vat", "vat amount", "vat total", "total tax",
    ],
    FIELD_TAX_RATE: [
        "نسبة الضريبة", "معدل الضريبة", "نسبة ضريبة القيمة المضافة",
        "معدل ضريبة القيمة المضافة", "% الضريبة", "نسبة VAT",
        "tax rate", "vat rate", "tax %", "vat %",
    ],
    FIELD_TOTAL_AMOUNT: [
        "المجموع الكلي", "الإجمالي", "المجموع شامل الضريبة", "الإجمالي شامل الضريبة",
        "الصافي", "المبلغ الإجمالي", "إجمالي الفاتورة", "القيمة الإجمالية",
        "المبلغ المطلوب", "المبلغ المستحق", "المجموع النهائي", "صافي المبلغ",
        "إجمالي المبلغ المستحق", "المجموع الصافي", "المبلغ الواجب سداده",
        "total", "total amount", "grand total", "net total", "amount due", "total due",
    ],
    FIELD_CURRENCY: [
        "العملة", "نوع العملة", "رمز العملة", "عملة الفاتورة",
        "currency", "curr",
    ],
}

# Line item key variations
_RAW_ITEM_VARIATIONS: Dict[str, List[str]] = {
    ITEM_DESCRIPTION: [
        "الوصف", "البيان", "التفاصيل", "الصنف", "اسم الصنف", "الخدمة",
        "اسم الخدمة", "بند", "البند", "شرح", "المواصفات", "وصف البند",
        "description", "item", "item description", "particulars", "service",
    ],
    ITEM_QUANTITY: [
        "الكمية", "الكميه", "العدد", "عدد الوحدات", "ك", "الكمية المطلوبة",
        "quantity", "qty", "count", "units",
    ],
    ITEM_UNIT_PRICE: [
        "سعر الوحدة", "سعر الوحده", "السعر", "سعر المفرد", "الفئة",
        "سعر الحبة", "سعر القطعة", "سعر البند",
        "unit price", "price", "rate", "unit cost",
    ],
    ITEM_AMOUNT: [
        "المبلغ", "القيمة", "القيمه", "المجموع", "الإجمالي للسطر",
        "مجموع البند", "إجمالي البند", "قيمة البند", "المبلغ الإجمالي للبند",
        "amount", "total", "item total", "line total", "extended price",
    ],
}


def _normalize_label(label: str) -> str:
    """
    Standardizes label string for dictionary lookups:
    strips diacritics, tatweel, unifies alef/hamza, converts teh marbuta, and lowercases.
    """
    if not label:
        return ""
    norm = normalize_arabic(
        str(label).strip().lower(),
        strip_tashkeel=True,
        strip_tatweel=True,
        norm_alef=True,
        norm_alef_maqsura=True,
        norm_teh_marbuta=True,
        norm_punctuation=True,
    )
    return norm.strip(": -_،,.;")


def _build_normalized_map(raw_map: Dict[str, List[str]]) -> Dict[str, str]:
    """Builds a normalized lookup table mapping normalized labels to schema field keys."""
    lookup: Dict[str, str] = {}
    for field_key, labels in raw_map.items():
        for label in labels:
            lookup[_normalize_label(label)] = field_key
    return lookup


# Pre-built lookup tables
_NORMALIZED_FIELD_MAP = _build_normalized_map(_RAW_FIELD_VARIATIONS)
_NORMALIZED_ITEM_MAP = _build_normalized_map(_RAW_ITEM_VARIATIONS)

# Complete master lookup dictionary
ARABIC_FIELD_MAP: Dict[str, str] = _NORMALIZED_FIELD_MAP.copy()


def get_canonical_arabic_label(field_name: str) -> str:
    """
    Returns the standard/canonical Arabic label for a given schema field name.
    
    Args:
        field_name (str): Schema field name (e.g. 'invoice_number').
        
    Returns:
        str: Canonical Arabic label (e.g. 'رقم الفاتورة').
    """
    return CANONICAL_ARABIC_LABELS.get(field_name, field_name)


def map_arabic_label(label: str, threshold: float = 0.8) -> Optional[str]:
    """
    Maps an Arabic or English label from invoice OCR to a standard schema field name.
    Uses exact normalized lookup first, followed by fuzzy similarity matching.
    
    Args:
        label (str): The raw label text extracted from OCR (e.g. 'رقم الفاتوره', 'الرقم الضريبي').
        threshold (float): Minimum similarity ratio for fuzzy matching (default 0.8).
        
    Returns:
        Optional[str]: Canonical schema field name if mapped, otherwise None.
    """
    if not label or not str(label).strip():
        return None

    clean_label = _normalize_label(label)
    if not clean_label:
        return None

    # 1. Exact normalized match
    if clean_label in _NORMALIZED_FIELD_MAP:
        return _NORMALIZED_FIELD_MAP[clean_label]

    # 1b. Check bilingual split (e.g. 'Date / التاريخ', 'TRN / الرقم الضريبي', 'Subtotal / المجموع الفرعي')
    if "/" in label or "|" in label or " - " in label:
        parts = re.split(r"[/|]|\s+-\s+", label)
        for part in parts:
            part_str = part.strip()
            if part_str:
                clean_part = _normalize_label(part_str)
                if clean_part in _NORMALIZED_FIELD_MAP:
                    return _NORMALIZED_FIELD_MAP[clean_part]

    # 2. Hierarchical Keyword & Compound Heuristics
    # Invoice Number (e.g., "رقم الفاتورة الضريبية", "فاتورة رقم", "Invoice No")
    if ("رقم" in clean_label or "كود" in clean_label or "مرجع" in clean_label or "سند" in clean_label or "no" in clean_label or "number" in clean_label) and ("فاتور" in clean_label or "invoice" in clean_label or "inv" in clean_label):
        return FIELD_INVOICE_NUMBER

    # Invoice Date vs Due Date
    if "تاريخ" in clean_label or "date" in clean_label:
        if any(k in clean_label for k in ["استحقاق", "سداد", "دفع", "انتهاء", "due", "expiry"]):
            return FIELD_DUE_DATE
        if any(k in clean_label for k in ["فاتور", "اصدار", "تحرير", "معامل", "بيع", "invoice", "issue", "bill"]):
            return FIELD_INVOICE_DATE
        return FIELD_INVOICE_DATE

    # Buyer Name & Address
    if any(k in clean_label for k in ["مشتري", "عميل", "زبون", "ساده", "طرف ثاني", "فاتوره الى", "buyer", "customer", "bill to"]):
        if "ضريب" in clean_label or "vat" in clean_label or "trn" in clean_label or "tin" in clean_label:
            return FIELD_BUYER_VAT_NUMBER
        if "عنوان" in clean_label or "address" in clean_label:
            return FIELD_BUYER_ADDRESS
        return FIELD_BUYER_NAME

    # Amounts & Totals
    if "شامل" in clean_label or "نهائي" in clean_label or "مطلوب" in clean_label or "grand" in clean_label:
        if "ضريب" in clean_label or "مجموع" in clean_label or "اجمالي" in clean_label or "مبلغ" in clean_label or "total" in clean_label:
            return FIELD_TOTAL_AMOUNT

    if "فرعي" in clean_label or "قبل الضريب" in clean_label or "بدون ضريب" in clean_label or "خاضع" in clean_label or "subtotal" in clean_label or "sub-total" in clean_label:
        return FIELD_SUBTOTAL

    # Tax Rate
    if ("نسب" in clean_label or "معدل" in clean_label or "%" in clean_label) and ("ضريب" in clean_label or "vat" in clean_label):
        return FIELD_TAX_RATE

    # Vendor VAT Number (e.g., "الرقم الضريبي للمنشأة")
    if "ضريب" in clean_label or "vat" in clean_label or "trn" in clean_label or "tin" in clean_label:
        if "رقم" in clean_label or "تسجيل" in clean_label or "منشاه" in clean_label or "تعريف" in clean_label:
            return FIELD_VENDOR_VAT_NUMBER
        if "مبلغ" in clean_label or "قيمه" in clean_label:
            return FIELD_TAX_AMOUNT

    # 3. Fuzzy similarity matching using difflib
    best_match_field: Optional[str] = None
    best_ratio: float = 0.0

    for known_label, field_key in _NORMALIZED_FIELD_MAP.items():
        ratio = difflib.SequenceMatcher(None, clean_label, known_label).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match_field = field_key

    if best_ratio >= threshold and best_match_field is not None:
        return best_match_field

    return None


def map_line_item_key(label: str, threshold: float = 0.8) -> Optional[str]:
    """
    Maps an Arabic or English line item header/key to a standard item field.
    
    Args:
        label (str): The column/field label for a line item (e.g. 'الوصف', 'الكمية').
        threshold (float): Minimum fuzzy matching similarity threshold.
        
    Returns:
        Optional[str]: 'description', 'quantity', 'unit_price', 'amount', or None.
    """
    if not label or not str(label).strip():
        return None

    clean_label = _normalize_label(label)
    if not clean_label:
        return None

    # 1. Exact normalized match
    if clean_label in _NORMALIZED_ITEM_MAP:
        return _NORMALIZED_ITEM_MAP[clean_label]

    # 1b. Check bilingual split (e.g. 'Description / الوصف', 'Qty / الكمية', 'Unit Price / سعر الوحدة')
    if "/" in label or "|" in label or " - " in label:
        parts = re.split(r"[/|]|\s+-\s+", label)
        for part in parts:
            part_str = part.strip()
            if part_str:
                clean_part = _normalize_label(part_str)
                if clean_part in _NORMALIZED_ITEM_MAP:
                    return _NORMALIZED_ITEM_MAP[clean_part]

    # 2. Keyword heuristics
    if "سعر" in clean_label or "فئة" in clean_label or "price" in clean_label or "rate" in clean_label:
        return ITEM_UNIT_PRICE
    if "كمي" in clean_label or "عدد" in clean_label or "qty" in clean_label:
        return ITEM_QUANTITY
    if "وصف" in clean_label or "بيان" in clean_label or "صنف" in clean_label or "خدم" in clean_label:
        return ITEM_DESCRIPTION
    if "مبلغ" in clean_label or "قيمة" in clean_label or "اجمالي" in clean_label:
        return ITEM_AMOUNT

    # 3. Fuzzy match
    best_match_field: Optional[str] = None
    best_ratio: float = 0.0

    for known_label, item_key in _NORMALIZED_ITEM_MAP.items():
        ratio = difflib.SequenceMatcher(None, clean_label, known_label).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match_field = item_key

    if best_ratio >= threshold and best_match_field is not None:
        return best_match_field

    return None


def map_line_item(item: Dict[str, Any], threshold: float = 0.8) -> Dict[str, Any]:
    """
    Standardizes line item dictionary keys into canonical field names.
    
    Args:
        item (Dict[str, Any]): Raw extracted line item dict.
        threshold (float): Fuzzy matching threshold.
        
    Returns:
        Dict[str, Any]: Standardized line item dict.
    """
    if not item or not isinstance(item, dict):
        return {}

    standardized: Dict[str, Any] = {}
    for key, value in item.items():
        canonical_key = map_line_item_key(str(key), threshold=threshold)
        if canonical_key:
            standardized[canonical_key] = value
        else:
            standardized[key] = value

    return standardized


def map_arabic_fields(ocr_fields: Dict[str, Any], threshold: float = 0.8) -> Dict[str, Any]:
    """
    Transforms a dictionary of OCR extracted key-value pairs with Arabic labels
    into standard extraction schema fields.
    
    Handles line_items arrays recursively if present.
    
    Args:
        ocr_fields (Dict[str, Any]): Dictionary of raw OCR key-value pairs.
        threshold (float): Fuzzy similarity match threshold.
        
    Returns:
        Dict[str, Any]: Dictionary mapped to standard canonical schema fields.
    """
    if not ocr_fields or not isinstance(ocr_fields, dict):
        return {}

    mapped_result: Dict[str, Any] = {}

    for raw_label, value in ocr_fields.items():
        # If the key is already line_items or line item list
        if raw_label in ["line_items", "البنود", "الاصناف", "الأصناف", "items"]:
            if isinstance(value, list):
                mapped_result["line_items"] = [
                    map_line_item(item, threshold=threshold) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                mapped_result["line_items"] = value
            continue

        canonical_field = map_arabic_label(str(raw_label), threshold=threshold)
        if canonical_field:
            mapped_result[canonical_field] = value
        else:
            mapped_result[raw_label] = value

    return mapped_result
