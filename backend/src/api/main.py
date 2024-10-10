from fastapi import FastAPI

from backend.src.api.routers import graphs, healthcheck

app = FastAPI()

app.include_router(healthcheck.router)
app.include_router(graphs.router)
