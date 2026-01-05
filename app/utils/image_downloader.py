from io import BytesIO

import requests
from PIL import Image

from app.core.logger import logger


def download_image(image_url: str) -> Image.Image:
    logger.info(f"Downloading image from {image_url}")
    response = requests.get(image_url)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))
