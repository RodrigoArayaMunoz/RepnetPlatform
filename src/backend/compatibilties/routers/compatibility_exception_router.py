from fastapi import APIRouter, File, HTTPException, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db_session
from services.compatibility_exception_service import (
    UNIVERSAL_EXCEPTION_COMMENT,
    process_compatibility_exceptions_excel,
)
from services.token_store import token_store

router = APIRouter(
    prefix="/compatibility-exceptions",
    tags=["compatibility-exceptions"],
)


@router.post("/upload")
async def upload_compatibility_exceptions_excel(
    file: UploadFile = File(...),
    db_session: AsyncSession = Depends(get_db_session),
):
    user_id = token_store.first_user_id()
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="No hay cuenta de Mercado Libre conectada",
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo no válido")

    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un Excel .xlsx o .xls",
        )

    file_bytes = await file.read()

    result = await process_compatibility_exceptions_excel(
        file_bytes=file_bytes,
        user_id=str(user_id),
        db_session=db_session,
    )

    return {
        **result,
        "filename": file.filename,
        "comment_used": UNIVERSAL_EXCEPTION_COMMENT,
    }