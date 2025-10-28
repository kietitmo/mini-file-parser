# 📘 File Parsing API – Technical Design Document

## 1. 🎯 Mục tiêu

Xây dựng một **FastAPI service** có khả năng:

* Nhận upload file (PDF scan/native, DOC/DOCX, PPTX, XLSX)
* Trích xuất nội dung dưới dạng **Markdown**
* Trả về metadata file + nội dung parse
* Giới hạn tần suất truy cập (rate limiting)
* Có **cấu hình linh hoạt** qua Pydantic Settings
* **Clean code**, **SOLID**, **Design pattern**

---

## 2. 🧩 Công nghệ sử dụng

| Chức năng           | Công cụ / Thư viện                |
| ------------------- | --------------------------------- |
| Web Framework       | FastAPI                           |
| Model Validation    | Pydantic v2                       |
| Rate limiting       | slowapi                           |
| PDF Native          | pdfplumber hoặc PyMuPDF           |
| PDF Scan            | pdf2image + pytesseract           |
| DOC/DOCX            | python-docx                       |
| PPTX                | python-pptx                       |
| XLSX                | pandas / openpyxl                 |
| Markdown conversion | markdownify hoặc custom converter |
| Logging             | built-in logging                  |
| File I/O            | aiofiles                          |

---

## 3. 🧱 Kiến trúc & Cấu trúc dự án

### Clean Architecture Overview

```
┌────────────────────────────┐
│        API Layer           │   → FastAPI endpoint
├────────────────────────────┤
│    Service Layer           │   → Business logic (parser factory, file service)
├────────────────────────────┤
│     Domain Layer           │   → Parsers, models (BaseParser, FileMetadata)
├────────────────────────────┤
│ Infrastructure Layer       │   → File I/O, settings, OCR tools, libraries
└────────────────────────────┘
```

### Folder Structure

```
file_parser_api/
├── app/
│   ├── main.py
│   ├── config.py                # Pydantic Settings
│   ├── models.py                # Pydantic models
│   ├── utils/
│   │   └── markdown_utils.py
│   ├── parsers/
│   │   ├── base_parser.py
│   │   ├── pdf_parser.py
│   │   ├── doc_parser.py
│   │   ├── ppt_parser.py
│   │   └── xlsx_parser.py
│   ├── services/
│   │   ├── parser_factory.py
│   │   └── file_service.py
│   └── api/
│       └── endpoints.py         # Upload endpoint
├── tests/
│   └── test_upload.py
├── requirements.txt
└── README.md
```

---

## 4. ⚙️ Pydantic Models

### 4.1 File Metadata & Response Model

```python
# app/models.py
from pydantic import BaseModel, Field
from typing import Optional
import uuid

class FileResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique file ID")
    filename: str
    size: int
    mime_type: str
    extracted_content: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "7e5f32f8-47a0-4b6b-b321-9c6e379b64d1",
                "filename": "report.pdf",
                "size": 1048576,
                "mime_type": "application/pdf",
                "extracted_content": "# Report 2024\n\n## Revenue\n- Increased by 20%."
            }
        }
```

### 4.2 App Settings (Config via Environment)

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "File Parsing API"
    version: str = "1.0.0"
    debug: bool = True
    upload_dir: str = "/tmp/uploads"
    rate_limit: str = "10/minute"
    ocr_lang: str = "eng"

    class Config:
        env_file = ".env"

settings = Settings()
```

> ✅ Bạn có thể cấu hình qua file `.env`:

```
APP_NAME="File Parsing API"
DEBUG=True
UPLOAD_DIR="/tmp/uploads"
RATE_LIMIT="20/minute"
OCR_LANG="vie"
```

---

## 5. 🧠 Domain Layer (Base Parser Interface)

```python
# app/parsers/base_parser.py
from abc import ABC, abstractmethod

