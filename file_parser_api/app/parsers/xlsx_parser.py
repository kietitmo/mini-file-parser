import pandas as pd
from pathlib import Path
from app.utils import get_logger
from app.utils.markdown_utils import to_markdown


class XLSXParser:
    def __init__(self):
        self.logger = get_logger(__name__)

    def _parse_sheet(self, xls: pd.ExcelFile, sheet_name: str) -> str:
        """Đọc và chuyển 1 sheet thành markdown."""
        try:
            self.logger.debug(f"📄 Đang đọc sheet: {sheet_name}")
            df = xls.parse(sheet_name)

            if df.empty:
                self.logger.debug(f"⚪ Sheet '{sheet_name}' trống.")
                return f"## Sheet: {sheet_name}\n*(Sheet trống)*"

            md_table = df.to_markdown(index=False)
            self.logger.debug(f"✅ Đọc xong sheet '{sheet_name}' ({df.shape[0]} hàng × {df.shape[1]} cột).")

            return f"## Sheet: {sheet_name}\n\n{md_table}\n"
        except Exception as e:
            self.logger.warning(f"⚠️ Lỗi khi đọc sheet '{sheet_name}': {e}")
            return f"## Sheet: {sheet_name}\n*(Không thể đọc nội dung do lỗi)*"

    def parse(self, file_path: str) -> str:
        """Phân tích file Excel và chuyển toàn bộ nội dung sang Markdown."""
        file_path = Path(file_path)
        self.logger.info(f"📊 Bắt đầu parsing Excel: {file_path.name}")

        try:
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            self.logger.info(f"📑 File '{file_path.name}' có {len(sheet_names)} sheet: {', '.join(sheet_names)}")

            md_parts = []
            for sheet in sheet_names:
                md_parts.append(self._parse_sheet(xls, sheet))

            result = "\n\n--- Sheet Break ---\n\n".join(md_parts)
            markdown_text = to_markdown(result.strip())

            self.logger.info(f"✅ Hoàn tất parsing Excel: {file_path.name}")
            return markdown_text

        except Exception as e:
            self.logger.critical(f"🔥 Lỗi nghiêm trọng khi xử lý Excel '{file_path.name}': {e}")
            return ""
