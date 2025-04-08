from fastapi import FastAPI
from .routers import graphs, healthcheck, helpers

app = FastAPI()

app.include_router(healthcheck.router)
app.include_router(graphs.router)
app.include_router(helpers.router)
