import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import NoCredentialsError

from app.core.config import settings
from app.core.logger import logger


def get_aws_client(service_name: str) -> BaseClient:
    is_local = settings.environment != "production"

    try:
        if is_local:
            logger.info(
                f"[AWS:{service_name}] Using local AWS profile: {settings.aws_profile}"
            )
            session = boto3.Session(
                profile_name=settings.aws_profile, region_name=settings.aws_region
            )
            return session.client(
                service_name, config=Config(region_name=settings.aws_region)
            )
        else:
            logger.info(f"[AWS:{service_name}] Using IAM role credentials (production)")
            return boto3.client(service_name, region_name=settings.aws_region)
    except NoCredentialsError as e:
        logger.error(f"[AWS:{service_name}] No credentials found: {e}")
        raise
    except Exception as e:
        logger.error(f"[AWS:{service_name}] Failed to create client: {e}")
        raise
