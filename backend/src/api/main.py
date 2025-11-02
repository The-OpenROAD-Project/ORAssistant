import os
from dotenv import load_dotenv

load_dotenv()

if os.getenv("USE_CUDA", "false").lower() != "true":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

from fastapi import FastAPI
from .routers import healthcheck, helpers, ui, conversations
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.database.config import init_database
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Initializing database connection...")
    init_database()
    yield
    logger.info("Shutting down...")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(healthcheck.router)
app.include_router(helpers.router)
app.include_router(ui.router)
app.include_router(conversations.router)
