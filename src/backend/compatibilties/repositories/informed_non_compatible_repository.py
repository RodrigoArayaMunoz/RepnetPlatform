from datetime import datetime, timezone

from sqlalchemy import select, func
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

    async def count_filtered(self, search_text: str = "") -> int:
        stmt = select(func.count()).select_from(InformedNonCompatibleMLC).where(
            InformedNonCompatibleMLC.has_exception.is_(True)
        )

        clean_search = str(search_text or "").strip().upper()
        if clean_search:
            stmt = stmt.where(
                InformedNonCompatibleMLC.mlc.ilike(f"%{clean_search}%")
            )

        result = await self.session.execute(stmt)
        return int(result.scalar_one() or 0)

    async def list_mlc_filtered_page(
        self,
        limit: int = 20,
        offset: int = 0,
        search_text: str = "",
    ) -> list[str]:
        stmt = (
            select(InformedNonCompatibleMLC.mlc)
            .where(InformedNonCompatibleMLC.has_exception.is_(True))
            .order_by(
                InformedNonCompatibleMLC.updated_at.desc(),
                InformedNonCompatibleMLC.mlc.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        clean_search = str(search_text or "").strip().upper()
        if clean_search:
            stmt = stmt.where(
                InformedNonCompatibleMLC.mlc.ilike(f"%{clean_search}%")
            )

        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [str(x).strip().upper() for x in rows if x]