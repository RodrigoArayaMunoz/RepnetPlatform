from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.informed_non_compatible_repository import InformedNonCompatibleRepository
from services.ml_client import ml_client
from config import settings

UNIVERSAL_EXCEPTION_COMMENT = settings.ml_compatibility_exception_comment
VALID_ITEM_COLUMNS = {"item_id", "mlc", "item", "id"}


def _normalize_column_name(value: str) -> str:
    return str(value or "").strip().lower()


def _extract_item_ids_from_excel(file_bytes: bytes) -> list[dict]:
    try:
        df = pd.read_excel(BytesIO(file_bytes))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo leer el archivo Excel: {exc}",
        )

    if df.empty:
        raise HTTPException(status_code=400, detail="El archivo Excel está vacío")

    normalized_map = {
        _normalize_column_name(col): col
        for col in df.columns
    }

    item_col = next(
        (original_col for normalized_col, original_col in normalized_map.items() if normalized_col in VALID_ITEM_COLUMNS),
        None,
    )

    if not item_col:
        raise HTTPException(
            status_code=400,
            detail="No se encontró una columna válida de item_id. Usa una de: item_id, mlc, item, id",
        )

    rows: list[dict] = []
    seen: set[str] = set()

    for idx, row in df.iterrows():
        raw_item_id = row.get(item_col)

        if pd.isna(raw_item_id):
            continue

        item_id = str(raw_item_id).strip()
        if not item_id:
            continue

        if item_id in seen:
            continue

        seen.add(item_id)
        rows.append(
            {
                "row_number": idx + 2,
                "item_id": item_id,
            }
        )

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="No se encontraron item_id válidos en el Excel",
        )

    return rows


async def process_compatibility_exceptions_excel(
    file_bytes: bytes,
    user_id: int | str,
    db_session: AsyncSession,
    access_token: str | None = None,
) -> dict:
    rows = _extract_item_ids_from_excel(file_bytes)

    repo = InformedNonCompatibleRepository(db_session)
    results: list[dict] = []

    for row in rows:
        item_id = row["item_id"]
        row_number = row["row_number"]

        try:
            response = await ml_client.add_item_compatibility_exception(
                access_token=access_token,
                item_id=item_id,
                comment=UNIVERSAL_EXCEPTION_COMMENT,
                user_id=user_id,
            )

            await repo.upsert_mlc(item_id)
            await db_session.commit()

            results.append(
                {
                    "row_number": row_number,
                    "item_id": item_id,
                    "comment": UNIVERSAL_EXCEPTION_COMMENT,
                    "success": True,
                    "status_code": 200,
                    "message": "Excepción cargada correctamente",
                    "response": response,
                }
            )

        except HTTPException as exc:
            await db_session.rollback()
            results.append(
                {
                    "row_number": row_number,
                    "item_id": item_id,
                    "comment": UNIVERSAL_EXCEPTION_COMMENT,
                    "success": False,
                    "status_code": exc.status_code,
                    "message": exc.detail,
                    "response": None,
                }
            )

        except Exception as exc:
            await db_session.rollback()
            results.append(
                {
                    "row_number": row_number,
                    "item_id": item_id,
                    "comment": UNIVERSAL_EXCEPTION_COMMENT,
                    "success": False,
                    "status_code": 500,
                    "message": f"Error inesperado: {exc}",
                    "response": None,
                }
            )

    success_count = sum(1 for x in results if x["success"])
    error_count = len(results) - success_count

    return {
        "ok": True,
        "total": len(results),
        "success": success_count,
        "errors": error_count,
        "universal_comment": UNIVERSAL_EXCEPTION_COMMENT,
        "results": results,
    }