from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "File Parsing API"
    version: str = "1.0.0"
    debug: bool = True
    upload_dir: str = "/tmp/uploads"
    rate_limit: str = "10/minute"
    ocr_lang: str = "vie+eng"
    log_level: str = "DEBUG"

    class Config:
        env_file = ".env"


settings = Settings()


