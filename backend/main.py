import os
import uvicorn
from dotenv import load_dotenv

from src.api.main import app

load_dotenv()


def main() -> None:
    uvicorn.run(
        app, host='127.0.0.1', port=8000, workers=int(os.getenv('BACKEND_WORKERS', 1))
    )


if __name__ == '__main__':
    main()
