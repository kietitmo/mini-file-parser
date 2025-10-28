import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler


def get_logger(name: str) -> logging.Logger:
    """
    Tạo logger chuẩn:
    - Ghi log ra file (xoay vòng tối đa 5 file, mỗi file 100MB)
    - Hiển thị log trên console
    - Format đẹp, đầy đủ thông tin
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        # === Tạo thư mục logs nếu chưa có ===
        logs_dir = Path("/app/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)

        # === Đặt tên file log chính ===
        log_filename = logs_dir / f"app.log"

        # === Cấu hình định dạng log ===
        formatter = logging.Formatter(
            fmt="%(asctime)s -- [%(levelname)s] -- %(name)s -- %(message)s -- %(filename)s -- line %(lineno)d",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # === Handler 1: Ghi ra file (xoay vòng 5 file, mỗi file 100MB) ===
        file_handler = RotatingFileHandler(
            log_filename,
            maxBytes=100 * 1024 * 1024,  # 100 MB
            backupCount=5,               # Giữ tối đa 5 file log cũ
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)

        # === Handler 2: In ra console ===
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # === Gắn handlers vào logger ===
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        # Log xác nhận khởi tạo
        logger.debug(f"Logger initialized for '{name}' → writing to {log_filename}")

    return logger
