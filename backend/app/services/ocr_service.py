import io
import os
from typing import Tuple, Dict, Any

class BaseOCREngine:
    def is_available(self) -> bool:
        raise NotImplementedError

    def extract_text(self, image_bytes: bytes) -> Tuple[str, float, bool]:
        """Returns: (extracted_text, confidence_score_0_to_1, needs_manual_review)"""
        raise NotImplementedError


class PaddleOCREngine(BaseOCREngine):
    """PaddleOCR 3.x local pipeline implementation"""
    def __init__(self):
        self._available = False
        self._ocr = None
        try:
            from paddleocr import PaddleOCR
            # Initialize CPU mode
            self._ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            self._available = True
        except Exception as e:
            self._available = False
            self._init_error = str(e)

    def is_available(self) -> bool:
        return self._available

    def extract_text(self, image_bytes: bytes) -> Tuple[str, float, bool]:
        if not self._available or not self._ocr:
            return "", 0.0, True

        import numpy as np
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(image)
        
        result = self._ocr.ocr(img_np, cls=True)
        if not result or not result[0]:
            return "", 0.0, True

        lines = []
        confidences = []
        for line in result[0]:
            text = line[1][0]
            conf = float(line[1][1])
            lines.append(text)
            confidences.append(conf)

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        full_text = "\n".join(lines)
        needs_review = avg_conf < 0.70 or len(full_text.strip()) < 30
        return full_text, avg_conf, needs_review


class TesseractOCREngine(BaseOCREngine):
    """Tesseract OCR fallback using pytesseract or PyMuPDF OCR integration"""
    def __init__(self):
        self._available = False
        try:
            import pytesseract
            # Test if tesseract executable is callable
            pytesseract.get_tesseract_version()
            self._available = True
        except Exception:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def extract_text(self, image_bytes: bytes) -> Tuple[str, float, bool]:
        if not self._available:
            return "", 0.0, True

        import pytesseract
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        words = []
        confs = []
        for word, conf in zip(data["text"], data["conf"]):
            if word.strip():
                words.append(word)
                if conf != "-1":
                    confs.append(float(conf) / 100.0)

        full_text = " ".join(words)
        avg_conf = sum(confs) / len(confs) if confs else 0.0
        needs_review = avg_conf < 0.65 or len(full_text.strip()) < 30
        return full_text, avg_conf, needs_review


class PyMuPDFOCREngine(BaseOCREngine):
    """PyMuPDF built-in OCR (uses Tesseract C-API if installed)"""
    def __init__(self):
        self._available = False
        try:
            import fitz
            # Check if fitz has OCR capability compiled
            self._available = hasattr(fitz, "get_textpage_ocr") or hasattr(fitz.Page, "get_textpage_ocr")
        except Exception:
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def extract_text_from_fitz_page(self, page) -> Tuple[str, float, bool]:
        try:
            tp = page.get_textpage_ocr(flags=0, dpi=250, full=True)
            text = tp.extractText()
            if text and len(text.strip()) > 30:
                return text, 0.85, False
        except Exception:
            pass
        return "", 0.0, True


class FallbackHeuristicEngine(BaseOCREngine):
    """Graceful fallback when no C-binary OCR engine is installed on Windows"""
    def is_available(self) -> bool:
        return True

    def extract_text(self, image_bytes: bytes) -> Tuple[str, float, bool]:
        # Clearly marked fallback; does not invent text, notifies user that manual review is needed
        msg = (
            "[OCR NOTICE: Image-only scanned page detected. Local OCR binary (Tesseract/PaddleOCR) "
            "is not installed or configured on this machine. Please review original document or install Tesseract.]"
        )
        return msg, 0.20, True


class OCRService:
    """Unified OCR Service routing to the best available local engine"""
    def __init__(self):
        self.paddle = PaddleOCREngine()
        self.tesseract = TesseractOCREngine()
        self.mupdf_ocr = PyMuPDFOCREngine()
        self.fallback = FallbackHeuristicEngine()

    def get_status(self) -> Dict[str, Any]:
        return {
            "paddleocr": self.paddle.is_available(),
            "tesseract": self.tesseract.is_available(),
            "mupdf_ocr": self.mupdf_ocr.is_available(),
            "active_engine": (
                "PaddleOCR" if self.paddle.is_available() else
                "Tesseract" if self.tesseract.is_available() else
                "PyMuPDF-OCR" if self.mupdf_ocr.is_available() else
                "Heuristic Fallback"
            )
        }

    def ocr_pixmap(self, pixmap, fitz_page=None) -> Tuple[str, float, str, bool]:
        """
        Takes a PyMuPDF Pixmap or Page and extracts OCR text.
        Returns: (extracted_text, confidence, engine_name, needs_review)
        """
        # Try PyMuPDF page OCR if page is passed
        if fitz_page and self.mupdf_ocr.is_available():
            text, conf, needs_review = self.mupdf_ocr.extract_text_from_fitz_page(fitz_page)
            if text and not needs_review:
                return text, conf, "PyMuPDF-OCR", False

        # Convert pixmap to PNG bytes
        img_bytes = pixmap.tobytes("png")

        if self.paddle.is_available():
            text, conf, needs_review = self.paddle.extract_text(img_bytes)
            if text:
                return text, conf, "PaddleOCR", needs_review

        if self.tesseract.is_available():
            text, conf, needs_review = self.tesseract.extract_text(img_bytes)
            if text:
                return text, conf, "Tesseract", needs_review

        text, conf, needs_review = self.fallback.extract_text(img_bytes)
        return text, conf, "Fallback", True

ocr_service = OCRService()
