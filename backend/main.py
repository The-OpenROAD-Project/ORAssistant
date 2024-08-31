from src.api.main import app
import uvicorn

import os
from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    uvicorn.run(
        app, host='127.0.0.1', port=8000, workers=int(os.getenv('BACKEND_WORKERS', 1))
    )


if __name__ == '__main__':
    main()