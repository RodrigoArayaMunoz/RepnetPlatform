import os
from fastapi import APIRouter, UploadFile, File, Form
from schemas_vehicle import ImportExcelResponse
from db import SessionLocal
from repositories.compatibility_candidate_repository import CompatibilityCandidateRepository
from tasks.compatibility_import_tasks import import_compatibility_excel_task

router = APIRouter(prefix="/compatibilities", tags=["Compatibility Import"])


@router.post("/import-excel", response_model=ImportExcelResponse)
async def import_excel(
    item_id: str = Form(...),
    file: UploadFile = File(...),
):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    db = SessionLocal()
    try:
        repo = CompatibilityCandidateRepository(db)
        job = repo.create_job(file_name=file.filename, item_id=item_id)
    finally:
        db.close()

    task = import_compatibility_excel_task.delay(job.id, file_path, item_id)

    return ImportExcelResponse(
        message="Importación iniciada",
        job_id=job.id,
        task_id=task.id,
    )