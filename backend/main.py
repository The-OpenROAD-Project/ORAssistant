import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

if os.getenv("USE_CUDA", "false").lower() != "true":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

from src.api.main import app  # noqa: E402


def main() -> None:
    uvicorn.run(
        app,
        host=os.getenv("BACKEND_URL", "0.0.0.0"),
        port=8000,
        workers=int(os.getenv("BACKEND_WORKERS", 1)),
    )


if __name__ == "__main__":
    main()
