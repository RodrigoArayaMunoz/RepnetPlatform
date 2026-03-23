from __future__ import annotations

from math import ceil

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.informed_non_compatible_repository import InformedNonCompatibleRepository
from services.ml_client import ml_client

DEFAULT_BATCH_SIZE = 20
MAX_BATCH_SIZE = 20


async def get_without_compatibilities_with_titles(
    db_session: AsyncSession,
    user_id: int | str,
    access_token: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_BATCH_SIZE,
    q: str | None = None,
) -> dict:
    safe_page = max(1, int(page))
    safe_page_size = max(1, min(int(page_size), MAX_BATCH_SIZE))
    offset = (safe_page - 1) * safe_page_size
    search_text = str(q or "").strip()

    repo = InformedNonCompatibleRepository(db_session)

    total = await repo.count_filtered(search_text=search_text)
    mlcs = await repo.list_mlc_filtered_page(
        limit=safe_page_size,
        offset=offset,
        search_text=search_text,
    )

    if not mlcs:
        total_pages = ceil(total / safe_page_size) if total > 0 else 0
        return {
            "ok": True,
            "items": [],
            "total": total,
            "page": safe_page,
            "page_size": safe_page_size,
            "total_pages": total_pages,
            "has_next": False,
            "has_prev": safe_page > 1,
        }

    items = await ml_client.get_items_multiget(
        item_ids=mlcs,
        access_token=access_token,
        user_id=user_id,
    )

    item_map = {item["id"]: item for item in items}

    results: list[dict] = []
    for mlc in mlcs:
        item = item_map.get(mlc)
        results.append(
            {
                "mlc": mlc,
                "title": item["title"] if item else "",
            }
        )

    total_pages = ceil(total / safe_page_size) if total > 0 else 0

    return {
        "ok": True,
        "items": results,
        "total": total,
        "page": safe_page,
        "page_size": safe_page_size,
        "total_pages": total_pages,
        "has_next": safe_page < total_pages,
        "has_prev": safe_page > 1,
    }