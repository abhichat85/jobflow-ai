from pydantic_settings import BaseSettings
from pathlib import Path

# Resolve .env relative to this file so it works regardless of CWD.
# config.py lives at  backend/app/config.py → root is three levels up.
_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = str(_ROOT / ".env")


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///data/db/jobflow.sqlite"
    redis_url: str = "redis://localhost:6379/0"
    firecrawl_api_key: str = ""
    tavily_api_key: str = ""
    data_dir: Path = Path("data")
    app_secret_key: str = "dev-secret-change-me-in-prod-must-be-32-chars-or-more"

    # env_ignore_empty: treat empty-string env vars (e.g. ANTHROPIC_API_KEY="" inherited
    # from a parent shell) as unset, so the .env file value wins.
    model_config = {
        "env_file": _ENV_FILE,
        "env_file_encoding": "utf-8",
        "env_ignore_empty": True,
    }


settings = Settings()
