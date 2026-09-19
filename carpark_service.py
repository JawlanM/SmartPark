import os
import random
import time
import threading
from yolo_service import find_parking

imgs_folder = "./images"

YOLO_CONCURRENCY_LIMIT = 2
yolo_semaphore = threading.Semaphore(YOLO_CONCURRENCY_LIMIT)

NUM_carparks = int(os.getenv("NUM_CARPARKS", "10"))

CACHE_TTL_secs = int(os.getenv("CACHE_TTL_SECS", "10"))

carpark_cache = {}

carparks = []

for i in range(1, NUM_carparks + 1):
    carparks.append({
        "carpark_id": f"CBD_{i:03}",
        "name": f"CBD Car Park {i}",
        "image_path": f"./images/img{i:03}.jpg"
    })

def take_photo():
    img_files = [
        f for f in os.listdir(imgs_folder)
        if f.lower().endswith(".jpg")
    ]

    if not img_files:
        raise FileNotFoundError("No parking(.jpg) images found in the images folder.")
    random_image = random.choice(img_files)

    return os.path.join(imgs_folder, random_image)

def analyse_carpark(carpark):
    
    carpark_id = carpark["carpark_id"]

    current_time = time.monotonic()

    # Check if the carpark is in the cache and if the cache is still valid
    if carpark_id in carpark_cache:
        cached_entry = carpark_cache[carpark_id]

        cached_age = current_time - cached_entry["timestamp"]

        if cached_age < CACHE_TTL_secs:
            cached_result = cached_entry["result"].copy()
            cached_result["cached"] = True
            return cached_result

    img_path = carpark["image_path"]
    with yolo_semaphore:
        parking_result = find_parking(img_path)

    # If not in cache or cache is expired, analyze the carpark
    result = {
        "carpark_id": carpark["carpark_id"],
        "name": carpark["name"],
        "available_parking": parking_result["available_parking"],
        "occupied_parking": parking_result["occupied_parking"],
        "total_parking": parking_result["total_parking"],
        "occupied_percentage": parking_result["occupied_percentage"],
        "cached": False
    }

    # Update the cache with the new result and timestamp
    carpark_cache[carpark_id] = {
        "result": result.copy(),
        "timestamp": time.monotonic()
    }

    return result

def find_best_carparks(n):

    SUM_target_carparks = 2 * n

    selected_carparks = random.sample(carparks, SUM_target_carparks)

    target_carparks = []

    for carpark in selected_carparks:
        result = analyse_carpark(carpark)
        target_carparks.append(result)

    target_carparks.sort(
        key=lambda carpark: carpark["available_parking"],
        reverse=True
    )

    return target_carparks[:n]

def get_carpark_by_id(carpark_id):
    for carpark in carparks:
        if carpark["carpark_id"] == carpark_id:
            return carpark

    return None


def get_all_carpark_status():
    results = []

    for carpark in carparks:
        result = analyse_carpark(carpark)

        results.append({
            "carpark_id": result["carpark_id"],
            "name": result["name"],
            "available_parking": result["available_parking"],
            "occupied_parking": result["occupied_parking"],
            "total_parking": result["total_parking"],
            "occupied_percentage": result["occupied_percentage"],
            "cached": result["cached"]
        })

    return results