class BaseParser(ABC):
    """Interface cho mọi parser"""
    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Trả về nội dung file dạng Markdown"""
        pass
```

---

## 6. 🧩 Cụ thể từng parser

### 6.1 PDF Parser (native + OCR)

```python
# app/parsers/pdf_parser.py
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from app.utils.markdown_utils import to_markdown
from app.config import settings

class PDFParser:
    def parse(self, file_path: str) -> str:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        if not text.strip():
            images = convert_from_path(file_path)
            for img in images:
                text += pytesseract.image_to_string(img, lang=settings.ocr_lang)

        return to_markdown(text)
```

### 6.2 DOC/DOCX Parser

```python
# app/parsers/doc_parser.py
from docx import Document
from app.utils.markdown_utils import to_markdown

class DocParser:
    def parse(self, file_path: str) -> str:
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
        return to_markdown(text)
```

### 6.3 PPTX Parser

```python
# app/parsers/ppt_parser.py
from pptx import Presentation
from app.utils.markdown_utils import to_markdown

class PPTParser:
    def parse(self, file_path: str) -> str:
        prs = Presentation(file_path)
        slides = []
        for i, slide in enumerate(prs.slides, start=1):
            content = [shape.text for shape in slide.shapes if hasattr(shape, "text")]
            slides.append(f"## Slide {i}\n" + "\n".join(content))
        return to_markdown("\n\n".join(slides))
```

### 6.4 XLSX Parser

```python
# app/parsers/xlsx_parser.py
import pandas as pd

class XLSXParser:
    def parse(self, file_path: str) -> str:
        xls = pd.ExcelFile(file_path)
        md = ""
        for sheet in xls.sheet_names:
            df = xls.parse(sheet)
            md += f"## Sheet: {sheet}\n"
            md += df.to_markdown(index=False)
            md += "\n\n"
        return md
```

---

## 7. 🏭 Parser Factory

```python
# app/services/parser_factory.py
from app.parsers.pdf_parser import PDFParser
from app.parsers.doc_parser import DocParser
from app.parsers.ppt_parser import PPTParser
from app.parsers.xlsx_parser import XLSXParser

class ParserFactory:
    """Factory Pattern chọn parser theo extension"""
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
```

---

## 8. 🧰 Markdown Utils

```python
# app/utils/markdown_utils.py
import re

def to_markdown(text: str) -> str:
    """Chuẩn hóa nội dung text sang Markdown"""
    text = text.replace("\r", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"•|- ", "- ", text)
    text = text.strip()
    return text
```

---

## 9. 🌐 API Endpoint (với Rate Limit)

```python
# app/api/endpoints.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uuid, aiofiles, os

from app.services.parser_factory import ParserFactory
from app.models import FileResponse
from app.config import settings

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/upload", response_model=FileResponse)
@limiter.limit(settings.rate_limit)
async def upload_file(file: UploadFile = File(...)):
    file_ext = file.filename.split(".")[-1].lower()
    file_id = str(uuid.uuid4())
    temp_path = os.path.join(settings.upload_dir, f"{file_id}.{file_ext}")

    os.makedirs(settings.upload_dir, exist_ok=True)

    async with aiofiles.open(temp_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    try:
        parser = ParserFactory.get_parser(file_ext)
        markdown_content = parser.parse(temp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return FileResponse(
        id=file_id,
        filename=file.filename,
        size=len(content),
        mime_type=file.content_type,
        extracted_content=markdown_content
    )
```

---

## 10. 🚀 Main Application

```python
# app/main.py
from fastapi import FastAPI
from app.api import endpoints
from app.config import settings
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

app.include_router(endpoints.router)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Chạy thử:

```bash
uvicorn app.main:app --reload
```

---

## 11. ✅ Ưu điểm tổng thể

| Tiêu chí                        | Đáp ứng                                              |
| ------------------------------- | ---------------------------------------------------- |
| **Code sạch (Clean Code)**      | ✅ Có phân tầng rõ ràng (API, Service, Domain, Utils) |
| **Tuân thủ SOLID**              | ✅ Mỗi parser 1 nhiệm vụ, mở rộng dễ dàng             |
| **Config linh hoạt (Pydantic)** | ✅ Dễ thay đổi qua `.env`                             |
| **Rate limiting**               | ✅ Có giới hạn request/IP                             |
| **Output Markdown**             | ✅ Chuẩn hóa nội dung parse                           |
| **Dễ mở rộng**                  | ✅ Thêm parser mới chỉ cần thêm subclass + mapping    |

---

## 12. 🔮 Hướng mở rộng tương lai

* 🧵 Thêm xử lý bất đồng bộ (async parser)
* 🧠 Cache kết quả parse (Redis)
* 🔐 Thêm JWT hoặc API key auth
* 📦 Lưu file đã parse vào DB hoặc S3
* 📈 Monitoring (Prometheus / OpenTelemetry)

---

## 13. 🐳 Docker hóa & Chạy nhanh

### 13.1 Build & Run với Docker

```bash
cd file_parser_api
docker build -t file-parser-api .
docker run --rm -p 8000:8000 \
  -e APP_NAME="File Parsing API" \
  -e DEBUG=true \
  -e UPLOAD_DIR=/tmp/uploads \
  -e RATE_LIMIT="10/minute" \
  -e OCR_LANG=eng \
  -v $(pwd)/uploads:/tmp/uploads \
  file-parser-api
```

Mở API docs ở: `http://localhost:8000/docs`

### 13.2 Docker Compose

```bash
cd file_parser_api
docker compose up -d --build
```

Compose đã mount thư mục `./uploads` vào container (`/tmp/uploads`).

### 13.3 Biến môi trường hỗ trợ

- `APP_NAME` (mặc định: "File Parsing API")
- `DEBUG` (mặc định: `True`)
- `UPLOAD_DIR` (mặc định: `/tmp/uploads`)
- `RATE_LIMIT` (mặc định: `10/minute`)
- `OCR_LANG` (mặc định: `eng`)
- `LOG_LEVEL` (mặc định: `INFO`) — thay đổi mức log (`DEBUG`, `INFO`, `WARNING`, ...)

> Lưu ý: Ảnh hưởng đến OCR/PDF
>
> - Image đã cài sẵn `tesseract-ocr` và `poppler-utils` để OCR scan PDF và convert ảnh từ PDF.
> - Nếu cần ngôn ngữ OCR khác, thêm gói tesseract tương ứng vào Dockerfile (ví dụ: `tesseract-ocr-vie`).

### 13.4 Logging

- Cấu hình qua `LOG_LEVEL` hoặc sửa `settings.log_level`.
- Log format: `timestamp level logger - message`.
- Ví dụ bật debug:
```bash
LOG_LEVEL=DEBUG docker compose up -d --build
```

