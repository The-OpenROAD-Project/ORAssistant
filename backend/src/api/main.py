from fastapi import FastAPI

from .routers import chains
from .routers import graphs

app = FastAPI()

app.include_router(chains.router)
app.include_router(graphs.router)
