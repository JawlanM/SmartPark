# SmartPark

A cloud parking availability service. It looks at car park camera images, counts empty and occupied spaces with a YOLO object detection model, and returns the car parks with the most free spaces.

Individual project for FIT3184 Cloud Computing at Monash University, deployed on Google Kubernetes Engine (GKE).

## What it does

**For drivers**
- `GET /api/find-carparks`: ranks candidate car parks by available spaces and returns the best ones, with free and occupied counts

**For operators**
- `GET /api/annotate-carpark`: returns a car park image with detected spaces marked
- `GET /api/operator/carpark-status`: current status of each car park
- `GET /api/operator/users-last-30-seconds`: recent unique users
- `GET /api/operator/dashboard`: a generated chart of activity

## How it runs on Google Cloud

- The API runs in Docker and is deployed to GKE from Google Artifact Registry.
- The detection model and about 1,010 parking images live in Google Cloud Storage, not in the image. An init container copies them into the pod at start-up, so the model can be updated without rebuilding the app.
- Pods scale horizontally on CPU, from 1 to 8 replicas, with GKE cluster autoscaling adding nodes when needed.
- A 10-second cache per car park avoids repeating detection, and a semaphore limits how many detections run at once.

## Load testing

Benchmarked with Locust across 16 configurations (1, 2, 4 and 8 pods with 5, 10, 20 and 30 concurrent users), with no failed requests in any run. Response time did not improve in line with pod count, because detection is CPU-bound and pods compete for node CPU, and each pod keeps its own cache.

## Tech stack

Python, FastAPI, Uvicorn, Ultralytics YOLO, OpenCV, Matplotlib, Docker, Kubernetes, GKE, Google Cloud Storage, Artifact Registry, Cloud Build, Locust, pytest.

## Running locally

```bash
git clone https://github.com/JawlanM/SmartPark.git
cd SmartPark
pip install -r requirements.txt
uvicorn app:app --port 8000
```

Settings come from environment variables:

| Variable | Purpose |
|---|---|
| `IMAGES_FOLDER` | Folder of car park images |
| `NUM_CARPARKS` | Number of car parks to simulate |
| `CACHE_TTL_SECS` | How long to reuse a detection result |

Tests:

```bash
pytest test
```

## Project structure

```
app.py                 API routes
carpark_service.py     ranking, caching and concurrency limit
yolo_service.py        model loading and detection
dashboard_service.py   operator dashboard chart
logging_service.py     request history
k8s/                   Kubernetes deployment and service
Dockerfile
```
