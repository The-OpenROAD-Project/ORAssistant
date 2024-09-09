from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str


@router.get('/healthcheck', response_model=HealthCheckResponse)
async def healthcheck() -> HealthCheckResponse:
    return HealthCheckResponse(status='ok')
