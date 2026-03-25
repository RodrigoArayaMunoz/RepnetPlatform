from fastapi import APIRouter
from schemas_vehicle import PublishResponse, ImportJobOut, CandidateOut
from db import SessionLocal
from repositories.compatibility_candidate_repository import CompatibilityCandidateRepository
from tasks.compatibility_publish_tasks import publish_compatibilities_task

router = APIRouter(prefix="/compatibilities", tags=["Compatibility Publish"])


@router.post("/publish/{job_id}", response_model=PublishResponse)
def publish_compatibilities(job_id: int):
    task = publish_compatibilities_task.delay(job_id)
    return PublishResponse(
        message="Publicación de compatibilidades iniciada",
        task_id=task.id,
    )


@router.get("/jobs/{job_id}", response_model=ImportJobOut)
def get_job(job_id: int):
    db = SessionLocal()
    try:
        repo = CompatibilityCandidateRepository(db)
        job = repo.get_job(job_id)
        return job
    finally:
        db.close()


@router.get("/jobs/{job_id}/rows", response_model=list[CandidateOut])
def get_job_rows(job_id: int):
    db = SessionLocal()
    try:
        repo = CompatibilityCandidateRepository(db)
        return repo.get_candidates_by_job(job_id)
    finally:
        db.close()