# Meta Segmentation Service

A RESTful FastAPI application for automatic instance segmentation using Meta's **SAM-2** model.

This service provides a complete API for submitting segmentation jobs, tracking their status, and retrieving results. Jobs are processed asynchronously in the background, with status and results stored in PostgreSQL.

---

## Tech Stack

- **FastAPI** – High-performance async Python backend  
- **Meta SAM-2** – Advanced image segmentation model  
- **PostgreSQL** – Database for job tracking and results
- **Docker & Docker Compose** – Containerized for CPU and GPU environments  
- **Local Storage** – Masks saved to disk and served via FastAPI  
- **Background Cleanup** – Scheduled job to delete files every hour  
- **Structured Logging**

---

## Architecture Overview

```
Client → POST /api/v1/jobs (submit job)
       → GET /api/v1/jobs/{uuid} (check status & get results)
       
API Service:
  - Creates job in PostgreSQL (status: PENDING)
  - Processes job asynchronously (status: PROCESSING)
  - Downloads image
  - Runs SAM-2 segmentation
  - Saves masks to local disk
  - Updates job in database (status: COMPLETED/ERROR)
  - Serves masks via FastAPI static files
```

---

## Getting Started

Clone the repository:

```bash
git clone git@github.com:ehsaantech/meta-sam-segmentation-api.git
cd meta-sam-segmentation-api
```

### Run with CPU (CPU-only)

> For local testing and development without GPU

```bash
docker compose -f docker-compose-cpu.yml up --build
```

This will start:
- PostgreSQL database on port 5432
- FastAPI application on port 8000

### Run with GPU (GPU-enabled)

> Requires a CUDA-compatible GPU and NVIDIA Container Toolkit installed

```bash
docker compose -f docker-compose-gpu.yml up --build
```

---

## Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env
# Application
app_name=SAM Segmentation API
log_level=INFO
environment=development
base_url=http://localhost:8000

# API Security
api_key=your-secret-api-key-here

# SAM Model
sam_model_path=/app/models/weights/sam_vit_h.pth
sam_model_s3_url=https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=sam_segmentation
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

---

## API Endpoints

> **Note:** All endpoints except `/health` require API key authentication via the `X-API-Key` header.

### Authentication

All API endpoints (except `/health`) require an API key to be provided in the request header:

```
X-API-Key: your-secret-api-key-here
```

### Create Job

Submit a new segmentation job. A unique UUID will be automatically generated for each job.

**POST** `/api/v1/jobs`

**Headers:**
```
X-API-Key: your-secret-api-key-here
Content-Type: application/json
```

**Request Body:**
```json
{
  "image_url": "https://cdn.example.com/images/sample.jpg"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "uuid": "abc123-def456-ghi789",
  "image_url": "https://cdn.example.com/images/sample.jpg",
  "status": "PENDING",
  "error_message": null,
  "masks": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "completed_at": null
}
```

### Get Job Status

Retrieve job status and results.

**GET** `/api/v1/jobs/{job_uuid}`

**Headers:**
```
X-API-Key: your-secret-api-key-here
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "uuid": "abc123-def456-ghi789",
  "image_url": "https://cdn.example.com/images/sample.jpg",
  "status": "COMPLETED",
  "error_message": null,
  "masks": [
    {
      "segment_id": 0,
      "mask_url": "http://localhost:8000/assets/abc123-def456-ghi789/mask_images/mask_000.png",
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
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z",
  "completed_at": "2024-01-15T10:35:00Z"
}
```

**Job Status Values:**
- `PENDING` - Job created, waiting to be processed
- `PROCESSING` - Job is currently being processed
- `COMPLETED` - Job completed successfully
- `ERROR` - Job failed (check `error_message` field)

### List Jobs

List all jobs with pagination and optional status filter.

**GET** `/api/v1/jobs?page=1&page_size=10&status=COMPLETED`

