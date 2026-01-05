from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str
    log_level: str
    mask_bucket_name: str
    sqs_queue_url: str
    app_server_url: str
    aws_region: str
    aws_profile: Optional[str] = None
    environment: str
    sam_model_path: str
    sam_model_s3_url: str
    base_url: str
    app_server_api_key: str

    class Config:
        env_file = ".env"


settings = Settings()
