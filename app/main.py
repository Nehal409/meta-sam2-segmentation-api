from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.logger import logger
from app.cron.cleanup import add_cleanup_cron

app = FastAPI(title="SAM-2 Image Segmentation Worker")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

add_cleanup_cron(app)


@app.get("/health")
def health_check():
    logger.info("Health check called.")
    return {"status": "ok"}
