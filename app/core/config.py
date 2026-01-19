from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str
    log_level: str
    environment: str
    sam_model_path: str
    sam_model_download_url: str
    base_url: str
    api_key: str
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
