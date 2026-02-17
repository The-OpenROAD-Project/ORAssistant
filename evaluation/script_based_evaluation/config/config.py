import os
from dotenv import load_dotenv, dotenv_values
from typing import Optional


def load_environment(env_path: str):
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"The specified .env file does not exist at {env_path}")
    load_dotenv(env_path, override=True)
    config = dotenv_values(env_path)
    api_key: Optional[str] = config.get("GOOGLE_API_KEY")
    if api_key is not None:
        os.environ["GOOGLE_API_KEY"] = api_key
    else:
        raise KeyError("GOOGLE_API_KEY not found in .env file or is None")


def get_config() -> dict[str, str]:
    config_raw = dotenv_values(".env")
    config = {k: v for k, v in config_raw.items() if v is not None}
    return config
