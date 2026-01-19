from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str
    log_level: str
    environment: str
    sam_model_path: str
    sam_model_s3_url: str
    base_url: str

    # API Security
    api_key: str = Field(..., description="API key for authentication")

    # Database settings
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
