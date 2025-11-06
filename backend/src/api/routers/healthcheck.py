from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str


@router.get("/healthcheck", response_model=HealthCheckResponse)
async def healthcheck() -> HealthCheckResponse:
    """
    An endpoint to verify that the API is up and running.

    Returns:
        HealthCheckResponse with status "ok"

    Example Response:
        ```json
        {
            "status": "ok"
        }
        ```
    """
    return HealthCheckResponse(status="ok")
