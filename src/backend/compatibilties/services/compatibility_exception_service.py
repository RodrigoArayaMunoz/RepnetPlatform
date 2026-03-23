from __future__ import annotations

from io import BytesIO

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from repositories.informed_non_compatible_repository import InformedNonCompatibleRepository
from services.ml_client import ml_client

UNIVERSAL_EXCEPTION_COMMENT = settings.ml_compatibility_exception_comment
VALID_ITEM_COLUMNS = {"item_id", "mlc", "item", "id"}


def _normalize_column_name(value: str) -> str:
    return str(value or "").strip().lower()


def _normalize_item_id(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def _extract_item_ids_from_excel(file_bytes: bytes) -> dict:
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
        (
            original_col
            for normalized_col, original_col in normalized_map.items()
            if normalized_col in VALID_ITEM_COLUMNS
        ),
        None,
    )

    if not item_col:
        raise HTTPException(
            status_code=400,
            detail="No se encontró una columna válida de item_id. Usa una de: item_id, mlc, item, id",
        )

    rows: list[dict] = []
    seen: set[str] = set()
    duplicate_rows: list[dict] = []
    empty_rows: list[int] = []

    for idx, row in df.iterrows():
        row_number = idx + 2
        raw_item_id = row.get(item_col)
        item_id = _normalize_item_id(raw_item_id)

        if not item_id:
            empty_rows.append(row_number)
            continue

        if item_id in seen:
            duplicate_rows.append(
                {
                    "row_number": row_number,
                    "item_id": item_id,
                    "message": "MLC duplicado en el Excel",
                }
            )
            continue

        seen.add(item_id)
        rows.append(
            {
                "row_number": row_number,
                "item_id": item_id,
            }
        )

    if not rows:
        raise HTTPException(
            status_code=400,
            detail="No se encontraron item_id válidos en el Excel",
        )

    return {
        "rows": rows,
        "excel_total_rows": len(df.index),
        "valid_unique_rows": len(rows),
        "duplicate_rows": duplicate_rows,
        "empty_rows": empty_rows,
    }


def _deduplicate_item_ids(item_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_ids: list[str] = []

    for item_id in item_ids:
        clean_id = _normalize_item_id(item_id)
        if not clean_id or clean_id in seen:
            continue
        seen.add(clean_id)
        unique_ids.append(clean_id)

    return unique_ids


async def process_compatibility_exceptions_excel(
    file_bytes: bytes,
    user_id: int | str,
    db_session: AsyncSession,
    access_token: str | None = None,
) -> dict:
    extracted = _extract_item_ids_from_excel(file_bytes)
    rows = extracted["rows"]

    repo = InformedNonCompatibleRepository(db_session)
    ml_results: list[dict] = []
    successful_item_ids: list[str] = []

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

            successful_item_ids.append(item_id)

            ml_results.append(
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
            ml_results.append(
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
            ml_results.append(
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

    db_inserted = 0
    db_updated = 0

    try:
        successful_item_ids = _deduplicate_item_ids(successful_item_ids)

        if successful_item_ids:
            existing_mlcs = await repo.get_existing_mlcs(successful_item_ids)

            to_insert = [mlc for mlc in successful_item_ids if mlc not in existing_mlcs]
            to_update = [mlc for mlc in successful_item_ids if mlc in existing_mlcs]

            db_inserted = await repo.bulk_insert_mlcs(
                to_insert,
                has_exception=True,
            )
            db_updated = await repo.bulk_update_mlcs(
                to_update,
                has_exception=True,
            )

        await db_session.commit()

    except Exception as exc:
        await db_session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Se cargaron excepciones en Mercado Libre, pero falló la persistencia en BD: {exc}",
        ) from exc

    duplicate_results = [
        {
            "row_number": item["row_number"],
            "item_id": item["item_id"],
            "comment": UNIVERSAL_EXCEPTION_COMMENT,
            "success": False,
            "status_code": 409,
            "message": item["message"],
            "response": None,
        }
        for item in extracted["duplicate_rows"]
    ]

    empty_results = [
        {
            "row_number": row_number,
            "item_id": "",
            "comment": UNIVERSAL_EXCEPTION_COMMENT,
            "success": False,
            "status_code": 400,
            "message": "Fila vacía o sin MLC válido",
            "response": None,
        }
        for row_number in extracted["empty_rows"]
    ]

    all_results = ml_results + duplicate_results + empty_results
    all_results.sort(key=lambda x: x["row_number"])

    success_count = sum(1 for x in all_results if x["success"])
    error_count = len(all_results) - success_count

    return {
        "ok": True,
        "total_excel_rows": extracted["excel_total_rows"],
        "total_valid_unique_rows": extracted["valid_unique_rows"],
        "duplicates_in_excel": len(extracted["duplicate_rows"]),
        "empty_rows": len(extracted["empty_rows"]),
        "processed_total": len(rows),
        "success": success_count,
        "errors": error_count,
        "db_inserted": db_inserted,
        "db_updated": db_updated,
        "db_persisted_total": db_inserted + db_updated,
        "universal_comment": UNIVERSAL_EXCEPTION_COMMENT,
        "results": all_results,
    }