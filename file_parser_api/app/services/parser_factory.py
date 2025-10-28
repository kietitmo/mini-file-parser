from app.parsers.pdf_parser import PDFParser
from app.parsers.doc_parser import DocParser
from app.parsers.ppt_parser import PPTParser
from app.parsers.xlsx_parser import XLSXParser


class ParserFactory:
    """Factory Pattern to choose parser based on file extension."""

    @staticmethod
    def get_parser(ext: str):
        mapping = {
            "pdf": PDFParser(),
            "doc": DocParser(),
            "docx": DocParser(),
            "pptx": PPTParser(),
            "xlsx": XLSXParser(),
        }
        parser = mapping.get(ext.lower())
        if not parser:
            raise ValueError(f"Unsupported file type: {ext}")
        return parser


