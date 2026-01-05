import os

import requests

from app.core.config import settings
from app.core.logger import logger

WEIGHT_S3_URL = settings.sam_model_s3_url
WEIGHT_PATH = settings.sam_model_path
TMP_PATH = WEIGHT_PATH + ".tmp"


def download_weights():
    os.makedirs(os.path.dirname(WEIGHT_PATH), exist_ok=True)

    if os.path.exists(WEIGHT_PATH):
        logger.info("Model weights already present. Skipping download.")
        return

    logger.info(f"Downloading SAM model weights from {WEIGHT_S3_URL}")
    try:
        with requests.get(WEIGHT_S3_URL, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(TMP_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        os.rename(TMP_PATH, WEIGHT_PATH)
        logger.info("Model weights downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download model weights: {e}")
        if os.path.exists(TMP_PATH):
            os.remove(TMP_PATH)
        raise


if __name__ == "__main__":
    download_weights()
