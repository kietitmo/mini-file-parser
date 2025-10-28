import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.services.parser_factory import ParserFactory
from app.services.file_service import save_upload_to_temp
from app.models import FileResponse
from app.config import settings
from app.utils import get_logger


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.post("/upload", response_model=FileResponse)
@limiter.limit(settings.rate_limit)
async def upload_file(request: Request, file: UploadFile = File(...)):
    """
    Upload và parse file sang Markdown.
    - Lưu file tạm → parse → xoá file tạm sau khi xử lý xong.
    - Giới hạn tốc độ theo cấu hình rate_limit trong settings.
    """
    temp_path = None
    try:
        logger.info("📤 Upload received: filename=%s content_type=%s", file.filename, file.content_type)

        # Đọc nội dung và lưu tạm
        content = await file.read()
        file_id, temp_path = await save_upload_to_temp(file.filename, content)
        logger.debug("🗂️ File tạm được lưu tại: %s", temp_path)

        # Lấy parser phù hợp
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        parser = ParserFactory.get_parser(file_ext)

        # Parse file sang markdown
        markdown_content = parser.parse(temp_path)
        logger.info("✅ Parsed file successfully: id=%s ext=%s size=%dB", file_id, file_ext, len(content))

        return FileResponse(
            id=file_id,
            file_name=file.filename,
            file_size=len(content),
            file_type=file.content_type,
            extracted_content=markdown_content,
        )

    except Exception as e:
        logger.exception("❌ Failed to process upload: filename=%s error=%s", file.filename, str(e))
        raise HTTPException(status_code=400, detail=f"Lỗi khi xử lý file: {str(e)}")

    finally:
        # Dọn dẹp file tạm, kể cả khi lỗi
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug("🧹 Đã xoá file tạm: %s", temp_path)
            except Exception as cleanup_err:
                logger.warning("⚠️ Không thể xoá file tạm %s: %s", temp_path, cleanup_err)
