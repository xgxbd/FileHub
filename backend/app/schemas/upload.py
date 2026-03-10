from pydantic import BaseModel, Field


class UploadSessionCreateRequest(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    total_size: int = Field(ge=1)
    chunk_size: int = Field(ge=1)
    total_chunks: int = Field(ge=1)
    mime_type: str = Field(default="application/octet-stream", min_length=1, max_length=128)
    file_hash: str | None = Field(default=None, max_length=128)


class UploadSessionResponse(BaseModel):
    upload_id: str
    status: str
    file_name: str
    total_size: int
    chunk_size: int
    total_chunks: int
    uploaded_chunks: list[int]