**Headers:**
```
X-API-Key: your-secret-api-key-here
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 10, max: 100)
- `status` (optional): Filter by status (PENDING, PROCESSING, COMPLETED, ERROR)

**Response:** `200 OK`
```json
{
  "jobs": [...],
  "total": 42,
  "page": 1,
  "page_size": 10
}
```

### Delete Job

Delete a job from the database.

**DELETE** `/api/v1/jobs/{job_uuid}`

**Headers:**
```
X-API-Key: your-secret-api-key-here
```

**Response:** `204 No Content`

### Health Check

**GET** `/health`

> **Note:** This endpoint is public and does not require authentication.

**Response:** `200 OK`
```json
{
  "status": "ok"
}
```

---

## Segmentation Workflow

1. **Client** submits a job via `POST /api/v1/jobs` with an image URL
2. **API** creates a job record in PostgreSQL with status `PENDING`
3. **Background Task** processes the job:
   - Updates status to `PROCESSING`
   - Downloads the image from the provided URL
   - Runs SAM-2 automatic segmentation
   - Saves mask images to `assets/{uuid}/mask_images/`
   - Updates job status to `COMPLETED` with segmentation results
4. **Client** polls `GET /api/v1/jobs/{uuid}` to check status and retrieve results
5. **Masks** are served via static files at `/assets/{uuid}/mask_images/mask_XXX.png`

---

## Directory Structure

```
meta-sam-segmentation-api/
├── app/
│   ├── core/              # Configuration, database, logging
│   ├── models/            # SQLAlchemy database models
│   ├── schemas/           # Pydantic request/response schemas
│   ├── services/          # Business logic (segmentation, job processing)
│   ├── utils/             # Utility functions
│   ├── cron/              # Scheduled tasks (cleanup)
│   └── main.py            # FastAPI application
├── assets/                # Stored masks (served via /assets)
├── models/                # SAM model weights
├── scripts/               # Download weights script
├── base-requirements.txt  # ML dependencies
├── app-requirements.txt   # Application dependencies
├── .env                   # Environment configuration
├── Dockerfile.cpu        # CPU-only Dockerfile
├── Dockerfile.gpu        # GPU-enabled Dockerfile
├── docker-compose-cpu.yml # CPU setup
└── docker-compose-gpu.yml # GPU setup
```

---

## Development Notes

* **Segmentation Logic:** `app/services/segmentation.py`
* **Job Processing:** `app/services/job_processor.py` (background tasks)
* **Database Models:** `app/models/job.py`
* **API Routers:** `app/api/v1/` (jobs, health)
* **Security:** `app/core/security.py` (API key authentication)
* **Main App:** `app/main.py` (minimal setup with router includes)
* **Model Weights:** Downloaded at container startup to `/models/weights/`
* **Mask Storage:** Output masks saved locally to `assets/{uuid}/mask_images/`
* **FastAPI Static Serving:** Masks served via `/assets/{uuid}/mask_images/mask_XXX.png`
* **Cleanup Job:** Periodic task (hourly) removes old asset folders
* **Database:** PostgreSQL with automatic table creation on startup

---

## Database Schema

The `jobs` table stores:
- `id`: Primary key
- `uuid`: Unique job identifier
- `image_url`: Source image URL
- `status`: Job status (PENDING, PROCESSING, COMPLETED, ERROR)
- `error_message`: Error details (if status is ERROR)
- `masks`: JSON array of segmentation results
- `created_at`: Job creation timestamp
- `updated_at`: Last update timestamp
- `completed_at`: Completion timestamp (if completed)

---

## Cleaning Up

Stop and remove containers:

```bash
# CPU setup
docker compose -f docker-compose-cpu.yml down

# GPU setup
docker compose -f docker-compose-gpu.yml down

# Remove volumes (including database data)
docker compose -f docker-compose-cpu.yml down -v
# or
docker compose -f docker-compose-gpu.yml down -v
```

---

## Scheduled Cleanup (Every Hour)

A background task runs every hour to delete folders inside `/assets` that are older than 1 hour to free up disk space. This does not affect job records in the database.

---

## API Documentation

Once the service is running, interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
