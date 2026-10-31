import os
import hashlib
from typing import Dict, Any, List
import fitz # PyMuPDF
from app.services.ocr_service import ocr_service

import re

def clean_table_cell(text: str) -> str:
    """Cleans up PDF table cell fragments, spacing, and Indian currency notations."""
    if not text:
        return ""
    # Normalize internal whitespace and newlines
    t = " ".join(text.split())
    # Standardize serial number headers
    t = re.sub(r"^Sr\s*[\.\s]*No[\s\.]*", "Sr. No.", t, flags=re.IGNORECASE)
    # Fix broken percentage headers
    t = re.sub(r"%ofSumInsured", "% of Sum Insured", t, flags=re.IGNORECASE)
    # Fix currency formatting with spaced digits e.g. 'Rs 2 00 000 . , ,' -> 'Rs. 2,00,000'
    m_cur = re.search(r'(?:Rs\.?|INR|₹)\s*(\d+)\s+(\d{2})\s+(\d{3})', t, re.IGNORECASE)
    if m_cur:
        t = re.sub(
            r'(?:Rs\.?|INR|₹)\s*(\d+)\s+(\d{2})\s+(\d{3})[\s\.,]*',
            f"Rs. {m_cur.group(1)},{m_cur.group(2)},{m_cur.group(3)}",
            t,
            flags=re.IGNORECASE
        )
    else:
        # Generic spaced Indian thousands/lakhs: e.g. '2 00 000'
        t = re.sub(r'\b(\d)\s+(\d{2})\s+(\d{3})\b', r'\1,\2,\3', t)
        t = re.sub(r'\bRs\.?\s*(\d[\d,]*)', r'Rs. \1', t, flags=re.IGNORECASE)
    # Strip trailing punctuation fragments like '. , ,'
    t = re.sub(r'[\s\.,]+$', '', t)
    return t.strip()

class PDFService:
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def extract_and_format_tables(page: fitz.Page) -> tuple[str, list[dict[str, Any]]]:
        """
        Detects and extracts structured tables from a PDF page using PyMuPDF table finder.
        Normalizes cell contents and converts into searchable markdown tables and explicit
        benefit key-value pairs suitable for SQLite FTS5 search.
        """
        structured_blocks: list[str] = []
        tables_metadata: list[dict[str, Any]] = []

        try:
            tabs = page.find_tables()
            if not tabs or not tabs.tables:
                return "", []

            for tab_idx, tab in enumerate(tabs.tables):
                raw_rows = tab.extract()
                if not raw_rows:
                    continue

                cleaned_rows: list[list[str]] = []
                for r in raw_rows:
                    row_cells = [clean_table_cell(c) for c in r]
                    if any(row_cells):
                        cleaned_rows.append(row_cells)

                if not cleaned_rows:
                    continue

                tables_metadata.append({
                    "table_index": tab_idx,
                    "rows": cleaned_rows
                })

                # Determine header row: if row 0 has only 1 filled cell and row 1 has multiple, row 0 is a title
                header_idx = 0
                if (
                    len(cleaned_rows) > 1
                    and sum(1 for c in cleaned_rows[0] if c) == 1
                    and sum(1 for c in cleaned_rows[1] if c) > 1
                ):
                    header_idx = 1
                    table_title = cleaned_rows[0][0]
                else:
                    table_title = f"Table {tab_idx + 1}"

                headers = cleaned_rows[header_idx]

                table_lines = [f"\n[TABLE: {table_title} (Page {page.number + 1})]\n"]
                table_lines.append("| " + " | ".join(headers) + " |")
                table_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

                for r_idx, row in enumerate(cleaned_rows):
                    if r_idx <= header_idx:
                        continue
                    padded_row = (row + [""] * len(headers))[:len(headers)]
                    table_lines.append("| " + " | ".join(padded_row) + " |")

                    # Check for footnote/note rows: e.g. starts with * or Note
                    first_cell = padded_row[0]
                    if first_cell.startswith("*") or first_cell.lower().startswith("note:"):
                        table_lines.append(f"  [Table Note] {first_cell}")
                        continue

                    # Create explicit semantic benefit/coverage pairs for indexing & retrieval
                    row_pairs = []
                    for h, val in zip(headers, padded_row):
                        if val and h and not re.match(r'^sr\.?\s*no\.?$', h, re.IGNORECASE):
                            row_pairs.append(f"{h}: {val}")
                    if row_pairs:
                        table_lines.append(f"  [Benefit Row] {' | '.join(row_pairs)}")

                structured_blocks.append("\n".join(table_lines))

        except Exception as e:
            print(f"Table extraction note (Page {page.number + 1}): {e}")

        return "\n\n".join(structured_blocks), tables_metadata

    @staticmethod
    def extract_document(file_path: str) -> Dict[str, Any]:
        """
        Extracts document pages using a hybrid pipeline:
        1. PyMuPDF normal digital extraction page-by-page.
        2. Detects, extracts, cleans, and indexes structured tables into page text.
        3. If a page has no usable text or is scanned, render at 250 DPI and route to OCR.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at {file_path}")

        doc = fitz.open(file_path)
        page_count = len(doc)
        pages_data: List[Dict[str, Any]] = []
        
        ocr_used_total = False
        confidence_list: List[float] = []

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_num = page_idx + 1

            # 1. Digital text extraction
            digital_text = page.get_text("text").strip()

            # 2. Extract and format structured tables
            table_text, tables = PDFService.extract_and_format_tables(page)
            has_tables = bool(table_text or len(tables) > 0)

            # Check if digital text is usable (at least 50 characters of non-whitespace text)
            is_usable_digital = len(digital_text) >= 50

            if is_usable_digital:
                if table_text:
                    text = f"{digital_text}\n\n{table_text}"
                else:
                    text = digital_text
                method = "digital"
                conf = 1.0
                needs_review = False
            else:
                # 3. Scanned or low-text page -> render to image at 250 DPI and run OCR
                ocr_used_total = True
                try:
                    pix = page.get_pixmap(dpi=250)
                    ocr_text, conf, engine_name, needs_review = ocr_service.ocr_pixmap(pix, fitz_page=page)
                    base_ocr = ocr_text if ocr_text.strip() else digital_text
                    if table_text:
                        text = f"{base_ocr}\n\n{table_text}"
                    else:
                        text = base_ocr
                    method = f"ocr_{engine_name.lower()}"
                except Exception as e:
                    text = f"[OCR Extraction Error on page {page_num}: {str(e)}]"
                    conf = 0.0
                    method = "ocr_error"
                    needs_review = True

            confidence_list.append(conf)
            pages_data.append({
                "page_number": page_num,
                "text": text,
                "extraction_method": method,
                "ocr_confidence": conf,
                "has_tables": has_tables,
                "needs_review": needs_review
            })

        doc.close()

        avg_conf = sum(confidence_list) / len(confidence_list) if confidence_list else 1.0

        return {
            "page_count": page_count,
            "pages": pages_data,
            "ocr_used": ocr_used_total,
            "ocr_confidence_avg": round(avg_conf, 3)
        }

pdf_service = PDFService()
