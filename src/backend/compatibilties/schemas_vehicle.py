from pydantic import BaseModel
from typing import Optional


class SyncDictionaryResponse(BaseModel):
    message: str
    task_id: str


class ImportExcelResponse(BaseModel):
    message: str
    job_id: int
    task_id: str


class PublishResponse(BaseModel):
    message: str
    task_id: str


class ImportJobOut(BaseModel):
    id: int
    file_name: str
    item_id: str
    status: str
    total_rows: int
    processed_rows: int
    resolved_rows: int
    error_rows: int

    class Config:
        from_attributes = True


class CandidateOut(BaseModel):
    id: int
    job_id: int
    row_number: int
    item_id: str

    brand_name: Optional[str] = None
    brand_id: Optional[str] = None
    model_name: Optional[str] = None
    model_id: Optional[str] = None
    year_name: Optional[str] = None
    year_id: Optional[str] = None
    version_name: Optional[str] = None
    version_id: Optional[str] = None
    engine_name: Optional[str] = None
    engine_id: Optional[str] = None
    transmission_name: Optional[str] = None
    transmission_id: Optional[str] = None

    product_id: Optional[str] = None
    search_status: str
    publish_status: str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True