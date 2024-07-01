from fastapi import FastAPI

from .routers import chains

app = FastAPI()

app.include_router(chains.router)
