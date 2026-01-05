import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import requests

from app.core.config import settings
from app.core.constants import COMPLETED, ERROR, PROCESSING, X_API_KEY
from app.core.logger import logger
from app.services.aws_client import get_aws_client
from app.services.segmentation import run_segmentation
from app.utils.image_downloader import download_image

sqs_client = get_aws_client("sqs")
executor = ThreadPoolExecutor(max_workers=4)


def process_job(job_data: Dict[str, Any]) -> None:
    """Process a single segmentation job"""
    uuid = job_data["uuid"]
    image_url = job_data["imageUrl"]

    logger.info(f"Processing job {uuid} with image {image_url}")

    try:
        # Fire-and-forget: notify app server in background that job is now being processed
        executor.submit(update_app_server, uuid, PROCESSING)

        # Download image
        image = download_image(image_url)

        # Apply SAM-2 segmentation
        segments_data = run_segmentation(image, uuid)

        # Update App Server with results
        update_app_server(uuid, COMPLETED, segments_data)

    except Exception as e:
        logger.error(f"Failed to process job {uuid}: {e}")
        # Notify app server of failure
        update_app_server(uuid, ERROR)
        # Re-raise the exception so the caller knows the job failed
        raise


def update_app_server(
    uuid: str, status: str, masks: Optional[List[Dict[str, Any]]] = None
) -> None:
    url = f"{settings.app_server_url}/{uuid}"

    payload: Dict[str, Any] = {"status": status}

    if masks is not None:
        payload["masks"] = masks

    headers = {
        "Content-Type": "application/json",
        X_API_KEY: settings.app_server_api_key,
    }

    try:
        response = requests.patch(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(
            f"Successfully updated app server for job {uuid} with status {status}"
        )
    except Exception as e:
        logger.error(f"Failed to update app server for job {uuid}: {e}")


def poll_queue():
    """Main polling loop"""
    logger.info("Starting SQS polling worker")

    while True:
        try:
            # Poll SQS queue every 10 seconds. Also if a message is received, it will be processed immediately.
            response = sqs_client.receive_message(
                QueueUrl=settings.sqs_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,
            )

            messages = response.get("Messages", [])

            if not messages:
                logger.info("No messages found, polling again...")
                continue

            for message in messages:
                receipt_handle = message["ReceiptHandle"]
                job_uuid = None  # Track UUID for error reporting

                try:
                    body = json.loads(message["Body"])
                    job_uuid = body.get("uuid")  # Extract UUID early for error handling
                    logger.info(f"Received SQS job: {body}")

                    # Process the job
                    process_job(body)

                    # Only delete message from queue if job processing was successful
                    sqs_client.delete_message(
                        QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt_handle
                    )

                    logger.info(
                        f"Job {job_uuid} completed successfully and removed from queue"
                    )

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in SQS message: {e}")
                    # Delete malformed message
                    sqs_client.delete_message(
                        QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt_handle
                    )

                except Exception as e:
                    logger.error(f"Failed to process job {job_uuid}: {e}")

                    # Job failed - do NOT delete the message from queue
                    # SQS will automatically retry the message based on the queue's retry policy
                    # The process_job function should have already updated the app server with ERROR status

        except Exception as e:
            logger.error(f"Error in polling loop: {e}")


if __name__ == "__main__":
    poll_queue()
