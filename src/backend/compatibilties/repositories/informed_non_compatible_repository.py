# src/backend/compatibilities/repositories/informed_non_compatible_repository.py
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db_models import InformedNonCompatibleMLC


class InformedNonCompatibleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_mlc(self, mlc: str) -> InformedNonCompatibleMLC | None:
        clean_mlc = str(mlc).strip().upper()

        stmt = select(InformedNonCompatibleMLC).where(
            InformedNonCompatibleMLC.mlc == clean_mlc
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_mlc(
        self,
        mlc: str,
        has_exception: bool = False,
    ) -> InformedNonCompatibleMLC:
        clean_mlc = str(mlc).strip().upper()
        now = datetime.now(timezone.utc)

        existing = await self.get_by_mlc(clean_mlc)
        if existing:
            existing.informed_at = now
            existing.updated_at = now
            existing.has_exception = has_exception
            await self.session.flush()
            return existing

        obj = InformedNonCompatibleMLC(
            mlc=clean_mlc,
            informed_at=now,
            updated_at=now,
            has_exception=has_exception,
        )
        self.session.add(obj)
        await self.session.flush()
        return obj