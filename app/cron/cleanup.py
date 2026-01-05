import shutil
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from app.core.logger import logger

ASSETS_DIR = Path("assets")
AGE_THRESHOLD_SECONDS = 3600  # 1 hour


def add_cleanup_cron(app: FastAPI):
    @app.on_event("startup")
    @repeat_every(seconds=3600)  # Every hour
    async def clean_old_assets():
        now = time.time()

        if not ASSETS_DIR.exists():
            logger.warning("Assets directory does not exist.")
            return

        deleted = 0
        for item in ASSETS_DIR.iterdir():
            if item.is_dir():
                created_time = item.stat().st_ctime
                if now - created_time > AGE_THRESHOLD_SECONDS:
                    try:
                        shutil.rmtree(item)
                        logger.info(f"Deleted old folder: {item}")
                        deleted += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {item}: {e}")

        logger.info(f"Cleanup complete. Deleted {deleted} folders.")
