from celery.utils.log import get_task_logger
from db import SessionLocal

from celery_app import celery_app
from repositories.vehicle_dictionary_repository import VehicleDictionaryRepository
from repositories.compatibility_candidate_repository import CompatibilityCandidateRepository
from services.excel_compatibility_service import ExcelCompatibilityService

logger = get_task_logger(__name__)


@celery_app.task(name="import_compatibility_excel_task")
def import_compatibility_excel_task(job_id: int, file_path: str, item_id: str):
    db = SessionLocal()
    try:
        dict_repo = VehicleDictionaryRepository(db)
        candidate_repo = CompatibilityCandidateRepository(db)
        service = ExcelCompatibilityService(dict_repo)

        df = service.read_excel(file_path)
        candidate_repo.update_job_stats(job_id, status="PROCESSING", total_rows=len(df))

        processed = 0
        resolved = 0
        errors = 0

        for idx, row in df.iterrows():
            data = service.process_row(row.to_dict(), item_id=item_id, row_number=idx + 2)
            data["job_id"] = job_id
            candidate_repo.create_candidate(data)

            processed += 1
            if data["search_status"] == "RESOLVED":
                resolved += 1
            elif data["search_status"] in ["ERROR", "NOT_FOUND", "AMBIGUOUS"]:
                errors += 1

        candidate_repo.update_job_stats(
            job_id,
            status="DONE",
            processed_rows=processed,
            resolved_rows=resolved,
            error_rows=errors,
        )

        return {"status": "success", "job_id": job_id}
    finally:
        db.close()