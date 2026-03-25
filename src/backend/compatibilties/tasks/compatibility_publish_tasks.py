from celery.utils.log import get_task_logger
from db import SessionLocal

from celery_app import celery_app
from repositories.compatibility_candidate_repository import CompatibilityCandidateRepository
from services.compatibility_publish_service import CompatibilityPublishService

logger = get_task_logger(__name__)


@celery_app.task(name="publish_compatibilities_task")
def publish_compatibilities_task(job_id: int):
    db = SessionLocal()
    try:
        repo = CompatibilityCandidateRepository(db)
        service = CompatibilityPublishService()

        rows = repo.get_resolved_not_sent(job_id)
        sent = 0
        failed = 0

        for row in rows:
            try:
                response = service.publish_candidate(item_id=row.item_id, product_id=row.product_id)
                repo.mark_published(row.id, response)
                sent += 1
            except Exception as exc:
                repo.mark_publish_failed(row.id, {"error": str(exc)})
                failed += 1

        return {"status": "success", "job_id": job_id, "sent": sent, "failed": failed}
    finally:
        db.close()