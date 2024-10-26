from fastapi import FastAPI

from .routers import healthcheck

app = FastAPI()

app.include_router(healthcheck.router)
