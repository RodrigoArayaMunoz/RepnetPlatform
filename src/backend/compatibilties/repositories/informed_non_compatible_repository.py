from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db_models import InformedNonCompatibleMLC


class InformedNonCompatibleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _normalize_mlc(self, mlc: str | None) -> str:
        return str(mlc or "").strip().upper()

    def _normalize_mlcs(self, mlcs: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()

        for mlc in mlcs:
            clean_mlc = self._normalize_mlc(mlc)
            if not clean_mlc:
                continue
            if clean_mlc in seen:
                continue
            seen.add(clean_mlc)
            normalized.append(clean_mlc)

        return normalized

    async def get_by_mlc(self, mlc: str) -> InformedNonCompatibleMLC | None:
        clean_mlc = self._normalize_mlc(mlc)

        if not clean_mlc:
            return None

        stmt = select(InformedNonCompatibleMLC).where(
            InformedNonCompatibleMLC.mlc == clean_mlc
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_existing_mlcs(self, mlcs: list[str]) -> set[str]:
        clean_mlcs = self._normalize_mlcs(mlcs)
        if not clean_mlcs:
            return set()

        stmt = select(InformedNonCompatibleMLC.mlc).where(
            InformedNonCompatibleMLC.mlc.in_(clean_mlcs)
        )
        result = await self.session.execute(stmt)
        return {
            self._normalize_mlc(value)
            for value in result.scalars().all()
            if self._normalize_mlc(value)
        }

    async def bulk_insert_mlcs(
        self,
        mlcs: list[str],
        has_exception: bool = False,
    ) -> int:
        clean_mlcs = self._normalize_mlcs(mlcs)
        if not clean_mlcs:
            return 0

        now = datetime.now(timezone.utc)
        objects = [
            InformedNonCompatibleMLC(
                mlc=mlc,
                informed_at=now,
                updated_at=now,
                has_exception=has_exception,
            )
            for mlc in clean_mlcs
        ]

        self.session.add_all(objects)
        await self.session.flush()
        return len(objects)

    async def bulk_update_mlcs(
        self,
        mlcs: list[str],
        has_exception: bool = False,
    ) -> int:
        clean_mlcs = self._normalize_mlcs(mlcs)
        if not clean_mlcs:
            return 0

        now = datetime.now(timezone.utc)

        stmt = (
            update(InformedNonCompatibleMLC)
            .where(InformedNonCompatibleMLC.mlc.in_(clean_mlcs))
            .values(
                informed_at=now,
                updated_at=now,
                has_exception=has_exception,
            )
        )

        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def upsert_mlc(
        self,
        mlc: str,
        has_exception: bool = False,
    ) -> InformedNonCompatibleMLC:
        clean_mlc = self._normalize_mlc(mlc)
        now = datetime.now(timezone.utc)

        if not clean_mlc:
            raise ValueError("MLC inválido")

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

        clean_search = self._normalize_mlc(search_text)
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

        clean_search = self._normalize_mlc(search_text)
        if clean_search:
            stmt = stmt.where(
                InformedNonCompatibleMLC.mlc.ilike(f"%{clean_search}%")
            )

        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [self._normalize_mlc(x) for x in rows if self._normalize_mlc(x)]