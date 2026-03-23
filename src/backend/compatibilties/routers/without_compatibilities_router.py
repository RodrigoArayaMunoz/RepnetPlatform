from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db_session
#from dependencies.auth import get_current_user_id, get_optional_access_token
from services.without_compatibilities_service import get_without_compatibilities_with_titles
from services.token_store import token_store
from services.ml_client import ml_client

router = APIRouter(prefix="/publications", tags=["publications"])


@router.get("/without-compatibilities-details")
async def without_compatibilities_details(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=20),
    db_session: AsyncSession = Depends(get_db_session),
):
    
        user_id = token_store.first_user_id()
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="No hay cuenta de Mercado Libre conectada",
        )

        access_token = await ml_client.get_valid_token(user_id)
        

        return await get_without_compatibilities_with_titles(
            db_session=db_session,
            user_id=user_id,
            access_token=access_token,
            page=page,
            page_size=page_size,
        )