import subprocess
import tempfile
import os
from pathlib import Path
from docx import Document
from typing import List
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from app.utils import get_logger
from app.utils.markdown_utils import to_markdown


class DocParser:
    def __init__(self):
        self.logger = get_logger(__name__)

    def _convert_doc_to_docx(self, doc_path: Path) -> Path:
        """Convert file .doc sang .docx bằng LibreOffice (CLI)."""
        temp_dir = tempfile.mkdtemp()
        output_path = Path(temp_dir) / (doc_path.stem + ".docx")

        try:
            self.logger.info(f"🔄 Converting .doc → .docx: {doc_path.name}")
            subprocess.run(
                ["libreoffice", "--headless", "--convert-to", "docx", "--outdir", temp_dir, str(doc_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if not output_path.exists():
                raise FileNotFoundError("Không tạo được file .docx sau khi convert.")
            self.logger.info(f"✅ Convert thành công: {output_path}")
            return output_path
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi convert .doc → .docx: {e}")
            raise

    def _extract_run_text(self, run):
        text = run.text.strip()
        if not text:
            return ""
        if run.bold:
            text = f"**{text}**"
        if run.italic:
            text = f"*{text}*"
        if run.underline:
            text = f"<u>{text}</u>"
        return text

    def _extract_paragraph(self, paragraph):
        return "".join(self._extract_run_text(run) for run in paragraph.runs)

    def _extract_table(self, table):
        rows = []
        for row in table.rows:
            cells = [" ".join(p.text.strip() for p in cell.paragraphs) for cell in row.cells]
            rows.append("| " + " | ".join(cells) + " |")
        if not rows:
            return ""
        header_sep = "|" + "|".join([" --- " for _ in rows[0].split("|") if _.strip()]) + "|"
        return "\n".join([rows[0], header_sep] + rows[1:])

    def _parse_docx(self, file_path: Path) -> str:
        doc = Document(file_path)
        parts: List[str] = []
        for element in doc.element.body:
            if element.tag.endswith("p"):
                from docx.text.paragraph import Paragraph
                p = Paragraph(element, doc)
                text = self._extract_paragraph(p)
                if text.strip():
                    parts.append(text)
            elif element.tag.endswith("tbl"):
                from docx.table import Table
                t = Table(element, doc)
                parts.append(self._extract_table(t))
        return to_markdown("\n\n".join(parts))

    def parse(self, file_path: str) -> str:
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        self.logger.info(f"📄 Đang xử lý file Word: {file_path.name}")

        try:
            if ext == ".docx":
                return self._parse_docx(file_path)

            elif ext == ".doc":
                converted_path = self._convert_doc_to_docx(file_path)
                try:
                    result = self._parse_docx(converted_path)
                finally:
                    # Xóa file tạm sau khi parse xong
                    try:
                        os.remove(converted_path)
                        os.rmdir(converted_path.parent)
                        self.logger.debug(f"🧹 Đã xoá file tạm {converted_path}")
                    except Exception as cleanup_err:
                        self.logger.warning(f"⚠️ Không xoá được file tạm: {cleanup_err}")
                return result

            else:
                self.logger.warning(f"⚠️ Định dạng không hỗ trợ: {ext}")
                return ""

        except Exception as e:
            self.logger.critical(f"🔥 Lỗi nghiêm trọng khi xử lý {file_path.name}: {e}")
            return ""
