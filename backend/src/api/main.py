from fastapi import FastAPI

from .routers import graphs

app = FastAPI()

app.include_router(graphs.router)
