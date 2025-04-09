import os

from fastapi import APIRouter, HTTPException, Header, Depends, status
from typing import Annotated
from api.v1.routes import v1_router

# Проверка апи ключа
API_KEY = os.getenv("API_KEY")

async def validate_apikey(api_key: Annotated[str, Header(description="API key")] = None):
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured"
        )
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API Key"
        )
api_key_dependency = Depends(validate_apikey)



api_router = APIRouter(prefix="/api", tags=["API"], dependencies=[api_key_dependency])
api_router.include_router(v1_router)