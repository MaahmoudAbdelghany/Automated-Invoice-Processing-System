"""
Unified Arabic Preprocessing Pipeline Module (الوحدة الرئيسية).
Coordinates Eastern numeral conversion, Arabic text normalization,
Hijri date detection/conversion, MENA currency detection, and field mapping
between OCR/Textract extraction and downstream NLP / LLM extraction.
"""

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

from src.arabic.currencies import (
    detect_currency,
    extract_currency_and_amount,
    get_country_vat_rate,
    parse_arabic_amount,
)
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
    map_arabic_fields,
    map_line_item,
)
from src.arabic.hijri import (
    HijriMatch,
    detect_hijri_date,
    replace_hijri_with_gregorian,
)
from src.arabic.normalizer import (
    detect_language,
    normalize_arabic,
)
from src.arabic.numerals import to_western_numerals


@dataclass
class PreprocessedInvoiceData:
    """Structured container for the output of the Arabic Preprocessor."""
    detected_language: str = "ar"
    detected_currency: Optional[str] = "SAR"
    statutory_vat_rate: Optional[Decimal] = Decimal("15.0")
    preprocessed_text: str = ""
    raw_text: str = ""
    mapped_fields: Dict[str, Any] = field(default_factory=dict)
    mapped_tables: List[Dict[str, Any]] = field(default_factory=list)
    hijri_conversions: List[Dict[str, Any]] = field(default_factory=list)
    original_ocr_output: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the preprocessed data to a serializable dictionary."""
        data = asdict(self)
        if self.statutory_vat_rate is not None:
            data["statutory_vat_rate"] = float(self.statutory_vat_rate)
        return data


class ArabicPreprocessor:
    """
    Unified Arabic Preprocessing Engine.
    Executes the multi-stage pipeline on OCR text, expense fields, and tables:
    1. Language detection (Arabic-first policy)
    2. Numeral normalization (Eastern/Persian -> Western)
    3. Arabic text normalization (Hamza, Tashkeel, Tatweel, Punctuation)
    4. MENA currency detection & statutory VAT lookup
    5. Hijri date detection & Gregorian conversion
    6. Arabic field label & line item mapping
    """

    def __init__(self, default_currency: str = "SAR"):
        self.default_currency = default_currency

    def preprocess(self, ocr_output: Dict[str, Any]) -> PreprocessedInvoiceData:
        """
        Executes the full Arabic preprocessing pipeline on raw OCR output.

        Args:
            ocr_output (Dict[str, Any]): Dictionary containing:
                - 'raw_text': str (Concatenated OCR text)
                - 'expense_fields': dict (Key-value pairs from OCR)
                - 'tables': list (Detected table rows)
                - 'confidence_scores': dict (Optional confidence metadata)

        Returns:
            PreprocessedInvoiceData: Fully preprocessed and standardized data container.
        """
        if not ocr_output:
            return PreprocessedInvoiceData(
                detected_language="ar",
                detected_currency=self.default_currency,
                statutory_vat_rate=get_country_vat_rate(self.default_currency),
                raw_text="",
                preprocessed_text="",
                original_ocr_output={},
            )

        raw_text = str(ocr_output.get("raw_text", "") or "")
        raw_expense_fields = dict(ocr_output.get("expense_fields", {}) or {})
        raw_tables = list(ocr_output.get("tables", []) or [])

        # Step 1: Language Detection (Arabic-first policy)
        combined_text_for_lang = raw_text + " " + " ".join(
            f"{k} {v}" for k, v in raw_expense_fields.items() if isinstance(v, str)
        )
        detected_lang = detect_language(combined_text_for_lang)

        # Step 2: Numeral Normalization on raw text
        westernized_text = to_western_numerals(raw_text)

        # Step 3: Arabic Text Normalization (Alef, Tashkeel, Tatweel, Punctuation)
        normalized_text = normalize_arabic(
            westernized_text,
            strip_tashkeel=True,
            strip_tatweel=True,
            norm_alef=True,
            norm_alef_maqsura=True,
            norm_teh_marbuta=False,
            norm_punctuation=True,
        )

        # Step 4: Currency & Statutory VAT Rate Detection
        detected_curr = detect_currency(
            raw_text + " " + str(raw_expense_fields), default=self.default_currency
        )
        vat_rate = get_country_vat_rate(detected_curr) if detected_curr else None

        # Step 5: Hijri Date Detection & Conversion in Text
        hijri_matches = detect_hijri_date(raw_text)
        hijri_conversions = [
            {
                "original_text": m.original_text,
                "hijri_year": m.hijri_year,
                "hijri_month": m.hijri_month,
                "hijri_day": m.hijri_day,
                "gregorian_iso": m.gregorian_iso,
            }
            for m in hijri_matches
        ]
        # Replace Hijri dates in text with dual Hijri + Gregorian representation
        preprocessed_text = replace_hijri_with_gregorian(normalized_text)

        # Step 6: Map and Normalize Expense Fields
        mapped_fields = self._process_expense_fields(
            raw_expense_fields, detected_currency=detected_curr
        )

        # Step 7: Map and Normalize Tables / Line Items
        mapped_tables = self._process_tables(raw_tables)

        return PreprocessedInvoiceData(
            detected_language=detected_lang,
            detected_currency=detected_curr,
            statutory_vat_rate=vat_rate,
            preprocessed_text=preprocessed_text,
            raw_text=raw_text,
            mapped_fields=mapped_fields,
            mapped_tables=mapped_tables,
            hijri_conversions=hijri_conversions,
            original_ocr_output=deepcopy(ocr_output),
        )

    def _process_expense_fields(
        self, raw_fields: Dict[str, Any], detected_currency: Optional[str]
    ) -> Dict[str, Any]:
        """
        Maps raw Arabic field labels to schema keys and cleans / normalizes their values.
        """
        if not raw_fields:
            return {}

        # 1. Map raw Arabic labels to canonical schema keys
        mapped = map_arabic_fields(raw_fields)
        cleaned_fields: Dict[str, Any] = {}

        monetary_fields = {
            FIELD_TOTAL_AMOUNT,
            FIELD_SUBTOTAL,
            FIELD_TAX_AMOUNT,
        }

        date_fields = {
            FIELD_INVOICE_DATE,
            FIELD_DUE_DATE,
        }

        for key, val in mapped.items():
            if val is None:
                cleaned_fields[key] = None
                continue

            str_val = str(val).strip()

            # Handle monetary fields (amounts)
            if key in monetary_fields:
                parsed_amount = parse_arabic_amount(str_val)
                if parsed_amount is not None:
                    cleaned_fields[key] = parsed_amount
                else:
                    cleaned_fields[key] = to_western_numerals(str_val)

            # Handle date fields (Hijri conversion if applicable)
            elif key in date_fields:
                hijri_matches = detect_hijri_date(str_val)
                if hijri_matches:
                    # Use the converted Gregorian ISO date
                    cleaned_fields[key] = hijri_matches[0].gregorian_iso
                else:
                    # Westernize numerals and clean
                    cleaned_fields[key] = to_western_numerals(str_val)

            # Handle tax rate (percentage)
            elif key == FIELD_TAX_RATE:
                parsed_rate = parse_arabic_amount(str_val)
                if parsed_rate is not None:
                    cleaned_fields[key] = parsed_rate
                else:
                    cleaned_fields[key] = to_western_numerals(str_val)

            # Handle currency field
            elif key == FIELD_CURRENCY:
                curr = detect_currency(str_val, default=detected_currency)
                cleaned_fields[key] = curr or str_val

            # Handle text fields (Vendor name, addresses, VAT number)
            else:
                western_val = to_western_numerals(str_val)
                norm_val = normalize_arabic(
                    western_val,
                    strip_tashkeel=True,
                    strip_tatweel=True,
                    norm_alef=True,
                    norm_alef_maqsura=True,
                    norm_teh_marbuta=False,
                    norm_punctuation=True,
                )
                cleaned_fields[key] = norm_val

        return cleaned_fields

    def _process_tables(self, raw_tables: List[Any]) -> List[Dict[str, Any]]:
        """
        Normalizes line items and tables: maps column headers and normalizes cell values.
        """
        if not raw_tables:
            return []

        processed_rows: List[Dict[str, Any]] = []

        for row in raw_tables:
            if not isinstance(row, dict):
                continue

            mapped_row = map_line_item(row)
            cleaned_row: Dict[str, Any] = {}

            for col_key, col_val in mapped_row.items():
                if col_val is None:
                    cleaned_row[col_key] = None
                    continue

                str_val = str(col_val).strip()

                if col_key in (ITEM_UNIT_PRICE, ITEM_AMOUNT, ITEM_QUANTITY):
                    parsed_num = parse_arabic_amount(str_val)
                    if parsed_num is not None:
                        cleaned_row[col_key] = parsed_num
                    else:
                        cleaned_row[col_key] = to_western_numerals(str_val)
                elif col_key == ITEM_DESCRIPTION:
                    norm_desc = normalize_arabic(
                        to_western_numerals(str_val),
                        strip_tashkeel=True,
                        strip_tatweel=True,
                        norm_alef=True,
                        norm_alef_maqsura=True,
                        norm_teh_marbuta=False,
                        norm_punctuation=True,
                    )
                    cleaned_row[col_key] = norm_desc
                else:
                    cleaned_row[col_key] = to_western_numerals(str_val)

            processed_rows.append(cleaned_row)

        return processed_rows


# Global default instance
_default_preprocessor = ArabicPreprocessor()


def preprocess_arabic_invoice(
    ocr_output: Dict[str, Any], default_currency: str = "SAR"
) -> PreprocessedInvoiceData:
    """
    Convenience functional API for running the unified Arabic preprocessing pipeline.

    Args:
        ocr_output (Dict[str, Any]): Raw OCR dictionary.
        default_currency (str): Fallback currency (default 'SAR').

    Returns:
        PreprocessedInvoiceData: Standardized preprocessed invoice data.
    """
    if default_currency == "SAR":
        return _default_preprocessor.preprocess(ocr_output)
    preprocessor = ArabicPreprocessor(default_currency=default_currency)
    return preprocessor.preprocess(ocr_output)


def preprocess(ocr_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node entry point for the Arabic preprocessing step.
    Converts OCR output to a standardized preprocessed dictionary.

    Args:
        ocr_output (Dict[str, Any]): The OCR state output.

    Returns:
        Dict[str, Any]: Preprocessed state dictionary.
    """
    result = _default_preprocessor.preprocess(ocr_output)
    return result.to_dict()
