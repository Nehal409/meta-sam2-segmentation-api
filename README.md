# Meta Segmentation Service

A modular FastAPI application for automatic instance segmentation using Meta's **SAM-2** model.

This backend service listens for segmentation jobs sent via an app server, processes them using SAM-2, stores output masks locally, and reports the result back to the app server.

---

## Tech Stack

- **FastAPI** – High-performance async Python backend  
- **Meta SAM-2** – Advanced image segmentation model  
- **Docker & Docker Compose** – Containerized for dev (CPU) and prod (GPU)  
- **AWS SQS** – Message queue for job distribution  
- **Local Storage** – Masks saved to disk and served via FastAPI  
- **Background Cleanup** – Scheduled job to delete files every hour  
- **Structured Logging**

---

## Architecture Overview

```

Client → App Server → SQS → \[SAM Segmentation Worker]
↓
\- Downloads image
\- Runs segmentation (SAM-2)
\- Saves masks on server machine temporarily
\- Serves masks over FastAPI
\- Sends result (mask URLs + boxes) to App Server

````

---

## Getting Started

Clone the repository:

```bash
git clone git@github.com:ehsaantech/customscape-sam-segmentation-api.git
cd customscape-sam-segmentation-api
````

### Run in Development (CPU-only)

> For local testing and development

```bash
docker compose -f docker-compose-dev.yml up --build
```

### Run in Production (GPU-enabled)

> Requires a CUDA-compatible GPU and NVIDIA Container Toolkit installed

```bash
docker compose up --build
```

---

## Environment Configuration

Create a `.env` file in the root directory:

Local development uses `~/.aws/credentials`; in production, use IAM role via EC2 instance.

---

## Segmentation Workflow

1. **Client** calls auto mask API on the **App Server**
2. App Server puts a job on **SQS** with `uuid` and `image_url`
3. **This SAM service**:

   * Polls the queue
   * Downloads the image
   * Runs SAM-2 segmentation
   * Saves masks to local disk (e.g., `assets/uuid/mask0.png`)
   * Serves them via FastAPI at `/assets/{uuid}/{mask}.png`
   * Sends results back to App Server using:

     ```
     PATCH /api/v1/re-imagine/auto-mask/{uuid}
     ```

---

## Example Job Payloads

### From App Server → SQS

```json
{
  "uuid": "abc123",
  "image_url": "https://cdn.example.com/images/sample.jpg"
}
```

### Sent Back → App Server

```json
{
  "uuid": "abc123",
  "status": "completed",
  "segments": [
    {
      "segment_id": 0,
      "mask_url": "http://your-sam-api.com/assets/abc123/mask_images/mask_000.png",
      "bbox": {
        "x": 120,
        "y": 150,
        "width": 80,
        "height": 60
      },
      "area": 4523,
      "stability_score": 0.92,
      "predicted_iou": 0.88,
      "center_point": {
        "x": 160,
        "y": 180
      }
    }
  ]
}
```
---

## Directory Structure

```
customscape-sam-segmentation-api/
├── app/                    # FastAPI app
├── assets/                 # Stored masks (served via /assets)
├── models/                 # SAM model weights
├── scripts/                # Download + wait logic
├── docker/
│   ├── dev/
│   │   └── Dockerfile, docker-compose.yml
│   └── prod/
│       └── 
├── base-requirements.txt   # Shared packages
├── app-requirements.txt    # App packages
├── .env                    # Environment config
├── Dockerfile 
├── Dockerfile.dev
├── docker-compose.yml 
├── docker-compose-dev.yml
```

---

## Development Notes

* **Segmentation Logic:** `app/services/segmentation.py`
* **Model Weights:** Downloaded at container startup to `/models/weights/`
* **Mask Storage:** Output masks saved locally to `assets/{uuid}/`
* **FastAPI Static Serving:** Masks served via `/assets/{uuid}/mask_images/maskX.png`
* **Cleanup Job:** Periodic task (e.g., hourly) removes old asset folders
* **Worker Polling:** `app/worker.py` polls SQS and triggers segmentation

---

## Cleaning Up

Stop and remove containers:

```bash
# Development
docker compose -f docker-compose-dev.yml down

# Production
docker compose down
```

---

## Scheduled Cleanup (Every Hour)

A background task runs every hour to delete folders inside `/assets` that are older than a threshold (e.g., 1 hour) to free up disk space.

---
