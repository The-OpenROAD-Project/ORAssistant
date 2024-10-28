import os
import uvicorn
from dotenv import load_dotenv

from backend.src.api.main import app

load_dotenv()


def main() -> None:
    uvicorn.run(
        app, host=os.getenv('BACKEND_URL','0.0.0.0'), port=8000, workers=int(os.getenv('BACKEND_WORKERS', 1))
    )


if __name__ == "__main__":
    main()
