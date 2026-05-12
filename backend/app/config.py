from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///data/db/jobflow.sqlite"
    redis_url: str = "redis://localhost:6379/0"
    firecrawl_api_key: str = ""
    tavily_api_key: str = ""
    data_dir: Path = Path("data")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
