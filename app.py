from fastapi import FastAPI, HTTPException
from yolo_service import find_parking, annotate_parking
from carpark_service import (find_best_carparks, 
                             carparks,
                             get_carpark_by_id,
                             take_photo
                             )
import time
from logging_service import log_request, request_logs, get_users_last_30_seconds


app = FastAPI()

@app.get("/")
def root():
    return {"Message": "SmartPark API running"}

@app.get("/api/test")
def test_parking():
    result = find_parking("./images/img305.jpg")
    return result

@app.get("/api/test-logs")
def test_logs():
    return request_logs

@app.get("/api/find-carparks")
def find_carparks(uuid: str, n: int):

    if n < 1:
        log_request(
            uuid=uuid,
            endpoint="/api/find-carparks",
            requested_n=n,
            status="failed",
            severity="ERROR"
        )

        raise HTTPException(
            status_code=400,
            detail="n must be greater than 0"
        )

    if 2 * n > len(carparks):
        log_request(
            uuid=uuid,
            endpoint="/api/find-carparks",
            requested_n=n,
            status="failed",
            severity="ERROR"
        )

        raise HTTPException(
            status_code=400,
            detail="Not enough car parks available to query 2*n car parks"
        )

    start_time = time.perf_counter()

    results = find_best_carparks(n)

    log_request(
        uuid=uuid,
        endpoint="/api/find-carparks",
        requested_n=n,
        status="success"
    )

    end_time = time.perf_counter()

    inference_time_ms = (end_time - start_time) * 1000

    return {
        "uuid": uuid,
        "status": "success",
        "msg": "success",
        "speed_inference": f"{inference_time_ms:.2f} ms",
        "requested_n": n,
        "results": results
    }

@app.get("/api/annotate-carpark")
def annotate_carpark(carpark_id: str):

    carpark = get_carpark_by_id(carpark_id)

    if carpark is None:
        raise HTTPException(
            status_code=404,
            detail="Car park not found"
        )

    img_path = take_photo()

    img_base64 = annotate_parking(img_path)

    return{
        "carpark_id": carpark_id,
        "status": "success",
        "msg": "success",
        "image_base64": img_base64
    }

@app.get("/api/operator/users-last-30-seconds")
def  user_last_30_seconds():
    user_count = get_users_last_30_seconds()

    return{
        "status": "success",
        "user_last_30_seconds": user_count
    }