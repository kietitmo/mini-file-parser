from typing import List
from pathlib import Path

import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import numpy as np

from app.utils.markdown_utils import to_markdown
from app.config import settings
from app.utils import get_logger


class PDFParser:
    def __init__(self):
        self.logger = get_logger(__name__)
        pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


    def _is_native_pdf(self, file_path: str, sample_pages: int = 3) -> bool:
        """Kiểm tra PDF có text layer (native) hay là file scan."""
        try:
            with pdfplumber.open(file_path) as pdf:
                if not pdf.pages:
                    self.logger.warning(f"⚠️ File PDF rỗng: {file_path}")
                    return False

                num_pages_to_check = min(len(pdf.pages), sample_pages)
                for i in range(num_pages_to_check):
                    page = pdf.pages[i]
                    text = page.extract_text() or ""
                    if text.strip():
                        self.logger.debug(f"✅ Trang {i + 1} có text layer.")
                        return True
                self.logger.debug(f"🔍 Không phát hiện text layer trong {num_pages_to_check} trang đầu.")
                return False
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi kiểm tra loại PDF ({file_path}): {e}")
            return False


    def _extract_text_native(self, file_path: str) -> str:
        """Trích xuất text từ PDF có text layer."""
        text_parts: List[str] = []
        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                self.logger.info(f"🧾 File có {total_pages} trang (native).")

                for i, page in enumerate(pdf.pages, start=1):
                    try:
                        text = page.extract_text() or ""
                        if text.strip():
                            text_parts.append(text.strip())
                            self.logger.debug(f"📘 Đã đọc trang {i}/{total_pages}")
                        else:
                            self.logger.debug(f"⚪ Trang {i} không có nội dung text.")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Lỗi khi đọc trang {i}: {e}")

            return "\n\n--- Page Break ---\n\n".join(text_parts)
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi trích xuất PDF native: {e}")
            return ""


    def _extract_text_ocr(self, file_path: str) -> str:
        """Trích xuất text từ PDF scan bằng OCR với Tesseract."""
        text_parts: List[str] = []
        try:
            self.logger.info("🔧 Chuyển trang PDF thành ảnh (DPI=300)...")
            images = convert_from_path(file_path, dpi=300)
            total_pages = len(images)
            self.logger.info(f"🖼 OCR {total_pages} trang...")

            for i, img in enumerate(images, start=1):
                try:
                    tesseract_config = r"--oem 3 --psm 6"
                    text = pytesseract.image_to_string(
                        img,
                        lang="vie+eng",
                        config=tesseract_config
                    )
                    text_parts.append(text.strip())
                    self.logger.debug(f"📝 OCR xong trang {i}/{total_pages}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Lỗi OCR trang {i}: {e}")
                    text_parts.append("")

            return "\n\n--- Page Break ---\n\n".join(text_parts)
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi OCR PDF: {e}")
            return ""


    def parse(self, file_path: str) -> str:
        """Hàm chính: phân loại PDF và trích xuất nội dung tương ứng."""
        file_path = str(Path(file_path))
        self.logger.info(f"🔍 Bắt đầu xử lý PDF: {Path(file_path).name}")

        try:
            # Phân loại PDF
            is_native = self._is_native_pdf(file_path)
            self.logger.info(f"📑 PDF '{Path(file_path).name}' là {'native' if is_native else 'scan'}.")

            # Trích xuất nội dung
            if is_native:
                text = self._extract_text_native(file_path)
            else:
                text = self._extract_text_ocr(file_path)

            if not text.strip():
                self.logger.warning(f"⚠️ File {Path(file_path).name} không trích xuất được nội dung.")
                return ""

            markdown_text = to_markdown(text.strip())
            self.logger.info(f"✅ Hoàn tất xử lý PDF: {Path(file_path).name}")
            return markdown_text

        except Exception as e:
            self.logger.critical(f"🔥 Lỗi nghiêm trọng khi xử lý file {file_path}: {e}")
            return ""
