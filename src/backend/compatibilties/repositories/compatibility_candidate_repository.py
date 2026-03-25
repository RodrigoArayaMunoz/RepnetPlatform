import json
from sqlalchemy.orm import Session

from models_vehicle import CompatibilityImportJob, CompatibilityCandidate


class CompatibilityCandidateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, file_name: str, item_id: str) -> CompatibilityImportJob:
        job = CompatibilityImportJob(
            file_name=file_name,
            item_id=item_id,
            status="PENDING",
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job_stats(
        self,
        job_id: int,
        *,
        status: str | None = None,
        total_rows: int | None = None,
        processed_rows: int | None = None,
        resolved_rows: int | None = None,
        error_rows: int | None = None,
    ) -> None:
        job = self.db.query(CompatibilityImportJob).filter(CompatibilityImportJob.id == job_id).first()
        if not job:
            return

        if status is not None:
            job.status = status
        if total_rows is not None:
            job.total_rows = total_rows
        if processed_rows is not None:
            job.processed_rows = processed_rows
        if resolved_rows is not None:
            job.resolved_rows = resolved_rows
        if error_rows is not None:
            job.error_rows = error_rows

        self.db.commit()

    def create_candidate(self, data: dict) -> CompatibilityCandidate:
        if "search_payload" in data and isinstance(data["search_payload"], dict):
            data["search_payload"] = json.dumps(data["search_payload"], ensure_ascii=False)
        if "search_response" in data and isinstance(data["search_response"], dict):
            data["search_response"] = json.dumps(data["search_response"], ensure_ascii=False)
        if "publish_response" in data and isinstance(data["publish_response"], dict):
            data["publish_response"] = json.dumps(data["publish_response"], ensure_ascii=False)

        row = CompatibilityCandidate(**data)
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_job(self, job_id: int):
        return self.db.query(CompatibilityImportJob).filter(CompatibilityImportJob.id == job_id).first()

    def get_candidates_by_job(self, job_id: int):
        return (
            self.db.query(CompatibilityCandidate)
            .filter(CompatibilityCandidate.job_id == job_id)
            .order_by(CompatibilityCandidate.row_number.asc())
            .all()
        )

    def get_resolved_not_sent(self, job_id: int):
        return (
            self.db.query(CompatibilityCandidate)
            .filter(
                CompatibilityCandidate.job_id == job_id,
                CompatibilityCandidate.search_status == "RESOLVED",
                CompatibilityCandidate.publish_status == "NOT_SENT",
            )
            .all()
        )

    def mark_published(self, candidate_id: int, response: dict | str):
        row = self.db.query(CompatibilityCandidate).filter(CompatibilityCandidate.id == candidate_id).first()
        if not row:
            return
        row.publish_status = "SENT"
        row.publish_response = response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)
        self.db.commit()

    def mark_publish_failed(self, candidate_id: int, response: dict | str):
        row = self.db.query(CompatibilityCandidate).filter(CompatibilityCandidate.id == candidate_id).first()
        if not row:
            return
        row.publish_status = "FAILED"
        row.publish_response = response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)
        self.db.commit()