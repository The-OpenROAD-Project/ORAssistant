from fastapi import FastAPI
from .routers import graphs, healthcheck,chains

app = FastAPI()

app.include_router(healthcheck.router)
app.include_router(graphs.router)
app.include_router(chains.router)
