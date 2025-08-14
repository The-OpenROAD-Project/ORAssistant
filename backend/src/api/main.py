from fastapi import FastAPI
from .routers import graphs, healthcheck, helpers, ui
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8001",  # mock endpoint
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(healthcheck.router)
app.include_router(graphs.router)
app.include_router(helpers.router)
app.include_router(ui.router)
