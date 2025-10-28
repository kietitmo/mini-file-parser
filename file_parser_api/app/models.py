from pydantic import BaseModel, Field
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
                "extracted_content": "# Report 2024\n\n## Revenue\n- Increased by 20%.",
            }
        }


